import frappe
from frappe.model.document import Document
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

class ClientEvaluationForm(Document):
    def validate(self):
        """Validate the client evaluation form"""
        if not self.project:
            frappe.throw("Project is required.")
        if not self.client:
            frappe.throw("Client is required.")
        
        # Validate that all evaluation fields are filled
        evaluation_fields = [
            "responsiveness_communication",
            "clarity_requirements", 
            "timeliness_approvals",
            "cooperation_engagement",
            "overall_satisfaction"
        ]
        
        for field in evaluation_fields:
            if not self.get(field):
                frappe.throw(f"{self.meta.get_field(field).label} is required.")

    def after_insert(self):
        """Notify relevant stakeholders when a new evaluation is created"""
        self.notify_evaluation_created()

    def notify_evaluation_created(self):
        """Send notification when a new client evaluation is created"""
        # Get project managers and system managers
        roles = ["Projects Manager", "System Manager"]
        users = frappe.get_all(
            "Has Role",
            filters={"role": ["in", roles], "parenttype": "User"},
            pluck="parent",
        )
        
        if not users:
            return

        recipients = list({u for u in users if u and u != "Administrator"})
        if not recipients:
            return

        subject = f"New Client Evaluation Created: {self.project} - {self.client}"
        notification = frappe._dict({
            "subject": subject,
            "from_user": frappe.session.user or "Administrator",
            "type": "Alert",
            "document_type": self.doctype,
            "document_name": self.name,
        })
        make_notification_logs(notification, recipients)

    def get_evaluation_summary(self):
        """Get a summary of the evaluation scores"""
        scores = {
            "responsiveness_communication": self.responsiveness_communication,
            "clarity_requirements": self.clarity_requirements,
            "timeliness_approvals": self.timeliness_approvals,
            "cooperation_engagement": self.cooperation_engagement,
            "overall_satisfaction": self.overall_satisfaction
        }
        
        # Convert text scores to numeric values
        score_map = {
            "Excellent": 5,
            "Good": 4,
            "Average": 3,
            "Poor": 2,
            "Very Poor": 1
        }
        
        numeric_scores = [score_map.get(score, 0) for score in scores.values()]
        average_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0
        
        return {
            "scores": scores,
            "average_score": round(average_score, 2),
            "total_score": sum(numeric_scores)
        }
