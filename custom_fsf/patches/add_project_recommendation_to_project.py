import frappe

def execute():
    """Add Project Recommendation link to Project DocType"""
    
    # Get the Project DocType
    project_doctype = frappe.get_doc("DocType", "Project")
    
    # Check if the link already exists
    existing_link = None
    for link in project_doctype.links:
        if link.link_doctype == "Project Recommendation":
            existing_link = link
            break
    
    if not existing_link:
        # Add the link
        project_doctype.append("links", {
            "link_doctype": "Project Recommendation",
            "link_fieldname": "project"
        })
        
        # Save the changes
        project_doctype.save()
        frappe.db.commit()
        
        print("Added Project Recommendation link to Project DocType")
    else:
        print("Project Recommendation link already exists in Project DocType")
