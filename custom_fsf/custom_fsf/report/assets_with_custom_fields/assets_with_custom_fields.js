frappe.query_reports["Assets with Custom Fields"] = {
	filters: [
		{
			fieldname: "asset_category",
			label: __("Asset Category"),
			fieldtype: "Link",
			options: "Asset Category",
			get_query: function() {
				return {
					filters: { is_main_category: 0 }
				};
			}
		},
		{
			fieldname: "main_category",
			label: __("Main Category"),
			fieldtype: "Link",
			options: "Asset Category",
			get_query: function() {
				return {
					filters: { is_main_category: 1 }
				};
			}
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nSubmitted\nPartially Depreciated\nFully Depreciated\nSold\nScrapped\nIn Maintenance\nOut of Order"
		},
		{
			fieldname: "custodian",
			label: __("Custodian"),
			fieldtype: "Link",
			options: "Employee"
		},
		{
			fieldname: "custom_field",
			label: __("Custom Field"),
			fieldtype: "Select",
			options: "",
			onchange: function() {
				// Dynamic filter will be handled by report
			}
		},
		{
			fieldname: "custom_field_value",
			label: __("Custom Field Value"),
			fieldtype: "Data",
			depends_on: "eval:doc.custom_field"
		}
	],

	onload: function(report) {
		// Load custom field options
		frappe.call({
			method: "custom_fsf.scripts.asset_category_custom_fields.get_all_custom_fields",
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					const options = [""].concat(r.message.map(f => f.field_label));
					const filter = report.get_filter("custom_field");
					if (filter) {
						filter.df.options = options.join("\n");
						filter.refresh();
					}
				}
			}
		});
	}
};
