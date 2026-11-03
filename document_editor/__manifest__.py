{
    "name": "DMS Editor",
    "version": "20.0.1.0.0",
    "category": "Documents",
    "summary": "Edit DOCX, XLSX and PPTX files from Odoo DMS using ONLYOFFICE",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
        "dms",
    ],
    "author": "Aayush Poudel",
    "data": [
        "views/editor_templates.xml",
        "views/dms_file_views.xml",
        "views/res_config_settings.xml",
    ],
    "installable": True,
    "application": True,
}