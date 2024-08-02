import copy
from datetime import date, datetime

import xlsxwriter
from odoo import fields, api, models
from odoo.exceptions import ValidationError
import re
import io
import json


class LoilvBaseReport(models.AbstractModel):
    _name = 'loilv.base.report'
    _description = 'loilv.base.report'

    def data_export_excel(self, record):
        try:
            query_string = self.env[record.x_res_model].browse(int(record.x_res_id)).query_string
            pattern = r'\{(\w+)\}'
            variables = re.findall(pattern, query_string)
            variables = list(set(variables))
            params = {}
            for v in variables:
                if v == 'current_user':
                    params.update({v: self.env.user.id})
                elif v == 'current_company':
                    params.update({v: self.env.company.id})
                elif record._fields[f'x_{v}'].type in ('many2one'):
                    if record[f'x_{v}']:
                        params.update({v: record[f'x_{v}'].id})
                elif record._fields[f'x_{v}'].type in ('one2many', 'many2many'):
                    if record[f'x_{v}']:
                        params.update({v: record[f'x_{v}'].ids})
                elif record._fields[f'x_{v}'].type in ('boolean'):
                    params.update({v: record[f'x_{v}']})
                else:
                    params.update({v: str(record[f'x_{v}'])})

            # Biểu thức chính quy để tìm các phần {where: [...]}
            where_pattern = re.compile(r"{where:\s*\[([^]]+)\]}")

            # Tìm tất cả các phần {where: [...]}
            where_clauses = where_pattern.findall(query_string)
            if where_clauses:
                list_where = []
                for idx, clause in enumerate(where_clauses, start=1):
                    # print(f"Where Clause {idx}:\n{clause.strip()}\n")
                    where_match = clause
                    # where_match = re.search(r'\{where:\[(.*?)\]\}', query_string, re.DOTALL)
                    if where_match:
                        where_clause = where_match
                        split_pattern = r',\s*(?![^()]*\))'
                        conditions = re.split(split_pattern, where_clause)
                        final_conditions = []
                        for condition in conditions:
                            condition_pattern = r'\{(\w+)\}'
                            condition_variables = re.findall(condition_pattern, condition)
                            new_condition = condition
                            for key, value in params.items():
                                if key not in condition_variables or value in ('False', 'None'):
                                    continue
                                if isinstance(value, list):
                                    new_condition = new_condition.replace(f"={{{key}}}", f' = any(array{{{key}}})')
                                placeholder = f'{{{key}}}'
                                if placeholder in condition:
                                    if isinstance(value, str):
                                        value = value.split(',')
                                        if len(value) > 1:
                                            new_condition = new_condition.replace(f"='{{{key}}}'", f' like any(array{{{key}}})')
                                            value = value
                                        else:
                                            value = f"{value[0]}"
                                    if isinstance(value, bool):
                                        value = str(value).lower()
                                    new_condition = new_condition.replace(placeholder, str(value))
                            if re.search(r'\{(\w+)\}', new_condition, re.DOTALL):
                                continue
                            if not new_condition or new_condition == '':
                                continue
                            final_conditions.append(new_condition)

                        # Tạo phần where mới nếu có điều kiện
                        if final_conditions:
                            where_string = "where " + " and ".join(list(set(final_conditions)))
                        else:
                            where_string = ""

                        where_source = "{where:[" + clause + "]}"
                        query_string = query_string.replace(where_source, where_string)
                        list_where.append(where_string)

                self._cr.execute(query_string)
                data = [x for x in self._cr.dictfetchall()]
                return data
            else:
                data = self.env['res.utility'].execute_postgresql(query=query_string, param=[], build_dict=True)
                return data
        except Exception as e:
            return str(e)

    def get_excel_file(self, res_model, res_id):
        record = self.env[res_model].browse(int(res_id))
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        self.generate_xlsx_report(workbook, record=record)
        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file

    def generate_xlsx_report(self, workbook, record):
        data = self.data_export_excel(record)
        config_report = self.env[record.x_res_model].browse(int(record.x_res_id))
        titles = json.loads(config_report.title_json)
        if not data:
            raise ValidationError('Không có dữ liệu')
        formats = self.get_format_workbook(workbook)
        worksheet = workbook.add_worksheet(config_report.name)
        worksheet.set_row(0, 25)
        worksheet.set_row(4, 30)
        worksheet.write(0, 0, record._description, formats.get('header_format'))
        headers = list(data[-1].keys())
        for col_num, header in enumerate(headers):
            worksheet.write(2, col_num, titles.get(header, header), formats.get('title_format'))
        # Ghi dữ liệu (các giá trị của dictionary)
        max_record = 500000
        for row_num, entry in enumerate(data, start=3):
            if row_num == max_record:
                worksheet = workbook.add_worksheet(config_report.name)
                worksheet.set_row(0, 25)
                worksheet.set_row(4, 30)
                worksheet.write(0, 0, record._description, formats.get('header_format'))
                headers = list(data[-1].keys())
                for col_num, header in enumerate(headers):
                    worksheet.write(2, col_num, titles.get(header, header), formats.get('title_format'))

            for col_num, (key, value) in enumerate(entry.items()):
                try:
                    if isinstance(value, float):
                        worksheet.write(row_num, col_num, value, formats.get('float_number_format'))
                    elif isinstance(value, int):
                        worksheet.write(row_num, col_num, value, formats.get('int_number_format'))
                    elif isinstance(value, date):
                        worksheet.write(row_num, col_num, value, formats.get('date_format'))
                    elif isinstance(value, datetime):
                        worksheet.write(row_num, col_num, value, formats.get('datetime_format'))
                    else:
                        worksheet.write(row_num, col_num, value, formats.get('normal_format'))
                except:
                    worksheet.write(row_num, col_num, value, formats.get('normal_format'))

    def preview_excel_to_html(self, res_model, res_id):
        try:
            record = self.env[res_model].browse(int(res_id))
            data = self.data_export_excel(record)
            if not data:
                return []
            if isinstance(data, str):
                return [[], [data]]
            key_data = list(data[-1].keys())
            result = [list(d.values()) for d in data]
            headers = []
            titles = json.loads(self.env[record.x_res_model].browse(int(record.x_res_id)).title_json)
            for k in key_data:
                headers.append(titles.get(k, k))
            return [headers, result]
        except Exception as e:
            return [[], [str(e)]]

    @api.model
    def get_format_workbook(self, workbook):
        header_format = {
            'bold': 1,
            'size': 20
        }
        title_format = {
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#dbeef4',
            'text_wrap': True,
        }
        subtotal_format = {
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#c2f7ad'
        }
        normal_format = {
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        }
        datetime_format = {
            'num_format': "dd/mm/yy hh:mm:ss",
        }
        align_right = {'align': 'right'}
        datetime_format.update(normal_format)
        float_number_format = {}
        center_format = copy.copy(normal_format)
        right_format = copy.copy(normal_format)
        italic_format = copy.copy(normal_format)
        italic_format.update({
            'border': 0,
            'italic': 1,
        })
        int_number_format = {}
        date_format = {
            'num_format': "dd/mm/yyyy",
        }
        date_format.update(normal_format)
        center_format.update({'align': 'center'})
        right_format.update({'align': 'right'})
        float_number_format.update(normal_format)
        int_number_format.update(normal_format)
        int_number_format.update(align_right)
        float_number_title_format = float_number_format.copy()
        float_number_title_format.update(title_format)
        int_number_title_format = int_number_format.copy()
        int_number_title_format.update(title_format)
        center_format_bold = center_format.copy()
        center_format_bold.update({'bold': 1, 'border': 0})

        italic_format_center = italic_format.copy()
        italic_format_center.update({'align': 'center'})

        title_format = workbook.add_format(title_format)
        datetime_format = workbook.add_format(datetime_format)
        normal_format = workbook.add_format(normal_format)
        italic_format = workbook.add_format(italic_format)
        center_format = workbook.add_format(center_format)
        right_format = workbook.add_format(right_format)
        header_format = workbook.add_format(header_format)
        center_format_bold = workbook.add_format(center_format_bold)
        italic_format_center = workbook.add_format(italic_format_center)

        float_number_format.update(align_right)
        float_number_format = workbook.add_format(float_number_format)
        float_number_format.set_num_format('#,##0.00')
        percentage_format = int_number_format.copy()
        int_number_format = workbook.add_format(int_number_format)
        int_number_format.set_num_format('#,##0')
        int_subtotal_format = workbook.add_format(subtotal_format)
        int_subtotal_format.set_num_format('#,##0')
        int_subtotal_format.set_align('right')
        subtotal_format = workbook.add_format(subtotal_format)
        percentage_format.update({'align': 'right', 'num_format': '0%'})
        percentage_format = workbook.add_format(percentage_format)

        float_number_title_format = workbook.add_format(float_number_title_format)
        float_number_title_format.set_num_format('#,##0.00')
        int_number_title_format = workbook.add_format(int_number_title_format)
        int_number_title_format.set_num_format('#,##0')
        date_format = workbook.add_format(date_format)

        return {
            'header_format': header_format,
            'title_format': title_format,
            'datetime_format': datetime_format,
            'date_format': date_format,
            'normal_format': normal_format,
            'italic_format': italic_format,
            'center_format': center_format,
            'right_format': right_format,
            'float_number_format': float_number_format,
            'int_number_format': int_number_format,
            'float_number_title_format': float_number_title_format,
            'int_number_title_format': int_number_title_format,
            'subtotal_format': subtotal_format,
            'int_subtotal_format': int_subtotal_format,
            'percentage_format': percentage_format,
            'center_format_bold': center_format_bold,
            'italic_format_center': italic_format_center,
        }