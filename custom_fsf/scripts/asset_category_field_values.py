import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint, getdate
import hashlib
import json

VALUE_TABLE_FIELD = "category_field_values"
VALUE_DOCTYPE = "Asset Category Field Value"
ASSET_DOCTYPE = "Asset"


def before_validate(doc, method=None):
	if not can_manage_category_values(doc):
		return
	sync_category_field_rows(doc)


def validate(doc, method=None):
	if not can_manage_category_values(doc):
		return
	validate_field_values(doc)


def ensure_asset_fields_for_data_import(doc, method=None):
	"""Ensure category-backed Asset columns EXIST before import preview/execution.

	Runs on every Data Import save, so it must stay cheap: backfill=False skips
	the per-asset value scan (only needed for export). Without this, every file
	upload re-scanned all assets and cleared the Asset meta cache — the cause of
	slow uploads as the asset count grew."""
	reference_doctype = doc.get("reference_doctype") if hasattr(doc, "get") else None
	if reference_doctype == ASSET_DOCTYPE:
		ensure_asset_export_import_fields(backfill=False)


def sync_category_field_rows(doc):
	"""Sync field rows based on Asset Category custom_fields"""
	if not doc.asset_category:
		doc.set(VALUE_TABLE_FIELD, [])
		return

	definitions = get_definition_rows(doc.asset_category)
	if not definitions:
		doc.set(VALUE_TABLE_FIELD, [])
		return

	# Map existing values (normalize field names for compatibility with old data)
	existing_values = {}
	for row in doc.get(VALUE_TABLE_FIELD, []) or []:
		if row.field_name:
			# Store with both original and scrubbed key for compatibility
			existing_values[row.field_name] = row.field_value or ""
			existing_values[frappe.scrub(row.field_name)] = row.field_value or ""
		# Also index by scrubbed label for old fields with manually set field_name
		if row.field_label:
			existing_values[frappe.scrub(row.field_label)] = row.field_value or ""

	# During data import the flattened Asset fields are the incoming source.
	# During normal form saves the child table remains the source of truth.
	for defn in definitions:
		field_name = defn["field_name"]
		export_fieldname = defn["export_fieldname"]
		# Read the hashed export field first: stale unhashed Custom Fields from
		# older deployments can shadow it with a default from a different category.
		field_value = doc.get(export_fieldname)
		if field_value in ("", None) and field_name != export_fieldname:
			field_value = doc.get(field_name)
		if frappe.flags.in_import:
			if field_value not in ("", None):
				existing_values[field_name] = field_value
				existing_values[frappe.scrub(field_name)] = field_value
				existing_values[export_fieldname] = field_value
		elif field_value not in ("", None) and field_name not in existing_values:
			existing_values[field_name] = field_value
			existing_values[export_fieldname] = field_value

	# Build new rows
	new_rows = []
	for defn in definitions:
		# Check dependency
		if defn.get("depends_on"):
			dep_field, dep_value = parse_depends_on(defn["depends_on"])
			if dep_field and existing_values.get(dep_field) != dep_value:
				continue

		field_value = normalize_category_field_value(defn, existing_values.get(defn["field_name"], ""))
		if doc.meta.get_field(defn["export_fieldname"]):
			doc.set(defn["export_fieldname"], field_value)

		new_rows.append({
			"field_name": defn["field_name"],
			"field_label": defn["field_label"],
			"field_type": defn["field_type"],
			"field_options": defn.get("field_options", ""),
			"is_mandatory": cint(defn.get("is_mandatory", 0)),
			"field_value": field_value,
			"depends_on": defn.get("depends_on", ""),
			"asset_category": doc.asset_category,
		})

	doc.set(VALUE_TABLE_FIELD, [])
	for row in new_rows:
		doc.append(VALUE_TABLE_FIELD, row)


def parse_depends_on(depends_on_str):
	"""Parse 'field_name=value' format"""
	if not depends_on_str or "=" not in depends_on_str:
		return None, None
	parts = depends_on_str.split("=", 1)
	# Scrub the field name to match how field_names are stored
	field_name = frappe.scrub(parts[0].strip())
	return field_name, parts[1].strip()


