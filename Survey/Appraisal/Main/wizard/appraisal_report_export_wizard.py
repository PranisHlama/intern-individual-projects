import base64
import io
import csv
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrAppraisalReportExportWizard(models.TransientModel):
    _name = 'hr.appraisal.report.export.wizard'
    _description = 'Export Appraisal Reports & Analytics'

    export_format = fields.Selection([
        ('csv', 'CSV Spreadsheet (.csv)'),
        ('pdf', 'Consolidated PDF Summary (.pdf)'),
    ], string='Export Format', default='csv', required=True)

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    department_id = fields.Many2one('hr.department', string='Department')
    stage_id = fields.Many2one('hr.appraisal.stage', string='Stage')

    file_data = fields.Binary(string='Exported File', readonly=True)
    file_name = fields.Char(string='Filename', readonly=True)

    def action_export_report(self):
        self.ensure_one()
        domain = []
        if self.date_from:
            domain.append(('date_start', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_close', '<=', self.date_to))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.stage_id:
            domain.append(('stage_id', '=', self.stage_id.id))

        appraisals = self.env['hr.appraisal'].search(domain)
        if not appraisals:
            raise UserError(_("No appraisals found matching the specified export filters."))

        if self.export_format == 'pdf':
            return self.env.ref('hr_appraisal_pro.action_report_hr_appraisal').report_action(appraisals)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            'Reference', 'Employee', 'Manager', 'Department', 'Job Position',
            'Review Period', 'Start Date', 'Deadline', 'Stage',
            'Competency Score', 'Goal Score', 'Final Score', 'Overdue'
        ])
        for app in appraisals:
            writer.writerow([
                app.name,
                app.employee_id.name,
                app.manager_id.name if app.manager_id else '',
                app.department_id.name if app.department_id else '',
                app.job_id.name if app.job_id else '',
                app.review_period,
                str(app.date_start),
                str(app.date_close),
                app.stage_id.name,
                f"{app.competency_score:.2f}",
                f"{app.goal_score:.2f}",
                f"{app.final_score:.2f}",
                'Yes' if app.is_overdue else 'No'
            ])

        encoded_data = base64.b64encode(output.getvalue().encode('utf-8'))
        self.write({
            'file_data': encoded_data,
            'file_name': f"appraisal_export_{fields.Date.today()}.csv",
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.report.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
