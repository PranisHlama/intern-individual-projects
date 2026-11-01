{
    "name": "Cafe Social Marketing",
    "version": "20.0.6.0.0",
    "summary": "Social marketing management for a multi-branch cafe chain",
    "description": """
        Social media content management for a multi-branch cafe chain.

        Features include:
        - Branch, social account and campaign management
        - Reusable post templates and scheduling
        - Pre-publication compliance validation
        - Marketing User / Marketing Manager approval workflow
        - Request Changes with required manager feedback
        - Read-only branch content calendar
        - Campaign date-range calendar and inclusive duration
        - AI-assisted content review through a local Ollama service
        - Dedicated video attachment support
        - TikTok Content Posting API draft upload integration
        - Facebook Page text and single-photo publishing with confirmed remote post IDs

        - Instagram attached JPEG publishing with automatic Cloudinary hosting
        - Visual Facebook, Instagram and TikTok account setup picker

        TikTok Direct Post and OAuth connection remain future integration steps.
    """,
    "author": "Pabin",
    "category": "Marketing",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
    ],
    "external_dependencies": {
        "python": ["requests", "PIL"],
    },
    "data": [
        "security/cafe_social_groups.xml",
        "security/ir.access.csv",
        "data/ir_cron.xml",
        "views/branch_views.xml",
        "views/account_picker_views.xml",
        "views/social_account_views.xml",
        "views/campaign_views.xml",
        "views/social_post_views.xml",
        "views/facebook_views.xml",
        "views/instagram_views.xml",
        "views/social_post_ai_views.xml",
        "views/post_template_views.xml",
        "views/review_calendar_views.xml",
        "views/campaign_calendar_views.xml",
        "views/menus.xml",
    ],
    "application": True,
    "installable": True,
}