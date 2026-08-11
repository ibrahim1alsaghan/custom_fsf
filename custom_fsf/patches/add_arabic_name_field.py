import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "User": [
            {
                "fieldname": "full_name_arabic",
                "label": "Full Name (Arabic)",
                "fieldtype": "Data",
                "insert_after": "full_name",
                "reqd": 0
            }
        ]
    }
    create_custom_fields(custom_fields)

    users = frappe.get_all("User",
        filters={"full_name_arabic": ("in", ["", None])},
        fields=["name", "full_name", "first_name"]
    )
    for user in users:
        frappe.db.set_value("User", user.name,
            "full_name_arabic",
            user.full_name or user.first_name or user.name,
            update_modified=False
        )

    if users:
        frappe.db.commit()

    frappe.db.set_value("Custom Field", "User-full_name_arabic", "reqd", 1)
    frappe.db.commit()