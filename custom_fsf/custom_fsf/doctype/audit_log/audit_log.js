// Copyright (c) 2025, ibrahim alsaghan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Audit Log", "refresh", function (frm) {
    // Parse the changed_data JSON and render the formatted view
    if (frm.doc.changed_data) {
        try {
            var data;
            
            // Handle different data types
            if (typeof frm.doc.changed_data === 'string') {
                data = JSON.parse(frm.doc.changed_data);
            } else if (typeof frm.doc.changed_data === 'object') {
                data = frm.doc.changed_data;
            } else {
                throw new Error('Invalid data type for changed_data');
            }
            
            // Try to render with template, fallback to manual HTML generation
            try {
                if (typeof frappe.render_template === 'function') {
                    // Use the template rendering like Version does
                    var rendered_html = frappe.render_template("audit_log_view", { 
                        doc: frm.doc, 
                        data: data 
                    });
                    $(rendered_html).appendTo(frm.fields_dict.changes_display.$wrapper.empty());
                } else {
                    throw new Error('frappe.render_template not available');
                }
            } catch (template_error) {
                console.warn("Template rendering failed, using fallback:", template_error);
                // Fallback: create a simple HTML representation
                var html = generate_audit_log_html(frm.doc, data);
                frm.fields_dict.changes_display.$wrapper.html(html);
            }
        } catch (e) {
            console.error("Error parsing changed_data:", e);
            // More detailed error information
            var error_details = e.stack || e.message || 'Unknown error';
            frm.fields_dict.changes_display.$wrapper.html(
                '<div class="alert alert-warning">' +
                '<strong>Error parsing changes data:</strong><br>' + 
                frappe.utils.escape_html(error_details) + 
                '</div>'
            );
        }
    } else {
        frm.fields_dict.changes_display.$wrapper.html(
            '<div class="text-muted"></div>'
        );
    }
});