def validate_field_values(doc):
	"""Validate field values"""
	for row in doc.get(VALUE_TABLE_FIELD, []) or []:
		field_type = row.field_type or "Text"
		field_value = row.field_value or ""
		field_label = row.field_label or ""
		is_mandatory = cint(row.is_mandatory)

		if is_mandatory and not field_value:
			frappe.throw(_("Field '{0}' is required.").format(frappe.bold(field_label)))

		if not field_value:
			continue

		if field_type == "Number":
			try:
				int(field_value)
			except ValueError:
				frappe.throw(_("Field '{0}' must be a number.").format(frappe.bold(field_label)))

		elif field_type == "Date":
			try:
				getdate(field_value)
			except Exception:
				frappe.throw(_("Field '{0}' must be a valid date.").format(frappe.bold(field_label)))

		elif field_type == "Select":
			options = parse_options(row.field_options)
			option_values = [o["value"] for o in options]
			if option_values and field_value not in option_values:
				frappe.throw(_("Field '{0}' must be one of: {1}").format(
					frappe.bold(field_label), ", ".join(option_values)
				))


def parse_options(options_str):
	"""Parse options - supports JSON or comma-separated"""
	if not options_str:
		return []

	# Try JSON first
	try:
		options = json.loads(options_str)
		if isinstance(options, list):
			result = []
			for opt in options:
				if isinstance(opt, dict):
					result.append(opt)
				else:
					result.append({"value": str(opt), "depends_on": ""})
			return result
	except (json.JSONDecodeError, TypeError):
		pass

	# Comma-separated
	return [{"value": o.strip(), "depends_on": ""} for o in options_str.split(",") if o.strip()]


def get_definition_rows(asset_category):
	"""Get field definitions from Asset Category"""
	if not asset_category or not frappe.db.exists("Asset Category", asset_category):
		return []

	category_doc = frappe.get_doc("Asset Category", asset_category)
	custom_fields = category_doc.get("custom_fields") or []

	definitions = []
	for field in custom_fields:
		if not field.field_label:
			continue

		# Generate field_name if not set
		field_name = field.field_name or frappe.scrub(field.field_label)

		# Parse depends_on to extract the field name for Select dependencies
		depends_on = field.depends_on or ""
		depends_on_field = ""
		if depends_on:
			depends_on_field = frappe.scrub(depends_on.split("=")[0].strip())

		# Build options JSON
		options_json = ""
		if field.field_type == "Select" and field.options:
			options = []
			for opt in field.options.split("\n"):
				opt = opt.strip()
				if opt:
					if "|" in opt:
						parts = opt.split("|", 1)
						value = parts[0].strip()
						dep = parts[1].strip() if len(parts) > 1 else ""
						options.append({"value": value, "depends_on": dep})
					else:
						options.append({"value": opt, "depends_on": ""})
			options_json = json.dumps(options)

		definitions.append({
			"field_name": field_name,
			"export_fieldname": get_export_import_fieldname(field_name, asset_category),
			"category": asset_category,
			"field_label": field.field_label,
			"field_type": field.field_type or "Text",
			"field_options": options_json,
			"is_mandatory": cint(field.is_mandatory),
			"depends_on": depends_on,
			"depends_on_field": depends_on_field,
		})

	return definitions


