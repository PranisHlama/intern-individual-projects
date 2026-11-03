import base64
import json
from datetime import datetime, timedelta, timezone

import jwt

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged

SECRET = "test-secret"


@tagged("post_install", "-at_install")
class TestOnlyofficeSession(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_str(
            "document_editor.onlyoffice_jwt_secret", SECRET
        )
        storage = cls.env["dms.storage"].create({"name": "s", "save_type": "database"})
        directory = cls.env["dms.directory"].create(
            {"name": "d", "is_root_directory": True, "storage_id": storage.id}
        )
        cls.file = cls.env["dms.file"].create(
            {
                "name": "doc.docx",
                "directory_id": directory.id,
                "content": base64.b64encode(b"PK v1").decode(),
            }
        )

    def _callback(self, status, key):
        token = jwt.encode(
            {
                "purpose": "dms_callback",
                "file_id": self.file.id,
                "user_id": self.env.uid,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            SECRET,
            algorithm="HS256",
        )
        response = self.url_open(
            f"/document_editor/dms/callback/{self.file.id}?token={token}",
            data=json.dumps({"status": status, "key": key}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json(), {"error": 0})
        self.file.invalidate_recordset()

    def test_session_lifecycle(self):
        key = self.file._onlyoffice_session_key()
        self.assertEqual(self.file._onlyoffice_session_key(), key)
        with self.assertRaises(UserError):
            self.file.lock()

        # A callback from an older session must not end the current one.
        self._callback(4, f"dms-{self.file.id}-old")
        self.assertEqual(self.file.onlyoffice_key, key)

        # Last editor left without changes: session over, locking works.
        self._callback(4, key)
        self.assertFalse(self.file.onlyoffice_key)
        self.file.lock()
        self.file.unlock()

    def test_external_change_starts_new_session(self):
        key = self.file._onlyoffice_session_key()
        self.file.write({"content": base64.b64encode(b"PK v2").decode()})
        self.assertFalse(self.file._onlyoffice_session_active())
        self.assertNotEqual(self.file._onlyoffice_session_key(), key)
