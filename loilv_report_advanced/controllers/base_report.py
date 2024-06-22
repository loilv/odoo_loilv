import json

from odoo import http, _
from odoo.http import request, _logger
from odoo.tools import date_utils


class MainApi(http.Controller):

    @http.route(['/download/stream_api'], type='http', cors=False, auth="none", csrf=False,
                methods=['PUT', 'POST', 'GET'])
    def export_excel(self, **kwargs):
        context = json.loads(kwargs.get('context', False))
        user = request.env.user.browse(request.env.context.get('uid'))
        data = request.env['loilv.base.report'].sudo().browse(int(kwargs.get('id'))).with_user(user).with_context(
            context).get_excel_file(kwargs.get('model', False), kwargs.get('id'))

        # Tạo response HTTP
        response = request.make_response(
            data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=export_excel.xlsx;')
            ])

        return response

    @http.route(['/preview/stream_api'], type='http', cors=False, auth="none", csrf=False,
                methods=['PUT', 'POST', 'GET'])
    def preview_excel(self, **kwargs):
        context = json.loads(kwargs.get('context', False))
        user = request.env.user.browse(request.env.context.get('uid'))
        data = request.env['loilv.base.report'].sudo().browse(int(kwargs.get('id'))).with_user(user).with_context(
            context).preview_excel_to_html(kwargs.get('model', False), kwargs.get('id'))
        return json.dumps(data, default=date_utils.json_default)
