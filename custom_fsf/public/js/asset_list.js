frappe.listview_settings["Asset"] = frappe.listview_settings["Asset"] || {};

// Store custom fields globally for filter use
frappe.listview_settings["Asset"]._custom_fields = [];
frappe.listview_settings["Asset"]._custom_field_filters = {};

const ASSET_IMPORT_TEMPLATE_FIELDS = [
	"name",
	"company",
	"item_code",
	"asset_name",
	"asset_category",
	"location",
	"gross_purchase_amount",
	"purchase_date",
	"available_for_use_date",
];

const ASSET_EXPORT_OPTIONAL_FIELDS = [
	"status",
	"custodian",
	"department",
	"cost_center",
];

const ASSET_EXPORT_ALLOWED_FIELDS = ASSET_IMPORT_TEMPLATE_FIELDS.concat(ASSET_EXPORT_OPTIONAL_FIELDS);

// Add custom field filters to Frappe's built-in filter system
frappe.listview_settings["Asset"].onload = function(listview) {
	// Load custom fields and add them to filter options
	load_custom_fields_for_filter(listview);
};

frappe.listview_settings["Asset"].refresh = function() {
	// Ensure custom field filters are applied
	apply_custom_field_filters();
};

function load_custom_fields_for_filter(listview) {
	frappe.call({
		method: "custom_fsf.scripts.asset_category_custom_fields.get_all_custom_fields",
		callback: function(r) {
			if (!r.message || r.message.length === 0) return;

			const customFields = r.message;
			frappe.listview_settings["Asset"]._custom_fields = customFields;

			// Add custom fields to the filter area's available fields
			add_custom_fields_to_filter_options(listview, customFields);
		}
	});
}

function add_custom_fields_to_filter_options(listview, customFields) {
	// Get the filter area
	const filterArea = listview.filter_area;
	if (!filterArea) return;

	// Ensure meta structures exist
	if (!frappe.meta.docfield_map["Asset"]) {
		frappe.meta.docfield_map["Asset"] = {};
	}
	if (!frappe.meta.docfield_list["Asset"]) {
		frappe.meta.docfield_list["Asset"] = [];
	}

	// Add custom fields to the standard_filters_wrapper
	customFields.forEach(cf => {
		// Skip if field_name is undefined or empty
		if (!cf.field_name || !cf.field_label) return;

		const fieldName = `_custom_${cf.field_name}`;

		// Create label with category name: "Field Label (Category Name)"
		const labelWithCategory = cf.category
			? `${cf.field_label} (${cf.category})`
			: cf.field_label;

		// Create a virtual field definition for each custom field
		const fieldDef = {
			fieldname: fieldName,
			fieldtype: cf.field_type === "Select" ? "Select" : "Data",
			label: labelWithCategory,
			options: cf.field_type === "Select" ? (cf.options || "") : "",
			is_custom_category_field: true,
			original_field_name: cf.field_name,
			category: cf.category,
			parent: "Asset"
		};

		// Add to the doctype's meta fields temporarily for filter purposes
		if (!frappe.meta.docfield_map["Asset"][fieldName]) {
			frappe.meta.docfield_map["Asset"][fieldName] = fieldDef;
			frappe.meta.docfield_list["Asset"].push(fieldDef);
		}
	});

	// Override the filter application to handle custom fields
	override_filter_application(listview);
}

function override_filter_application(listview) {
	// Store original get_args method
	if (!listview._original_get_args) {
		listview._original_get_args = listview.get_args;
	}

	// Override get_args to handle custom field filters
	listview.get_args = function() {
		const args = listview._original_get_args.call(this);

		// Check for custom field filters in the current filters
		const customFilters = [];
		const standardFilters = [];

		if (args.filters) {
			args.filters.forEach(filter => {
				const fieldname = filter[1];
				if (fieldname && fieldname.startsWith("_custom_")) {
					const originalFieldName = fieldname.replace("_custom_", "");
					customFilters.push({
						field_name: originalFieldName,
						value: filter[3]
					});
				} else {
					standardFilters.push(filter);
				}
			});
		}

		// If we have custom field filters, we need to resolve them to asset names
		if (customFilters.length > 0) {
			args.filters = standardFilters;
			frappe.listview_settings["Asset"]._custom_field_filters = customFilters;

			// Get matching assets synchronously
			let matchingAssets = null;
			frappe.call({
				method: "custom_fsf.scripts.asset_category_custom_fields.filter_assets_by_custom_fields",
				args: { filters: customFilters },
				async: false,
				callback: function(r) {
					matchingAssets = r.message || [];
				}
			});

			if (matchingAssets && matchingAssets.length > 0) {
				args.filters.push(["Asset", "name", "in", matchingAssets]);
			} else if (customFilters.length > 0) {
				// No matches found, add impossible filter
				args.filters.push(["Asset", "name", "=", "__no_match__"]);
			}
		}

		return args;
	};
}

