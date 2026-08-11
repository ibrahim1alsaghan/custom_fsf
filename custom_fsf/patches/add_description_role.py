import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Role": [
            {
                "fieldname": "description",
                "label": "Role Description",
                "fieldtype": "Data",
                "insert_after": "role_name",
                "reqd": 0
            }
        ]
    }

    create_custom_fields(custom_fields)
