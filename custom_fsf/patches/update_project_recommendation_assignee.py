import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Update Project Recommendation assignee field to filter by Project Manager role"""
    
    # Get the DocType
    doctype = frappe.get_doc("DocType", "Project Recommendation")
    
    # Find the assignee field and update it
    for field in doctype.fields:
        if field.fieldname == "assignee":
            field.get_query = "custom_fsf.utils.get_project_managers"
            break
    
    # Save the changes
    doctype.save()
    frappe.db.commit()
    
    print("Updated Project Recommendation assignee field to filter by Project Manager role")
