from odoo import fields, api, models


class InheritModel(models.Model):
    _inherit = 'ir.model'

    @api.model
    def _instanciate(self, model_data):
        model_class = super(InheritModel, self)._instanciate(model_data)
        if self._context.get('inherit_model') != 'loilv.base.report':
            parents = model_class._inherit or []
            parents = [parents] if isinstance(parents, str) else parents
            model_class._inherit = parents + ['loilv.base.report']
        return model_class