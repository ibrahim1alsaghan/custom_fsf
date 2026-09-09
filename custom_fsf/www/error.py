import frappe
from frappe import _
from frappe.utils.response import is_traceback_allowed

no_cache = 1


def get_context(context):
	if frappe.flags.in_migrate:
		return

	context.error_title = context.error_title or _("Something Went Wrong")
	context.error_message = context.error_message or _(
		"An unexpected error occurred while building this page. Please try again, "
		"or contact the system administrator if the problem persists."
	)
	# Drives whether the traceback block starts expanded; `frappe.local.dev_server`
	# is not guaranteed to be in the web context, so set it explicitly.
	context.dev_server = bool(getattr(frappe.local, "dev_server", False))

	return {
		"error": frappe.get_traceback().replace("<", "&lt;").replace(">", "&gt;")
		if is_traceback_allowed()
		else ""
	}
