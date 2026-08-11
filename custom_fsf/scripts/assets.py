import frappe
from frappe import _


def set_existing_asset_on_import(doc, method=None):
	"""During Data Import, always mark assets as existing assets."""
	if frappe.flags.in_import:
		doc.is_existing_asset = 1


def validate_import_row(doc, method=None):
    """Friendly, column-aware validation for Asset rows coming from Data
    Import. Runs before ERPNext's own validations, which produce messages
    like "Item None does not exist" — useless to an end user because they
    name neither the spreadsheet column nor the actual problem (an empty
    required cell, or a link value that doesn't exist).

    Collects every problem in the row and throws one bilingual (ar/en)
    message naming each column the way the user sees it in the template.
    """
    if not frappe.flags.in_import:
        return

    meta = frappe.get_meta("Asset")
    problems = []

    for df in meta.fields:
        value = doc.get(df.fieldname)
        label_en = df.label or df.fieldname
        label_ar = frappe._(df.label, lang="ar") if df.label else df.fieldname

        if df.reqd and (value is None or value == ""):
            problems.append(
                f"العمود '{label_ar}' فارغ وهو حقل مطلوب — "
                f"Column '{label_en}' is empty but required"
            )
        elif df.fieldtype == "Link" and value and not frappe.db.exists(df.options, value):
            target_ar = frappe._(df.options, lang="ar")
            line = (
                f"العمود '{label_ar}': القيمة '{value}' غير موجودة في سجلات {target_ar} — "
                f"Column '{label_en}': value '{value}' not found in {df.options}"
            )
            if df.fieldname == "custodian":
                line += (
                    "<br>↳ استخدم رقم الموظف (مثال: HR-EMP-00001) وليس الاسم أو البريد الإلكتروني — "
                    "use the Employee ID, not the name or email"
                )
            problems.append(line)

    if problems:
        frappe.throw(
            "<br><br>".join(problems),
            title=frappe._("Import Row Errors"),
        )



def _get_employee(user):
    """Return the Employee name linked to this user, or None. Uses
    db.get_value so callers don't crash when the user has no linked Employee
    record (System Manager, HD agents, document users, etc.)."""
    return frappe.db.get_value("Employee", {"user_id": user}, "name")


def get_permission_query_conditions(user):
    """Row-level Asset visibility.

    - Asset Manager: every asset.
    - Anyone else with an Employee record: assets where they are the
      custodian, plus assets whose custodian is a direct report of theirs
      (Employee.reports_to) — so a department manager sees his team's
      assets without any extra role.
    """
    if not user:
        return "1=0"

    if "Asset Manager" in frappe.get_roles(user):
        return ""

    employee = _get_employee(user)
    if not employee:
        return "1=0"

    emp = frappe.db.escape(employee)
    return (
        f"(`tabAsset`.custodian = {emp}"
        f" OR `tabAsset`.custodian IN"
        f" (SELECT `name` FROM `tabEmployee` WHERE `reports_to` = {emp}))"
    )


def has_permission(doc, ptype, user):
    """Doc-level access: only Asset Managers may open the Asset form (or
    write/submit/etc.). Custodians and their managers consume assets from
    the list view only — the row filter above decides what they see there."""
    return "Asset Manager" in frappe.get_roles(user)

def validate_asset_sale(doc, method):
    """
    Prevent selling fixed assets with a custodian assigned.
    Hooked into Sales Invoice `before_submit`.
    """
    for item in doc.items:
        if item.asset:
            asset = frappe.get_doc("Asset", item.asset)

            if asset.custodian:
                frappe.throw(
                    _("Cannot sell asset '{0}' because it has a custodian assigned to {1}. Please clear the custodian field before selling.")
                    .format(asset.name, asset.custodian)
                )


def validate_asset_movement(doc, method):
    """
    Validate Asset Movement - prevent moving Scrapped or Sold assets.
    Hooked into Asset Movement `validate`.
    """
    invalid_statuses = ["Scrapped", "Sold"]

    for row in doc.assets:
        if not row.asset:
            continue

        asset_status = frappe.db.get_value("Asset", row.asset, "status")

        if asset_status in invalid_statuses:
            frappe.throw(
                _("Cannot move asset '{0}' because it has status '{1}'. Only active assets can be moved or assigned.").format(
                    frappe.bold(row.asset),
                    frappe.bold(asset_status)
                ),
                title=_("Invalid Asset Status")
            )
