import frappe


def execute():
	"""
	Add Translation records for notification subjects that are created
	in background jobs (where _() uses system language = Arabic).
	"""

	translations = [
		{
			"source_text": "Failed to send email with subject:",
			"translated_text": "فشل إرسال البريد الإلكتروني بالموضوع التالي:",
		},
		{
			"source_text": "Reminder: Logs may be deleted soon by retention rules",
			"translated_text": "تذكير: قد يتم حذف السجلات قريبًا وفقًا لقواعد الاحتفاظ.",
		},
	]

	for t in translations:
		existing = frappe.db.get_value(
			"Translation",
			{"language": "ar", "source_text": t["source_text"]},
			"name",
		)
		if existing:
			frappe.db.set_value("Translation", existing, "translated_text", t["translated_text"])
		else:
			frappe.get_doc({
				"doctype": "Translation",
				"language": "ar",
				"source_text": t["source_text"],
				"translated_text": t["translated_text"],
			}).insert(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache()
