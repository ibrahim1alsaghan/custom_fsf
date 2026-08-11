import frappe


def execute():
	"""Set FSF logo, homepage, and website branding on fresh install."""
	logo_url = "/assets/custom_fsf/images/fsf.png"

	# Website Settings: logo + homepage + clear old navbar items
	ws = frappe.get_single("Website Settings")
	ws.splash_image = logo_url
	ws.app_logo = logo_url
	ws.banner_image = logo_url
	ws.home_page = "landing"
	ws.top_bar_items = []  # Clear old navbar items that cause the old design
	ws.footer_items = []
	ws.save(ignore_permissions=True)

	# Desk navbar logo
	ns = frappe.get_single("Navbar Settings")
	ns.app_logo = logo_url
	ns.save(ignore_permissions=True)

	frappe.db.commit()
