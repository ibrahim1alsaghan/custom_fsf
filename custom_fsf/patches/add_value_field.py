import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    add_description_and_value_fields()

def add_description_and_value_fields():
    custom_fields = {
        "Project": [
            {
                "fieldname": "project_description",
                "label": "Description",
                "fieldtype": "Data",
                "insert_after": "project_name"
            },
            {
                "fieldname": "project_value",
                "label": "Value",
                "fieldtype": "Currency",
                "insert_after": "project_description"
            }
        ]
    }

    create_custom_fields(custom_fields)
