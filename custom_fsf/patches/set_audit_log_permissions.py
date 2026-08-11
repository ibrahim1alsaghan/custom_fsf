import frappe

def execute():
    # 1. Create role if it doesn't exist
    if not frappe.db.exists("Role", "Audit Viewer"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "Audit Viewer",
            "desk_access": 1,
            "module": "custom fsf",
            "description": "Can view and export audit logs"
        }).insert(ignore_permissions=True)

    # 2. Remove any existing permission rows for this role on this DocType
    frappe.db.delete("Custom DocPerm", {
        "parent": "Audit Log",
        "role": "Audit Viewer"
    })

    # 3. Insert new permission row
    frappe.get_doc({
        "doctype": "Custom DocPerm",
        "role": "Audit Viewer",
        "parent": "Audit Log",
        "parenttype": "DocType",
        "permlevel": 0,
        "read": 1,
        "export": 1,
        "print": 1,
        "report": 1,
        "share": 1
    }).insert(ignore_permissions=True)

    frappe.clear_cache(doctype="Audit Log")
    frappe.db.commit()