function apply_custom_field_filters() {
	// This is called on refresh to ensure filters are properly applied
	// Filters are handled in get_args override
}

// Override Frappe's DataExporter for Asset doctype to show custom field labels
$(document).ready(function() {
    frappe.require("data_import_tools.bundle.js", () => {
        const OriginalDataExporter = frappe.data_import.DataExporter;

        // Custom Asset DataExporter that shows actual custom field labels
        frappe.data_import.AssetDataExporter = class AssetDataExporter extends OriginalDataExporter {
            constructor(doctype, exporting_for) {
                super(doctype, exporting_for);
                // Get selected items from current list view
                this.selected_items = this.get_selected_items();
            }

            get_selected_items() {
                // Try to get selected items from current list view
                if (cur_list && cur_list.doctype === "Asset") {
                    const checked = cur_list.get_checked_items();
                    if (checked && checked.length > 0) {
                        return checked.map(item => item.name);
                    }
                }
                return [];
            }

            async make_dialog() {
                // Fetch custom field definitions from all Asset Categories
                this.custom_field_definitions = await this.fetch_custom_field_definitions();

                this.dialog = new frappe.ui.Dialog({
                    title: __("Export Data"),
                    fields: this.get_dialog_fields(),
                    primary_action_label: __("Export"),
                    primary_action: () => this.export_records(),
                    on_page_show: () => this.select_mandatory(),
                });

                this.make_filter_area();
                this.make_select_all_buttons();

                // If items are selected, set filter and default to "by_filter"
                if (this.selected_items.length > 0) {
                    this.dialog.set_value("export_records", "by_filter");
                    // Add name filter with selected items
                    setTimeout(() => {
                        this.filter_group.add_filters_to_filter_group([
                            ["Asset", "name", "in", this.selected_items]
                        ]);
                        this.update_record_count_message();
                    }, 100);
                }

                this.update_record_count_message();
                this.dialog.show();
            }

            get_dialog_fields() {
                // Determine default export type
                let defaultExportType = "all";
                if (this.exporting_for === "Insert New Records") {
                    defaultExportType = "blank_template";
                } else if (this.selected_items && this.selected_items.length > 0) {
                    defaultExportType = "by_filter";
                }

                let fields = [
                    {
                        fieldtype: "Select",
                        fieldname: "file_type",
                        label: __("File Type"),
                        options: ["Excel", "CSV"],
                        default: "CSV",
                    },
                    {
                        fieldtype: "Select",
                        fieldname: "export_records",
                        label: __("Export Type"),
                        options: [
                            { label: __("All Records"), value: "all" },
                            { label: __("Filtered Records"), value: "by_filter" },
                            { label: __("5 Records"), value: "5_records" },
                            { label: __("Blank Template"), value: "blank_template" },
                        ],
                        default: defaultExportType,
                        change: () => this.update_record_count_message(),
                    },
                    {
                        fieldtype: "HTML",
                        fieldname: "filter_area",
                        depends_on: (doc) => doc.export_records === "by_filter",
                    },
                    { fieldtype: "Section Break" },
                    { fieldtype: "HTML", fieldname: "select_all_buttons" },
                    {
                        label: __(this.doctype),
                        fieldname: this.doctype,
                        fieldtype: "MultiCheck",
                        columns: 2,
                        on_change: () => this.update_primary_action(),
                        options: this.get_multicheck_options(this.doctype),
                        sort_options: false,
                    },
                ];

                if (this.custom_field_definitions && this.custom_field_definitions.length > 0) {
                    this.get_custom_category_field_groups().forEach((group) => {
                        fields.push({
                            label: group.category,
                            fieldname: group.fieldname,
                            fieldtype: "MultiCheck",
                            columns: 1,
                            on_change: () => this.update_primary_action(),
                            options: group.fields.map(cf => ({
                                label: cf.field_label,
                                value: cf.export_fieldname,
                                checked: false,
                                description: cf.field_name,
                            })),
                        });
                    });
                }

                return fields;
            }

            async fetch_custom_field_definitions() {
                return new Promise((resolve) => {
                    frappe.call({
                        method: "custom_fsf.scripts.asset_category_field_values.get_all_custom_field_definitions",
                        args: { asset_names: this.selected_items || [] },
                        async: false,
                        callback: (r) => resolve(r.message || [])
                    });
                });
            }

            get_custom_category_field_groups() {
                const groups = [];

                this.get_custom_category_field_options().forEach((field) => {
                    const categories = field.categories && field.categories.length
                        ? field.categories
                        : [__("Uncategorized")];

                    categories.forEach((category) => {
                        let group = groups.find(item => item.category === category);
                        if (!group) {
                            group = {
                                category,
                                fieldname: `custom_category_fields_${groups.length}`,
                                fields: [],
                            };
                            groups.push(group);
                        }
                        group.fields.push(field);
                    });
                });

                return groups;
            }

            get_custom_category_field_options() {
                return (this.custom_field_definitions || []).slice().sort((a, b) => {
                    const aOrder = Array.isArray(a.category_order) ? a.category_order[0] : 9999;
                    const bOrder = Array.isArray(b.category_order) ? b.category_order[0] : 9999;
                    const aCategory = (a.categories && a.categories[0]) || "";
                    const bCategory = (b.categories && b.categories[0]) || "";
                    const aLabel = a.field_label || a.field_name || "";
                    const bLabel = b.field_label || b.field_name || "";

                    return (
                        aOrder - bOrder ||
                        aCategory.localeCompare(bCategory) ||
                        aLabel.localeCompare(bLabel)
                    );
                });
            }

            get_multicheck_options(doctype, child_fieldname = null) {
                const options = super.get_multicheck_options(doctype, child_fieldname);
                if (doctype !== this.doctype || child_fieldname) {
                    return options;
                }

                // Virtual fields are added to Asset meta only for list filters.
                // They should not appear in the export/import field picker.
                const customFieldNames = new Set();
                (this.custom_field_definitions || []).forEach(cf => {
                    if (cf.field_name) customFieldNames.add(cf.field_name);
                    if (cf.export_fieldname) customFieldNames.add(cf.export_fieldname);
                });
                return options
                    .filter(option => {
                        const value = String(option.value || "");
                        return (
                            ASSET_EXPORT_ALLOWED_FIELDS.includes(value) &&
                            !value.startsWith("_custom_") &&
                            !customFieldNames.has(value)
                        );
                    })
                    .map(option => {
                        if (ASSET_IMPORT_TEMPLATE_FIELDS.includes(option.value)) {
                            option.checked = true;
                            option.danger = true;
                        }
                        return option;
                    });
            }

            export_records() {
                let values = this.dialog.get_values();
                let custom_fields = this.get_selected_custom_category_fields(values);
                let parent_fields = values[this.doctype] || [];

                ASSET_IMPORT_TEMPLATE_FIELDS.forEach(fieldname => {
                    if (!parent_fields.includes(fieldname)) {
                        parent_fields.push(fieldname);
                    }
                });

                let filters = values.export_records === "by_filter" ? this.get_filters() : null;

                frappe.call({
                    method: "custom_fsf.overrides.export.export_asset_custom",
                    args: {
                        parent_fields: parent_fields,
                        custom_fields: custom_fields,
                        filters: filters,
                        export_type: values.export_records,
                    },
                    freeze: true,
                    freeze_message: __("Exporting..."),
                    callback: (r) => {
                        if (r.message && r.message.data) {
                            if (values.file_type === "Excel") {
                                this.downloadExcel(r.message.data);
                            } else {
                                this.downloadCSV(r.message.data);
                            }
                        }
                    }
                });
            }

            get_selected_custom_category_fields(values) {
                const selected = [];
                Object.keys(values || {}).forEach((key) => {
                    if (!key.startsWith("custom_category_fields_")) {
                        return;
                    }
                    (values[key] || []).forEach((fieldname) => {
                        if (!selected.includes(fieldname)) {
                            selected.push(fieldname);
                        }
                    });
                });
                return selected;
            }

            downloadExcel(data) {
                const form = document.createElement("form");
                form.method = "POST";
                form.action = "/api/method/custom_fsf.scripts.asset_category_field_values.download_assets_excel_data";
                form.target = "_blank";

                const input = document.createElement("input");
                input.type = "hidden";
                input.name = "data";
                input.value = JSON.stringify(data);
                form.appendChild(input);

                const csrf = document.createElement("input");
                csrf.type = "hidden";
                csrf.name = "csrf_token";
                csrf.value = frappe.csrf_token;
                form.appendChild(csrf);

                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
            }

            downloadCSV(data) {
                const BOM = "\uFEFF";
                const csvContent = data.map(row =>
                    row.map(cell => {
                        const str = String(cell == null ? "" : cell);
                        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
                            return '"' + str.replace(/"/g, '""') + '"';
                        }
                        return str;
                    }).join(",")
                ).join("\n");

                const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" });
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = "Assets.csv";
                link.click();
                URL.revokeObjectURL(link.href);
            }
        };

        // Override DataExporter to use custom class for Asset
        frappe.data_import.DataExporter = class extends OriginalDataExporter {
            constructor(doctype, exporting_for) {
                if (doctype === "Asset") {
                    return new frappe.data_import.AssetDataExporter(doctype, exporting_for);
                }
                super(doctype, exporting_for);
            }
        };
    });
});
