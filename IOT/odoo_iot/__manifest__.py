{
    "name": "Odoo CUPS Printing",
    "version": "20.0.1.0.0",
    "category": "Tools/Printing",
    "summary": "Print Odoo PDF reports using CUPS",
    "description": """
        Odoo CUPS Printing
        ==================
        Configure CUPS printers and send rendered Odoo
        PDF reports directly to a CUPS printer.
    """,
    "author": "Custom",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/cups_config_views.xml",
        "wizard/cups_print_wizard_views.xml",
        "views/cups_menus.xml",
    ],
    "application": True,
    "installable": True,
}