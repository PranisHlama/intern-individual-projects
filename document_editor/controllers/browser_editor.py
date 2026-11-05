import base64
import html
import io
import json
import logging
import os
import re
import zipfile
from urllib.parse import quote

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request

from .common import get_file_binary, json_response

_logger = logging.getLogger(__name__)

# Extension -> editor shown in the browser. `signature` is the header an
# uploaded file must have: DOCX, XLSX and PPTX are ZIP containers.
BROWSER_EDITORS = {
    "docx": {
        "name": "SuperDoc",
        "template": "document_editor.superdoc_editor_page",
        "mimetype": (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        "signature": b"PK",
    },
    "xlsx": {
        "name": "BetterOffice",
        "template": "document_editor.betteroffice_editor_page",
        "mimetype": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        "signature": b"PK",
    },
    "pptx": {
        "name": "BetterOffice",
        "template": "document_editor.betteroffice_editor_page",
        "mimetype": (
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),
        "signature": b"PK",
    },
    "pdf": {
        "name": "PDF.js",
        "template": "document_editor.pdfjs_editor_page",
        "mimetype": "application/pdf",
        "signature": b"%PDF",
    },
}

# Refuse uploads larger than this to avoid filling memory.
MAX_FILE_SIZE = 100 * 1024 * 1024

STATIC_SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "src")


def _asset_version():
    """Changes whenever an editor JS/CSS file changes. Odoo lets browsers
    cache static files for a week, so the editor URLs carry this as ?v= to
    stop a browser from mixing a new page with old cached scripts."""
    return str(max(
        int(entry.stat().st_mtime)
        for folder in ("js", "css")
        for entry in os.scandir(os.path.join(STATIC_SRC, folder))
    ))


