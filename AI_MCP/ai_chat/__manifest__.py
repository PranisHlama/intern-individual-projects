{
    "name": "AI Chat",
    "version": "20.0.1.0.0",
    "summary": "AI assistant for Odoo",
    "category": "Productivity",
    "author": "Your Name",
    "license": "LGPL-3",

    "depends": [
        "web",
        "mrp",
    ],

    "data": [],

    "assets": {
        "web.assets_backend": [
            "ai_chat/static/src/js/ai_systray.js",
            "ai_chat/static/src/xml/ai_systray.xml",
            "ai_chat/static/src/css/ai_systray.css",
        ],
    },

    "installable": True,
    "application": True,
}
