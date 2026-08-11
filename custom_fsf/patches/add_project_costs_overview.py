import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    add_project_costs_overview_fields()

def add_project_costs_overview_fields():
    custom_fields = {
        "Project": [
            {
                "fieldname": "section_costs_overview",  # NEW name to avoid conflict
                "label": "Cost Overview",
                "fieldtype": "Section Break",
                "insert_after": "project_milestones",
                "collapsible": 1
            },
            {
                "fieldname": "costs_total_invoiced",
                "label": "Total Invoiced",
                "fieldtype": "Currency",
                "read_only": 1,
                "insert_after": "section_costs_overview"
            },
            {
                "fieldname": "costs_total_paid",
                "label": "Total Paid",
                "fieldtype": "Currency",
                "read_only": 1,
                "insert_after": "costs_total_invoiced"
            },
            {
                "fieldname": "costs_outstanding_balance",
                "label": "Outstanding Balance",
                "fieldtype": "Currency",
                "read_only": 1,
                "insert_after": "costs_total_paid"
            }
        ]
    }

    create_custom_fields(custom_fields)