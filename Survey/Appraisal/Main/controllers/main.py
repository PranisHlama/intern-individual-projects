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

    @http.route('/appraisal/survey/portal/<int:survey_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def survey_portal(self, survey_id, **kwargs):
        """Google Forms Lookalike Web Portal for Appraisal Surveys."""
        survey = request.env['hr.appraisal.survey'].sudo().browse(survey_id)
        if not survey.exists():
            return request.not_found()

        if not survey.answer_ids and survey.state != 'submitted':
            survey.action_load_questions()

        is_success = kwargs.get('success') == '1' or survey.state == 'submitted'
        survey_type_label = dict(survey._fields['survey_type'].selection).get(survey.survey_type, 'Appraisal Survey')
        job_title = survey.job_id.name if survey.job_id else 'Staff Member'

        if is_success:
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{survey_type_label} - Response Recorded</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: #f0ebf8;
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 24px 16px;
            display: flex;
            justify-content: center;
        }}
        .gform-container {{
            width: 100%;
            max-width: 640px;
        }}
        .gform-card {{
            background: #ffffff;
            border: 1px solid #dadce0;
            border-radius: 8px;
            padding: 28px 32px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(60,64,67,0.15);
        }}
        .gform-header-card {{
            border-top: 10px solid #673ab7;
        }}
        .gform-title {{
            font-size: 28px;
            font-weight: 400;
            color: #202124;
            margin: 0 0 12px 0;
        }}
        .gform-msg {{
            font-size: 14px;
            color: #202124;
            line-height: 1.5;
            margin-bottom: 24px;
        }}
        .gform-link {{
            color: #673ab7;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }}
        .gform-link:hover {{
            text-decoration: underline;
        }}
        .gform-badge {{
            display: inline-block;
            background: #e6f4ea;
            color: #137333;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="gform-container">
        <div class="gform-card gform-header-card">
            <span class="gform-badge">✓ Submitted</span>
            <h1 class="gform-title">{survey_type_label}</h1>
            <div class="gform-msg">
                Your response has been recorded.<br>
                Thank you for completing the performance review survey for <b>{job_title}</b>.
            </div>
            <a href="javascript:window.close();" class="gform-link">Close window</a>
        </div>
    </div>
</body>
</html>"""
            return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

        # Render Google Forms Questionnaire Page
        questions_html = ""
        for i, ans in enumerate(survey.answer_ids, 1):
            req_star = '<span style="color:#d93025;"> *</span>' if ans.is_required else ''
            desc_html = f'<div style="font-size:12px; color:#70757a; margin-top:4px;">{ans.description}</div>' if ans.description else ''
            
            # Horizontal radio scale (1 to 5) like Google Forms Linear Scale
            scale_options = ""
            for val in ['1', '2', '3', '4', '5']:
                checked = 'checked' if ans.rating == val else ''
                scale_options += f"""
                <label style="display:flex; flex-direction:column; align-items:center; cursor:pointer; min-width:44px;">
                    <span style="font-size:12px; color:#5f6368; margin-bottom:6px;">{val}</span>
                    <input type="radio" name="rating_{ans.id}" value="{val}" {checked} {'required' if ans.is_required else ''} style="accent-color:#673ab7; width:18px; height:18px; cursor:pointer;">
                </label>"""

            questions_html += f"""
            <div class="gform-card">
                <div style="font-size:15px; font-weight:500; color:#202124; margin-bottom:8px;">
                    {i}. {ans.question_name}{req_star}
                </div>
                {desc_html}
                <div style="display:flex; align-items:center; justify-content:space-between; margin:20px 0; padding:0 8px;">
                    <span style="font-size:13px; color:#70757a;">{ans.rating_label_min or 'Poor'}</span>
                    <div style="display:flex; gap:16px;">
                        {scale_options}
                    </div>
                    <span style="font-size:13px; color:#70757a;">{ans.rating_label_max or 'Excellent'}</span>
                </div>
                <div style="margin-top:12px;">
                    <input type="text" name="comment_{ans.id}" value="{ans.comments or ''}" placeholder="Remarks / Evidence (optional)" style="width:100%; border:none; border-bottom:1px solid #dadce0; padding:8px 0; font-size:14px; outline:none; font-family:inherit; transition:border 0.2s;" onfocus="this.style.borderBottom='2px solid #673ab7'" onblur="this.style.borderBottom='1px solid #dadce0'">
                </div>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{survey_type_label} - Google Forms Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: #f0ebf8;
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 24px 16px;
            display: flex;
            justify-content: center;
        }}
        .gform-container {{
            width: 100%;
            max-width: 640px;
        }}
        .gform-card {{
            background: #ffffff;
            border: 1px solid #dadce0;
            border-radius: 8px;
            padding: 24px 28px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(60,64,67,0.12), 0 1px 2px rgba(60,64,67,0.24);
        }}
        .gform-header-card {{
            border-top: 10px solid #673ab7;
            padding-top: 24px;
        }}
        .gform-title {{
            font-size: 28px;
            font-weight: 400;
            color: #202124;
            margin: 0 0 10px 0;
        }}
        .gform-desc {{
            font-size: 13.5px;
            color: #5f6368;
            line-height: 1.5;
            margin-bottom: 16px;
        }}
        .gform-required-note {{
            color: #d93025;
            font-size: 12.5px;
            font-weight: 500;
        }}
        .gform-field-label {{
            font-size: 15px;
            font-weight: 500;
            color: #202124;
            margin-bottom: 8px;
            display: block;
        }}
        .gform-btn-submit {{
            background-color: #673ab7;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 10px 28px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            transition: background 0.2s, box-shadow 0.2s;
        }}
        .gform-btn-submit:hover {{
            background-color: #512da8;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }}
        .gform-btn-clear {{
            background: transparent;
            color: #5f6368;
            border: none;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
        }}
        .gform-btn-clear:hover {{
            color: #202124;
        }}
        .gform-textarea {{
            width: 100%;
            border: 1px solid #dadce0;
            border-radius: 4px;
            padding: 10px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            box-sizing: border-box;
            resize: vertical;
            min-height: 80px;
        }}
        .gform-textarea:focus {{
            border-color: #673ab7;
        }}
    </style>
</head>
<body>
    <div class="gform-container">
        <form action="/appraisal/survey/portal/{survey_id}/submit" method="POST">
            <!-- Header Card -->
            <div class="gform-card gform-header-card">
                <h1 class="gform-title">{survey_type_label}</h1>
                <div class="gform-desc">
                    Performance appraisal evaluation form for <b>{job_title}</b>. All ratings are scored on a scale from 1 (Poor) to 5 (Excellent).
                </div>
                <div class="gform-required-note">* Indicates required question</div>
            </div>

            <!-- Respondent Information Card (Only Job Position & Survey Type) -->
            <div class="gform-card">
                <div class="gform-field-label">Job Position <span style="color:#d93025;">*</span></div>
                <div style="font-size:14px; color:#202124; margin-bottom:16px; font-weight:500;">
                    {job_title}
                </div>
                <div class="gform-field-label">Survey Type <span style="color:#d93025;">*</span></div>
                <div style="font-size:14px; color:#202124;">
                    {survey_type_label}
                </div>
                <!-- Date of Submission: Hidden as explicitly requested -->
            </div>

            <!-- Dynamic Questions Generated by Top Level Managers -->
            {questions_html}

            <!-- Overall Feedback Card -->
            <div class="gform-card">
                <div class="gform-field-label">Overall Reflections &amp; Recommendations</div>
                <div style="font-size:12px; color:#70757a; margin-bottom:8px;">
                    Provide any general feedback, milestone takeaways, or development recommendations.
                </div>
                <textarea name="general_feedback" class="gform-textarea" placeholder="Your answer">{survey.general_feedback or ''}</textarea>
            </div>

            <!-- Footer / Submit -->
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
                <button type="submit" class="gform-btn-submit">Submit</button>
                <a href="javascript:window.close();" class="gform-btn-clear">Clear form</a>
            </div>
        </form>
    </div>
</body>
</html>"""
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route('/appraisal/survey/portal/<int:survey_id>/submit', type='http', auth='public', methods=['POST'], csrf=False)
    def survey_portal_submit(self, survey_id, **post):
        """Processes submission of Google Forms styled survey."""
        survey = request.env['hr.appraisal.survey'].sudo().browse(survey_id)
        if not survey.exists():
            return request.not_found()

        for ans in survey.answer_ids:
            rating_key = f'rating_{ans.id}'
            comment_key = f'comment_{ans.id}'
            vals = {}
            if rating_key in post:
                vals['rating'] = post[rating_key]
            if comment_key in post:
                vals['comments'] = post[comment_key]
            if vals:
                ans.write(vals)

        if 'general_feedback' in post:
            survey.general_feedback = post['general_feedback']

        survey.action_submit()
        return request.redirect(f'/appraisal/survey/portal/{survey_id}?success=1')
