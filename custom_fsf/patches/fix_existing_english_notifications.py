import frappe


def execute():
	"""Fix existing Notification Log entries that have English subjects
	for Arabic-language users."""

	translations = {
		"Failed to send email with subject:": "فشل إرسال البريد الإلكتروني بالموضوع التالي:",
		"Reminder: Logs may be deleted soon by retention rules": "تذكير: قد يتم حذف السجلات قريبًا وفقًا لقواعد الاحتفاظ.",
	}

	for english_prefix, arabic_prefix in translations.items():
		# Find notifications with English subjects for Arabic users
		notifications = frappe.get_all(
			"Notification Log",
			filters=[
				["subject", "like", f"{english_prefix}%"],
			],
			fields=["name", "subject", "for_user"],
		)

		for notif in notifications:
			user_lang = frappe.db.get_value("User", notif.for_user, "language") or "ar"
			if user_lang in ("en", "english"):
				continue

			new_subject = arabic_prefix + notif.subject[len(english_prefix):]
			frappe.db.set_value(
				"Notification Log", notif.name, "subject", new_subject,
				update_modified=False,
			)

	frappe.db.commit()
