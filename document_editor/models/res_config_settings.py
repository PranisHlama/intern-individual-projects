from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    onlyoffice_url = fields.Char(
        string="ONLYOFFICE URL",
        config_parameter="document_editor.onlyoffice_url",
    )

    onlyoffice_internal_url = fields.Char(
        string="ONLYOFFICE Internal URL",
        config_parameter="document_editor.onlyoffice_internal_url",
        help="How the Odoo server reaches ONLYOFFICE, e.g. http://onlyoffice "
        "in Docker. Leave empty if Odoo can use the public URL.",
    )

    odoo_base_url = fields.Char(
        string="Odoo Base URL",
        config_parameter="document_editor.odoo_base_url",
    )

    onlyoffice_jwt_secret = fields.Char(
        string="ONLYOFFICE JWT Secret",
        config_parameter="document_editor.onlyoffice_jwt_secret",
    )
