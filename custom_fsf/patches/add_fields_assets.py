# import frappe
# from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# def execute():
#     valid_categories = ["Server", "Printer", "API / URL", "Application", "PC", "Switch", "Router", "URL"]
#     condition = f'eval:{valid_categories} .includes(doc.asset_category)'
#     server_only = 'eval:doc.asset_category === "Server"'
#     printer_only = 'eval:doc.asset_category === "Printer"'
#     pc_only = 'eval:doc.asset_category === "PC"'
#     api_only = 'eval:doc.asset_category === "API / URL"'
#     app_only = 'eval:doc.asset_category === "Application"'
#     switch_only = 'eval:doc.asset_category === "Switch"'
#     router_only = 'eval:doc.asset_category === "Router"'

#     custom_fields = {
#         "Asset": [
#             {
#                 "fieldname": "section_asset_details",
#                 "label": "Asset Details",
#                 "fieldtype": "Section Break",
#                 "insert_after": "disposal_date",
#                 "collapsible": 1
#             },
#             {
#                 "fieldname": "asset_description",
#                 "label": "Description",
#                 "fieldtype": "Small Text",
#                 "insert_after": "section_asset_details",
#                 "depends_on": condition,
#                 "mandatory_depends_on": condition
#             },
#             {
#                 "fieldname": "model",
#                 "label": "Model",
#                 "fieldtype": "Data",
#                 "insert_after": "asset_description",
#                 "depends_on": condition,
#                 "mandatory_depends_on": condition
#             },
#             {
#                 "fieldname": "version",
#                 "label": "Version",
#                 "fieldtype": "Data",
#                 "insert_after": "model",
#                 "depends_on": condition,
#                 "mandatory_depends_on": condition
#             },
#             {
#                 "fieldname": "serial_number",
#                 "label": "Serial Number",
#                 "fieldtype": "Data",
#                 "insert_after": "version",
#                 "depends_on": condition,
#                 "mandatory_depends_on": condition
#             },
#             {
#                 "fieldname": "mac_address",
#                 "label": "MAC Address",
#                 "fieldtype": "Data",
#                 "insert_after": "serial_number",
#                 "depends_on": condition,
#                 "mandatory_depends_on": condition
#             },
#             {
#                 "fieldname": "ip_address",
#                 "label": "IP Address",
#                 "fieldtype": "Data",
#                 "insert_after": "mac_address",
#                 "depends_on": 'eval:["Server", "Router", "PC"].includes(doc.asset_category)',
#                 "mandatory_depends_on": 'eval:["Server", "Router", "PC"].includes(doc.asset_category)'
#             },
#             {
#                 "fieldname": "os",
#                 "label": "OS",
#                 "fieldtype": "Data",
#                 "insert_after": "ip_address",
#                 "depends_on": 'eval:["Server", "PC"].includes(doc.asset_category)',
#                 "mandatory_depends_on": 'eval:["Server", "PC"].includes(doc.asset_category)'
#             },
#             {
#                 "fieldname": "ram",
#                 "label": "RAM",
#                 "fieldtype": "Data",
#                 "insert_after": "os",
#                 "depends_on": 'eval:["Server", "PC"].includes(doc.asset_category)',
#                 "mandatory_depends_on": 'eval:["Server", "PC"].includes(doc.asset_category)'
#             },
#             {
#                 "fieldname": "cpu",
#                 "label": "CPU",
#                 "fieldtype": "Data",
#                 "insert_after": "ram",
#                 "depends_on": 'eval:["Server", "PC"].includes(doc.asset_category)',
#                 "mandatory_depends_on": 'eval:["Server", "PC"].includes(doc.asset_category)'
#             },
#             {
#                 "fieldname": "disk_space",
#                 "label": "Disk Space",
#                 "fieldtype": "Data",
#                 "insert_after": "cpu",
#                 "depends_on": server_only,
#                 "mandatory_depends_on": server_only
#             },
#             {
#                 "fieldname": "printer_type",
#                 "label": "Printer Type",
#                 "fieldtype": "Data",
#                 "insert_after": "disk_space",
#                 "depends_on": printer_only,
#                 "mandatory_depends_on": printer_only
#             },
#             {
#                 "fieldname": "toner_model",
#                 "label": "Toner Model",
#                 "fieldtype": "Data",
#                 "insert_after": "printer_type",
#                 "depends_on": printer_only,
#                 "mandatory_depends_on": printer_only
#             },
#             {
#                 "fieldname": "endpoint_url",
#                 "label": "Endpoint URL",
#                 "fieldtype": "Data",
#                 "insert_after": "toner_model",
#                 "depends_on": api_only,
#                 "mandatory_depends_on": api_only
#             },
#             {
#                 "fieldname": "auth_type",
#                 "label": "Auth Type",
#                 "fieldtype": "Data",
#                 "insert_after": "endpoint_url",
#                 "depends_on": api_only
#             },
#             {
#                 "fieldname": "api_owner",
#                 "label": "Owner",
#                 "fieldtype": "Link",
#                 "options": "User",
#                 "insert_after": "auth_type",
#                 "depends_on": api_only
#             },
#             {
#                 "fieldname": "license_key",
#                 "label": "License Key",
#                 "fieldtype": "Data",
#                 "insert_after": "api_owner",
#                 "depends_on": app_only,
#                 "mandatory_depends_on": app_only
#             },
#             {
#                 "fieldname": "hdd",
#                 "label": "HDD",
#                 "fieldtype": "Data",
#                 "insert_after": "license_key",
#                 "depends_on": pc_only,
#                 "mandatory_depends_on": pc_only
#             },
#             {
#                 "fieldname": "domain_joined",
#                 "label": "Domain Joined",
#                 "fieldtype": "Check",
#                 "insert_after": "hdd",
#                 "depends_on": pc_only
#             },
#             {
#                 "fieldname": "ports",
#                 "label": "Number of Ports",
#                 "fieldtype": "Int",
#                 "insert_after": "domain_joined",
#                 "depends_on": switch_only,
#                 "mandatory_depends_on": switch_only
#             },
#             {
#                 "fieldname": "firmware",
#                 "label": "Firmware",
#                 "fieldtype": "Data",
#                 "insert_after": "ports",
#                 "depends_on": switch_only
#             },
#             {
#                 "fieldname": "ip_range",
#                 "label": "IP Range",
#                 "fieldtype": "Data",
#                 "insert_after": "firmware",
#                 "depends_on": router_only,
#                 "mandatory_depends_on": router_only
#             },
#             {
#                 "fieldname": "admin_credentials",
#                 "label": "Admin Credentials",
#                 "fieldtype": "Data",
#                 "insert_after": "ip_range",
#                 "depends_on": router_only
#             }
#         ]
#     }

#     create_custom_fields(custom_fields)