def ensure_asset_export_import_fields(asset_category=None, backfill=True):
	"""Mirror category field definitions to hidden Asset custom fields.

	Frappe's Data Export and Data Import tools only understand DocType fields. The
	visible Asset UI stores these values in a child table, so these hidden fields
	serve as import/export columns and are synchronized on Asset validation.
	"""
	if not frappe.db.exists("DocType", ASSET_DOCTYPE):
		return

	definition_map = {}
	for category in get_categories_for_export_import(asset_category):
		for defn in get_definition_rows(category):
			export_fn = defn.get("export_fieldname")
			if not export_fn or not defn.get("field_label"):
				continue
			if is_core_asset_field(defn.get("field_name")):
				continue
			definition_map[export_fn] = defn

	if not definition_map:
		return

	fields = []
	insert_after = VALUE_TABLE_FIELD
	for defn in definition_map.values():
		field = {
			"fieldname": defn["export_fieldname"],
			"label": f"{defn['field_label']} ({defn.get('category', '')})",
			"fieldtype": get_asset_export_import_fieldtype(defn.get("field_type")),
			"insert_after": insert_after,
			"hidden": 1,
			"allow_on_submit": 1,
			"no_copy": 1,
			"description": _("Synchronized from Asset Category Field Values for Data Import/Export."),
		}

		if field["fieldtype"] == "Select":
			field["options"] = get_select_field_options(defn.get("field_options"))

		fields.append(field)
		insert_after = defn["export_fieldname"]

	# Only create + invalidate the Asset meta cache when a column is actually
	# missing. In steady state every column already exists, so this collapses
	# to one cheap query instead of create_custom_fields + clear_cache on
	# every call. (clear_cache(Asset) is expensive — it rebuilds the meta.)
	existing = set(
		frappe.get_all(
			"Custom Field",
			filters={"dt": ASSET_DOCTYPE, "fieldname": ["in", list(definition_map.keys())]},
			pluck="fieldname",
		)
	)
	missing = [f for f in fields if f["fieldname"] not in existing]
	if missing:
		create_custom_fields({ASSET_DOCTYPE: missing}, ignore_validate=True)
		frappe.clear_cache(doctype=ASSET_DOCTYPE)

	# The backfill copies child-table values into the hidden export columns and
	# scans every asset — O(asset count). It's only needed for EXPORT (export
	# refreshes the columns itself) and when definitions change. The Data Import
	# path passes backfill=False: an import only needs the columns to EXIST so
	# the uploaded file can map to them; it never reads pre-filled values.
	if backfill:
		backfill_asset_export_import_values(definition_map)


def get_categories_for_export_import(asset_category=None):
	if asset_category:
		return [asset_category] if frappe.db.exists("Asset Category", asset_category) else []

	return frappe.get_all("Asset Category", pluck="name")


def is_core_asset_field(field_name):
	meta = frappe.get_meta(ASSET_DOCTYPE)
	df = meta.get_field(field_name)
	return bool(df and not getattr(df, "is_custom_field", False))


def get_asset_export_import_fieldtype(field_type):
	if field_type == "Date":
		return "Date"
	if field_type == "Number":
		return "Int"
	if field_type == "Select":
		return "Select"
	return "Small Text"


def get_select_field_options(field_options):
	options = parse_options(field_options)
	return "\n".join(option["value"] for option in options if option.get("value"))


def backfill_asset_export_import_values(definition_map=None):
	"""Copy existing child-table values into the hidden Asset columns.

	definition_map is keyed by export_fieldname (category-scoped). Each entry
	includes "field_name" and "category" so we can match the right column per asset.
	"""
	definition_map = definition_map or {}
	if not definition_map:
		return

	# Secondary index: (field_name, category) → export_fieldname
	fn_cat_to_export = {
		(defn["field_name"], defn.get("category")): export_fn
		for export_fn, defn in definition_map.items()
		if defn.get("field_name") and defn.get("category")
	}

	unique_field_names = list({defn["field_name"] for defn in definition_map.values() if defn.get("field_name")})
	if not unique_field_names:
		return

	values = frappe.get_all(
		VALUE_DOCTYPE,
		filters={
			"parenttype": ASSET_DOCTYPE,
			"parentfield": VALUE_TABLE_FIELD,
			"field_name": ["in", unique_field_names],
		},
		fields=["parent", "field_name", "field_value"],
	)

	if not values:
		return

	# Fetch asset categories in one query
	asset_names = list({row.parent for row in values if row.parent})
	asset_category_map = {
		r.name: r.asset_category
		for r in frappe.get_all(
			ASSET_DOCTYPE,
			filters={"name": ["in", asset_names]},
			fields=["name", "asset_category"],
		)
	}

	for row in values:
		if not row.parent or not row.field_name:
			continue
		cat = asset_category_map.get(row.parent)
		export_fn = fn_cat_to_export.get((row.field_name, cat))
		if not export_fn:
			continue
		defn = definition_map[export_fn]
		field_value = normalize_category_field_value(defn, row.field_value or "")
		if field_value == "" and defn.get("field_type") in ("Number", "Date"):
			continue
		frappe.db.set_value(
			ASSET_DOCTYPE,
			row.parent,
			export_fn,
			field_value,
			update_modified=False,
		)


