import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	# Clean up old custom fields and doctypes first
	cleanup_old_custom_fields()

	# Create child table DocTypes
	create_category_custom_field_doctype()
	create_category_field_option_doctype()
	create_asset_category_field_value_doctype()

	# Add custom fields to existing DocTypes
	ensure_asset_category_custom_fields()
	ensure_asset_classification_fields()
	ensure_asset_category_value_table()
	ensure_asset_export_import_fields()


def cleanup_old_custom_fields():
	"""Remove old custom fields and doctypes from previous implementation"""
	# Drop old custom fields from Asset Category
	old_fields = [
		("Asset Category", "section_category_custom_fields"),
		("Asset Category", "category_custom_fields"),
	]

	for doctype, fieldname in old_fields:
		custom_field_name = frappe.db.exists(
			"Custom Field", {"dt": doctype, "fieldname": fieldname}
		)
		if custom_field_name:
			frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True)
			frappe.db.commit()

	# Drop old DocType if exists
	if frappe.db.exists("DocType", "Asset Category Custom Field"):
		# First check if there's any data
		try:
			frappe.delete_doc("DocType", "Asset Category Custom Field", ignore_permissions=True, force=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Could not delete old DocType: {e}")

	frappe.clear_cache(doctype="Asset Category")


def create_category_custom_field_doctype():
	"""
	Child table for defining custom fields on Asset Category
	Simple editable grid with all fields visible inline
	"""
	doctype_name = "Category Custom Field"

	fields = [
		{
			"fieldname": "field_label",
			"label": "Field Label",
			"fieldtype": "Data",
			"reqd": 1,
			"in_list_view": 1,
			"columns": 2,
		},
		{
			"fieldname": "field_name",
			"label": "Field Name",
			"fieldtype": "Data",
			"read_only": 1,
			"hidden": 1,
		},
		{
			"fieldname": "field_type",
			"label": "Type",
			"fieldtype": "Select",
			"options": "Text\nNumber\nDate\nSelect",
			"default": "Text",
			"reqd": 1,
			"in_list_view": 1,
			"columns": 1,
		},
		{
			"fieldname": "is_mandatory",
			"label": "Required",
			"fieldtype": "Check",
			"default": 0,
			"in_list_view": 1,
			"columns": 1,
		},
		{
			"fieldname": "options",
			"label": "Options",
			"fieldtype": "Small Text",
			"in_list_view": 1,
			"columns": 3,
			"description": "For Select: one option per line",
		},
		{
			"fieldname": "depends_on",
			"label": "Show When",
			"fieldtype": "Data",
			"in_list_view": 1,
			"columns": 2,
			"description": "e.g. field_name=value",
		},
	]

	upsert_child_doctype(doctype_name, fields, {"module": "Custom FSF", "editable_grid": 0})


def create_category_field_option_doctype():
	"""
	Child table for Select field options with dependency support
	Used when admin needs cascading dropdowns
	"""
	doctype_name = "Category Field Option"

	fields = [
		{
			"fieldname": "option_value",
			"label": "Option",
			"fieldtype": "Data",
			"reqd": 1,
			"in_list_view": 1,
			"columns": 4,
		},
		{
			"fieldname": "show_when",
			"label": "Show When Parent =",
			"fieldtype": "Data",
			"in_list_view": 1,
			"columns": 3,
			"description": "Leave empty to always show",
		},
		{
			"fieldname": "idx",
			"label": "Order",
			"fieldtype": "Int",
			"default": 0,
			"in_list_view": 1,
			"columns": 1,
		},
	]

	upsert_child_doctype(doctype_name, fields, {"module": "Custom FSF", "editable_grid": 1})


def create_asset_category_field_value_doctype():
	"""
	Child table for storing field values on Asset documents
	"""
	doctype_name = "Asset Category Field Value"

	fields = [
		{
			"fieldname": "field_label",
			"label": "Field",
			"fieldtype": "Data",
			"read_only": 1,
			"in_list_view": 1,
			"columns": 3,
		},
		{
			"fieldname": "field_type",
			"label": "Type",
			"fieldtype": "Data",
			"read_only": 1,
			"in_list_view": 1,
			"columns": 1,
		},
		{
			"fieldname": "field_value",
			"label": "Value",
			"fieldtype": "Data",
			"in_list_view": 1,
			"columns": 4,
			"allow_on_submit": 1,
		},
		{
			"fieldname": "is_mandatory",
			"label": "Required",
			"fieldtype": "Check",
			"read_only": 1,
			"columns": 1,
		},
		# Hidden fields for processing
		{
			"fieldname": "field_name",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "field_options",
			"fieldtype": "Text",
			"hidden": 1,
		},
		{
			"fieldname": "depends_on",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "depends_on_field",
			"fieldtype": "Data",
			"hidden": 1,
		},
		{
			"fieldname": "asset_category",
			"fieldtype": "Data",
			"hidden": 1,
		},
	]

	upsert_child_doctype(doctype_name, fields, {"module": "Custom FSF", "editable_grid": 1})


def ensure_asset_category_custom_fields():
	"""Add custom fields table to Asset Category"""
	custom_fields = {
		"Asset Category": [
			{
				"fieldname": "is_main_category",
				"label": "Is Main Category",
				"fieldtype": "Check",
				"insert_after": "asset_category_name",
				"default": "0",
				"description": "Check if this is a main category",
			},
			{
				"fieldname": "main_category",
				"label": "Main Category",
				"fieldtype": "Link",
				"options": "Asset Category",
				"insert_after": "is_main_category",
				"depends_on": "eval:!doc.is_main_category",
				"mandatory_depends_on": "eval:!doc.is_main_category",
				"description": "Select the main category",
			},
			{
				"fieldname": "section_custom_fields",
				"label": "Custom Fields for Assets",
				"fieldtype": "Section Break",
				"insert_after": "finance_books",
				"depends_on": "eval:!doc.is_main_category",
			},
			{
				"fieldname": "custom_fields",
				"label": "Custom Fields",
				"fieldtype": "Table",
				"options": "Category Custom Field",
				"insert_after": "section_custom_fields",
				"depends_on": "eval:!doc.is_main_category",
			},
		]
	}

	create_custom_fields(custom_fields, ignore_validate=True)
	frappe.clear_cache(doctype="Asset Category")


def ensure_asset_classification_fields():
	"""Add Main Category field to Item"""
	custom_fields = {
		"Item": [
			{
				"fieldname": "main_asset_category",
				"label": "Main Category",
				"fieldtype": "Link",
				"options": "Asset Category",
				"insert_after": "is_grouped_asset",
				"depends_on": "eval:doc.is_fixed_asset",
				"mandatory_depends_on": "eval:doc.is_fixed_asset",
			},
		]
	}

	create_custom_fields(custom_fields, ignore_validate=True)
	frappe.clear_cache(doctype="Item")


def ensure_asset_category_value_table():
	"""Add category field values table to Asset"""
	custom_fields = {
		"Asset": [
			{
				"fieldname": "main_asset_category",
				"label": "Main Category",
				"fieldtype": "Link",
				"options": "Asset Category",
				"insert_after": "asset_category",
				"read_only": 1,
				"fetch_from": "asset_category.main_category",
				"fetch_if_empty": 1,
			},
			{
				"fieldname": "section_category_fields",
				"label": "Category Fields",
				"fieldtype": "Section Break",
				"insert_after": "main_asset_category",
				"collapsible": 1,
				"depends_on": "eval:doc.asset_category",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "category_field_values",
				"label": "Field Values",
				"fieldtype": "Table",
				"options": "Asset Category Field Value",
				"insert_after": "section_category_fields",
				"depends_on": "eval:doc.asset_category",
				"allow_on_submit": 1,
			},
		]
	}

	create_custom_fields(custom_fields, ignore_validate=True)
	frappe.clear_cache(doctype="Asset")


def ensure_asset_export_import_fields():
	"""Create hidden Asset fields for category values so Data Export/Import can map them."""
	from custom_fsf.scripts.asset_category_field_values import ensure_asset_export_import_fields

	ensure_asset_export_import_fields()


def upsert_child_doctype(doctype_name, fields, additional_values=None):
	"""Create or update a child table DocType"""
	additional_values = additional_values or {}

	if frappe.db.exists("DocType", doctype_name):
		doc = frappe.get_doc("DocType", doctype_name)
	else:
		doc = frappe.new_doc("DocType")
		doc.name = doctype_name

	doc.module = additional_values.get("module", "Custom FSF")
	doc.custom = 1
	doc.istable = 1
	doc.editable_grid = additional_values.get("editable_grid", 1)
	doc.engine = "InnoDB"

	doc.fields = []
	for field_def in fields:
		doc.append("fields", field_def)

	doc.permissions = []
	doc.flags.ignore_links = True
	doc.flags.ignore_validate = True

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	frappe.clear_cache(doctype=doctype_name)
