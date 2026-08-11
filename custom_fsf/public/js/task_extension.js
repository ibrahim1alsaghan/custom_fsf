frappe.ui.form.on('Task', {
    refresh: function(frm) {
        // Set up field visibility based on assignment type
        toggle_assignment_fields(frm);

        // Add help text for managers
        if (frappe.user.has_role('Projects Manager')) {
            frm.set_intro(__('You can assign this task to a specific user or to an entire department. Department members will see tasks assigned to their department.'));
        }
    },

    assignment_type: function(frm) {
        toggle_assignment_fields(frm);

        // Clear the other field when switching assignment type
        if (frm.doc.assignment_type === 'Department') {
            // Clear user assignment when switching to department
            frm.clear_table('_assign');
            frm.refresh_field('_assign');
        } else if (frm.doc.assignment_type === 'User') {
            // Clear department when switching to user
            frm.set_value('assigned_department', '');
        }
    },

    onload: function(frm) {
        // Set default assignment type for new tasks
        if (frm.is_new() && !frm.doc.assignment_type) {
            frm.set_value('assignment_type', 'User');
        }

        // Filter departments to show only active ones
        frm.set_query('assigned_department', function() {
            return {
                filters: {
                    'disabled': 0
                }
            };
        });
    }
});

function toggle_assignment_fields(frm) {
    const is_department = frm.doc.assignment_type === 'Department';

    // Show/hide assigned_department based on assignment type
    frm.toggle_display('assigned_department', is_department);
    frm.toggle_reqd('assigned_department', is_department);

    // Optionally show a note when department is selected
    if (is_department && frm.doc.assigned_department) {
        frm.dashboard.set_headline(
            __('This task is assigned to department: {0}', [frm.doc.assigned_department])
        );
    } else {
        frm.dashboard.set_headline('');
    }
}
