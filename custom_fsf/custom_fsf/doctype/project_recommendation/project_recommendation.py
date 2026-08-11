import frappe
from frappe.model.document import Document
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

class ProjectRecommendation(Document):
    def after_insert(self):
        self.notify_new_recommendation()

    def on_update(self):
        self.notify_if_assignee_changed()

    def validate(self):
        if not self.priority:
            frappe.throw("Priority is required.")
        if not self.assignee:
            frappe.throw("Assignee is required.")

        # Only assignee can change the review status
        if self.get_doc_before_save():
            prev = self.get_doc_before_save()
            if prev.review_status != self.review_status:
                if frappe.session.user != self.assignee and not frappe.has_role("System Manager"):
                    frappe.throw("Only the assigned user or System Manager can change the review status.")

    def notify_new_recommendation(self):
        """Notify when a new recommendation is created"""
        if not self.assignee:
            return
            
        subject = f"New Project Recommendation: {self.title}"
        notification = frappe._dict({
            "subject": subject,
            "from_user": frappe.session.user or "Administrator",
            "type": "Alert",
            "document_type": self.doctype,
            "document_name": self.name
        })
        make_notification_logs(notification, [self.assignee])

    def notify_if_assignee_changed(self):
        """Notify when assignee is changed"""
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        if old_doc.assignee != self.assignee and self.assignee:
            subject = f"You've been assigned to review: {self.title}"
            notification = frappe._dict({
                "subject": subject,
                "from_user": frappe.session.user or "Administrator",
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            })
            make_notification_logs(notification, [self.assignee])