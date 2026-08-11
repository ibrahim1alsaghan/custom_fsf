import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    create_project_escalation_table()
    set_fields_in_list_view()
    create_project_custom_fields()

def create_project_escalation_table():
    if frappe.db.exists("DocType", "Project Escalation Table"):
        return  # Already created

    doc = frappe.new_doc("DocType")
    doc.name = "Project Escalation Table"
    doc.module = "Projects"
    doc.custom = 1
    doc.istable = 1
    doc.is_submittable = 0
    doc.doctype = "DocType"

    doc.append("fields", {"fieldname": "subject", "label": "Subject", "fieldtype": "Data"})
    doc.append("fields", {"fieldname": "description", "label": "Description", "fieldtype": "Small Text"})
    doc.append("fields", {"fieldname": "escalated_by", "label": "Escalated By", "fieldtype": "Link", "options": "User"})
    doc.append("fields", {"fieldname": "escalated_to", "label": "Escalated To", "fieldtype": "Link", "options": "User"})
    doc.append("fields", {"fieldname": "date_raised", "label": "Date Raised", "fieldtype": "Date"})
    doc.append("fields", {
        "fieldname": "severity",
        "label": "Severity/Urgency",
        "fieldtype": "Select",
        "options": "Low\nMedium\nHigh\nCritical"
    })
    doc.append("fields", {
        "fieldname": "status",
        "label": "Status",
        "fieldtype": "Select",
        "options": "Open\nUnder Review\nResolved"
    })

    doc.append("permissions", {
        "role": "System Manager"
    })

    doc.save()
    frappe.db.commit()

def set_fields_in_list_view():
    """Enable fields to show in table grid view."""
    fields_to_enable = ["subject", "escalated_by", "escalated_to", "date_raised", "severity", "status"]

    for fieldname in fields_to_enable:
        df = frappe.get_doc("DocField", {
            "parent": "Project Escalation Table",
            "fieldname": fieldname
        })
        df.in_list_view = 1
        df.save()

    frappe.db.commit()

def create_project_custom_fields():
    custom_fields = {
        "Project": [
            {
                "fieldname": "section_escalations",
                "label": "Escalations",
                "fieldtype": "Section Break",
                "insert_after": "project_milestones",
                "collapsible": 1
            },
            {
                "fieldname": "project_escalations",
                "label": "Project Escalations",
                "fieldtype": "Table",
                "options": "Project Escalation Table",
                "insert_after": "section_escalations"
            }
        ]
    }

    create_custom_fields(custom_fields)
# test