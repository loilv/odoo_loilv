/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import * as actionService from "@web/webclient/actions/action_service";
import {registry} from "@web/core/registry";

function _getReportUrl(action, type) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};
    if (action.data && JSON.stringify(action.data) !== "{}") {
        // build a query string with `action.data` (it's the place where reports
        // using a wizard to customize the output traditionally put their options)
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }
        if (type === "html") {
            const context = encodeURIComponent(JSON.stringify(env.services.user.context));
            url += `?context=${context}`;
        }
    }
    return url;
}

async function _triggerPreviewAfterPrintPDF(action, options, type) {
    if (action.report_type === 'qweb-pdf') {
        const url = _getReportUrl(action, 'pdf');
        window.open(url, '_blank');
        return true;
    }
}

patch(actionService, 'preview_pdf patching', {
    async _triggerDownload(action, options, type) {
        return _triggerDownloadCustomPrintPDF(action, options, type)
    }
})

registry.category("ir.actions.report handlers").add("preview_pdf", _triggerPreviewAfterPrintPDF);