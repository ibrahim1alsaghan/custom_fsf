import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    """Remove/hide the gender field on User."""
    custom_field_name = "User-gender"

    # Remove any custom field named gender on User
    if frappe.db.exists("Custom Field", custom_field_name):
        frappe.delete_doc("Custom Field", custom_field_name)

    # Hide and make non-required the core gender field if it exists
    if frappe.db.has_column("User", "gender"):
        make_property_setter("User", "gender", "hidden", 1, "Check")
        make_property_setter("User", "gender", "reqd", 0, "Check")

