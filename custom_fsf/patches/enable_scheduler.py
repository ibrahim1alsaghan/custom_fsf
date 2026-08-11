import frappe


def execute():
	"""Enable the scheduler so that scheduled tasks (auto-close, SLA breach, etc.) run."""
	frappe.utils.scheduler.enable_scheduler()
	frappe.db.commit()
