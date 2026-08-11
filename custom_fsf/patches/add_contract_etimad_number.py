import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DT = "Project"
ALLOWED_ROLES = ["System Manager", "Projects Manager"]

def execute():
    add_contract_fields()
    ensure_level_zero_for_allowed_roles()
    ensure_level_one_for_allowed_roles()
    revoke_level_one_from_others()
    frappe.clear_cache(doctype=DT)

def add_contract_fields():
    """Add fields with permlevel=1 so only roles with permlevel-1 perms can see them."""
    custom_fields = {
        DT: [
            {
                "fieldname": "section_contract_info",
                "label": "Contract Information",
                "fieldtype": "Section Break",
                "insert_after": "department",
                "collapsible": 1,
                "permlevel": 1,
            },
            {
                "fieldname": "contract_number",
                "label": "Contract Number",
                "fieldtype": "Data",
                "insert_after": "section_contract_info",
                "length": 50,        # VARCHAR(50)
                "permlevel": 1,
                "in_global_search": 0,
                "translatable": 0,
            },
            {
                "fieldname": "column_break_contract_info",
                "fieldtype": "Column Break",
                "insert_after": "contract_number",
                "permlevel": 1,
            },
            {
                "fieldname": "etimad_number",
                "label": "Etimad Number",
                "fieldtype": "Data",
                "insert_after": "column_break_contract_info",
                "length": 50,
                "permlevel": 1,
                "in_global_search": 0,
                "translatable": 0,
            },
        ]
    }
    create_custom_fields(custom_fields, update=True)

def ensure_level_zero_for_allowed_roles():
    """Make sure a permlevel 0 row exists for each allowed role (required by Frappe)."""
    parent = frappe.get_doc("DocType", DT)
    existing = {(p.role, p.permlevel) for p in parent.permissions}
    changed = False
    for role in ALLOWED_ROLES:
        if (role, 0) not in existing:
            parent.append("permissions", {"role": role, "permlevel": 0, "read": 1})
            changed = True
    if changed:
        parent.save()

def ensure_level_one_for_allowed_roles():
    """Grant permlevel 1 read/write for allowed roles (so they see/edit the fields)."""
    parent = frappe.get_doc("DocType", DT)
    idx = {(p.role, p.permlevel): p for p in parent.permissions}
    changed = False
    for role in ALLOWED_ROLES:
        if (role, 1) not in idx:
            parent.append("permissions", {"role": role, "permlevel": 1, "read": 1, "write": 1})
            changed = True
        else:
            p = idx[(role, 1)]
            if not p.read or not p.write:
                p.read = 1
                p.write = 1
                changed = True
    if changed:
        parent.save()

def revoke_level_one_from_others():
    """Remove any permlevel 1 rows for roles NOT in ALLOWED_ROLES."""
    parent = frappe.get_doc("DocType", DT)
    changed = False
    # iterate over a copy since we're mutating the child table
    for p in list(parent.permissions):
        if p.permlevel == 1 and p.role not in ALLOWED_ROLES:
            parent.permissions.remove(p)
            changed = True
    if changed:
        parent.save()
