import io
import zipfile
from unittest.mock import Mock, patch

import jwt

from odoo import Command
from odoo.tests import HttpCase, new_test_user, tagged

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def office_file(text):
    """Small OOXML-like package (a ZIP, like a real DOCX/XLSX)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as package:
        # Fixed timestamp so the same text always gives the same bytes.
        entry = zipfile.ZipInfo("word/document.xml", date_time=(2020, 1, 1, 0, 0, 0))
        package.writestr(entry, text)
    return buffer.getvalue()


@tagged("post_install", "-at_install")
class TestOwnerEmployeeFlow(HttpCase):
    """A shop owner and an employee exchange and co-edit a document through
    the real HTTP routes. Only the ONLYOFFICE server itself is simulated: the
    test sends the callbacks it sends and serves the file it would return."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        params = cls.env["ir.config_parameter"].sudo()
        params.set_str("document_editor.onlyoffice_jwt_secret", "x" * 32)
        params.set_str("document_editor.onlyoffice_url", "https://docs.example.com")
        params.set_str("document_editor.odoo_base_url", cls.base_url())

        cls.owner = new_test_user(cls.env, "owner", groups="dms.group_dms_manager")
        cls.employee = new_test_user(cls.env, "employee", groups="dms.group_dms_user")
        cls.outsider = new_test_user(cls.env, "outsider", groups="dms.group_dms_user")

        shop = cls.env["dms.access.group"].create(
            {
                "name": "Coffee shop staff",
                "perm_create": True,
                "perm_write": True,
                "perm_unlink": True,
                "explicit_user_ids": [Command.set((cls.owner | cls.employee).ids)],
            }
        )
        storage = cls.env["dms.storage"].create({"name": "Shop", "save_type": "database"})
        cls.folder = cls.env["dms.directory"].create(
            {
                "name": "Shared with staff",
                "is_root_directory": True,
                "storage_id": storage.id,
                "group_ids": [Command.link(shop.id)],
            }
        )

    def _upload(self, login, name, content, mimetype=DOCX):
        self.authenticate(login, login)
        response = self.url_open(
            "/web/binary/upload_dms_file",
            data={"directory_id": self.folder.id, "csrf_token": self.csrf_token()},
            files={"ufile": (name, content, mimetype)},
        )
        response.raise_for_status()
        result = response.json()[0]
        self.assertNotIn("error", result, result)
        return self.env["dms.file"].browse(result["id"])

    def _config(self, login, dms_file):
        self.authenticate(login, login)
        self.assertEqual(
            self.url_open(f"/document_editor/dms/open/{dms_file.id}").status_code, 200
        )
        response = self.url_open(f"/document_editor/dms/config/{dms_file.id}")
        response.raise_for_status()
        return response.json()

    def _anonymous_get(self, url):
        """A request without any Odoo login (ONLYOFFICE, a shared link)."""
        self.logout()
        return self.url_open(url)

    def _onlyoffice_callback(
        self,
        config,
        status,
        user,
        edited,
        url="https://docs.example.com/cache/edited.docx",
        expected=None,
    ):
        """What the ONLYOFFICE server does: POST to the callback URL and, on
        status 2/6, serve the edited file at `url` for Odoo to download.
        Returns the mocked download so callers can check what was fetched."""
        download = Mock(content=edited, raise_for_status=Mock())
        with patch(
            "odoo.addons.document_editor.controllers.onlyoffice.requests.get",
            return_value=download,
        ) as get:
            response = self.url_open(
                config["editorConfig"]["callbackUrl"],
                json={
                    "status": status,
                    "key": config["document"]["key"],
                    "url": url,
                    "filetype": "docx",
                    "users": [str(user.id)],
                },
            )
        self.assertEqual(response.json(), expected or {"error": 0})
        return get

    def test_owner_and_employee_share_and_co_edit(self):
        # 1. Owner sends a document: uploads it into the shared folder.
        menu = self._upload("owner", "menu.docx", office_file("v1"))
        self.assertIn(menu, self.env["dms.file"].with_user(self.employee).search([]))
        self.assertNotIn(menu, self.env["dms.file"].with_user(self.outsider).search([]))

        # 2. Outsider (DMS user, not staff) cannot open it in the editor.
        self.authenticate("outsider", "outsider")
        response = self.url_open(f"/document_editor/dms/open/{menu.id}")
        self.assertEqual(response.status_code, 403)

        # 3. Employee opens it; ONLYOFFICE downloads it without a session.
        employee_config = self._config("employee", menu)
        self.assertTrue(employee_config["token"])
        source = self._anonymous_get(employee_config["document"]["url"])
        self.assertEqual(source.content, office_file("v1"))

        # 4. Employee presses Save mid-session (forcesave): owner who joins
        #    afterwards lands in the SAME co-editing session.
        self._onlyoffice_callback(employee_config, 6, self.employee, office_file("v2"))
        menu.invalidate_recordset()
        self.assertEqual(bytes(menu.content), office_file("v2"))
        owner_config = self._config("owner", menu)
        self.assertEqual(
            owner_config["document"]["key"], employee_config["document"]["key"]
        )

        # 5. Both close; ONLYOFFICE sends the merged document once.
        self._onlyoffice_callback(owner_config, 2, self.employee, office_file("v3"))
        menu.invalidate_recordset()
        self.assertEqual(bytes(menu.content), office_file("v3"))
        self.assertFalse(menu.onlyoffice_key)
        note = menu.message_ids[:1]
        self.assertEqual(note.author_id, self.employee.partner_id)
        self.assertIn("ONLYOFFICE", note.body)

        # 6. Employee sends a file back; the owner sees it.
        stock = self._upload("employee", "stock.xlsx", office_file("stock"))
        self.assertIn(stock, self.env["dms.file"].with_user(self.owner).search([]))

        # 7. Owner shares the file by link with someone without an account.
        menu._portal_ensure_token()
        shared = self._anonymous_get(
            f"/my/dms/file/{menu.id}/download?access_token={menu.access_token}"
        )
        self.assertEqual(shared.status_code, 200)
        self.assertEqual(shared.content, office_file("v3"))

    def test_expired_or_forged_download_token_is_refused(self):
        menu = self._upload("owner", "menu.docx", office_file("v1"))
        url = self._config("owner", menu)["document"]["url"]
        base, token = url.split("?token=")
        expires, signature = token.split(".")
        forged = f"{base}?token={int(expires) + 1}.{signature}"
        self.assertEqual(self._anonymous_get(forged).status_code, 403)
        expired = f"{base}?token=1.{signature}"
        self.assertEqual(self._anonymous_get(expired).status_code, 403)

    def test_edited_file_is_fetched_from_onlyoffice_only(self):
        menu = self._upload("owner", "menu.docx", office_file("v1"))
        config = self._config("owner", menu)

        # The browser-facing address is swapped for the internal one, which
        # is how the Odoo server reaches ONLYOFFICE inside Docker.
        self.env["ir.config_parameter"].sudo().set_str(
            "document_editor.onlyoffice_internal_url", "http://onlyoffice"
        )
        get = self._onlyoffice_callback(config, 6, self.owner, office_file("v2"))
        self.assertEqual(get.call_args.args[0], "http://onlyoffice/cache/edited.docx")

        # Any other host is refused and the file is left untouched.
        with self.assertLogs(
            "odoo.addons.document_editor.controllers.onlyoffice", "ERROR"
        ):
            get = self._onlyoffice_callback(
                config,
                2,
                self.owner,
                office_file("evil"),
                url="http://db:5432/secrets",
                expected={"error": 1},
            )
        get.assert_not_called()
        menu.invalidate_recordset()
        self.assertEqual(bytes(menu.content), office_file("v2"))

    def test_onlyoffice_signed_callback_and_unsaved_audit(self):
        menu = self._upload("owner", "menu.docx", office_file("v1"))
        config = self._config("employee", menu)
        key = config["document"]["key"]
        callback = config["editorConfig"]["callbackUrl"].split("?")[0]
        self.logout()

        # The real server signs callbacks with the shared secret (no query
        # token); a wrong signature is refused.
        body = {"status": 4, "key": key}
        forged = jwt.encode({"payload": body}, "y" * 32, algorithm="HS256")
        response = self.url_open(
            callback, json=body, headers={"Authorization": f"Bearer {forged}"}
        )
        self.assertEqual(response.status_code, 403)
        signed = jwt.encode({"payload": body}, "x" * 32, algorithm="HS256")
        response = self.url_open(
            callback, json=body, headers={"Authorization": f"Bearer {signed}"}
        )
        self.assertEqual(response.json(), {"error": 0})
        menu.invalidate_recordset()
        self.assertFalse(menu.onlyoffice_key)

        # Leaving without saving leaves a note credited to the editor.
        response = self.url_open(config["unsavedAuditUrl"], json={}, method="POST")
        self.assertEqual(response.json(), {"error": 0})
        note = menu.message_ids[:1]
        self.assertEqual(note.author_id, self.employee.partner_id)
        self.assertIn("without saving", note.body)

    def test_markdown_is_saved_back_as_markdown(self):
        """ONLYOFFICE edits Markdown as DOCX; the save is converted back."""
        notes = self._upload("owner", "notes.md", b"# v1\n", "text/markdown")
        config = self._config("owner", notes)
        self.assertEqual(config["document"]["fileType"], "md")

        files = {
            "https://docs.example.com/cache/edited.docx": office_file("v2"),
            "https://docs.example.com/cache/converted.md": b"# v2\n",
        }
        conversion = Mock(
            raise_for_status=Mock(),
            json=Mock(
                return_value={
                    "endConvert": True,
                    "fileUrl": "https://docs.example.com/cache/converted.md",
                }
            ),
        )
        controller = "odoo.addons.document_editor.controllers.onlyoffice.requests"
        with (
            patch(
                f"{controller}.get",
                side_effect=lambda url, **kw: Mock(
                    content=files[url], raise_for_status=Mock()
                ),
            ),
            patch(f"{controller}.post", return_value=conversion) as post,
        ):
            response = self.url_open(
                config["editorConfig"]["callbackUrl"],
                json={
                    "status": 2,
                    "key": config["document"]["key"],
                    "url": "https://docs.example.com/cache/edited.docx",
                    "filetype": "docx",
                    "users": [str(self.owner.id)],
                },
            )
        self.assertEqual(response.json(), {"error": 0})

        url, request = post.call_args.args[0], post.call_args.kwargs
        self.assertEqual(url, "https://docs.example.com/ConvertService.ashx")
        self.assertEqual(request["json"]["filetype"], "docx")
        self.assertEqual(request["json"]["outputtype"], "md")
        self.assertEqual(
            request["json"]["url"], "https://docs.example.com/cache/edited.docx"
        )
        self.assertTrue(request["headers"]["Authorization"].startswith("Bearer "))

        notes.invalidate_recordset()
        self.assertEqual(bytes(notes.content), b"# v2\n")
