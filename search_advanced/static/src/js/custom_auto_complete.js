/** @odoo-module **/

import {AutoComplete} from "@web/core/autocomplete/autocomplete";


export class CustomAutoComplete extends AutoComplete {
}

CustomAutoComplete.template = 'CustomAutocomplete'
CustomAutoComplete.props = {
    ...AutoComplete.props
}
CustomAutoComplete.defaultProps = {
    ...AutoComplete.defaultProps,
}
