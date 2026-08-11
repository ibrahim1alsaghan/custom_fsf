import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    create_project_milestone_table()
    set_fields_in_list_view()
    create_project_custom_fields()

def create_project_milestone_table():
    if frappe.db.exists("DocType", "Project Milestone Table"):
        return  # Already created

    doc = frappe.new_doc("DocType")
    doc.name = "Project Milestone Table"
    doc.module = "Projects"
    doc.custom = 1
    doc.istable = 1
    doc.is_submittable = 0
    doc.doctype = "DocType"

    doc.append("fields", {
        "fieldname": "description",
        "label": "Description",
        "fieldtype": "Data"
    })
    doc.append("fields", {
        "fieldname": "due_date",
        "label": "Due Date",
        "fieldtype": "Date"
    })
    doc.append("fields", {
        "fieldname": "status",
        "label": "Status",
        "fieldtype": "Select",
        "options": "Planned\nIn Progress\nCompleted\nCancelled\nOn Hold"
    })
    doc.append("fields", {
        "fieldname": "value",
        "label": "Value",
        "fieldtype": "Currency"
    })
    doc.append("fields", {
        "fieldname": "notes",
        "label": "Notes",
        "fieldtype": "Small Text"
    })

    doc.append("permissions", {
        "role": "System Manager"
    })

    doc.save()
    frappe.db.commit()

def set_fields_in_list_view():
    """Ensure list view fields show in the grid view."""
    fields_to_enable = ["description", "due_date", "status", "value"]

    for fieldname in fields_to_enable:
        df = frappe.get_doc("DocField", {
            "parent": "Project Milestone Table",
            "fieldname": fieldname
        })
        df.in_list_view = 1
        df.save()

    frappe.db.commit()

def create_project_custom_fields():
    custom_fields = {
        "Project": [
            {
                "fieldname": "section_milestones",
                "label": "Milestones",
                "fieldtype": "Section Break",
                "insert_after": "department",
                "collapsible": 1
            },
            {
                "fieldname": "project_milestones",
                "label": "Project Milestones",
                "fieldtype": "Table",
                "options": "Project Milestone Table",
                "insert_after": "section_milestones"
            }
        ]
    }

    create_custom_fields(custom_fields)
