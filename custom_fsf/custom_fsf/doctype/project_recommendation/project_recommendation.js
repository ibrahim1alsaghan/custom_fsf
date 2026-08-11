frappe.ui.form.on('Project Recommendation', {
  onload: function(frm) {
    set_review_status_readonly(frm);
  },
  refresh: function(frm) {
    set_review_status_readonly(frm);
  },
  assignee: function(frm) {
    set_review_status_readonly(frm);
  },
  review_status: function(frm) {
    // Only allow assignee or System Manager to change status
    const current_user = frappe.session.user;
    const assignee = frm.doc.assignee;
    
    if (current_user !== assignee && !frappe.user.has_role("System Manager")) {
      frappe.msgprint("Only the assigned user or System Manager can change the review status.");
      frm.set_value("review_status", "Undecided");
    }
  }
});

function set_review_status_readonly(frm) {
  const current_user = frappe.session.user;
  const assignee = frm.doc.assignee;

  // Only assignee or System Manager can change the review status
  const is_allowed = current_user === assignee || frappe.user.has_role("System Manager");
  
  frm.set_df_property("review_status", "read_only", !is_allowed);
  
  // If not allowed, ensure status is "Undecided"
  if (!is_allowed && frm.doc.review_status !== "Undecided") {
    frm.set_value("review_status", "Undecided");
  }
}