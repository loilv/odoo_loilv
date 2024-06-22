from odoo import http, _
from odoo.http import request, _logger


class MainApi(http.Controller):
    @http.route(['/api/get_ids'], type='json', cors='*', auth="public", csrf=False,
                methods=['PUT', 'POST'])
    def get_rec_name(self, model=None, kw=None, **post):
        if model:
            ids = request.env[model].sudo().name_search(name=kw, limit=8)
            return [id[0] for id in ids]
        return False
