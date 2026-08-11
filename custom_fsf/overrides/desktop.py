import frappe
from frappe.desk.desktop import get_desktop_page as original_get_desktop_page


@frappe.whitelist()
def get_desktop_page(page):
	"""Wrapper around Frappe's get_desktop_page that hides Dashboard-type
	workspace shortcuts the user can't actually use.

	Frappe's Workspace.is_item_allowed() blanket-allows "Dashboard" shortcuts
	(unlike DocType/Report shortcuts, which are permission-checked), so e.g.
	a plain Employee on the Assets workspace would still see the "Dashboard"
	shortcut even though every chart and number card on it is role-gated to
	Asset Manager. Hide the shortcut when none of the dashboard's charts or
	cards are visible to the user.
	"""
	result = original_get_desktop_page(page)

	items = result.get("shortcuts", {}).get("items") if isinstance(result, dict) else None
	if items:
		result["shortcuts"]["items"] = [
			item
			for item in items
			if item.get("type") != "Dashboard" or _can_view_dashboard(item.get("link_to"))
		]

	return result


def _can_view_dashboard(name):
	if not name or not frappe.db.exists("Dashboard", name):
		return True

	dashboard = frappe.get_cached_doc("Dashboard", name)

	for chart in dashboard.charts:
		if chart.chart and frappe.has_permission("Dashboard Chart", doc=chart.chart):
			return True

	for card in dashboard.cards:
		if card.card and frappe.has_permission("Number Card", doc=card.card):
			return True

	return False
