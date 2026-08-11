import frappe
from frappe import _

# These hooks are now deprecated - using standalone Category Field Definition DocType instead


def before_save(doc, method=None):
	"""
	Validate custom fields before saving Asset Category
	"""
	validate_no_duplicate_fields(doc)


def validate_no_duplicate_fields(doc):
	"""Prevent duplicate field labels in custom_fields table"""
	if not doc.get("custom_fields"):
		return

	seen_labels = {}
	seen_names = {}

	for row in doc.custom_fields:
		# Check duplicate field_label
		if row.field_label:
			label_lower = row.field_label.strip().lower()
			if label_lower in seen_labels:
				frappe.throw(
					_("Duplicate field label '{0}' found in row {1}. Each field must have a unique label.").format(
						frappe.bold(row.field_label),
						row.idx
					),
					title=_("Duplicate Field")
				)
			seen_labels[label_lower] = row.idx

		# Check duplicate field_name
		field_name = row.field_name or frappe.scrub(row.field_label or "")
		if field_name:
			if field_name in seen_names:
				frappe.throw(
					_("Duplicate field name '{0}' found in row {1}. Each field must have a unique name.").format(
						frappe.bold(field_name),
						row.idx
					),
					title=_("Duplicate Field")
				)
			seen_names[field_name] = row.idx


def on_update(doc, method=None):
	"""
	Handle field updates including migrations and deletions
	"""
	from custom_fsf.scripts.asset_category_field_values import ensure_asset_export_import_fields

	ensure_asset_export_import_fields(doc.name)

	if not doc.get("custom_fields"):
		return

	# Check for field migrations (renamed fields)
	for row in doc.custom_fields:
		if hasattr(row, "__migrate_from") and row.__migrate_from:
			migrate_field_data(doc.name, row.__migrate_from, row.field_name)
			delattr(row, "__migrate_from")

	# Handle deleted fields - clean up their data
	if hasattr(doc, "_deleted_fields") and doc._deleted_fields:
		for field_name in doc._deleted_fields:
			delete_field_data(doc.name, field_name)
		doc._deleted_fields = []


def migrate_field_data(asset_category, old_field_name, new_field_name):
	"""
	Migrate field data when a field is renamed
	"""
	if not frappe.db.exists("DocType", "Asset Category Field Value"):
		return

	# Update field_name in all Asset Category Field Value records
	frappe.db.sql("""
		UPDATE `tabAsset Category Field Value`
		SET field_name = %s
		WHERE asset_category = %s AND field_name = %s
	""", (new_field_name, asset_category, old_field_name))

	frappe.db.commit()


def delete_field_data(asset_category, field_name):
	"""
	Delete field data when a field is removed
	"""
	if not frappe.db.exists("DocType", "Asset Category Field Value"):
		return

	frappe.db.delete("Asset Category Field Value", {
		"asset_category": asset_category,
		"field_name": field_name
	})


@frappe.whitelist()
def check_field_has_data(asset_category, field_name):
	"""
	Check if a custom field has any data in Assets.
	Returns count of assets with data for this field.
	"""
	if not asset_category or not field_name:
		return {"has_data": False, "count": 0}

	# Check Asset Category Field Value child table
	count = frappe.db.count(
		"Asset Category Field Value",
		filters={
			"asset_category": asset_category,
			"field_name": field_name,
			"field_value": ["!=", ""]
		}
	)

	return {"has_data": count > 0, "count": count}


@frappe.whitelist()
def check_removed_fields_data(asset_category, removed_fields):
	"""
	Check if any of the removed fields have data in Assets.
	"""
	import json
	if isinstance(removed_fields, str):
		removed_fields = json.loads(removed_fields)

	if not asset_category or not removed_fields:
		return {"has_data": False, "count": 0, "fields_with_data": []}

	fields_with_data = []
	total_count = 0

	for field_name in removed_fields:
		count = frappe.db.count(
			"Asset Category Field Value",
			filters={
				"asset_category": asset_category,
				"field_name": field_name,
				"field_value": ["!=", ""]
			}
		)
		if count > 0:
			fields_with_data.append(field_name)
			total_count += count

	return {
		"has_data": len(fields_with_data) > 0,
		"count": total_count,
		"fields_with_data": fields_with_data
	}


