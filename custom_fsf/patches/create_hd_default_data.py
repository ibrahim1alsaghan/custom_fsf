"""
Create default data for Help Desk module:
- Default priorities with SLA times
- Default "Unspecified" ticket type and category
"""

import frappe


def execute():
	"""Create default Help Desk data."""
	create_default_priorities()
	create_default_type()
	create_default_category()


def create_default_priorities():
	"""Create default HD Ticket Priority records."""
	priorities = [
		{
			"priority_name": "Urgent",
			"priority_name_ar": "عاجل",
			"resolution_time_hours": 4,
			"color": "#F44336",
			"sort_order": 1,
			"is_active": 1
		},
		{
			"priority_name": "High",
			"priority_name_ar": "عالي",
			"resolution_time_hours": 8,
			"color": "#FF9800",
			"sort_order": 2,
			"is_active": 1
		},
		{
			"priority_name": "Medium",
			"priority_name_ar": "متوسط",
			"resolution_time_hours": 72,
			"color": "#2196F3",
			"sort_order": 3,
			"is_active": 1
		},
		{
			"priority_name": "Low",
			"priority_name_ar": "منخفض",
			"resolution_time_hours": 120,
			"color": "#4CAF50",
			"sort_order": 4,
			"is_active": 1
		}
	]

	for priority_data in priorities:
		priority_name = priority_data["priority_name"]
		if not frappe.db.exists("HD Ticket Priority", priority_name):
			doc = frappe.get_doc({
				"doctype": "HD Ticket Priority",
				**priority_data
			})
			doc.insert(ignore_permissions=True)
		else:
			doc = frappe.get_doc("HD Ticket Priority", priority_name)
			for key, value in priority_data.items():
				doc.set(key, value)
			doc.save(ignore_permissions=True)

	frappe.db.commit()


def create_default_type():
	"""Create default 'Unspecified' ticket type."""
	if not frappe.db.exists("HD Ticket Type", "Unspecified"):
		doc = frappe.get_doc({
			"doctype": "HD Ticket Type",
			"type_name": "Unspecified",
			"type_name_ar": "غير محدد",
			"description": "Default ticket type for unclassified tickets",
			"is_active": 1
		})
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("HD Ticket Type", "Unspecified")
		doc.type_name_ar = "غير محدد"
		doc.save(ignore_permissions=True)

	frappe.db.commit()


def create_default_category():
	"""Create default 'Unspecified' category."""
	if not frappe.db.exists("HD Ticket Category", "Unspecified"):
		doc = frappe.get_doc({
			"doctype": "HD Ticket Category",
			"category_name": "Unspecified",
			"category_name_ar": "غير محدد",
			"description": "Default category for unclassified tickets",
			"is_active": 1
		})
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("HD Ticket Category", "Unspecified")
		doc.category_name_ar = "غير محدد"
		doc.save(ignore_permissions=True)

	frappe.db.commit()
