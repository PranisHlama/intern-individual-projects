import shutil
import subprocess
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CupsConfig(models.Model):
    _name = "cups.config"
    _description = "CUPS Printer Configuration"
    _order = "name"

    name = fields.Char(
        string="Configuration Name",
        required=True,
        default="CUPS Server",
    )

    server_host = fields.Char(
        string="CUPS Host",
        required=True,
        default="cups",
    )

    server_port = fields.Integer(
        string="CUPS Port",
        required=True,
        default=631,
    )

    printer_name = fields.Char(
        string="Printer Queue",
        required=True,
        default="Odoo_PDF",
    )

    is_default = fields.Boolean(
        string="Default Printer",
        default=False,
    )

    active = fields.Boolean(
        default=True,
    )

    notes = fields.Text(
        string="Notes",
    )

    @api.constrains(
        "server_host",
        "server_port",
        "printer_name",
    )
    def _check_configuration(self):
        for record in self:
            host = (record.server_host or "").strip()
            printer = (record.printer_name or "").strip()

            if (
                not host
                or any(char.isspace() for char in host)
                or "/" in host
            ):
                raise ValidationError(
                    _("Enter a valid CUPS hostname or IP address.")
                )

            if not 1 <= record.server_port <= 65535:
                raise ValidationError(
                    _("CUPS port must be between 1 and 65535.")
                )

            if not re.fullmatch(
                r"[A-Za-z0-9_.-]+",
                printer,
            ):
                raise ValidationError(
                    _("Invalid printer queue name.")
                )

    @api.model
    def get_default_config(self):
        config = self.search(
            [
                ("active", "=", True),
                ("is_default", "=", True),
            ],
            limit=1,
        )

        if not config:
            config = self.search(
                [("active", "=", True)],
                limit=1,
            )

        return config

    def write(self, vals):
        result = super().write(vals)

        if vals.get("is_default"):
            for record in self.filtered("is_default"):
                (self - record).write({
                    "is_default": False,
                })

        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records.filtered("is_default"):
            (self - record).write({
                "is_default": False,
            })

        return records

    def action_test_connection(self):
        self.ensure_one()

        lpstat = shutil.which("lpstat")

        if not lpstat:
            raise UserError(
                _("CUPS client is not installed. Install cups-client.")
            )

        command = [
            lpstat,
            "-h",
            "%s:%s" % (
                self.server_host,
                self.server_port,
            ),
            "-p",
            self.printer_name,
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise UserError(
                _("CUPS connection timed out.")
            )

        if result.returncode != 0:
            raise UserError(
                result.stderr or result.stdout or
                _("Unable to connect to CUPS printer.")
            )

        raise UserError(
            _("CUPS connection successful:\n%s")
            % result.stdout
        )

    def action_open_print_wizard(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Print PDF Report"),
            "res_model": "cups.print.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_printer_id": self.id,
                "active_model": self.env.context.get(
                    "active_model"
                ),
                "active_ids": self.env.context.get(
                    "active_ids", []
                ),
            },
        }