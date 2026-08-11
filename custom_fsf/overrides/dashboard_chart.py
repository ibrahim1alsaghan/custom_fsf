import frappe
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get as original_get


@frappe.whitelist()
def get(**kwargs):
	"""Wrapper around Frappe's dashboard_chart.get that translates labels."""
	result = original_get(**kwargs)

	if result and isinstance(result, dict) and "labels" in result:
		result["labels"] = [_(label) if label else label for label in result["labels"]]

	return result
