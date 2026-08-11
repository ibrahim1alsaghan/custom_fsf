import frappe

def execute():
    """Add Client Evaluation Form link to Project DocType"""
    
    # Get the Project DocType
    project_doctype = frappe.get_doc("DocType", "Project")
    
    # Check if the link already exists
    existing_link = None
    for link in project_doctype.links:
        if link.link_doctype == "Client Evaluation Form":
            existing_link = link
            break
    
    if not existing_link:
        # Add the link
        project_doctype.append("links", {
            "link_doctype": "Client Evaluation Form",
            "link_fieldname": "project"
        })
        
        # Save the changes
        project_doctype.save()
        frappe.db.commit()
        
        print("Added Client Evaluation Form link to Project DocType")
    else:
        print("Client Evaluation Form link already exists in Project DocType")
