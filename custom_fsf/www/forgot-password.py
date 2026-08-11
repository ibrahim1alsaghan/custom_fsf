import frappe

no_cache = True

def get_context(context):
    # Redirect if already logged in
    if frappe.session.user != "Guest":
        frappe.local.flags.redirect_location = "/app"
        raise frappe.Redirect
    
    context.no_cache = 1
    context.no_header = True
    context.no_footer = True
    
    return context