class BrowserEditorController(http.Controller):
    """
    In-browser Office editing without a document server.

    The browser downloads the file from Odoo, edits it locally (SuperDoc
    for DOCX, BetterOffice for XLSX and PPTX, PDF.js for PDF) and uploads
    the result. Every route
    runs as the logged-in user, so normal DMS access rules apply and no
    tokens are needed.
    """

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def _get_editable_file(self, file_id):
        """Return (file, editor, error, status) for the current user."""
        dms_file = request.env["dms.file"].browse(file_id)

        if not dms_file.exists():
            return dms_file, None, _("Document not found."), 404

        editor = BROWSER_EDITORS.get((dms_file.extension or "").lower())

        if not editor:
            return dms_file, None, _(
                "Browser editing is available for %s files only.",
                ", ".join(ext.upper() for ext in BROWSER_EDITORS),
            ), 400

        if not dms_file.permission_write:
            return dms_file, editor, _(
                "You do not have permission to edit this document."
            ), 403

        if dms_file.is_locked and not dms_file.is_lock_editor:
            return dms_file, editor, _(
                "This document is locked by %s.", dms_file.locked_by.name
            ), 423

        # ONLYOFFICE's final save would overwrite changes made here.
        if dms_file._onlyoffice_session_open():
            return dms_file, editor, _(
                "This document is open in ONLYOFFICE. "
                "Close it there before using this editor."
            ), 423

        return dms_file, editor, None, 200

    def _get_pptx_font_families(self, binary):
        """Font families a presentation names, so the editor can load them."""
        families = set()

        try:
            with zipfile.ZipFile(io.BytesIO(binary)) as package:
                for name in package.namelist():
                    if name.startswith("ppt/") and name.endswith(".xml"):
                        # "+mj-lt" style values point at theme fonts.
                        families.update(
                            re.findall(rb'typeface="([^"+][^"]*)"', package.read(name))
                        )
        except zipfile.BadZipFile:
            return []

        return sorted(
            html.unescape(family.decode("utf-8", "replace"))
            for family in families
        )

    # ---------------------------------------------------------
    # OPEN EDITOR
    # ---------------------------------------------------------

    @http.route(
        "/document_editor/browser/open/<int:file_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def open_editor(self, file_id, **kwargs):
        dms_file, editor, error, status = self._get_editable_file(file_id)

        if error:
            return request.make_response(
                error,
                headers=[("Content-Type", "text/plain; charset=utf-8")],
                status=status,
            )

        dms_action = request.env.ref("dms.action_dms_file")

        font_families = None

        if dms_file.extension.lower() == "pptx":
            font_families = json.dumps(
                self._get_pptx_font_families(get_file_binary(dms_file))
            )

        return request.render(
            editor["template"],
            {
                "file": dms_file,
                "format": dms_file.extension.lower(),
                "content_url": f"/document_editor/browser/content/{dms_file.id}",
                "save_url": f"/document_editor/browser/save/{dms_file.id}",
                "checksum": dms_file.checksum or "",
                "csrf_token": request.csrf_token(),
                "user_name": request.env.user.name or "User",
                "user_email": request.env.user.email or "",
                "return_url": f"/odoo/action-{dms_action.id}/{dms_file.id}",
                "font_families": font_families,
                "asset_version": _asset_version(),
            },
        )

    # ---------------------------------------------------------
    # DOCUMENT CONTENT
    # ---------------------------------------------------------

    @http.route(
        "/document_editor/browser/content/<int:file_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def document_content(self, file_id, **kwargs):
        dms_file, editor, error, status = self._get_editable_file(file_id)

        if error:
            return request.make_response(error, status=status)

        binary = get_file_binary(dms_file)

        if not binary:
            return request.make_response(_("File has no content."), status=404)

        return request.make_response(
            binary,
            headers=[
                ("Content-Type", editor["mimetype"]),
                (
                    "Content-Disposition",
                    f"inline; filename*=UTF-8''{quote(dms_file.name or '')}",
                ),
                ("Cache-Control", "no-store"),
            ],
        )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    @http.route(
        "/document_editor/browser/save/<int:file_id>",
        type="http",
        auth="user",
        methods=["POST"],
    )
    def save_document(self, file_id, checksum=None, **kwargs):
        dms_file, editor, error, status = self._get_editable_file(file_id)

        if error:
            return json_response({"error": error}, status=status)

        upload = request.httprequest.files.get("file")

        if not upload:
            return json_response({"error": _("No document was uploaded.")}, status=400)

        binary = upload.read(MAX_FILE_SIZE + 1)

        if len(binary) > MAX_FILE_SIZE:
            return json_response({"error": _("The document is too large.")}, status=413)

        if not binary.startswith(editor["signature"]):
            return json_response(
                {"error": _("The editor returned invalid file data.")},
                status=400,
            )

        old_checksum = dms_file.checksum

        # Someone else saved this file after the editor was opened.
        # Refuse instead of silently overwriting their changes.
        if (checksum or "") != (old_checksum or ""):
            return json_response(
                {
                    "error": _(
                        "This document was changed by someone else after "
                        "you opened it. Reload the editor to get the latest "
                        "version; your unsaved changes will be lost."
                    ),
                    "conflict": True,
                },
                status=409,
            )

        if dms_file._get_checksum(binary) == old_checksum:
            return json_response({"saved": False, "checksum": old_checksum})

        try:
            # Written as the current user, so DMS access rules apply.
            dms_file.write(
                {"content": base64.b64encode(binary).decode("ascii")}
            )
        except AccessError as error:
            return json_response({"error": str(error)}, status=403)

        dms_file.message_post(
            body=_("Document content was modified using %s.", editor["name"]),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

        _logger.info(
            "AUDIT: DMS file %s modified with %s by user %s (%s). "
            "Checksum changed from %s to %s.",
            dms_file.id,
            editor["name"],
            request.env.user.id,
            request.env.user.name,
            old_checksum,
            dms_file.checksum,
        )

        return json_response({"saved": True, "checksum": dms_file.checksum})
