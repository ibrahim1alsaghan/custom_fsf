frappe.provide("custom_fsf.asset_fields");

// Add custom CSS for seamless styling
(function() {
    if (document.getElementById('custom-field-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'custom-field-styles';
    style.textContent = `
        /* Make inputs blend into the grid cell */
        .custom-value-input {
            width: 100% !important;
            min-height: 30px !important;
            padding: 8px 10px !important;
            font-size: var(--text-base) !important;
            font-family: inherit !important;
            color: var(--text-color) !important;
            background: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            box-sizing: border-box !important;
        }
        
        .custom-value-input:focus {
            background: var(--fg-color) !important;
        }
        
        .custom-value-input::placeholder {
            color: var(--text-muted) !important;
        }
        
        /* Select styling */
        select.custom-value-input {
            cursor: pointer !important;
            appearance: none !important;
            -webkit-appearance: none !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e") !important;
            background-position: right 8px top 50% !important;
            background-repeat: no-repeat !important;
            background-size: 12px !important;
            padding-right: 28px !important;
        }
        
        /* Date input */
        input[type="date"].custom-value-input::-webkit-calendar-picker-indicator {
            cursor: pointer !important;
            opacity: 0.5 !important;
        }
        
        input[type="date"].custom-value-input::-webkit-calendar-picker-indicator:hover {
            opacity: 1 !important;
        }
        
        /* Number input - hide spinners */
        input[type="number"].custom-value-input::-webkit-outer-spin-button,
        input[type="number"].custom-value-input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        
        input[type="number"].custom-value-input {
            -moz-appearance: textfield !important;
        }
        
        /* Dark mode */
        [data-theme="dark"] select.custom-value-input {
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%239ca3af' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e") !important;
        }

        /* RTL support - arrow on left side */
        [dir="rtl"] select.custom-value-input,
        .rtl select.custom-value-input {
            background-position: left 8px top 50% !important;
            padding-right: 10px !important;
            padding-left: 28px !important;
            text-align: right !important;
        }
    `;
    document.head.appendChild(style);
})();

// Store field definitions
custom_fsf.asset_fields.definitions = {};

custom_fsf.asset_fields = {
    ensure_category_fields(frm, options = {}) {
        const forceRefresh = options.force || false;

        if (!frm.fields_dict?.category_field_values) return;

        if (frm.doc.docstatus === 1) {
            frm.refresh_field("category_field_values");
            toggleCategoryField(frm, (frm.doc.category_field_values || []).length > 0);
            hideGridButtons(frm);
            // Still setup grid for submitted docs
            setTimeout(() => customizeValueFields(frm), 200);
            return;
        }

        const hasValues = Array.isArray(frm.doc.category_field_values) && 
                          frm.doc.category_field_values.length > 0;

        // Use asset_category (which comes from Item's sub_asset_category)
        const selectedCategory = frm.doc.asset_category;

        if (!selectedCategory) {
            if (hasValues) {
                frm.doc.category_field_values = [];
                frm.refresh_field("category_field_values");
            }
            toggleCategoryField(frm, false);
            return;
        }

        // Always fetch fresh definitions to get latest options
        frappe.call({
            method: "custom_fsf.scripts.asset_category_field_values.get_category_field_definitions",
            args: { asset_category: selectedCategory },
            freeze: false,
            callback: (r) => {
                const definitions = r.message || [];
                
                // Store definitions for use in grid rendering
                custom_fsf.asset_fields.definitions = {};
                definitions.forEach(def => {
                    custom_fsf.asset_fields.definitions[def.field_name] = def;
                });

                // Get existing values
                const existingValues = {};
                (frm.doc.category_field_values || []).forEach((row) => {
                    if (row.field_name) existingValues[row.field_name] = row.field_value || "";
                });

                // Only rebuild rows if forcing refresh or new
                if (forceRefresh || frm.is_new() || !hasValues) {
                    frm.doc.category_field_values = [];
                    definitions.forEach((def) => {
                        frm.add_child("category_field_values", {
                            field_name: def.field_name,
                            field_label: def.field_label,
                            field_type: def.field_type || "Text",
                            field_options: def.field_options || "",
                            is_mandatory: def.is_mandatory,
                            field_value: existingValues[def.field_name] || "",
                            depends_on: def.depends_on || "",
                            depends_on_field: def.depends_on_field || "",
                            asset_category: frm.doc.asset_category,
                        });
                    });
                    frm.refresh_field("category_field_values");
                } else {
                    // Update existing rows with fresh options from definitions
                    (frm.doc.category_field_values || []).forEach((row) => {
                        const def = custom_fsf.asset_fields.definitions[row.field_name];
                        if (def) {
                            row.field_type = def.field_type || "Text";
                            row.field_options = def.field_options || "";
                            row.is_mandatory = def.is_mandatory;
                            row.depends_on_field = def.depends_on_field || "";
                        }
                    });
                    frm.refresh_field("category_field_values");
                }

                toggleCategoryField(frm, definitions.length > 0);
                hideGridButtons(frm);
                
                // Setup grid rendering
                setTimeout(() => customizeValueFields(frm), 100);
                setTimeout(() => customizeValueFields(frm), 300);
                setTimeout(() => customizeValueFields(frm), 600);
            },
            error: () => toggleCategoryField(frm, false),
        });
    },
};

function toggleCategoryField(frm, show) {
    if (!frm.fields_dict?.category_field_values) return;
    frm.set_df_property("category_field_values", "hidden", !show);
}

function hideGridButtons(frm) {
    const grid = frm.fields_dict?.category_field_values?.grid;
    if (!grid?.wrapper) return;
    grid.wrapper.find(".grid-add-row, .btn-add-row, .grid-add-multiple-rows, .grid-remove-rows, .grid-row-delete, .grid-remove-row").hide();
}

function customizeValueFields(frm) {
    const grid = frm.fields_dict?.category_field_values?.grid;
    if (!grid?.wrapper) return;

    const rows = frm.doc.category_field_values || [];

    // Build a map of field values for dependency checking (normalize field names)
    const fieldValues = {};
    rows.forEach(r => {
        if (r.field_name) {
            // Store with both original and scrubbed key for compatibility
            fieldValues[r.field_name] = r.field_value || "";
            fieldValues[frappe.scrub(r.field_name)] = r.field_value || "";
        }
        // Also index by scrubbed label for old fields with manually set field_name
        if (r.field_label) {
            fieldValues[frappe.scrub(r.field_label)] = r.field_value || "";
        }
    });

    rows.forEach((row, idx) => {
        const $gridRow = grid.wrapper.find(`.grid-row[data-idx="${idx + 1}"]`);
        if (!$gridRow.length) return;

        // Translate field_type column
        const $typeCell = $gridRow.find('[data-fieldname="field_type"]');
        if ($typeCell.length && row.field_type) {
            $typeCell.text(__(row.field_type));
        }

        // Handle field-level visibility (depends_on = "field_name=value")
        const def = custom_fsf.asset_fields.definitions[row.field_name];
        const dependsOn = def?.depends_on || row.depends_on || "";

        if (dependsOn && dependsOn.includes("=")) {
            const [depFieldRaw, depValue] = dependsOn.split("=").map(s => s.trim());
            // Normalize field name to match how field_names are stored (scrubbed)
            const depField = frappe.scrub(depFieldRaw);
            const currentValue = fieldValues[depField] || "";

            if (currentValue !== depValue) {
                // Hide this row - dependency not met
                $gridRow.hide();
                // Clear the value when hidden
                if (row.field_value) {
                    row.field_value = "";
                    frm.dirty();
                }
                return;
            } else {
                // Show this row - dependency met
                $gridRow.show();
            }
        } else {
            $gridRow.show();
        }

        const $valueCell = $gridRow.find('[data-fieldname="field_value"]');
        if (!$valueCell.length) return;

        // Check if re-rendering is needed
        if ($valueCell.attr('data-customized') === 'true') {
            const fieldType = row.field_type || "Text";
            const $existingInput = $valueCell.find('.custom-value-input');

            // Check if the input type matches
            let needsRerender = false;
            if (fieldType === "Select" && !$existingInput.is('select')) {
                needsRerender = true;
            } else if (fieldType === "Date" && $existingInput.attr('type') !== 'date') {
                needsRerender = true;
            } else if (fieldType === "Number" && $existingInput.attr('type') !== 'number') {
                needsRerender = true;
            } else if (fieldType === "Text" && $existingInput.attr('type') !== 'text') {
                needsRerender = true;
            }

            // For Select fields with dependencies, check if parent value changed
            if (fieldType === "Select" && !needsRerender) {
                const dependsOnField = def?.depends_on_field || row.depends_on_field || "";
                if (dependsOnField) {
                    // Match parent row by scrubbed field_name or label for compatibility
                    const parentRow = rows.find(r =>
                        frappe.scrub(r.field_name) === dependsOnField ||
                        frappe.scrub(r.field_label) === dependsOnField
                    );
                    const currentParentValue = parentRow?.field_value || "";
                    const cachedParentValue = $valueCell.attr('data-parent-value') || "";
                    if (currentParentValue !== cachedParentValue) {
                        needsRerender = true;
                    }
                }
            }

            if (!needsRerender) {
                return; // Already correctly customized
            }
        }
        
        $valueCell.attr('data-customized', 'true');
        $valueCell.empty();

        const fieldType = row.field_type || "Text";
        let $input;

        // Get options from stored definitions or row data (reuse def from above)
        const fieldOptions = (def && def.field_options) || row.field_options || "";

        switch (fieldType) {
            case "Number":
                $input = $(`<input type="number" class="custom-value-input" step="1" placeholder="${__('Enter number')}">`);
                $input.val(row.field_value || '');
                $input.on('change', function() {
                    const val = $(this).val();
                    if (val && isNaN(parseInt(val))) {
                        frappe.show_alert({ message: __("Must be a number"), indicator: 'orange' });
                        $(this).val('');
                        updateRowValue(frm, idx, '');
                    } else {
                        updateRowValue(frm, idx, val);
                    }
                });
                break;

            case "Date":
                $input = $(`<input type="date" class="custom-value-input">`);
                $input.val(row.field_value || '');
                $input.on('change', function() {
                    updateRowValue(frm, idx, $(this).val());
                });
                break;

            case "Select":
                let options = [];
                try {
                    options = JSON.parse(fieldOptions || '[]');
                } catch (e) {
                    console.warn('Failed to parse field options:', fieldOptions);
                    options = [];
                }

                // Get parent field value if this field depends on another
                const dependsOnField = def?.depends_on_field || row.depends_on_field || "";
                let parentValue = "";
                if (dependsOnField) {
                    // Find parent field's current value in the rows (match by scrubbed name or label)
                    const parentRow = rows.find(r =>
                        frappe.scrub(r.field_name) === dependsOnField ||
                        frappe.scrub(r.field_label) === dependsOnField
                    );
                    parentValue = parentRow?.field_value || "";
                }

                // Filter options based on dependency
                let filteredOptions = options.filter(opt => {
                    // Handle new structured format: {value: "x", depends_on: "y"}
                    if (typeof opt === 'object' && opt.value) {
                        // Show if no dependency OR dependency matches parent value
                        return !opt.depends_on || opt.depends_on === parentValue;
                    }
                    // Handle old string format - always show
                    return true;
                });

                $input = $(`<select class="custom-value-input" data-field-name="${row.field_name}" data-depends-on="${dependsOnField}"></select>`);
                $input.append(`<option value="">${__('Select...')}</option>`);

                // Store parent value for change detection
                if (dependsOnField) {
                    $valueCell.attr('data-parent-value', parentValue);
                }

                if (filteredOptions.length > 0) {
                    filteredOptions.forEach(opt => {
                        // Handle both object and string formats
                        const optValue = typeof opt === 'object' ? opt.value : opt;
                        const escaped = frappe.utils.escape_html(optValue);
                        const selected = row.field_value === optValue ? 'selected' : '';
                        $input.append(`<option value="${escaped}" ${selected}>${escaped}</option>`);
                    });
                }

                // Clear value if it's not in filtered options
                if (row.field_value && dependsOnField) {
                    const validValues = filteredOptions.map(opt => typeof opt === 'object' ? opt.value : opt);
                    if (!validValues.includes(row.field_value)) {
                        row.field_value = "";
                        $input.val("");
                        frm.dirty();
                    }
                }

                $input.on('change', function() {
                    updateRowValue(frm, idx, $(this).val());
                    // Re-render dependent fields when Select value changes
                    setTimeout(() => {
                        customizeValueFields(frm);
                    }, 50);
                });
                break;

            default: // Text
                $input = $(`<input type="text" class="custom-value-input" placeholder="${__('Enter value')}">`);
                $input.val(row.field_value || '');
                $input.on('change input', function() {
                    updateRowValue(frm, idx, $(this).val());
                });
                break;
        }

        $valueCell.append($input);
    });
}

function updateRowValue(frm, idx, value) {
    if (frm.doc.category_field_values?.[idx]) {
        frm.doc.category_field_values[idx].field_value = value;
        frm.dirty();
    }
}

// Event Handlers
frappe.ui.form.on("Asset", {
    setup(frm) {
        if (frm.fields_dict.category_field_values) {
            frm.fields_dict.category_field_values.grid.cannot_add_rows = true;
            frm.fields_dict.category_field_values.grid.cannot_delete_rows = true;
        }
    },
    
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.custodian && frappe.user.has_role("Accounts Manager")) {
            frm.add_custom_button(__("Return"), () => {
                frappe.confirm(__("Are you sure you want to return this asset?"), () => {
                    frappe.call({
                        method: "custom_fsf.overrides.assets.return_asset",
                        args: { asset_name: frm.doc.name },
                        callback: (r) => {
                            if (!r.exc) {
                                frappe.show_alert({ message: __("Asset returned"), indicator: "green" });
                                frm.reload_doc();
                            }
                        },
                    });
                });
            }, __("Actions"));
        }

        custom_fsf.asset_fields.ensure_category_fields(frm);
        
        setTimeout(() => hideGridButtons(frm), 200);
    },

    // When asset_category changes: load custom fields and fetch main category
    asset_category(frm) {
        custom_fsf.asset_fields.ensure_category_fields(frm, { force: true });

        // Fetch main_asset_category from asset_category's main_category
        if (frm.doc.asset_category) {
            frappe.db.get_value("Asset Category", frm.doc.asset_category, "main_category", (r) => {
                if (r && r.main_category) {
                    frm.set_value("main_asset_category", r.main_category);
                } else {
                    frm.set_value("main_asset_category", "");
                }
            });
        } else {
            frm.set_value("main_asset_category", "");
        }
    },
});

