// Asset Category Extension - Simple inline custom fields table

frappe.ui.form.on("Asset Category", {
	setup: function(frm) {
		// Filter: Main Category shows only main categories
		frm.set_query("main_category", function() {
			return {
				filters: { "is_main_category": 1 }
			};
		});

		// Store original custom_fields for comparison on save
		frm._original_custom_fields = [];
	},

	refresh: function(frm) {
		// Hide custom fields section for main categories
		if (frm.doc.is_main_category) {
			frm.set_df_property("section_custom_fields", "hidden", 1);
			frm.set_df_property("custom_fields", "hidden", 1);
		} else {
			frm.set_df_property("section_custom_fields", "hidden", 0);
			frm.set_df_property("custom_fields", "hidden", 0);
		}

		// Store original fields for comparison
		if (!frm.is_new()) {
			frm._original_custom_fields = (frm.doc.custom_fields || []).map(f => ({
				field_name: f.field_name,
				field_label: f.field_label
			}));
		}
	},

	before_save: function(frm) {
		// Note: Individual field deletion warnings are handled by before_custom_fields_remove
		// This is a fallback check in case fields are removed another way
		if (frm._skip_data_check) {
			frm._skip_data_check = false;
			return;
		}
	},

	is_main_category: function(frm) {
		if (frm.doc.is_main_category) {
			frm.set_value("main_category", "");
			frm.set_df_property("section_custom_fields", "hidden", 1);
			frm.set_df_property("custom_fields", "hidden", 1);
		} else {
			frm.set_df_property("section_custom_fields", "hidden", 0);
			frm.set_df_property("custom_fields", "hidden", 0);
		}
	}
});

// Handle Category Custom Field child table
frappe.ui.form.on("Category Custom Field", {
	form_render: function(frm, cdt, cdn) {
		// Store original field_name when row is rendered for edit validation
		const row = locals[cdt][cdn];
		if (row.field_name && !row.__original_field_name) {
			row.__original_field_name = row.field_name;
		}
	},

	field_label: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.field_label) return;

		const newFieldName = frappe.scrub(row.field_label);
		const oldFieldName = row.__original_field_name || row.field_name;

		// If field name is changing and this is not a new row
		if (oldFieldName && oldFieldName !== newFieldName && !frm.is_new() && frm.doc.name) {
			// Check if old field has data
			frappe.call({
				method: "custom_fsf.scripts.asset_category_custom_fields.check_field_has_data",
				args: {
					asset_category: frm.doc.name,
					field_name: oldFieldName
				},
				async: false,
				callback: function(r) {
					if (r.message && r.message.has_data) {
						frappe.confirm(
							__("Changing field name from '{0}' to '{1}' will affect {2} asset(s). The existing data will be migrated. Continue?",
								[oldFieldName, newFieldName, r.message.count]),
							function() {
								// User confirmed - update field_name and store migration info
								row.field_name = newFieldName;
								row.__migrate_from = oldFieldName;
								row.__original_field_name = newFieldName;
								frm.refresh_field("custom_fields");
							},
							function() {
								// User cancelled - revert to original label
								const originalLabel = frm._original_custom_fields.find(f => f.field_name === oldFieldName);
								if (originalLabel) {
									row.field_label = originalLabel.field_label;
								}
								row.field_name = oldFieldName;
								frm.refresh_field("custom_fields");
							}
						);
						return;
					}
					// No data - just update
					row.field_name = newFieldName;
					row.__original_field_name = newFieldName;
					frm.refresh_field("custom_fields");
				}
			});
		} else {
			// New row or no change in field_name
			row.field_name = newFieldName;
			frm.refresh_field("custom_fields");
		}
	},

	field_type: function(frm, cdt, cdn) {
		// Show help for options when Select type is chosen
		const row = locals[cdt][cdn];
		if (row.field_type === "Select" && !row.options) {
			frappe.show_alert({
				message: __("For Select fields, add options in the 'Options' column (one per line)"),
				indicator: "blue"
			}, 5);
		}
	},

	before_custom_fields_remove: function(frm, cdt, cdn) {
		// Skip if already confirmed or new document
		if (frm._confirmed_delete === cdn || frm.is_new() || !frm.doc.name) {
			frm._confirmed_delete = null;
			return;
		}

		const row = locals[cdt][cdn];
		if (!row) return;

		const field_name = row.field_name || frappe.scrub(row.field_label || "");
		if (!field_name) return;

		// Check if field has data - synchronous call
		let hasData = false;
		let dataCount = 0;

		frappe.call({
			method: "custom_fsf.scripts.asset_category_custom_fields.check_field_has_data",
			args: {
				asset_category: frm.doc.name,
				field_name: field_name
			},
			async: false,
			callback: function(r) {
				if (r.message && r.message.has_data) {
					hasData = true;
					dataCount = r.message.count;
				}
			}
		});

		if (hasData) {
			// Show confirmation and prevent immediate deletion
			frappe.confirm(
				__("This field has data in {0} asset(s). Deleting it will remove all related data. Are you sure?", [dataCount]),
				function() {
					// User confirmed - set flag and remove row
					frm._confirmed_delete = cdn;
					const grid = frm.get_field("custom_fields").grid;
					const gridRow = grid.get_row(cdn);
					if (gridRow) {
						gridRow.remove();
					}
				}
			);
			// Throw to prevent this deletion attempt
			throw new Error("Confirmation required");
		}
	}
});


