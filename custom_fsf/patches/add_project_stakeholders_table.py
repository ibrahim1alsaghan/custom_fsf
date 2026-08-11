import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    create_project_stakeholders_table()
    set_fields_in_list_view()
    create_project_custom_fields()

def create_project_stakeholders_table():
    if frappe.db.exists("DocType", "Project Stakeholders Table"):
        return

    doc = frappe.new_doc("DocType")
    doc.name = "Project Stakeholders Table"
    doc.module = "Projects"
    doc.custom = 1
    doc.istable = 1
    doc.doctype = "DocType"

    doc.append("fields", {"fieldname": "stakeholder_type", "label": "Stakeholder Type", "fieldtype": "Select", "options": "Contact\nEmployee\nCustomer"})
    doc.append("fields", {"fieldname": "stakeholder", "label": "Stakeholder", "fieldtype": "Dynamic Link", "options": "stakeholder_type", "depends_on": "eval:doc.stakeholder_type"})
    doc.append("fields", {"fieldname": "description", "label": "Description", "fieldtype": "Small Text"})
    doc.append("fields", {"fieldname": "role", "label": "Project Role", "fieldtype": "Select", "options": "Sponsor\nProject Owner\nProject Manager\nTeam Member\nOther"})
    doc.append("fields", {"fieldname": "raci", "label": "RACI Role", "fieldtype": "Select", "options": "Responsible\nAccountable\nConsulted\nInformed"})
    doc.append("fields", {"fieldname": "responsibilities", "label": "Responsibilities", "fieldtype": "Text"})

    doc.append("permissions", {
        "role": "System Manager"
    })

    doc.save()
    frappe.db.commit()

def set_fields_in_list_view():
    fields_to_enable = ["stakeholder_type", "stakeholder", "role", "raci"]
    for fieldname in fields_to_enable:
        df = frappe.get_doc("DocField", {
            "parent": "Project Stakeholders Table",
            "fieldname": fieldname
        })
        df.in_list_view = 1
        df.save()
    frappe.db.commit()

def create_project_custom_fields():
    custom_fields = {
        "Project": [
            {
                "fieldname": "section_stakeholders",
                "label": "Stakeholders",
                "fieldtype": "Section Break",
                "insert_after": "project_milestones",
                "collapsible": 1
            },
            {
                "fieldname": "project_stakeholders",
                "label": "Project Stakeholders",
                "fieldtype": "Table",
                "options": "Project Stakeholders Table",
                "insert_after": "section_stakeholders"
            }
        ]
    }

    create_custom_fields(custom_fields)
