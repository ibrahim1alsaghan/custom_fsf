import frappe

def add_app_name():
    frappe.db.set_value('System Settings', None, 'app_name', 'Facilities Security Forces')