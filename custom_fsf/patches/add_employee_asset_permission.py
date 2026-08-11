import frappe

def execute():
    if not frappe.db.exists("Custom DocPerm", {"parent": "Asset", "role": "Employee", "permlevel": 0}):
        doc = frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": "Asset",
            "parenttype": "DocType",
            "role": "Employee",
            "permlevel": 0,
            "read": 1
        })
        doc.insert()
        frappe.db.commit()
        print("✅ Added read permission for 'Employee' on 'Asset'")
    else:
        print("⚠️ Permission already exists")
