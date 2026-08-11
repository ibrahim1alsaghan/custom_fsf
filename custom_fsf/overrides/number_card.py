import frappe
from frappe.desk.doctype.number_card.number_card import (
	has_permission as original_has_permission,
)


def has_permission(doc, ptype, user):
	"""Frappe's Number Card has_permission allows any user who can read the
	underlying doctype (Number Card has no `roles` table in this version).
	Plain Employees have row-filtered read on Asset, so the company-wide
	asset cards on the Asset dashboard would render for them. Keep every
	Asset-based card manager-only; defer to Frappe's logic for the rest."""
	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True

	if doc.document_type == "Asset" and "Asset Manager" not in roles:
		return False

	return original_has_permission(doc, ptype, user)
