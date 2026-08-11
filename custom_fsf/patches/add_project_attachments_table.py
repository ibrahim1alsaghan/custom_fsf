import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    create_project_attachment_table()
    add_attachments_section_to_project()

def create_project_attachment_table():
    if frappe.db.exists("DocType", "Project Attachment Table"):
        return

    doc = frappe.new_doc("DocType")
    doc.name = "Project Attachment Table"
    doc.module = "Projects"
    doc.custom = 1
    doc.istable = 1
    doc.is_submittable = 0
    doc.doctype = "DocType"

    doc.append("fields", {
        "fieldname": "attachment_name",
        "label": "Attachment Name",
        "fieldtype": "Data",
        "in_list_view": 1
    })
    doc.append("fields", {
        "fieldname": "attachment_file",
        "label": "Attachment",
        "fieldtype": "Attach",
        "in_list_view": 1
    })
    doc.append("fields", {
        "fieldname": "description",
        "label": "Description",
        "fieldtype": "Small Text",
        "in_list_view": 0
    })

    doc.append("permissions", {
        "role": "System Manager"
    })

    doc.save()
    frappe.db.commit()

def add_attachments_section_to_project():
    custom_fields = {
        "Project": [
            {
                "fieldname": "section_attachments",
                "label": "Attachments",
                "fieldtype": "Section Break",
                "insert_after": "project_milestones",  # After milestone table
                "collapsible": 1
            },
            {
                "fieldname": "project_attachments",
                "label": "Project Attachments",
                "fieldtype": "Table",
                "options": "Project Attachment Table",
                "insert_after": "section_attachments"
            }
        ]
    }

    create_custom_fields(custom_fields)
