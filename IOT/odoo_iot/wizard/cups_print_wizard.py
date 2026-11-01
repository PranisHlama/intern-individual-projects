import os
import shutil
import subprocess
import tempfile

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CupsPrintWizard(models.TransientModel):
    _name = "cups.print.wizard"
    _description = "CUPS PDF Print Wizard"

    report_id = fields.Many2one(
        "ir.actions.report",
        string="PDF Report",
        required=True,
        domain=[
            ("report_type", "=", "qweb-pdf"),
        ],
    )

    printer_id = fields.Many2one(
        "cups.config",
        string="Printer",
        required=True,
        domain=[
            ("active", "=", True),
        ],
    )

    record_ids = fields.Char(
        string="Record IDs",
        required=True,
        help="Enter record IDs separated by commas.",
    )

    copies = fields.Integer(
        string="Copies",
        default=1,
        required=True,
    )

    job_title = fields.Char(
        string="Print Job Title",
        default="Odoo PDF Report",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        active_ids = self.env.context.get(
            "active_ids", []
        )

        if active_ids and "record_ids" in fields_list:
            values["record_ids"] = ",".join(
                str(record_id)
                for record_id in active_ids
            )

        if "printer_id" in fields_list:
            if not values.get("printer_id"):
                printer = self.env[
                    "cups.config"
                ].get_default_config()

                if printer:
                    values["printer_id"] = printer.id

        return values

    def _get_record_ids(self):
        self.ensure_one()

        try:
            ids = [
                int(value.strip())
                for value in self.record_ids.split(",")
                if value.strip()
            ]
        except (ValueError, AttributeError):
            raise UserError(
                _("Enter valid comma-separated record IDs.")
            )

        if not ids or any(record_id <= 0 for record_id in ids):
            raise UserError(
                _("Enter at least one positive record ID.")
            )

        if len(ids) != len(set(ids)):
            raise UserError(
                _("Duplicate record IDs are not allowed.")
            )

        return ids

    def action_print(self):
        self.ensure_one()

        if self.copies < 1 or self.copies > 999:
            raise UserError(
                _("Copies must be between 1 and 999.")
            )

        if not self.printer_id.active:
            raise UserError(
                _("The selected printer is inactive.")
            )

        if self.report_id.report_type != "qweb-pdf":
            raise UserError(
                _("Please select a QWeb PDF report.")
            )

        ids = self._get_record_ids()
        model_name = self.report_id.model

        if not model_name or model_name not in self.env:
            raise UserError(
                _("The report model is unavailable.")
            )

        records = self.env[model_name].browse(ids).exists()

        if set(records.ids) != set(ids):
            raise UserError(
                _("Some selected records do not exist.")
            )

        records.check_access_rights("read")
        records.check_access_rule("read")

        lp = shutil.which("lp")

        if not lp:
            raise UserError(
                _(
                    "The lp command was not found. "
                    "Install cups-client in the Odoo container."
                )
            )

        try:
            pdf_content, output_type = (
                self.env["ir.actions.report"]._render_qweb_pdf(
                    self.report_id.report_name,
                    res_ids=ids,
                )
            )
        except Exception as error:
            raise UserError(
                _("PDF rendering failed: %s") % str(error)
            )

        if (
            output_type != "pdf"
            or not pdf_content
            or not pdf_content.startswith(b"%PDF")
        ):
            raise UserError(
                _("The report did not produce a valid PDF.")
            )

        fd, pdf_path = tempfile.mkstemp(
            prefix="odoo-cups-",
            suffix=".pdf",
        )

        try:
            with os.fdopen(fd, "wb") as pdf_file:
                pdf_file.write(pdf_content)

            printer = self.printer_id

            command = [
                lp,
                "-h",
                "%s:%s" % (
                    printer.server_host,
                    printer.server_port,
                ),
                "-d",
                printer.printer_name,
                "-n",
                str(self.copies),
                "-t",
                (self.job_title or "Odoo PDF")[:120],
                pdf_path,
            ]

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                raise UserError(
                    _("CUPS print request timed out.")
                )

            if result.returncode != 0:
                raise UserError(
                    result.stderr
                    or result.stdout
                    or _("CUPS rejected the print job.")
                )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Print Job Submitted"),
                    "message": (
                        result.stdout
                        or _("PDF sent successfully to CUPS.")
                    ),
                    "type": "success",
                    "sticky": False,
                },
            }

        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)