function generate_audit_log_html(doc, data) {
    // Fallback HTML generator when template rendering fails
    var html = '<div class="audit-log-info">';
    
    // Document creation info
    if (data.creation || data.created_by) {
        html += '<h4>' + __('Document Created') + '</h4>';
        html += '<table class="table table-bordered">';
        if (data.created_by) html += '<tr><td><strong>' + __('Created By') + '</strong></td><td>' + frappe.utils.escape_html(data.created_by) + '</td></tr>';
        if (data.creation) html += '<tr><td><strong>' + __('Creation Date') + '</strong></td><td>' + frappe.utils.escape_html(data.creation) + '</td></tr>';
        if (data.document_name) html += '<tr><td><strong>' + __('Document Name') + '</strong></td><td>' + frappe.utils.escape_html(data.document_name) + '</td></tr>';
        if (data.updater_reference) html += '<tr><td><strong>' + __('Via Data Import') + '</strong></td><td>' + frappe.utils.escape_html(data.updater_reference) + '</td></tr>';
        if (data.docstatus !== undefined) html += '<tr><td><strong>' + __('Document Status') + '</strong></td><td>' + frappe.utils.escape_html(data.docstatus) + '</td></tr>';
        html += '</table>';
    }
    
    // Document deletion info
    if (data.deleted) {
        html += '<h4>' + __('Document Deleted') + '</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td><strong>' + __('Deleted At') + '</strong></td><td>' + frappe.utils.escape_html(data.deleted_at || '') + '</td></tr>';
        html += '</table>';
    }
    
    // Changes
    if (data.changed && data.changed.length) {
        html += '<h4>' + __('Values Changed') + '</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><td style="width: 33%">' + __('Property') + '</td><td style="width: 33%">' + __('Original Value') + '</td><td style="width: 33%">' + __('New Value') + '</td></tr></thead>';
        html += '<tbody>';
        
        for (var i = 0; i < data.changed.length; i++) {
            var change = data.changed[i];
            html += '<tr>';
            html += '<td>' + frappe.utils.escape_html(change[0] || '') + '</td>';
            html += '<td class="diff-remove">' + frappe.utils.escape_html(change[1] || '') + '</td>';
            html += '<td class="diff-add">' + frappe.utils.escape_html(change[2] || '') + '</td>';
            html += '</tr>';
        }
        
        html += '</tbody></table>';
    }
    
    // Added/Removed items with better formatting
    var action_types = [
        {key: 'added', title: __('Rows Added'), class: 'diff-add'},
        {key: 'removed', title: __('Rows Removed'), class: 'diff-remove'}
    ];
    
    for (var j = 0; j < action_types.length; j++) {
        var action = action_types[j];
        if (data[action.key] && data[action.key].length) {
            html += '<h4>' + action.title + '</h4>';
            html += '<table class="table table-bordered">';
            html += '<thead><tr><td style="width: 25%">' + __('Table Field') + '</td><td style="width: 35%">' + __('Summary') + '</td><td style="width: 40%">' + __('Details') + '</td></tr></thead>';
            html += '<tbody>';
            
            for (var k = 0; k < data[action.key].length; k++) {
                var item = data[action.key][k];
                var table_name = item[0] || 'Unknown';
                var summary = '';
                var details = '';
                
                if (item.length >= 2 && typeof item[1] === 'object') {
                    var obj = item[1];
                    
                    // Generate user-friendly summary
                    if (obj.role) {
                        summary = 'Role: ' + obj.role;
                    } else if (obj.item_code) {
                        summary = 'Item: ' + obj.item_code;
                        if (obj.qty) summary += ' (Qty: ' + obj.qty + ')';
                    } else if (obj.allow && obj.for_value) {
                        summary = 'Permission: ' + obj.allow + ' - ' + obj.for_value;
                    } else if (obj.title) {
                        summary = 'Title: ' + obj.title;
                    } else if (obj.name && !obj.name.startsWith('new-')) {
                        summary = 'Name: ' + obj.name;
                    } else {
                        // Find first meaningful field
                        var meaningful_fields = ['subject', 'description', 'email', 'phone', 'address'];
                        for (var m = 0; m < meaningful_fields.length; m++) {
                            if (obj[meaningful_fields[m]]) {
                                summary = meaningful_fields[m].charAt(0).toUpperCase() + meaningful_fields[m].slice(1) + ': ' + obj[meaningful_fields[m]];
                                break;
                            }
                        }
                        if (!summary) summary = 'Child table entry';
                    }
                    
                    // Create collapsible details
                    var clean_obj = {};
                    var system_fields = ['__unsaved', 'doctype', 'name', 'owner', 'creation', 'modified', 'modified_by', 'idx', 'parent', 'parentfield', 'parenttype'];
                    for (var key in obj) {
                        if (system_fields.indexOf(key) === -1 && obj[key] !== null && obj[key] !== '') {
                            clean_obj[key] = obj[key];
                        }
                    }
                    
                    details = '<details style="font-size: 11px;">' +
                             '<summary>View Details</summary>' +
                             '<pre style="margin-top: 5px; max-height: 150px; overflow-y: auto; background: #f8f9fa; padding: 5px; border-radius: 3px;">' +
                             JSON.stringify(clean_obj, null, 2) +
                             '</pre></details>';
                } else {
                    summary = 'Data entry';
                    details = '<pre style="font-size: 11px;">' + JSON.stringify(item[1] || {}, null, 2) + '</pre>';
                }
                
                html += '<tr>';
                html += '<td><strong>' + frappe.utils.escape_html(table_name.replace('_', ' ').toUpperCase()) + '</strong></td>';
                html += '<td class="' + action.class + '">' + frappe.utils.escape_html(summary) + '</td>';
                html += '<td>' + details + '</td>';
                html += '</tr>';
            }
            
            html += '</tbody></table>';
        }
    }
    
    // Row changes
    if (data.row_changed && data.row_changed.length) {
        html += '<h4>' + __('Row Values Changed') + '</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><td style="width: 25%">' + __('Table Field') + '</td><td style="width: 15%">' + __('Row #') + '</td><td style="width: 20%">' + __('Property') + '</td><td style="width: 20%">' + __('Original Value') + '</td><td style="width: 20%">' + __('New Value') + '</td></tr></thead>';
        html += '<tbody>';
        
        for (var n = 0; n < data.row_changed.length; n++) {
            var row_change = data.row_changed[n];
            var table_field = row_change[0];
            var row_index = row_change[1];
            var changes = row_change[3] || [];
            
            for (var o = 0; o < changes.length; o++) {
                var change = changes[o];
                html += '<tr>';
                html += '<td>' + frappe.utils.escape_html(table_field || '') + '</td>';
                html += '<td>' + frappe.utils.escape_html(row_index || '') + '</td>';
                html += '<td>' + frappe.utils.escape_html(change[0] || '') + '</td>';
                html += '<td class="diff-remove">' + frappe.utils.escape_html(change[1] || '') + '</td>';
                html += '<td class="diff-add">' + frappe.utils.escape_html(change[2] || '') + '</td>';
                html += '</tr>';
            }
        }
        
        html += '</tbody></table>';
    }
    
    // Workflow transitions
    if (data.workflow_transition) {
        html += '<h4>Workflow Transition</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td><strong>From State</strong></td><td class="diff-remove">' + frappe.utils.escape_html(data.workflow_transition.from_state || 'None') + '</td></tr>';
        html += '<tr><td><strong>To State</strong></td><td class="diff-add">' + frappe.utils.escape_html(data.workflow_transition.to_state) + '</td></tr>';
        html += '<tr><td><strong>Action</strong></td><td>' + frappe.utils.escape_html(data.workflow_transition.action) + '</td></tr>';
        if (data.workflow_transition.timestamp) {
            html += '<tr><td><strong>Timestamp</strong></td><td>' + frappe.utils.escape_html(data.workflow_transition.timestamp) + '</td></tr>';
        }
        html += '</table>';
    }
    
    // Permission changes
    if (data.permission_change) {
        html += '<h4>Permission Change</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td><strong>Target DocType</strong></td><td>' + frappe.utils.escape_html(data.permission_change.target_doctype || '') + '</td></tr>';
        if (data.permission_change.target_document) {
            html += '<tr><td><strong>Target Document</strong></td><td>' + frappe.utils.escape_html(data.permission_change.target_document) + '</td></tr>';
        }
        html += '<tr><td><strong>Affected User</strong></td><td>' + frappe.utils.escape_html(data.permission_change.affected_user || '') + '</td></tr>';
        html += '<tr><td><strong>Action</strong></td><td class="diff-add">' + frappe.utils.escape_html(data.permission_change.action || '') + '</td></tr>';
        if (data.permission_change.timestamp) {
            html += '<tr><td><strong>Timestamp</strong></td><td>' + frappe.utils.escape_html(data.permission_change.timestamp) + '</td></tr>';
        }
        html += '</table>';
    }
    
    // Events
    if (data.event) {
        html += '<h4>Event</h4>';
        html += '<p><strong>' + frappe.utils.escape_html(data.event) + '</strong></p>';
    }
    
    // Document status transitions
    if (data.docstatus_transition) {
        html += '<h4>Document Status Change</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><td style="width: 50%">From</td><td style="width: 50%">To</td></tr></thead>';
        html += '<tbody>';
        html += '<tr>';
        html += '<td class="diff-remove">' + frappe.utils.escape_html(data.docstatus_transition.before || '') + '</td>';
        html += '<td class="diff-add">' + frappe.utils.escape_html(data.docstatus_transition.after || '') + '</td>';
        html += '</tr>';
        html += '</tbody></table>';
    }
    
    // Impersonation info
    if (data.impersonated_by) {
        html += '<h4>Impersonation Info</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td><strong>Impersonated By</strong></td><td>' + frappe.utils.escape_html(data.impersonated_by) + '</td></tr>';
        if (data.audit_user) {
            html += '<tr><td><strong>Audit User</strong></td><td>' + frappe.utils.escape_html(data.audit_user) + '</td></tr>';
        }
        html += '</table>';
    }
    
    html += '</div>';
    return html;
}