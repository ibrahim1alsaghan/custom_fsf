import frappe


ALLOWED_FILE_EXTENSIONS = (
	"PDF",
	"CSV",
	"DOCX",
	"XLSX",
	"JPG",
	"JPEG",
	"PNG",
	"WEBP",
	"AVIF",
	"MOV",
)


def execute():
	"""Apply the approved upload allowlist and keep guest uploads disabled."""
	settings = frappe.get_single("System Settings")
	allowed_extensions = "\n".join(ALLOWED_FILE_EXTENSIONS)

	if (
		settings.allowed_file_extensions == allowed_extensions
		and not settings.allow_guests_to_upload_files
	):
		return

	settings.allowed_file_extensions = allowed_extensions
	settings.allow_guests_to_upload_files = 0
	settings.save(ignore_permissions=True)
