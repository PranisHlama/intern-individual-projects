from odoo import fields, models
from odoo.exceptions import AccessError, UserError


class DmsFile(models.Model):
    _inherit = "dms.file"

    # ONLYOFFICE co-editing session: everyone opening the file must get the
    # same document key until the last editor leaves, even after a forcesave
    # changes the checksum. `onlyoffice_checksum` is the content the session
    # last synced with Odoo; a different checksum means the file changed
    # outside the session, which then no longer applies.
    onlyoffice_key = fields.Char(copy=False, readonly=True)
    onlyoffice_checksum = fields.Char(copy=False, readonly=True)

    def _onlyoffice_session_active(self):
        self.ensure_one()
        return bool(
            self.onlyoffice_key and self.onlyoffice_checksum == self.checksum
        )

    def _onlyoffice_session_key(self):
        """Return the active session key, starting a session if needed."""
        self.ensure_one()
        if not self._onlyoffice_session_active():
            self.sudo().write(
                {
                    "onlyoffice_key": f"dms-{self.id}-{self.checksum}",
                    "onlyoffice_checksum": self.checksum,
                }
            )
        return self.onlyoffice_key

    def lock(self):
        # ONLYOFFICE saves for all co-editors; a lock would block those saves.
        if any(record._onlyoffice_session_active() for record in self):
            raise UserError(
                self.env._(
                    "This document is open in ONLYOFFICE. "
                    "Close it there before locking it."
                )
            )
        return super().lock()

    def action_open_onlyoffice(self):
        self.ensure_one()

        supported_extensions = {
            # Document editor
            "docx",
            "md",

            # Spreadsheet editor
            "xlsx",
            "csv",

            # Presentation editor
            "pptx",

            # PDF editor
            "pdf",
        }

        extension = (self.extension or "").lower()

        if extension not in supported_extensions:
            raise AccessError(
                "ONLYOFFICE editing is available for "
                "DOCX, XLSX, PPTX, CSV, PDF and Markdown files."
            )

        if not self.permission_write:
            raise AccessError(
                "You do not have permission to edit this document."
            )

        return {
            "type": "ir.actions.act_url",
            "url": f"/document_editor/dms/open/{self.id}",
            "target": "self",
        }

    def action_open_browser_editor(self):
        # Type, permission and lock checks happen in the open route.
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": f"/document_editor/browser/open/{self.id}",
            "target": "self",
        }