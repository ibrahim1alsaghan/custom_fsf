import frappe


# Workspaces visible after installation, with role restrictions and sidebar order.
# Assets is first (sequence_id 1.0) so it is the default desk landing page: the
# desk lands on the first workspace the user can see. Because Assets is
# role-gated (Asset Manager + Employee via setup_module_roles), only users with
# asset access land there; everyone else falls through to their first visible
# workspace. "Home" is intentionally absent → hidden by the sweep below.
ALLOWED_WORKSPACES = {
	"Assets": {"roles": ["Asset Manager"], "sequence_id": 1.0},
	"LMS": {"roles": [], "sequence_id": 2.0},
	"Tasks": {"roles": ["Projects User", "Projects Manager"], "sequence_id": 3.0},
	"Document Library": {"roles": ["Document Viewer", "Document Manager"], "sequence_id": 4.0},
	"Help Desk": {"roles": [], "sequence_id": 5.0},
	"Help Desk Admin": {"roles": ["HD Agent", "HD Manager", "System Manager"], "sequence_id": 6.0},
	"Users": {"roles": ["HR Manager", "System Manager"], "sequence_id": 7.0},
	"Audit Logs": {"roles": ["Audit Viewer", "System Manager"], "sequence_id": 8.0},
}


def execute():
	"""Hide all workspaces except the allowed ones and set role restrictions."""
	allowed_names = list(ALLOWED_WORKSPACES.keys())
	placeholders = ", ".join(["%s"] * len(allowed_names))

	# Hide all workspaces not in the allowed list
	frappe.db.sql(
		f"UPDATE `tabWorkspace` SET `is_hidden` = 1 WHERE `name` NOT IN ({placeholders})",
		allowed_names,
	)

	# Ensure allowed workspaces are visible with correct order
	for ws_name, config in ALLOWED_WORKSPACES.items():
		if not frappe.db.exists("Workspace", ws_name):
			continue

		frappe.db.set_value("Workspace", ws_name, {
			"is_hidden": 0,
			"sequence_id": config["sequence_id"],
		})

		# Clear existing role restrictions
		frappe.db.sql(
			"DELETE FROM `tabHas Role` WHERE `parent` = %s AND `parenttype` = 'Workspace'",
			ws_name,
		)

		# Insert new role restrictions
		for role in config["roles"]:
			if not frappe.db.exists("Role", role):
				continue
			frappe.get_doc({
				"doctype": "Has Role",
				"parent": ws_name,
				"parenttype": "Workspace",
				"parentfield": "roles",
				"role": role,
			}).db_insert()

	frappe.db.commit()
