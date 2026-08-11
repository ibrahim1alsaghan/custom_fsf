import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	columns = [
		{
			"label": _("Asset"),
			"fieldname": "asset",
			"fieldtype": "Link",
			"options": "Asset",
			"width": 150
		},
		{
			"label": _("Asset Name"),
			"fieldname": "asset_name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Asset Category"),
			"fieldname": "asset_category",
			"fieldtype": "Link",
			"options": "Asset Category",
			"width": 150
		},
		{
			"label": _("Main Category"),
			"fieldname": "main_category",
			"fieldtype": "Link",
			"options": "Asset Category",
			"width": 150
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Custodian"),
			"fieldname": "custodian",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150
		},
	]

	# Add dynamic custom field columns
	custom_fields = get_custom_field_columns(filters)
	columns.extend(custom_fields)

	return columns


def get_custom_field_columns(filters):
	"""Get custom field definitions as columns"""
	columns = []
	seen_fields = set()

	# Get categories to include
	category_filter = {}
	if filters and filters.get("asset_category"):
		category_filter["name"] = filters.get("asset_category")
	else:
		category_filter["is_main_category"] = 0

	categories = frappe.get_all("Asset Category", filters=category_filter, pluck="name")

	for category_name in categories:
		try:
			category = frappe.get_doc("Asset Category", category_name)
			if not category.get("custom_fields"):
				continue

			for row in category.custom_fields:
				field_name = row.field_name or frappe.scrub(row.field_label or "")
				if field_name and field_name not in seen_fields:
					seen_fields.add(field_name)
					columns.append({
						"label": _(row.field_label),
						"fieldname": f"cf_{field_name}",
						"fieldtype": "Data",
						"width": 150
					})
		except Exception:
			continue

	return columns


def get_data(filters):
	data = []

	# Build asset filters
	asset_filters = {}
	if filters:
		if filters.get("asset_category"):
			asset_filters["asset_category"] = filters.get("asset_category")
		if filters.get("main_category"):
			asset_filters["main_asset_category"] = filters.get("main_category")
		if filters.get("status"):
			asset_filters["status"] = filters.get("status")
		if filters.get("custodian"):
			asset_filters["custodian"] = filters.get("custodian")

	assets = frappe.get_all(
		"Asset",
		filters=asset_filters,
		fields=["name", "asset_name", "asset_category", "main_asset_category", "status", "custodian"],
		order_by="name"
	)

	for asset in assets:
		row = {
			"asset": asset.name,
			"asset_name": asset.asset_name,
			"asset_category": asset.asset_category,
			"main_category": asset.main_asset_category,
			"status": asset.status,
			"custodian": asset.custodian
		}

		# Get custom field values
		custom_values = frappe.get_all(
			"Asset Category Field Value",
			filters={"parent": asset.name},
			fields=["field_name", "field_value"]
		)

		for cv in custom_values:
			row[f"cf_{cv.field_name}"] = cv.field_value

		data.append(row)

	return data
