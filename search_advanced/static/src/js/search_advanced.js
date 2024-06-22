/** @odoo-module **/
import {Component, useState, onMounted, useExternalListener, useRef, useEffect} from "@odoo/owl";
import {ControlPanel} from "@web/search/control_panel/control_panel";
import {patch} from "@web/core/utils/patch";
import {AutoComplete} from "@web/core/autocomplete/autocomplete";
import {useService, useAutofocus} from "@web/core/utils/hooks";
import {fuzzyLookup} from "@web/core/utils/search";
import {CustomAutoComplete} from "./custom_auto_complete";
import {useChildRef} from "@web/core/utils/hooks";
import {KeepLast} from "@web/core/utils/concurrency";
import {Domain} from "@web/core/domain";
import {TagsList} from "@web/views/fields/many2many_tags/tags_list";
import {DateTimePicker, DatePicker} from "@web/core/datepicker/datepicker";
import {
    formatDate,
    serializeDate,
} from "@web/core/l10n/dates";


patch(ControlPanel.prototype, "search_advanced", {
    setup() {
        this._super(...arguments);
        this.fieldState = {}
        this.listField = []
        if (this.env.searchModel && this.env.searchModel.searchItems) {
            for (const [key, value] of Object.entries(this.env.searchModel.searchItems)) {
                if (value.fieldType === "selection") {
                    value['selection'] = this.env.searchModel.searchViewFields[value['fieldName']].selection
                }
                if (value.type === 'field') {
                    this.listField.push(value)
                    this.fieldState[value.fieldName] = ''
                }
            }
        }
    },

    toggleSearch() {
        const $el = $(this.root.el)
        $el.find('#search_advanced_body').toggle()

    },
    onClickSearchAdvanced() {
        this.env.config.querySearch.query.push(this.env.config.querySearchInput)
        _.each(this.env.config.querySearch.query, (q) => {
            for (const [key, value] of Object.entries(q)) {
                this.env.searchModel.addAutoCompletionValues(value.id, value.value)
            }
        })
        this.env.searchModel.createNewFilters(this.env.config.domainFilter.filter);
        this.env.config.domainFilter.filter = []
    },
    onClickRemove() {
        const $el = $(this.root.el)
        $el.find('.o_facet_remove').click()
        this.env.config.querySearchInput = {};
        this.env.config.querySearch.query = [];
        $el.find('.o_s_input').val('');
        $el.find('.o_input').val('');
        $el.find('.o_datepicker_input').val('');
        $el.find('.o_tag_color_0').remove()
    },
    get getFieldSearch() {
        return this.listField
    },
    fieldProps(field) {
        let operator = 'ilike'
        if (field.operator) {
            operator = field.operator
        } else if (field.fieldType !== 'char') {
            operator = '='
        }
        console.log(field, 1111111111)
        return {
            fieldDescription: field.description,
            selection: field.selection,
            resModel: this.env.searchModel.searchViewFields[field.fieldName].relation,
            fieldType: field.fieldType,
            fieldName: field.fieldName,
            domain: field.domain,
            id: field.id,
            operator: operator
        }
    }

});


export class SearchAdvanced extends Component {
    setup() {
        this.orm = useService("orm");
        this.rpc = useService('rpc')
        this.pager = useState({offset: 0, limit: 20});
        this.keepLast = new KeepLast();
        this.dataSearch = useState({data: []})
        this.onFocus = ''
        this.inputRef = useChildRef();
        this.domainSearch = useState({domain: []})
        this.env.config.domainFilter = useState({filter: [], domainArray: []})
        this.domainArray = []
        this.env.config.querySearch = useState({query: []})
        this.env.config.querySearchInput = {}
        const {fieldDescription, resModel, fieldType, fieldName, id, operator} = this.props;
        this.dataTags = useState({data: []})
    }


    async _updateInputValue(event) {
        this.env.config.querySearchInput = {}
        let query = {}
        if (event.target.value) {
            query[event.target.dataset.field] = {}
            query[event.target.dataset.field]['id'] = event.target.dataset.id
            query[event.target.dataset.field]['value'] = {}
            query[event.target.dataset.field]['value']['label'] = event.target.value
            query[event.target.dataset.field]['value']['operator'] = 'ilike'
            query[event.target.dataset.field]['value']['value'] = event.target.value
        } else {
            query = {}
        }
        this.env.config.querySearchInput = query
    }

