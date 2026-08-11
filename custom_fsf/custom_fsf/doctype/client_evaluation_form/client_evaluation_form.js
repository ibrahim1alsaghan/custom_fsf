frappe.ui.form.on('Client Evaluation Form', {
    onload: function(frm) {
        // Set default values
        if (frm.is_new()) {
            frm.set_value("evaluation_date", frappe.datetime.get_today());
        }
        
        // Load client from project if project is selected
        if (frm.doc.project && !frm.doc.client) {
            load_client_from_project(frm);
        }
    },

    project: function(frm) {
        // Auto-populate client when project is selected
        if (frm.doc.project && !frm.doc.client) {
            load_client_from_project(frm);
        }
    },

    refresh: function(frm) {
        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__("View Project"), function() {
                frappe.set_route("Form", "Project", frm.doc.project);
            }, __("Actions"));
            
            frm.add_custom_button(__("View Client"), function() {
                frappe.set_route("Form", "Customer", frm.doc.client);
            }, __("Actions"));
            
            // Add evaluation summary button
            frm.add_custom_button(__("Evaluation Summary"), function() {
                show_evaluation_summary(frm);
            }, __("Actions"));
        }
    }
});

function load_client_from_project(frm) {
    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Project",
            name: frm.doc.project,
            fieldname: "customer"
        },
        callback: function(r) {
            if (r.message && r.message.customer) {
                frm.set_value("client", r.message.customer);
            }
        }
    });
}

function show_evaluation_summary(frm) {
    let summary = frm.doc.get_evaluation_summary();
    
    let content = `
        <div style="padding: 20px;">
            <h3>Client Evaluation Summary</h3>
            <table class="table table-bordered">
                <tr>
                    <td><strong>Responsiveness & Communication:</strong></td>
                    <td>${summary.scores.responsiveness_communication}</td>
                </tr>
                <tr>
                    <td><strong>Clarity of Requirements:</strong></td>
                    <td>${summary.scores.clarity_requirements}</td>
                </tr>
                <tr>
                    <td><strong>Timeliness of Approvals:</strong></td>
                    <td>${summary.scores.timeliness_approvals}</td>
                </tr>
                <tr>
                    <td><strong>Cooperation & Engagement:</strong></td>
                    <td>${summary.scores.cooperation_engagement}</td>
                </tr>
                <tr>
                    <td><strong>Overall Satisfaction:</strong></td>
                    <td>${summary.scores.overall_satisfaction}</td>
                </tr>
                <tr style="background-color: #f8f9fa; font-weight: bold;">
                    <td><strong>Average Score:</strong></td>
                    <td>${summary.average_score}/5.0</td>
                </tr>
            </table>
        </div>
    `;
    
    frappe.msgprint({
        title: "Evaluation Summary",
        message: content,
        indicator: summary.average_score >= 4 ? "green" : summary.average_score >= 3 ? "orange" : "red"
    });
}
