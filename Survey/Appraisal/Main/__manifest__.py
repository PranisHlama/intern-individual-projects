{
    'name': 'Employee Appraisals Pro',
    'version': '20.0.1.0.0',
    'category': 'Human Resources/Appraisals',
    'sequence': 75,
    'summary': 'Enterprise-Grade Employee Performance Appraisals & Goal Management',
    'description': """
Employee Appraisals Pro (hr_appraisal_pro)
===========================================
A complete, enterprise-grade appraisal and performance management module for Odoo 20.

Key Features:
-------------
* **Multi-stage Appraisal Lifecycle**: Fully customizable stages (Draft, Waiting Self Assessment, Self Assessment Submitted, Waiting Manager Review, Manager Review Completed, Waiting HR Validation, Completed, Cancelled).
* **Self-Assessment & Manager Evaluation**: Rich dynamic questionnaires, conditional logic, rating matrices, and confidential comments.
* **Competency Management & Weighted Scoring**: Weighted competency ratings, customizable rating scales (1-5, 1-10, qualitative), automated score calculation with manual override capabilities.
* **Goal & Milestone Tracking**: Objectives with weight, progress, status, and automated carry-forward of unfinished goals to future appraisal cycles.
* **Skill Matrix & Career Development**: Integration with hr_skills, gap analysis, career development plans, and training recommendations.
* **Calendar & Meeting Integration**: Direct scheduling of 1-on-1 performance review meetings with video conferencing links and attendance tracking.
* **Automated Recurring Plans**: Schedule appraisals monthly, quarterly, semiannually, annually, or custom intervals with automated batch generation.
* **Executive Owl Dashboard**: Responsive, real-time analytics for Employees, Managers, and HR Officers.
* **Security & Confidentiality**: Multi-company isolation, strict role-based access control (Employee, Manager, HR Officer, HR Manager), and confidential note protection.
* **Wizards & Bulk Actions**: Batch creation, manager reassignment, deadline updates, reminder notifications, and comprehensive data export.
* **Professional QWeb & SQL Analytics**: Printable appraisal reports and multi-dimensional pivot/graph analysis.
    """,
    'author': 'Antigravity Solutions',
    'website': 'https://www.odoo.com/app/appraisals',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'calendar',
        'hr',
        'hr_skills',
        'resource',
    ],
    'data': [
        'security/hr_appraisal_security.xml',
        'security/ir.access.csv',
        'data/hr_appraisal_data.xml',
        'data/hr_appraisal_template_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_appraisal_stage_views.xml',
        'views/hr_appraisal_template_views.xml',
        'views/hr_appraisal_competency_views.xml',
        'views/hr_appraisal_goal_template_views.xml',
        'views/hr_appraisal_goal_views.xml',
        'views/hr_appraisal_career_views.xml',
        'views/hr_appraisal_meeting_views.xml',
        'views/hr_appraisal_survey_views.xml',
        'views/hr_appraisal_views.xml',
        'views/hr_appraisal_plan_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/appraisal_create_wizard_views.xml',
        'wizard/appraisal_bulk_manager_wizard_views.xml',
        'wizard/appraisal_bulk_deadline_wizard_views.xml',
        'wizard/appraisal_reminder_wizard_views.xml',
        'wizard/appraisal_report_export_wizard_views.xml',
        'report/hr_appraisal_report.xml',
        'report/hr_appraisal_report_templates.xml',
        'report/hr_appraisal_analysis_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_appraisal_pro/static/src/scss/hr_appraisal.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
