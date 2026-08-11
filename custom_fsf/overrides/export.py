import frappe
from frappe import _
import json

ASSET_IMPORT_TEMPLATE_FIELDS = [
	"name",
	"company",
	"item_code",
	"asset_name",
	"asset_category",
	"location",
	"gross_purchase_amount",
	"purchase_date",
	"available_for_use_date",
]


@frappe.whitelist()
def export_asset_custom(parent_fields=None, custom_fields=None, filters=None, export_type="all"):
	"""
	Export Asset with selected parent fields and custom fields as columns.
	Called from the custom Asset DataExporter in asset_list.js.
	custom_fields is a list of category-scoped export_fieldnames.
	"""
	from custom_fsf.scripts.asset_category_field_values import (
		ensure_asset_export_import_fields,
		get_export_import_fieldname,  # needed for category-scoped custom field lookup
	)

	# backfill=False: this export reads custom values straight from the child
	# table below, so it never uses the hidden export columns — only needs them
	# to exist. Skipping the per-asset backfill (O(asset count)) is what stops
	# the export/template download from hanging on large sites.
	ensure_asset_export_import_fields(backfill=False)

	# Parse inputs
	if isinstance(parent_fields, str):
		parent_fields = json.loads(parent_fields)
	if isinstance(custom_fields, str):
		custom_fields = json.loads(custom_fields)
	if isinstance(filters, str) and filters and filters != "null":
		filters = json.loads(filters)
	elif filters == "null" or filters is None:
		filters = {}

	parent_fields = parent_fields or []
	custom_fields = custom_fields or []
	filters = filters or {}

	parent_fields = list(dict.fromkeys([*ASSET_IMPORT_TEMPLATE_FIELDS, *parent_fields]))

	# Build lookup maps from all Asset Categories:
	#   export_fieldname → Arabic label
	#   export_fieldname → {field_name, category}
	custom_field_label_map = {}
	defn_lookup = {}
	all_categories = frappe.get_all("Asset Category", pluck="name")
	for cat in all_categories:
		if not frappe.db.exists("Asset Category", cat):
			continue
		category_doc = frappe.get_doc("Asset Category", cat)
		for field in category_doc.get("custom_fields") or []:
			if not field.field_label:
				continue
			fn = field.field_name or frappe.scrub(field.field_label)
			export_fn = get_export_import_fieldname(fn, cat)
			custom_field_label_map[export_fn] = f"{field.field_label} ({cat})"
			defn_lookup[export_fn] = {"field_name": fn, "category": cat}

	# Build headers
	meta = frappe.get_meta("Asset")
	field_label_map = {df.fieldname: _(df.label) for df in meta.fields}
	field_label_map["name"] = _("ID")

	headers = [_("Sr")]
	for fn in parent_fields:
		headers.append(field_label_map.get(fn, fn))
	for export_fn in custom_fields:
		headers.append(custom_field_label_map.get(export_fn, export_fn))

	# Handle export type
	limit = None
	if export_type == "5_records":
		limit = 5
	elif export_type == "blank_template":
		return {"data": [headers]}

	# Always include asset_category in the query for the per-category value lookup
	query_fields = list(dict.fromkeys([*parent_fields, "asset_category"]))

	assets = frappe.get_all(
		"Asset",
		filters=filters,
		fields=query_fields,
		order_by="creation desc",
		limit_page_length=limit or 0,
	)

	# Build data rows
	data = [headers]
	for i, asset in enumerate(assets):
		row = [i + 1]

		for fn in parent_fields:
			row.append(asset.get(fn, "") or "")

		# Fetch custom field values from child table, keyed by field_name
		field_values = frappe.get_all(
			"Asset Category Field Value",
			filters={"parent": asset.name, "parenttype": "Asset"},
			fields=["field_name", "field_value"],
		)
		value_map = {fv.field_name: fv.field_value or "" for fv in field_values if fv.field_name}

		asset_category = asset.get("asset_category")
		for export_fn in custom_fields:
			d = defn_lookup.get(export_fn)
			if d and d["category"] == asset_category:
				row.append(value_map.get(d["field_name"], ""))
			else:
				row.append("")

		data.append(row)

	return {"data": data}
