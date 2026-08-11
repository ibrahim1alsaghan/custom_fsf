import json
import frappe


def execute():
	"""
	Remove the 'HD Dashboard' shortcut from the Help Desk Admin workspace
	in the database. The JSON fixture is already clean; this patch ensures
	any previously synced DB record is also cleaned up.
	"""
	workspace_name = "Help Desk Admin"

	if not frappe.db.exists("Workspace", workspace_name):
		return

	# 1. Remove from the shortcuts child table
	frappe.db.delete(
		"Workspace Shortcut",
		{"parent": workspace_name, "link_to": "hd-dashboard"},
	)

	# 2. Remove from the content JSON (the layout field)
	content_raw = frappe.db.get_value("Workspace", workspace_name, "content")
	if content_raw:
		try:
			content = json.loads(content_raw)
			cleaned = [
				item for item in content
				if not (
					item.get("type") == "shortcut"
					and item.get("data", {}).get("shortcut_name") == "HD Dashboard"
				)
			]
			if len(cleaned) != len(content):
				frappe.db.set_value(
					"Workspace", workspace_name, "content", json.dumps(cleaned)
				)
		except (json.JSONDecodeError, AttributeError):
			pass

	frappe.db.commit()
