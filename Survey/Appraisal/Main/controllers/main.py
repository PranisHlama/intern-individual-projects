import json
from odoo import http, _
from odoo.http import request

class HrAppraisalApiController(http.Controller):

    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, default=str),
            headers=[('Content-Type', 'application/json')],
            status=status
        )

    @http.route('/api/v1/appraisals', type='http', auth='user', methods=['GET'], csrf=False)
    def list_appraisals(self, **kwargs):
        """Retrieve appraisals visible to the authenticated user."""
        domain = []
        user = request.env.user
        
        is_hr = user.has_group('hr_appraisal_pro.group_appraisal_officer')
        if not is_hr:
            domain = ['|', ('employee_user_id', '=', user.id), ('manager_user_id', '=', user.id)]

        appraisals = request.env['hr.appraisal'].search(domain, order='date_close asc')
        results = [{
            'id': app.id,
            'name': app.name,
            'employee_id': app.employee_id.id,
            'employee_name': app.employee_id.name,
            'manager_name': app.manager_id.name if app.manager_id else None,
            'department': app.department_id.name if app.department_id else None,
            'review_period': app.review_period,
            'date_start': str(app.date_start),
            'date_close': str(app.date_close),
            'stage': app.stage_id.name,
            'state': app.state,
            'final_score': app.final_score,
            'is_overdue': app.is_overdue,
        } for app in appraisals]

        return self._json_response({'status': 'success', 'data': results})

    @http.route('/api/v1/appraisal/<int:appraisal_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_appraisal_detail(self, appraisal_id, **kwargs):
        """Retrieve detailed appraisal record with questionnaires and competencies."""
        appraisal = request.env['hr.appraisal'].browse(appraisal_id)
        if not appraisal.exists():
            return self._json_response({'status': 'error', 'message': 'Appraisal not found'}, status=404)

        data = {
            'id': appraisal.id,
            'name': appraisal.name,
            'employee': {
                'id': appraisal.employee_id.id,
                'name': appraisal.employee_id.name,
                'job_position': appraisal.job_id.name if appraisal.job_id else None,
                'department': appraisal.department_id.name if appraisal.department_id else None,
            },
            'manager': {
                'id': appraisal.manager_id.id if appraisal.manager_id else None,
                'name': appraisal.manager_id.name if appraisal.manager_id else None,
            },
            'dates': {
                'start_date': str(appraisal.date_start),
                'deadline': str(appraisal.date_close),
                'completed_date': str(appraisal.date_completed) if appraisal.date_completed else None,
            },
            'scores': {
                'competency_score': appraisal.competency_score,
                'goal_score': appraisal.goal_score,
                'calculated_score': appraisal.calculated_score,
                'final_score': appraisal.final_score,
            },
            'stage': {
                'id': appraisal.stage_id.id,
                'name': appraisal.stage_id.name,
                'state': appraisal.state,
            },
            'competencies': [{
                'id': comp.id,
                'name': comp.competency_id.name,
                'category': comp.category_id.name,
                'weight': comp.weight,
                'self_score': comp.self_score,
                'manager_score': comp.manager_score,
                'final_score': comp.final_score,
                'manager_comments': comp.manager_comments,
            } for comp in appraisal.competency_line_ids],
            'goals': [{
                'id': g.id,
                'name': g.name,
                'weight': g.weight,
                'progress': g.progress,
                'status': g.status,
                'due_date': str(g.due_date),
            } for g in appraisal.goal_ids],
        }

        return self._json_response({'status': 'success', 'data': data})

    @http.route('/api/v1/appraisal/<int:appraisal_id>/submit_self', type='http', auth='user', methods=['POST'], csrf=False)
    def submit_self_assessment(self, appraisal_id, **kwargs):
        """Submit self-assessment text and advance state."""
        appraisal = request.env['hr.appraisal'].browse(appraisal_id)
        if not appraisal.exists():
            return self._json_response({'status': 'error', 'message': 'Appraisal not found'}, status=404)

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            body = kwargs

        vals = {}
        for field in ['self_strengths', 'self_development_areas', 'self_career_aspirations', 'self_general_comments']:
            if field in body:
                vals[field] = body[field]

        if vals:
            appraisal.write(vals)

        try:
            appraisal.action_submit_self_assessment()
            return self._json_response({'status': 'success', 'message': 'Self-assessment submitted successfully.'})
        except Exception as e:
            return self._json_response({'status': 'error', 'message': str(e)}, status=400)

    @http.route('/api/v1/appraisal/<int:appraisal_id>/submit_manager', type='http', auth='user', methods=['POST'], csrf=False)
    def submit_manager_evaluation(self, appraisal_id, **kwargs):
        """Submit manager feedback and ratings."""
        appraisal = request.env['hr.appraisal'].browse(appraisal_id)
        if not appraisal.exists():
            return self._json_response({'status': 'error', 'message': 'Appraisal not found'}, status=404)

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
        except Exception:
            body = kwargs

        vals = {}
        for field in ['manager_overall_summary', 'manager_strengths', 'manager_weaknesses', 'manager_goals_feedback', 'promotion_recommendation']:
            if field in body:
                vals[field] = body[field]

        if vals:
            appraisal.write(vals)

        try:
            appraisal.action_submit_manager_review()
            return self._json_response({'status': 'success', 'message': 'Manager review completed successfully.'})
        except Exception as e:
            return self._json_response({'status': 'error', 'message': str(e)}, status=400)

    @http.route('/api/v1/appraisal/<int:appraisal_id>/validate_hr', type='http', auth='user', methods=['POST'], csrf=False)
    def validate_hr(self, appraisal_id, **kwargs):
        """HR final sign-off and validation."""
        if not request.env.user.has_group('hr_appraisal_pro.group_appraisal_officer'):
            return self._json_response({'status': 'error', 'message': 'Unauthorized. HR Officer access required.'}, status=403)

        appraisal = request.env['hr.appraisal'].browse(appraisal_id)
        if not appraisal.exists():
            return self._json_response({'status': 'error', 'message': 'Appraisal not found'}, status=404)

        try:
            appraisal.action_validate_hr()
            return self._json_response({'status': 'success', 'message': 'Appraisal validated and finalized.'})
        except Exception as e:
            return self._json_response({'status': 'error', 'message': str(e)}, status=400)

    @http.route('/api/v1/appraisal/dashboard_stats', type='http', auth='user', methods=['GET'], csrf=False)
    def get_dashboard_stats(self, **kwargs):
        """Fetch dashboard KPIs JSON."""
        data = request.env['hr.appraisal'].get_dashboard_metrics()
        return self._json_response({'status': 'success', 'data': data})
