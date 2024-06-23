/** @odoo-module **/
import {FormRenderer} from "@web/views/form/form_renderer";
import {loadJS} from "@web/core/assets";
const Dialog = require('web.Dialog');
import {formView} from '@web/views/form/form_view';
import {registry} from "@web/core/registry"

const {useRef, onPatched, onMounted, useState, onWillStart} = owl;

export class LoilvReportAdvancedRenderer extends FormRenderer {
    setup() {
        super.setup();
        this.headers = useState({
            data: []
        })
        this.dataTable = null
        onWillStart(() =>
            loadJS("/loilv_report_advanced/static/src/libs/datatables.min.js")
        );
    }

    async previewData() {
        const self = this
        const root = this.env.model.root
        await root.save()
        const model = root.resModel
        const id = root.data.id
        self.env.services.ui.block();
        $.ajax({
            url: '/preview/stream_api',
            type: 'POST',
            data: {
                'model': model,
                'id': id,
                'company_id': this.env.model.root.context.allowed_company_ids,
                'context': JSON.stringify(root.context)
            },
            success: async function (data) {
                self.env.services.ui.unblock();
                const result = JSON.parse(data);

                self.headers.data = result.length === 0 ? [] : result[0].map(t => ({'title': t}));
                if (self.headers.data.length === 0 || (Array.isArray(result) && result.length === 0)) {
                    if (self.dataTable) {
                        self.dataTable.clear().draw();
                    }
                    alert('Không có dữ liệu!.')
                    return;
                }

                if (self.dataTable) {
                    self.dataTable.clear().draw();
                    self.dataTable.rows.add(result[1]).draw();
                } else {
                    self.dataTable = $('#table-preview').DataTable({
                        columns: self.headers.data,
                        data: result[1],
                        order: [],
                    });
                }
            },
            error: function () {
                self.env.services.ui.unblock();
            }
        });

    }

    async downloadData() {
        const self = this
        const root = this.env.model.root
        await root.save()
        const model = root.resModel
        const id = root.data.id
        self.env.services.ui.block();
        $.ajax({
            url: '/download/stream_api',
            type: 'POST',
            data: {
                'model': model,
                'id': id,
                'company_id': this.env.model.root.context.allowed_company_ids,
                'context': JSON.stringify(root.context)
            },
            xhrFields: {
                responseType: 'blob'
            },
            success: function (data) {
                self.env.services.ui.unblock();
                var a = document.createElement('a');
                var url = window.URL.createObjectURL(data);
                a.href = url;
                a.download = root.data.display_name + '.xlsx';
                document.body.append(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            },
            error: function () {
                self.env.services.ui.unblock();
            }
        });
    }
}

export const JsClassExportExcel = {
    ...formView,
    Renderer: LoilvReportAdvancedRenderer
};
registry.category("views").add("loilv_report_advanced_form", JsClassExportExcel);