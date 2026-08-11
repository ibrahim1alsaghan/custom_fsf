frappe.ui.form.on("Project", {
    onload_post_render(frm) {
        if (!frm.is_new()) {
            frappe.call({
                method: "custom_fsf.utils.get_project_cost_summary",
                args: { project: frm.doc.name },
                callback(r) {
                    if (r.message) {
                        frm.set_value("costs_total_invoiced", r.message.invoiced);
                        frm.set_value("costs_total_paid", r.message.paid);
                        frm.set_value("costs_outstanding_balance", r.message.invoiced - r.message.paid);
                    }
                }
            });
        }
    },

    refresh(frm) {
        if (frm.is_new()) return;

        // Check if user has Projects Manager role
        const is_project_manager = frappe.user.has_role("Projects Manager");

        // Add transactions shortcut on the dashboard
        if (frm.dashboard?.add_transactions) {
            frm.dashboard.add_transactions([
                {
                    label: __("Related"),
                    items: ["Lessons Learned", "Project Recommendation", "Client Evaluation Form"],
                },
            ]);
        }

        // Only show buttons for Project Managers
        if (is_project_manager) {
            // Grouped buttons for Lessons Learned
            frm.add_custom_button(
                __("New Lessons Learned"),
                () => {
                    frappe.new_doc("Lessons Learned", { project: frm.doc.name });
                },
                __("Lessons Learned")
            );

            frm.add_custom_button(
                __("View Lessons Learned"),
                () => {
                    frappe.set_route("List", "Lessons Learned", {
                        project: frm.doc.name,
                    });
                },
                __("Lessons Learned")
            );

            // Grouped buttons for Project Recommendations
            frm.add_custom_button(
                __("New Project Recommendation"),
                () => {
                    frappe.new_doc("Project Recommendation", { project: frm.doc.name });
                },
                __("Project Recommendation")
            );

            frm.add_custom_button(
                __("View Project Recommendation"),
                () => {
                    frappe.set_route("List", "Project Recommendation", {
                        project: frm.doc.name,
                    });
                },
                __("Project Recommendation")
            );

            // Grouped buttons for Client Evaluation Forms
            frm.add_custom_button(
                __("New Client Evaluation"),
                () => {
                    frappe.new_doc("Client Evaluation Form", { project: frm.doc.name });
                },
                __("Client Evaluations")
            );

            frm.add_custom_button(
                __("View Client Evaluations"),
                () => {
                    frappe.set_route("List", "Client Evaluation Form", {
                        project: frm.doc.name,
                    });
                },
                __("Client Evaluations")
            );
        }
    },
});
