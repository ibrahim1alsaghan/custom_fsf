app_name = "custom_fsf"
app_title = "custom fsf"
app_publisher = "ibrahim alsaghan"
app_description = "custom changes for fsf"
app_email = "i.alsaghan@tamkeentech.sa"
app_license = "mit"

# required_apps = []
app_dependencies = ["lms"]
patches = "custom_fsf.patches.txt"

# App Logo — overrides ERPNext/Frappe logo in desk navbar and login page
app_logo_url = "/assets/custom_fsf/images/fsf.png"

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "custom-fsf",
# 		"logo": "/assets/custom-fsf/logo.png",
# 		"title": "fsf app",
# 		"route": "/custom-fsf",
# 		"has_permission": "custom-fsf.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/custom-fsf/css/custom-fsf.css"
# app_include_js = "/assets/custom-fsf/js/custom-fsf.js"

#for the desk
app_include_css = "/assets/custom_fsf/css/theme_desk_v1.css"
app_include_js = [
    "/assets/custom_fsf/js/toolbar_add_button_language.js",
    "/assets/custom_fsf/js/arabic_time_translations.js",
    "/assets/custom_fsf/js/session_expired_arabic.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/custom-fsf/css/custom-fsf.css"
# web_include_js = "/assets/custom-fsf/js/custom-fsf.js"

#for the login page
web_include_css = [
    "/assets/custom_fsf/css/theme_desk_2.css",
]
# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "custom-fsf/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "custom-fsf/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "landing"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Website Redirects
# -----------------
website_redirects = [
    {"source": "/login", "target": "/signin"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "custom-fsf.utils.jinja_methods",
# 	"filters": "custom-fsf.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "custom-fsf.install.before_install"
# after_install = "custom-fsf.install.after_install"

after_install = [
    "custom_fsf.utils.ensure_dependencies",  # Check and install missing dependencies first
    # "custom_fsf.commands.patch_lms.run_patch", ##
    "custom_fsf.patches.add_arabic_name_field.execute",
    "custom_fsf.patches.add_description_role.execute",
    "custom_fsf.patches.add_project_milestones_table.execute",
    "custom_fsf.patches.add_project_attachments_table.execute",
    "custom_fsf.patches.add_project_escalation_table.execute",
    "custom_fsf.patches.add_project_stakeholders_table.execute",
    "custom_fsf.patches.add_value_field.execute",
    "custom_fsf.patches.add_project_costs_overview.execute",
    # "custom_fsf.patches.add_fields_assets.execute",
    "custom_fsf.patches.add_assets_category_custom_fields.execute",
    "custom_fsf.patches.add_employee_asset_permission.execute",
    "custom_fsf.patches.set_audit_log_permissions.execute",
    "custom_fsf.patches.create_lessons_learned_print_formats.execute",
    "custom_fsf.patches.add_lessons_learned_list_print.execute",
    "custom_fsf.patches.update_project_recommendation_assignee.execute",
    "custom_fsf.patches.add_project_recommendation_to_project.execute",
    "custom_fsf.patches.add_client_evaluation_to_project.execute",
    "custom_fsf.patches.create_client_evaluation_print_format.execute",
    "custom_fsf.patches.drop_gender_field_user.execute",
    "custom_fsf.patches.create_hd_default_data.execute",
    "custom_fsf.patches.setup_hd_workspace.execute",
    "custom_fsf.patches.enable_scheduler.execute",
    "custom_fsf.patches.setup_app_logo.execute",
    "custom_fsf.patches.setup_workspaces.execute",
    "custom_fsf.patches.setup_module_roles.execute",
    "custom_fsf.patches.add_employee_to_users_workspace.execute",
    "custom_fsf.translations_manager.apply_translations",
]
after_migrate = [
    "custom_fsf.patches.add_app_name.add_app_name",
    "custom_fsf.patches.add_arabic_name_field.execute",
    "custom_fsf.patches.add_description_role.execute",
    "custom_fsf.patches.add_project_milestones_table.execute",
    "custom_fsf.patches.add_project_attachments_table.execute",
    "custom_fsf.patches.add_project_escalation_table.execute",
    "custom_fsf.patches.add_project_stakeholders_table.execute",
    "custom_fsf.patches.add_value_field.execute",
    "custom_fsf.patches.add_project_costs_overview.execute",
    # "custom_fsf.patches.add_fields_assets.execute",
    "custom_fsf.patches.add_assets_category_custom_fields.execute",
    "custom_fsf.patches.add_employee_asset_permission.execute",
    "custom_fsf.patches.add_contract_etimad_number.execute",
    "custom_fsf.patches.set_audit_log_permissions.execute",
    "custom_fsf.patches.create_lessons_learned_print_formats.execute",
    "custom_fsf.patches.add_lessons_learned_list_print.execute",
    "custom_fsf.patches.add_lessons_learned_in_project.execute",
    "custom_fsf.patches.update_project_recommendation_assignee.execute",
    "custom_fsf.patches.add_project_recommendation_to_project.execute",
    "custom_fsf.patches.add_client_evaluation_to_project.execute",
    "custom_fsf.patches.create_client_evaluation_print_format.execute",
    "custom_fsf.patches.drop_gender_field_user.execute",
    "custom_fsf.patches.create_hd_default_data.execute",
    "custom_fsf.patches.setup_hd_workspace.execute",
    "custom_fsf.patches.setup_app_logo.execute",
    "custom_fsf.patches.setup_workspaces.execute",
    "custom_fsf.patches.set_session_timeout_arabic.execute",
    "custom_fsf.patches.add_arabic_notification_translations.execute",
    "custom_fsf.patches.fix_existing_english_notifications.execute",
    "custom_fsf.patches.remove_hd_dashboard_shortcut.execute",
    "custom_fsf.patches.setup_module_roles.execute",
    "custom_fsf.patches.add_employee_to_users_workspace.execute",
    "custom_fsf.translations_manager.apply_translations",
]

# Uninstallation
# ------------

# before_uninstall = "custom-fsf.uninstall.before_uninstall"
# after_uninstall = "custom-fsf.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "custom-fsf.utils.before_app_install"
# after_app_install = "custom-fsf.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "custom-fsf.utils.before_app_uninstall"
# after_app_uninstall = "custom-fsf.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "custom-fsf.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
permission_query_conditions = {
    "Library": "custom_fsf.custom_fsf.doctype.library.library.library_permission_query",
    "Asset": "custom_fsf.scripts.assets.get_permission_query_conditions",
    "HD Ticket": "custom_fsf.hd.doctype.hd_ticket.hd_ticket.hd_ticket_permission_query",
    "Task": "custom_fsf.scripts.tasks.get_permission_query_conditions"
}

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }
has_permission = {
    "Library": "custom_fsf.custom_fsf.doctype.library.library.library_has_permission",
    "Asset": "custom_fsf.scripts.assets.has_permission",
    "HD Ticket": "custom_fsf.hd.doctype.hd_ticket.hd_ticket.hd_ticket_has_permission",
    "Task": "custom_fsf.scripts.tasks.has_permission",
    # Enforces the Number Card `roles` table (Frappe's own hook ignores it),
    # so role-gated cards like the Asset dashboard totals stay manager-only.
    "Number Card": "custom_fsf.overrides.number_card.has_permission",
}


# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    # Block dangerous file extensions (.php, .html, .svg, ...) by real filename,
    # closing the mimetype-based bypass in Frappe's built-in check. See H-002.
    "File": "custom_fsf.overrides.file_upload.CustomFile",
}

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
### this is for create new password after create new user " check for apps/sprint2_pages/sprint2_pages/utils.py " ###
doc_events = {
    "Notification Log": {
        "before_insert": "custom_fsf.overrides.notification_log.translate_subject",
    },
    "User": {
        "after_insert": "custom_fsf.utils.after_insert_user",
        "validate": "custom_fsf.utils.validate_user",
    },
    "Task": {
        "on_update": "custom_fsf.scripts.tasks.send_notification_on_task_status_change",
        "before_save": "custom_fsf.scripts.tasks.disable_changes"
    },
    "Project": {
        "on_update": "custom_fsf.utils.update_project_costs_summary",
        "after_insert": "custom_fsf.utils.update_project_costs_summary",
        "before_save": "custom_fsf.utils.validate_contract_etimad"
    },
    "Sales Invoice": {
        "before_submit": "custom_fsf.scripts.assets.validate_asset_sale"
    },
    "Asset Movement": {
        "validate": "custom_fsf.scripts.assets.validate_asset_movement"
    },
    "Asset": {
        "before_insert": "custom_fsf.scripts.assets.set_existing_asset_on_import",
        "before_validate": [
            # Column-aware bilingual errors for Data Import rows; must run
            # before ERPNext's validate_item ("Item None does not exist").
            "custom_fsf.scripts.assets.validate_import_row",
            "custom_fsf.scripts.asset_category_field_values.before_validate",
        ],
        "validate": "custom_fsf.scripts.asset_category_field_values.validate",
        "on_submit": "custom_fsf.utils.notify_new_custodian_on_submit",
        "on_update_after_submit": "custom_fsf.utils.notify_new_custodian_on_submit"
    },
    "Asset Category": {
        "before_save": "custom_fsf.scripts.asset_category_custom_fields.before_save",
        "on_update": "custom_fsf.scripts.asset_category_custom_fields.on_update",
        "on_trash": "custom_fsf.scripts.asset_category_custom_fields.on_trash",
    },
    "Data Import": {
        "validate": "custom_fsf.scripts.asset_category_field_values.ensure_asset_fields_for_data_import",
    },
    "Comment": {
        "before_save": "custom_fsf.overrides.comment.sanitize_comment_html",
        "before_insert": "custom_fsf.hd.doctype.hd_ticket.hd_ticket.validate_hd_ticket_comment",
        "after_insert": [
            "custom_fsf.hd.doctype.hd_ticket.hd_ticket.notify_requester_on_comment",
            "custom_fsf.hd.doctype.hd_ticket.hd_ticket.auto_progress_on_requester_comment",
        ],
    },
     "*": {
        "after_insert": "custom_fsf.custom_fsf.doctype.audit_log.audit_log.log_create",
        "on_update": "custom_fsf.custom_fsf.doctype.audit_log.audit_log.log_update",
        "on_trash": "custom_fsf.custom_fsf.doctype.audit_log.audit_log.log_delete",
    }
}

doctype_js = {
    "Project": "public/js/project.js",
    "Asset": "public/js/asset_extension.js",
    "Asset Category": "public/js/asset_category_extension.js",
    "Item": "public/js/item_extension.js",
    "Role": "public/js/role_fix_show_users.js",
}

doctype_list_js = {
    "Asset": "public/js/asset_list.js",
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "hourly": [
        "custom_fsf.scripts.tasks.send_task_due_reminders",
        "custom_fsf.utils.update_project_costs_summary",
        "custom_fsf.hd.doctype.hd_ticket.hd_ticket.auto_close_resolved_tickets",
        "custom_fsf.hd.doctype.hd_ticket.hd_ticket.check_and_notify_overdue_tickets",
    ],
    "daily": [
        "custom_fsf.hd.doctype.hd_team_member.hd_team_member.deactivate_expired_team_members",
        "custom_fsf.api.security_alert.fetch_nca_alerts",
    ],
    "monthly": [
        "custom_fsf.scripts.monthly_log_reminder.send_log_retention_reminder"
    ]
}
# scheduler_events = {
# 	"all": [
# 		"custom-fsf.tasks.all"
# 	],
# 	"daily": [
# 		"custom-fsf.tasks.daily"
# 	],
# 	"hourly": [
# 		"custom-fsf.tasks.hourly"
# 	],
# 	"weekly": [
# 		"custom-fsf.tasks.weekly"
# 	],
# 	"monthly": [
# 		"custom-fsf.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "custom-fsf.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "custom-fsf.event.get_events"
# }
#
override_whitelisted_methods = {
    "erpnext.assets.doctype.asset.depreciation.scrap_asset": "custom_fsf.overrides.assets.scrap_asset",
    "frappe.core.doctype.user.user.get_role_profile": "custom_fsf.overrides.user.get_role_profile",
    "frappe.desk.doctype.dashboard_chart.dashboard_chart.get": "custom_fsf.overrides.dashboard_chart.get",
    # Hides Dashboard-type workspace shortcuts (e.g. the Asset dashboard)
    # from users who can't see any of the dashboard's charts/cards.
    "frappe.desk.desktop.get_desktop_page": "custom_fsf.overrides.desktop.get_desktop_page",
    # Export failed Data Import rows in the same format as the upload
    # (xlsx → xlsx) instead of always CSV.
    "frappe.core.doctype.data_import.data_import.download_errored_template": "custom_fsf.overrides.data_import.download_errored_template",

        # Validate request-controlled order_by and group_by parameters.
    "frappe.desk.reportview.get": (
        "custom_fsf.overrides.reportview.get"
    ),
    "frappe.desk.reportview.get_list": (
        "custom_fsf.overrides.reportview.get_list"
    ),
    "frappe.desk.reportview.get_count": (
        "custom_fsf.overrides.reportview.get_count"
    ),

}


# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "custom-fsf.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["custom-fsf.utils.before_request"]
# after_request = ["custom-fsf.utils.after_request"]

# Job Events
# ----------
# before_job = ["custom-fsf.utils.before_job"]
# after_job = ["custom-fsf.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"custom-fsf.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
