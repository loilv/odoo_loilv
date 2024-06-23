from odoo import fields, api, models, SUPERUSER_ID
import xml.etree.ElementTree as ET

from odoo.modules import get_resource_path

FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]


class LoiLVReportSetup(models.Model):
    _name = 'loilv.report.list'
    _description = 'Cấu hình báo cáo'

    name = fields.Char(string='Tên báo cáo')
    report_type = fields.Selection([
        ('stock', 'Báo cáo kho'),
        ('sale', 'Báo cáo bán hàng'),
        ('purchase', 'Báo cáo mua hàng'),
        ('accounting', 'Báo cáo kế toán'),
        ('other', 'Báo cáo khác'),
    ], string='Loại báo cáo')
    model_name = fields.Char(string='Tên model')
    query_string = fields.Text(string='Câu truy vấn')
    title_json = fields.Text('Json title', default={})
    setup_params = fields.One2many('loilv.report.setup.parameter', 'report_id', string='Cấu hình đầu vào')
    access_ids = fields.One2many('loilv.report.access', 'report_id', string='Cấu hình quyền')
    model_id = fields.Many2one('ir.model')
    view_id = fields.Many2one('ir.ui.view')
    action_id = fields.Many2one('ir.actions.act_window')
    menu_id = fields.Many2one('ir.ui.menu')

    def create_view_from_xml(self):
        ir_view = self.env['ir.ui.view']
        path = get_resource_path('loilv_report_advanced', 'data', 'xml_default.txt')
        with open(path, 'r', encoding='utf-8') as file:
            xml_string = file.read()
        xml_string_from_tree = xml_string
        string_left = ''
        string_right = ''
        for param in self.setup_params:
            if param.ttype == 'many2many':
                field_str = """
                <field name="x_%s" widget='many2many_tags' options=\"{'no_create': True}\"/>
                """ % (param.name)
            elif param.ttype == 'many2one':
                field_str = """
                <field name="x_%s" options=\"{'no_create': True}\"/>
                """ % (param.name)
            else:
                field_str = """
                <field name="x_%s"/>
                """ % (param.name)

            if param.group == '1':
                string_left += field_str
            else:
                string_right += field_str
        xml_string = xml_string_from_tree % (
            string_left,
            string_right
        )
        return ir_view.create({
            "name": self.name,
            "model": f"x_{self.model_name}",
            "type": "form",
            "mode": "primary",
            "active": True,
            "arch_prev": xml_string,
            "arch_db": xml_string

        })

    def create_action_menu(self):
        ir_action = self.env['ir.actions.act_window']
        ir_action = ir_action.create({
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': f"x_{self.model_name}",
            'view_mode': "form",
            'context': {
                'default_x_res_id': self.id,
                'default_x_res_model': self._name,
                'default_x_name': self.name
            }
        })

        menu = self.env['ir.ui.menu'].create({
            'name': self.name,
            'parent_id': self.env.ref('loilv_report_advanced.loilv_setup_report_public_root').id,
            'action': 'ir.actions.act_window,{}'.format(ir_action.id),
        })
        self.menu_id = menu.id
        self.action_id = ir_action.id
        return ir_action

    def prepare_value_create_model_report(self):
        params = []
        for param in self.setup_params:
            params.append((0, 0, {
                'name': f"x_{param.name}",
                'field_description': param.description,
                'ttype': param.ttype,
                'required': param.required,
                'relation': param.relation,
                'domain': param.domain,

            }))
        params += [
            (0, 0, {
                'name': f"x_res_id",
                'field_description': 'Report',
                'ttype': 'integer',
            }),
            (0, 0, {
                'name': f"x_res_model",
                'field_description': 'Report',
                'ttype': 'char',
            }),
            (0, 0, {
                'name': f"x_name",
                'field_description': 'Name',
                'ttype': 'char',
            })
        ]

        access = []
        for _ac in self.access_ids:
            access.append((0, 0, {
                'name': _ac.name,
                'group_id': _ac.group_id.id,
                'perm_read': _ac.perm_read,
                'perm_write': _ac.perm_write,
                'perm_create': _ac.perm_create

            }))
        return {
            'name': self.name,
            'model': f"x_{self.model_name}",
            'transient': True,
            'state': 'manual',
            'field_id': params,
            'access_ids': access
        }

    def confirm(self):
        self.del_model()
        report_model = self.env['ir.model'].create(self.prepare_value_create_model_report())
        report_view = self.create_view_from_xml()
        self.model_id = report_model.id
        self.view_id = report_view.id
        action = self.create_action_menu().read()[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Đã tạo thành công báo cáo %s' % self.name,
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }

    def del_model(self):
        if self.model_id and self.view_id:
            self.env[self.model_id.model].search([]).sudo().unlink()
            self.action_id.sudo().unlink()
            self.menu_id.sudo().unlink()
            self.view_id.sudo().unlink()
            self.model_id.sudo().unlink()

    def unlink(self):
        for rec in self:
            rec.del_model()
        return super().unlink()

    def view_report(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': f"x_{self.model_name}",
            'view_id': False,
            'view_mode': 'form',
            'context': {
                'default_x_res_id': self.id,
                'default_x_res_model': self._name,
                'default_x_name': self.name,
            },
            'target': 'current',
        }

    def write_query_string(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('loilv_report_advanced.loilv_report_list_view_view_form_query').id, 'form')],
            'target': 'current',
        }

    def write_title_excel(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('loilv_report_advanced.loilv_report_list_view_view_form_json').id, 'form')],
            'target': 'current',
        }


class LoiLVReportSetupParameter(models.Model):
    _name = 'loilv.report.setup.parameter'
    _description = 'Cấu hình đầu vào báo cáo'

    report_id = fields.Many2one('loilv.report.list')
    name = fields.Char(string='Tên trường')
    description = fields.Char(string='Mô tả trường')
    ttype = fields.Selection(selection=FIELD_TYPES, string='Kiểu dữ liệu', required=True)
    relation = fields.Char(string='Tên model quan hệ')
    domain = fields.Char(string='Tên miền', default="[]")
    many2many_model = fields.Char(string='Bảng trung gian')
    column_1 = fields.Char(string='Cột 1')
    column_2 = fields.Char(string='Cột 2')
    group = fields.Selection([('1', 'Hiển thị trái'), ('2', 'Hiển thị phải')], string='Cách hiển thị')
    required = fields.Boolean(string='Bắt buộc', default=False)


class LoiLVReportResponseSetup(models.Model):
    _name = 'loilv.report.setup.response'
    _description = 'Cấu hình đầu ra báo cáo'

    name = fields.Char(string='Tên truờng')
    description = fields.Char(string='Mô tả')


class LoilvReportAccess(models.Model):
    _name = 'loilv.report.access'
    _description = 'Quyền truy cập báo cáo'

    report_id = fields.Many2one('loilv.report.list')
    name = fields.Char(string='Tên quyền')
    group_id = fields.Many2one('res.groups', string='Nhóm quyền')
    perm_read = fields.Boolean(string='Quyền đọc', default=True)
    perm_write = fields.Boolean(string='Quyền ghi', default=True)
    perm_create = fields.Boolean(string='Quyền tạo', default=True)
