/** @odoo-module **/
import {FormRenderer} from "@web/views/form/form_renderer";
import {FormController} from "@web/views/form/form_controller";
import {loadJS, loadCSS} from "@web/core/assets";

const Dialog = require('web.Dialog');
import {formView} from '@web/views/form/form_view';
import {registry} from "@web/core/registry"

const {useRef, onPatched, onMounted, useState, onWillStart} = owl;

export class LoilvReportAdvancedController extends FormController {

}

export class LoilvReportAdvancedRenderer extends FormRenderer {
    setup() {
        super.setup();
        this.headers = useState({
            data: null
        })
        this.dataTable = null
        onWillStart(() =>
            loadJS("/forlife_report_advanced/static/src/libs/datatables.min.js")
        );
    }

    async previewData() {
        const self = this
        const root = this.env.model.root
        await root.save()
        const model = root.resModel
        const id = root.data.id
        if (!id) {
            return false
        }
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
                const result = JSON.parse(data)
                if (self.dataTable) {
                    self.dataTable.clear().draw();
                    self.dataTable.rows.add(result[1]).draw()
                    return true
                } else {
                    let title = []
                    _.each(result[0], function (t) {
                        title.push({'title': t})
                    })
                    self.dataTable = $('#table-preview').DataTable({
                        columns: title,
                        data: result[1]
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
        if (!id) {
            return false
        }
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
    Renderer: LoilvReportAdvancedRenderer,
    Controller: LoilvReportAdvancedController
};
registry.category("views").add("loilv_report_advanced_form", JsClassExportExcel);