    onSelect(option) {
        let query = {}
        if (option.id) {
            query = {}
            query[option.id] = {}
            query[option.id]['id'] = this.props.id
            query[option.id]['value'] = {}
            query[option.id]['value']['label'] = option.label
            query[option.id]['value']['operator'] = this.props.operator
            query[option.id]['value']['value'] = option.res_id
            const item = {
                resId: option.res_id,
                text: option.label,
                onDelete: () => this.deleteTag(option.res_id, option.id, this.props.id),
            }
            this.dataTags.data.push(item)
        }
        this.env.config.querySearch.query.push(query)
    }

    deleteTag(id, option_id, props_id) {
        this.dataTags.data.splice(this.dataTags.data.findIndex(v => v.resId === id), 1);
        this.env.config.querySearch.query.splice(this.env.config.querySearch.query.findIndex(v => v.id === props_id), 1);
    }

    get sources() {
        if (this.props.fieldType === 'selection') {
            let optionValue = []
            this.props.selection.forEach(function (i, v) {
                optionValue.push({
                    'id': i[0],
                    'label': i[1],
                    'res_id': i[0]
                })
            })
            return [
                {
                    placeholder: this.env._t("Loading..."),
                    options: optionValue,
                },
            ];
        }
        return [
            {
                placeholder: this.env._t("Loading..."),
                options: this.loadOptionsSources.bind(this),
            },
        ];
    }

    async loadDataSources() {
        const {limit, offset} = this.pager;
        if (this.props.domain) {
            const cleanedString = this.props.domain.replace(/[\[\]\(\)']/g, '');
            const subArray = cleanedString.split(', ');
            const subarraySize = 3;
            const nestedArray = [];
            for (let i = 0; i < subArray.length; i += subarraySize) {
                this.domainSearch.domain.push(subArray.slice(i, i + subarraySize));
            }
        }
        return this.orm.webSearchRead(this.props.resModel, this.domainSearch.domain, ["display_name"], {
            limit: limit,
            offset: offset,
        });
    }

    async loadOptionsSources(request) {
        const datas = await this.loadDataSources();
        this.dataSearchPass = datas.records.map((record) => ({
            label: record.display_name,
            res_id: record.id,
        }));
        if (!request) {
            return this.dataSearchPass.slice(0, 8);
        }
        const fuzzySearch = fuzzyLookup(request, this.dataSearchPass, (d) => d.label).slice(0, 8);
        if (!fuzzySearch.length) {
            fuzzySearch.push({
                label: this.env._t("No records"),
                classList: "o_m2o_no_result",
                unselectable: true,
            });
        }
        return fuzzySearch;
    }

    async onChangeSearchField(event) {
        if (this.props.fieldType === 'selection') {
            return false;
        }
        let finalArray = []
        if (this.props.domain) {
            const cleanedString = this.props.domain.replace(/[\[\]\(\)']/g, '');
            const subArray = cleanedString.split(', ');
            const subarraySize = 3;
            const nestedArray = [];
            for (let i = 0; i < subArray.length; i += subarraySize) {
                finalArray.push(subArray.slice(i, i + subarraySize));
            }
        }
        const ids = await this.rpc('/api/get_ids', {'model': this.props.resModel, 'kw': event.target.value});
        finalArray.push(['id', 'in', ids])
        this.domainSearch.domain = finalArray
        this.pager.offset = 0;
        const {length, records} = await this.keepLast.add(this.loadDataSources());
        this.dataSearch.data = records;
        this.pager.total = length;
    }

    get tags() {
        return this.dataTags.data
    }

    async onValueChangeTo(newValue) {
        if (newValue) {
            const field = this.props.fieldName
            const type = this.props.fieldType
            const description = this.props.fieldDescription
            const id = this.props.id
            this.env.config.domainFilter.domainArray.push([field, '<=', serializeDate(newValue)])
            this.domainArray.push(formatDate(newValue))
            this.env.config.domainFilter.filter.push({
                "description": `${description} trong khoảng ${this.domainArray[0]} - ${this.domainArray[1]}`,
                "domain": new Domain(this.env.config.domainFilter.domainArray).toString(),
                "type": "filter",
                "groupId": id,
                "id": id
            })
        }
    }

    async onValueChangeFrom(newValue) {
        if (newValue) {
            const field = this.props.fieldName
            this.env.config.domainFilter.domainArray = []
            this.env.config.domainFilter.domainArray.push([field, '>=', serializeDate(newValue)])
            this.domainArray.push(formatDate(newValue))
        }
    }
}

SearchAdvanced.template = 'SearchAdvancedFormView'
SearchAdvanced.components = {AutoComplete, CustomAutoComplete, TagsList, DateTimePicker, DatePicker}

patch(ControlPanel, "controller_panel_add_component", {
    components: {...ControlPanel.components, SearchAdvanced}
});

