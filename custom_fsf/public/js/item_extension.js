// Item Extension - Cascading Asset Category Selection
// Main Category (mandatory) -> Asset Category (mandatory, filtered by Main)

frappe.ui.form.on("Item", {
	setup(frm) {
		// Filter: Main Category shows only main categories (is_main_category = 1)
		frm.set_query("main_asset_category", function() {
			return {
				filters: {
					"is_main_category": 1
				}
			};
		});

		// Filter: Asset Category shows only sub categories under selected Main
		frm.set_query("asset_category", function() {
			if (frm.doc.main_asset_category) {
				return {
					filters: {
						"main_category": frm.doc.main_asset_category,
						"is_main_category": 0
					}
				};
			}
			// If no main selected, show all sub categories
			return {
				filters: {
					"is_main_category": 0
				}
			};
		});
	},

	refresh(frm) {
		// Make asset_category mandatory when is_fixed_asset is checked
		updateAssetCategoryMandatory(frm);
	},

	is_fixed_asset(frm) {
		updateAssetCategoryMandatory(frm);
		if (!frm.doc.is_fixed_asset) {
			frm.set_value("main_asset_category", "");
			frm.set_value("asset_category", "");
		}
	},

	// When Main Category changes: clear Asset Category
	main_asset_category(frm) {
		frm.set_value("asset_category", "");
	}
});

function updateAssetCategoryMandatory(frm) {
	const isMandatory = frm.doc.is_fixed_asset ? 1 : 0;
	frm.set_df_property("asset_category", "reqd", isMandatory);
}

