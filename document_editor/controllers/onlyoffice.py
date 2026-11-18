"""ONLYOFFICE integration: real-time co-editing of DMS files.

Flow:
1. /open/<id>    (user)  editor page; loads ONLYOFFICE's api.js.
2. /config/<id>  (user)  signed editor config with the session key.
3. /content/<id> (token) ONLYOFFICE downloads the file once per session.
4. /callback/<id> (JWT)  ONLYOFFICE reports the session state and, on
                         save, the URL of the edited file to store.
5. /unsaved-audit/<id>   browser beacon when an editor leaves unsaved.
"""

import base64
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import jwt
import requests

from odoo import _, http
from odoo.http import request

from .common import get_file_binary, get_param, json_response, text_response

_logger = logging.getLogger(__name__)

OOXML = "application/vnd.openxmlformats-officedocument."

# Extension -> ONLYOFFICE editor and how to validate a returned file.
OFFICE_FILE_TYPES = {
    "docx": {
        "document_type": "word",
        "mimetype": OOXML + "wordprocessingml.document",
        "label": "DOCX",
        "binary_type": "ooxml",
    },
    "md": {
        "document_type": "word",
        "mimetype": "text/markdown; charset=utf-8",
        "label": "Markdown",
        "binary_type": "text",
    },
    "xlsx": {
        "document_type": "cell",
        "mimetype": OOXML + "spreadsheetml.sheet",
        "label": "XLSX",
        "binary_type": "ooxml",
    },
    "csv": {
        "document_type": "cell",
        "mimetype": "text/csv; charset=utf-8",
        "label": "CSV",
        "binary_type": "text",
    },
    "pdf": {
        "document_type": "pdf",
        "mimetype": "application/pdf",
        "label": "PDF",
        "binary_type": "pdf",
    },
    "pptx": {
        "document_type": "slide",
        "mimetype": OOXML + "presentationml.presentation",
        "label": "PPTX",
        "binary_type": "ooxml",
    },
}

# ONLYOFFICE downloads the file once, when a session starts.
CONTENT_TOKEN_LIFETIME = timedelta(hours=24)
CALLBACK_TOKEN_LIFETIME = timedelta(hours=24)


def get_extension(filename):
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


