# Copyright (c) 2024, Custom FSF and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_role_profile(role_profile: str):
	"""
	Override for frappe.core.doctype.user.user.get_role_profile
	Fixes the bug where frappe.get_doc() was called with incorrect parameters.
	"""
	if not role_profile:
		frappe.throw(_("Role Profile is required"))
	
	# Step 1: Try to get by document name first (normal case)
	# Since autoname is set to "role_profile", the name should match the role_profile field value
	if frappe.db.exists("Role Profile", role_profile):
		role_profile_doc = frappe.get_doc("Role Profile", role_profile)
		return role_profile_doc.roles
	
	# Step 2: Edge case - Role Profile might have been renamed
	# Search by the role_profile field value in case there's a mismatch
	# This handles cases where the document name doesn't match what's stored in User records
	matching_profile = frappe.db.get_value(
		"Role Profile",
		{"role_profile": role_profile},
		"name"
	)
	
	if matching_profile:
		# Found by field value - document exists but name is different
		role_profile_doc = frappe.get_doc("Role Profile", matching_profile)
		return role_profile_doc.roles
	
	# Step 3: Not found at all - provide helpful error message
	# Check if any Role Profiles exist to give better context
	all_profiles = frappe.get_all("Role Profile", pluck="name", limit=5)
	
	if all_profiles:
		frappe.throw(
			_("Role Profile '{0}' not found. It may have been renamed or deleted. "
			  "Please select a valid Role Profile from the list.").format(role_profile),
			title=_("Role Profile Not Found")
		)
	else:
		frappe.throw(
			_("Role Profile '{0}' not found. No Role Profiles exist in the system.").format(role_profile),
			title=_("Role Profile Not Found")
		)