frappe.ui.form.on("Asset Category Field Value", {
    form_render(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row) return;

        setTimeout(() => {
            const gridRow = frm.fields_dict.category_field_values.grid.grid_rows_by_docname[cdn];
            if (gridRow?.form?.dialog) customizeDialogField(gridRow.form.dialog, row, frm);
        }, 100);
    },
    
    field_value(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row?.field_type === "Number" && row.field_value && isNaN(parseInt(row.field_value))) {
            frappe.show_alert({ message: __("Must be a number"), indicator: 'orange' });
            frappe.model.set_value(cdt, cdn, 'field_value', '');
        }
    }
});

function customizeDialogField(dialog, row, frm) {
    if (!dialog || !row) return;

    const $wrapper = dialog.$wrapper.find('[data-fieldname="field_value"]');
    if (!$wrapper.length || $wrapper.attr('data-dialog-customized')) return;
    $wrapper.attr('data-dialog-customized', 'true');

    const $input = $wrapper.find('input');
    if (!$input.length) return;

    // Get options from stored definitions
    const def = custom_fsf.asset_fields.definitions[row.field_name];
    const fieldOptions = (def && def.field_options) || row.field_options || "";

    switch (row.field_type) {
        case "Number":
            $input.attr('type', 'number').attr('step', '1');
            break;
        case "Date":
            $input.attr('type', 'date');
            break;
        case "Select":
            let options = [];
            try { options = JSON.parse(fieldOptions || '[]'); } catch (e) {}

            // Get parent field value if this field depends on another
            const dependsOnField = def?.depends_on_field || row.depends_on_field || "";
            let parentValue = "";
            if (dependsOnField && frm) {
                const rows = frm.doc.category_field_values || [];
                const parentRow = rows.find(r =>
                    frappe.scrub(r.field_name) === dependsOnField ||
                    frappe.scrub(r.field_label) === dependsOnField
                );
                parentValue = parentRow?.field_value || "";
            }

            // Filter options based on dependency
            let filteredOptions = options.filter(opt => {
                if (typeof opt === 'object' && opt.value) {
                    return !opt.depends_on || opt.depends_on === parentValue;
                }
                return true;
            });

            if (filteredOptions.length) {
                const $select = $('<select class="form-control"></select>');
                $select.append(`<option value="">${__('Select...')}</option>`);
                filteredOptions.forEach(opt => {
                    const optValue = typeof opt === 'object' ? opt.value : opt;
                    const escaped = frappe.utils.escape_html(optValue);
                    $select.append(`<option value="${escaped}" ${row.field_value === optValue ? 'selected' : ''}>${escaped}</option>`);
                });
                $select.on('change', () => $input.val($select.val()).trigger('change'));
                $input.hide().after($select);
            }
            break;
    }
}