class DocumentEditorController(http.Controller):
    # Kept as an attribute for code that used to read it from here.
    OFFICE_FILE_TYPES = OFFICE_FILE_TYPES

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _get_editor_secret(self):
        return get_param("document_editor.onlyoffice_jwt_secret")

    def _get_office_file_info(self, filename):
        """ONLYOFFICE information for a supported file, else None."""
        return OFFICE_FILE_TYPES.get(get_extension(filename))

    def _validate_binary(self, binary, file_info, extension):
        """Check a file returned by ONLYOFFICE looks like its type:
        OOXML files are ZIP packages, PDF starts with %PDF, CSV/MD are
        UTF-8 text."""
        if not binary:
            raise ValueError("ONLYOFFICE returned an empty file.")

        binary_type = file_info["binary_type"]

        if binary_type == "ooxml" and not binary.startswith(b"PK"):
            raise ValueError(
                f"ONLYOFFICE returned invalid {extension.upper()} data."
            )

        if binary_type == "pdf" and not binary.startswith(b"%PDF"):
            raise ValueError("ONLYOFFICE returned invalid PDF data.")

        if binary_type == "text":
            try:
                binary.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(
                    f"ONLYOFFICE returned invalid UTF-8 "
                    f"{extension.upper()} data."
                ) from error

    # ---------------------------------------------------------
    # CONTENT TOKEN (ONLYOFFICE -> /content)
    # ---------------------------------------------------------

    def _sign_content(self, file_record, expires, secret):
        message = f"{file_record.id}:{file_record.checksum}:{expires}".encode()
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    def _make_token(self, file_record):
        """Token for ONLYOFFICE to download the current file. Bound to
        this file version and expiring, so a leaked editor config does
        not grant download access forever."""
        secret = self._get_editor_secret()

        if not secret:
            return False

        expires = int(
            (datetime.now(timezone.utc) + CONTENT_TOKEN_LIFETIME).timestamp()
        )
        return f"{expires}.{self._sign_content(file_record, expires, secret)}"

    def _check_token(self, file_record, token):
        secret = self._get_editor_secret()
        expires, _sep, signature = (token or "").partition(".")

        if not (secret and expires.isdigit() and signature):
            return False

        if int(expires) < datetime.now(timezone.utc).timestamp():
            return False

        return hmac.compare_digest(
            signature, self._sign_content(file_record, int(expires), secret)
        )

    # ---------------------------------------------------------
    # CALLBACK AUTHENTICATION (ONLYOFFICE -> /callback)
    # ---------------------------------------------------------

    def _make_callback_token(self, file_record):
        """Our own signed token in the callback URL; it also records
        which user opened the editor."""
        secret = self._get_editor_secret()

        if not secret:
            return False

        payload = {
            "purpose": "dms_callback",
            "file_id": file_record.id,
            "user_id": request.env.user.id,
            "exp": datetime.now(timezone.utc) + CALLBACK_TOKEN_LIFETIME,
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    def _decode_callback_token(self, file_record, token):
        """Payload of our callback token if valid for this file."""
        secret = self._get_editor_secret()

        if not secret or not token:
            return False

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return False

        if payload.get("purpose") != "dms_callback":
            return False

        try:
            token_file_id = int(payload.get("file_id", 0))
        except (TypeError, ValueError):
            return False

        return payload if token_file_id == file_record.id else False

    def _get_bearer_token(self):
        """JWT from the ONLYOFFICE Authorization header."""
        authorization = request.httprequest.headers.get("Authorization") or ""
        scheme, _sep, value = authorization.partition(" ")

        if scheme.lower() != "bearer" or not value.strip():
            return False

        return value.strip()

    def _is_file_callback_key(self, file_record, key):
        """Whether an ONLYOFFICE document key belongs to this DMS file."""
        prefix = f"dms-{file_record.id}-"
        return isinstance(key, str) and key.startswith(prefix) and len(key) > len(prefix)

    def _decode_onlyoffice_callback_token(self, file_record, token, callback_data):
        """Validate a JWT signed by ONLYOFFICE and bind it to this file."""
        secret = self._get_editor_secret()

        if not secret or not token:
            return False

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return False

        claims = payload.get("payload", payload)

        if not isinstance(claims, dict):
            return False

        token_key = claims.get("key")
        token_document = claims.get("document")

        if isinstance(token_document, dict):
            token_key = token_key or token_document.get("key")

        if not (
            self._is_file_callback_key(file_record, token_key)
            and self._is_file_callback_key(file_record, callback_data.get("key"))
        ):
            return False

        if "file_id" in claims:
            try:
                if int(claims["file_id"]) != file_record.id:
                    return False
            except (TypeError, ValueError):
                return False

        return payload

    def _decode_callback_auth(self, file_record, query_token, callback_data):
        """Accept an ONLYOFFICE JWT (body or header), else our own token."""
        for token in (callback_data.get("token"), self._get_bearer_token()):
            payload = self._decode_onlyoffice_callback_token(
                file_record, token, callback_data
            )
            if payload:
                return payload

        return self._decode_callback_token(file_record, query_token)

    # ---------------------------------------------------------
    # SAVING AN EDITED FILE
    # ---------------------------------------------------------

    def _get_edited_file_url(self, edited_url):
        """Where the Odoo server downloads an edited file from.

        ONLYOFFICE builds the URL from the address the browser used, which
        the Odoo server may not reach (e.g. localhost:8080 inside Docker), so
        it is rewritten to the internal URL when one is set. Any other host
        is refused: the callback must not make Odoo fetch arbitrary URLs.
        """
        public = (get_param("document_editor.onlyoffice_url") or "").rstrip("/")
        internal = (
            get_param("document_editor.onlyoffice_internal_url") or ""
        ).rstrip("/")

        for prefix in filter(None, (public, internal)):
            if edited_url.startswith(prefix + "/"):
                return (internal or public) + edited_url[len(prefix):]

        raise ValueError(
            "ONLYOFFICE returned a file URL outside the configured "
            "ONLYOFFICE server."
        )

    def _get_editor_user(self, data, callback_payload):
        """User credited with an edit: the last one ONLYOFFICE lists in
        `users`, else the user who opened the editor (callback token)."""
        users = request.env["res.users"].sudo()
        candidates = []

        if data.get("users"):
            candidates.append(data["users"][-1])

        candidates.append(callback_payload.get("user_id", 0))

        for user_id in candidates:
            try:
                user = users.browse(int(user_id))
            except (TypeError, ValueError):
                continue
            if user_id and user.exists():
                return user

        return request.env.user

    def _post_edit_audit(self, dms_file, editor_user):
        """Note the edit in the file's chatter."""
        dms_file.message_post(
            body=_("Document content was modified using ONLYOFFICE."),
            author_id=editor_user.partner_id.id,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

    def _convert_with_onlyoffice(self, file_url, from_type, to_type):
        """Convert a file ONLYOFFICE can reach (its own cache) with the
        ONLYOFFICE conversion service, and return the converted bytes."""
        secret = self._get_editor_secret()
        server = (
            get_param("document_editor.onlyoffice_internal_url")
            or get_param("document_editor.onlyoffice_url")
            or ""
        ).rstrip("/")

        payload = {
            "async": False,
            "filetype": from_type,
            "outputtype": to_type,
            "key": f"convert-{uuid.uuid4().hex}",
            "title": f"document.{from_type}",
            "url": file_url,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        response = requests.post(
            f"{server}/ConvertService.ashx",
            json={**payload, "token": token},
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("error") or not result.get("endConvert") or not result.get("fileUrl"):
            raise ValueError(
                f"ONLYOFFICE could not convert {from_type} to {to_type}: {result}"
            )

        converted = requests.get(
            self._get_edited_file_url(result["fileUrl"]),
            timeout=60,
            allow_redirects=False,
        )
        converted.raise_for_status()
        return converted.content

    def _download_edited_file(self, data, dms_file, extension, file_info):
        """Fetch and validate the edited file a save callback points to."""
        callback_file_type = (data.get("filetype") or "").lower().lstrip(".")
        edited_url = data.get("url")

        if not edited_url:
            raise ValueError("ONLYOFFICE did not provide an edited document URL.")

        # With assemblyFormatAsOrigin ONLYOFFICE returns the original format.
        if callback_file_type and callback_file_type != extension:
            if extension == "csv":
                _logger.warning(
                    "ONLYOFFICE returned %s for CSV file %s. Attempting "
                    "conversion back to CSV is required.",
                    callback_file_type,
                    dms_file.id,
                )
            elif extension == "md":
                # DOCX is expected: it is converted back to Markdown below.
                if callback_file_type != "docx":
                    raise ValueError(
                        f"ONLYOFFICE returned {callback_file_type} instead of "
                        f"Markdown for {dms_file.name}."
                    )
            elif extension == "pdf":
                raise ValueError(
                    f"ONLYOFFICE returned {callback_file_type} instead of "
                    f"PDF for {dms_file.name}."
                )
            else:
                raise ValueError(
                    "ONLYOFFICE returned an unexpected file type: "
                    f"{callback_file_type}. Expected {extension}."
                )

        download_url = self._get_edited_file_url(edited_url)

        _logger.info(
            "Downloading edited %s for DMS file %s from ONLYOFFICE: %s",
            file_info["label"],
            dms_file.id,
            download_url,
        )

        # A redirect could lead outside ONLYOFFICE.
        response = requests.get(download_url, timeout=60, allow_redirects=False)
        response.raise_for_status()
        binary = response.content

        returned_type = callback_file_type or extension

        # ONLYOFFICE edits Markdown as DOCX and cannot save it back as
        # Markdown, so convert the edited DOCX with its conversion service.
        if extension == "md" and returned_type == "docx":
            binary = self._convert_with_onlyoffice(download_url, "docx", "md")
            returned_type = "md"

        if extension == "csv" and returned_type != "csv":
            if returned_type != "xlsx":
                raise ValueError(
                    f"ONLYOFFICE returned an unsupported format "
                    f"({returned_type}) while saving a CSV file."
                )
            if not binary.startswith(b"PK"):
                raise ValueError(
                    "ONLYOFFICE returned invalid XLSX data for CSV conversion."
                )
            raise ValueError(
                "CSV was opened successfully, but ONLYOFFICE returned XLSX "
                "instead of CSV. Enable assemblyFormatAsOrigin in the "
                "ONLYOFFICE server configuration so the original CSV format "
                "is returned on save."
            )

        returned_info = OFFICE_FILE_TYPES.get(returned_type)

        if not returned_info:
            raise ValueError(f"Unsupported returned file type: {returned_type}")

        self._validate_binary(binary, returned_info, returned_type)
        return binary

    def _save_edited_file(self, dms_file, binary, editor_user, file_info):
        """Store the edited content as the editor, with a chatter note."""
        old_checksum = dms_file.checksum

        if old_checksum == dms_file._get_checksum(binary):
            _logger.info(
                "No content change detected for DMS file %s; skipping audit.",
                dms_file.id,
            )
            return

        dms_file_as_editor = dms_file.with_user(editor_user).sudo()
        dms_file_as_editor.write(
            {"content": base64.b64encode(binary).decode("ascii")}
        )
        saved_checksum = dms_file_as_editor.checksum

        if saved_checksum != old_checksum:
            self._post_edit_audit(dms_file_as_editor, editor_user)
            _logger.info(
                "AUDIT: DMS file %s (%s) modified by user %s (%s). "
                "Checksum changed from %s to %s.",
                dms_file.id,
                file_info["label"],
                editor_user.id,
                editor_user.name,
                old_checksum,
                saved_checksum,
            )

    # ---------------------------------------------------------
    # ROUTES
    # ---------------------------------------------------------

    @http.route(
        "/document_editor/dms/open/<int:file_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def open_editor(self, file_id, **kwargs):
        dms_file = request.env["dms.file"].browse(file_id)

        if not dms_file.exists():
            return request.not_found()

        if not self._get_office_file_info(dms_file.name):
            return text_response(
                _(
                    "ONLYOFFICE editing is currently available for DOCX, "
                    "XLSX, PPTX, CSV, PDF and Markdown files."
                ),
                400,
            )

        if dms_file.is_locked and not dms_file.is_lock_editor:
            return text_response(
                _(
                    "This document is locked by %s. Co-editing needs it unlocked.",
                    dms_file.locked_by.name,
                ),
                423,
            )

        if not dms_file.permission_write:
            return text_response(
                _("You do not have permission to edit this document."), 403
            )

        onlyoffice_url = get_param("document_editor.onlyoffice_url")

        if not onlyoffice_url:
            return text_response(_("ONLYOFFICE URL is not configured."), 500)

        # Browsers silently block an http editor script on an https page.
        if request.httprequest.scheme == "https" and onlyoffice_url.startswith(
            "http://"
        ):
            return text_response(
                _(
                    "ONLYOFFICE URL must start with https:// because Odoo is "
                    "served over https. Fix it in Settings > Document Editor."
                ),
                500,
            )

        dms_action = request.env.ref("dms.action_dms_file")

        return request.render(
            "document_editor.onlyoffice_editor_page",
            {
                "file": dms_file,
                "config_url": f"/document_editor/dms/config/{dms_file.id}",
                "onlyoffice_url": onlyoffice_url.rstrip("/"),
                "return_url": f"/odoo/action-{dms_action.id}/{dms_file.id}",
            },
        )

    @http.route(
        "/document_editor/dms/config/<int:file_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def editor_config(self, file_id, **kwargs):
        dms_file = request.env["dms.file"].browse(file_id)

        if not dms_file.exists():
            return request.not_found()

        filename = dms_file.name or ""
        extension = get_extension(filename)
        file_info = self._get_office_file_info(filename)

        if not file_info:
            return json_response(
                {
                    "error": "Only DOCX, XLSX, PPTX, CSV, PDF and Markdown "
                    "files are supported."
                },
                400,
            )

        if not dms_file.permission_write:
            return json_response(
                {"error": "You do not have permission to edit this document."},
                403,
            )

        secret = self._get_editor_secret()

        if not secret:
            _logger.error("ONLYOFFICE JWT secret is not configured.")
            return json_response(
                {"error": "ONLYOFFICE JWT secret is not configured."}, 500
            )

        odoo_base_url = get_param("document_editor.odoo_base_url")

        if not odoo_base_url:
            return json_response({"error": "Odoo Base URL is not configured."}, 500)

        odoo_base_url = odoo_base_url.rstrip("/")
        content_token = self._make_token(dms_file)
        callback_token = self._make_callback_token(dms_file)

        if not content_token or not callback_token:
            return json_response(
                {"error": "Unable to generate document access or callback token."},
                500,
            )

        routes = f"{odoo_base_url}/document_editor/dms"
        config = {
            "documentType": file_info["document_type"],
            "document": {
                "fileType": extension,
                # Shared by every co-editor until the session closes.
                "key": dms_file._onlyoffice_session_key(),
                "title": filename,
                "url": f"{routes}/content/{dms_file.id}?token={quote(content_token)}",
                "permissions": {"edit": True, "download": True, "print": True},
            },
            "editorConfig": {
                "mode": "edit",
                "callbackUrl": (
                    f"{routes}/callback/{dms_file.id}?token={quote(callback_token)}"
                ),
                # Real-time co-editing.
                "coEditing": {"mode": "fast", "change": False},
                "customization": {
                    "autosave": False,
                    "forcesave": True,
                    "savetitle": True,
                },
                "user": {
                    "id": str(request.env.user.id),
                    "name": request.env.user.name or "User",
                },
            },
            "unsavedAuditUrl": (
                f"{routes}/unsaved-audit/{dms_file.id}"
                f"?token={quote(callback_token)}"
                f"&initial_checksum={quote(dms_file.checksum or '')}"
            ),
        }

        # Open PDFs in the PDF editor, not as fillable forms.
        if extension == "pdf":
            config["document"]["isForm"] = False

        config["token"] = jwt.encode(config, secret, algorithm="HS256")

        _logger.info(
            "ONLYOFFICE config generated for DMS file %s (%s)",
            dms_file.id,
            file_info["label"],
        )
        return json_response(config)

    @http.route(
        "/document_editor/dms/content/<int:file_id>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def document_content(self, file_id, token=None, **kwargs):
        dms_file = request.env["dms.file"].sudo().browse(file_id)

        if not dms_file.exists():
            return request.not_found()

        if not self._check_token(dms_file, token):
            return text_response("Invalid token", 403)

        filename = dms_file.name or ""
        file_info = self._get_office_file_info(filename)

        if not file_info:
            return text_response(
                "Only DOCX, XLSX, PPTX, CSV, PDF and Markdown files are supported.",
                400,
            )

        binary = get_file_binary(dms_file)

        if not binary:
            return text_response("File has no content.", 404)

        return request.make_response(
            binary,
            headers=[
                ("Content-Type", file_info["mimetype"]),
                ("Content-Disposition", f"inline; filename*=UTF-8''{quote(filename)}"),
            ],
        )

    @http.route(
        "/document_editor/dms/callback/<int:file_id>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def dms_callback(self, file_id, token=None, **kwargs):
        dms_file = request.env["dms.file"].sudo().browse(file_id)

        if not dms_file.exists():
            return json_response({"error": 1}, 404)

        data = request.httprequest.get_json(silent=True)

        if not isinstance(data, dict):
            data = {}

        callback_payload = self._decode_callback_auth(dms_file, token, data)

        if not callback_payload:
            return json_response({"error": 1}, 403)

        try:
            status = data.get("status")
            extension = get_extension(dms_file.name)
            file_info = self._get_office_file_info(dms_file.name)

            if not file_info:
                raise ValueError("Unsupported DMS document type.")

            _logger.info(
                "ONLYOFFICE callback for DMS file %s: status=%s, filetype=%s, "
                "forcesavetype=%s",
                file_id,
                status,
                (data.get("filetype") or "").lower().lstrip(".") or "unknown",
                data.get("forcesavetype"),
            )

            # 2 = saved after everyone left, 6 = forcesave (Save button).
            if status in (2, 6):
                binary = self._download_edited_file(
                    data, dms_file, extension, file_info
                )
                editor_user = self._get_editor_user(data, callback_payload)
                self._save_edited_file(dms_file, binary, editor_user, file_info)
                _logger.info(
                    "Successfully processed updated %s for DMS file %s (%s bytes)",
                    file_info["label"],
                    file_id,
                    len(binary),
                )

            elif status in (3, 7):
                _logger.error(
                    "ONLYOFFICE reported a save error for DMS file %s: %s",
                    file_id,
                    data,
                )

            # Track the co-editing session (ignore callbacks of an older one):
            # 6 = forcesave, session continues on the new content;
            # 2 = saved after everyone left, 4 = closed unchanged,
            # 3 = final save failed: the session is over.
            if dms_file.onlyoffice_key == data.get("key"):
                if status == 6:
                    dms_file.write({"onlyoffice_checksum": dms_file.checksum})
                elif status in (2, 3, 4):
                    dms_file.write(
                        {"onlyoffice_key": False, "onlyoffice_checksum": False}
                    )

            return json_response({"error": 0})

        except Exception:
            _logger.exception("ONLYOFFICE callback failed for DMS file %s", file_id)
            return json_response({"error": 1}, 500)

    @http.route(
        "/document_editor/dms/unsaved-audit/<int:file_id>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def unsaved_edit_audit(self, file_id, token=None, initial_checksum=None, **kwargs):
        dms_file = request.env["dms.file"].sudo().browse(file_id)

        if not dms_file.exists():
            return json_response({"error": 1}, 404)

        # Saved meanwhile: nothing was lost.
        if not initial_checksum or dms_file.checksum != initial_checksum:
            return json_response({"error": 0, "audited": False})

        callback_payload = self._decode_callback_token(dms_file, token)

        if not callback_payload:
            return json_response({"error": 1}, 403)

        try:
            user_id = int(callback_payload.get("user_id", 0))
        except (TypeError, ValueError):
            user_id = 0

        editor_user = request.env["res.users"].sudo().browse(user_id)

        if not editor_user.exists():
            return json_response({"error": 1}, 403)

        dms_file.with_user(editor_user).sudo().message_post(
            body=_(
                "Document was edited in ONLYOFFICE and the editing session "
                "was left without saving."
            ),
            author_id=editor_user.partner_id.id,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        _logger.info(
            "AUDIT: DMS file %s was edited and left without saving by user %s (%s).",
            file_id,
            editor_user.id,
            editor_user.name,
        )
        return json_response({"error": 0})