@frappe.whitelist()
def get_custom_fields_for_category(asset_category):
	"""
	Get all custom fields defined for an asset category.
	Used for building filters and search options.
	"""
	if not asset_category:
		return []

	category = frappe.get_doc("Asset Category", asset_category)
	if not category.get("custom_fields"):
		return []

	return [
		{
			"field_name": row.field_name or frappe.scrub(row.field_label or ""),
			"field_label": row.field_label,
			"field_type": row.field_type,
			"options": row.options,
			"is_mandatory": row.is_mandatory
		}
		for row in category.custom_fields
	]


@frappe.whitelist()
def get_all_custom_fields():
	"""
	Get all custom fields from all asset categories.
	Used for global search and filter options.
	"""
	fields = []
	seen_field_names = set()

	categories = frappe.get_all(
		"Asset Category",
		filters={"is_main_category": 0},
		pluck="name"
	)

	for category_name in categories:
		try:
			category = frappe.get_doc("Asset Category", category_name)
			if not category.get("custom_fields"):
				continue

			for row in category.custom_fields:
				# Ensure we have a valid field_label
				field_label = row.field_label or ""
				if not field_label.strip():
					continue

				field_name = row.field_name or frappe.scrub(field_label)
				if not field_name or field_name in seen_field_names:
					continue

				seen_field_names.add(field_name)
				fields.append({
					"field_name": field_name,
					"field_label": field_label,
					"field_type": row.field_type or "Data",
					"options": row.options or "",
					"category": category_name
				})
		except Exception:
			continue

	return fields


@frappe.whitelist()
def search_assets_by_custom_field(field_name, field_value, asset_category=None):
	"""
	Search assets by custom field value.
	Returns list of asset names matching the criteria.
	"""
	filters = {
		"field_name": field_name,
		"field_value": ["like", f"%{field_value}%"]
	}

	if asset_category:
		filters["asset_category"] = asset_category

	# Get parent assets that have matching field values
	results = frappe.get_all(
		"Asset Category Field Value",
		filters=filters,
		fields=["parent"],
		distinct=True
	)

	return [r.parent for r in results]


@frappe.whitelist()
def get_custom_field_filter_options(field_name, asset_category=None):
	"""
	Get unique values for a custom field (for Select filter dropdowns).
	"""
	filters = {
		"field_name": field_name,
		"field_value": ["!=", ""]
	}

	if asset_category:
		filters["asset_category"] = asset_category

	results = frappe.get_all(
		"Asset Category Field Value",
		filters=filters,
		fields=["field_value"],
		distinct=True,
		order_by="field_value"
	)

	return [r.field_value for r in results]


@frappe.whitelist()
def filter_assets_by_custom_fields(filters):
	"""
	Filter assets by multiple custom field values.
	Used by the built-in Frappe filter system.

	Args:
		filters: List of dicts with field_name and value keys

	Returns:
		List of asset names matching ALL filter criteria
	"""
	import json
	if isinstance(filters, str):
		filters = json.loads(filters)

	if not filters:
		return []

	# Start with all assets
	matching_assets = None

	for f in filters:
		field_name = f.get("field_name")
		value = f.get("value")

		if not field_name or not value:
			continue

		# Find assets matching this filter
		results = frappe.get_all(
			"Asset Category Field Value",
			filters={
				"field_name": field_name,
				"field_value": ["like", f"%{value}%"]
			},
			fields=["parent"],
			distinct=True
		)

		current_matches = set(r.parent for r in results)

		if matching_assets is None:
			matching_assets = current_matches
		else:
			# Intersection - asset must match ALL filters
			matching_assets = matching_assets.intersection(current_matches)

		# Early exit if no matches
		if not matching_assets:
			return []

	return list(matching_assets) if matching_assets else []


def on_trash(doc, method=None):
	"""
	When Asset Category is deleted, clean up related field definitions
	"""
	# Clean up Category Field Definitions for this category
	if frappe.db.exists("DocType", "Category Field Definition"):
		definitions = frappe.get_all(
			"Category Field Definition",
			filters={"asset_category": doc.name},
			pluck="name"
		)
		for name in definitions:
			# First delete related options
			if frappe.db.exists("DocType", "Category Field Option"):
				frappe.db.delete("Category Field Option", {"field_definition": name})
			# Then delete the definition
			frappe.delete_doc("Category Field Definition", name, ignore_permissions=True)

	# Clean up Asset Category Field Values
	if frappe.db.exists("DocType", "Asset Category Field Value"):
		frappe.db.delete("Asset Category Field Value", {"asset_category": doc.name})