def get_export_import_fieldname(field_name, category=None):
	"""Return a DB-column-safe fieldname for hidden Asset import/export fields.

	Always includes a (field_name, category) hash suffix so the same field_name
	in two different Asset Categories never maps to the same hidden column on Asset.
	"""
	scrubbed = frappe.scrub(field_name or "")
	safe_fieldname = "".join(char for char in scrubbed if char.isalnum() or char == "_").strip("_")

	if not safe_fieldname:
		safe_fieldname = "category_field"

	if safe_fieldname[0].isdigit():
		safe_fieldname = f"category_{safe_fieldname}"

	combined = f"{field_name or ''}::{category or ''}"
	suffix = hashlib.sha1(combined.encode("utf-8")).hexdigest()[:8]
	safe_fieldname = f"{safe_fieldname}_{suffix}"

	return safe_fieldname[:120]


def normalize_category_field_value(defn, value):
	"""Store category field values in the format expected by the dynamic UI."""
	if value in ("", None):
		return ""

	if defn.get("field_type") == "Date":
		return getdate(value).isoformat()

	return str(value)


@frappe.whitelist()
def normalize_existing_asset_category_field_values():
	"""Normalize stored category field values after import/export field changes."""
	rows = frappe.get_all(
		VALUE_DOCTYPE,
		filters={"parenttype": ASSET_DOCTYPE, "parentfield": VALUE_TABLE_FIELD},
		fields=["name", "field_name", "field_type", "field_value"],
	)

	for row in rows:
		normalized_value = normalize_category_field_value(
			{"field_type": row.field_type}, row.field_value
		)
		if normalized_value != (row.field_value or ""):
			frappe.db.set_value(
				VALUE_DOCTYPE,
				row.name,
				"field_value",
				normalized_value,
				update_modified=False,
			)
	frappe.db.commit()


def can_manage_category_values(doc):
	if not frappe.db.exists("DocType", VALUE_DOCTYPE):
		return False
	meta = frappe.get_meta(doc.doctype)
	return meta.get_field(VALUE_TABLE_FIELD) is not None


@frappe.whitelist()
def get_category_field_definitions(asset_category):
	"""API endpoint for frontend - get field definitions for a specific category"""
	return get_definition_rows(asset_category)


@frappe.whitelist()
def get_all_custom_field_definitions(asset_names=None):
	"""Get all unique custom field definitions from all Asset Categories for Export dialog"""
	# backfill=False: this runs every time the export/import dialog OPENS (to
	# populate the field picker). It only needs the columns to exist, not the
	# per-asset value scan — that scan is what made the dialog hang on large
	# sites. Without this, opening "Download Template" stalls before it even
	# appears, regardless of the blank-template choice.
	ensure_asset_export_import_fields(backfill=False)

	all_fields = {}
	if isinstance(asset_names, str):
		asset_names = json.loads(asset_names)

	if asset_names:
		categories = frappe.get_all(
			ASSET_DOCTYPE,
			filters={"name": ["in", asset_names]},
			pluck="asset_category",
			distinct=True,
		)
	else:
		categories = frappe.get_all("Asset Category", pluck="name")

	for cat in categories:
		definitions = get_definition_rows(cat)
		for defn in definitions:
			export_fn = defn["export_fieldname"]
			all_fields[export_fn] = {
				"field_name": defn["field_name"],
				"export_fieldname": export_fn,
				"field_label": defn["field_label"],
				"field_type": defn["field_type"],
				"field_options": defn.get("field_options", ""),
				"category": cat,
				"categories": [cat],
				"category_order": [categories.index(cat)],
			}

	return sorted(
		all_fields.values(),
		key=lambda field: (
			field["category_order"][0] if field["category_order"] else 9999,
			field["categories"][0] if field["categories"] else "",
			field["field_label"] or field["field_name"],
		),
	)


@frappe.whitelist()
def download_assets_excel_data(data=None):
	"""Generate Excel file from data array - called by JS export"""
	from frappe.utils.xlsxutils import make_xlsx

	if not data:
		frappe.throw(_("No data provided"))

	if isinstance(data, str):
		data = json.loads(data)

	# A header-only payload (no data rows) is still a valid export — it produces an
	# empty template, matching the CSV path. Only reject a completely empty payload.
	if not data:
		frappe.throw(_("No data to export"))

	xlsx_file = make_xlsx(data, "Assets")

	frappe.response["filename"] = "Assets.xlsx"
	frappe.response["filecontent"] = xlsx_file.getvalue()
	frappe.response["type"] = "binary"
