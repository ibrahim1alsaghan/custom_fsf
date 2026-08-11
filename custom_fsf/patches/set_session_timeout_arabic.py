import frappe


def execute():
	"""Ensure system default language is Arabic and clean up old wrong Translation."""

	system_settings = frappe.get_single("System Settings")
	if system_settings.language != "ar":
		system_settings.language = "ar"
		system_settings.save(ignore_permissions=True)

	# Remove old Translation record with wrong source text
	old_name = frappe.db.get_value(
		"Translation",
		{"language": "ar", "source_text": "You are not permitted to access this resource. Login to access"},
		"name",
	)
	if old_name:
		frappe.delete_doc("Translation", old_name, ignore_permissions=True)
		frappe.db.commit()
