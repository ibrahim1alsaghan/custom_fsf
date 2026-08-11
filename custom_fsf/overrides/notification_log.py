import frappe

TRANSLATION_MAP = {
	"ar": {
		"Failed to send email with subject:": "فشل إرسال البريد الإلكتروني بالموضوع التالي:",
		"Reminder: Logs may be deleted soon by retention rules": "تذكير: قد يتم حذف السجلات قريبًا وفقًا لقواعد الاحتفاظ.",
	},
}


def translate_subject(doc, method=None):
	if not doc.for_user or not doc.subject:
		return

	user_lang = frappe.db.get_value("User", doc.for_user, "language") or "ar"
	if user_lang in ("en", "english"):
		return

	lang_map = TRANSLATION_MAP.get(user_lang)
	if not lang_map:
		return

	for english_prefix, arabic_prefix in lang_map.items():
		if doc.subject.startswith(english_prefix):
			doc.subject = arabic_prefix + doc.subject[len(english_prefix):]
			break
