import frappe

def get_permission_query_conditions(user):
    """Return permission query conditions for Audit Viewer role"""
    if not user:
        user = frappe.session.user
    
    if "Audit Viewer" in frappe.get_roles(user):
        return ""
    
    return ""

def has_permission(doc, ptype, user):
    """Check if user has permission for Audit Log"""
    if not user:
        user = frappe.session.user
    
    if "Audit Viewer" in frappe.get_roles(user):
        if ptype in ["read", "export", "print", "report"]:
            return True
        return False
    
    return True
