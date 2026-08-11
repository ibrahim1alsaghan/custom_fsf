import frappe
from frappe import _
import json
from datetime import datetime, timedelta


def get_permission_query_conditions(user):
    """
    Permission query to filter tasks:
    - Administrator and Projects Manager see all tasks
    - Any other user (Projects User, Employee, etc.) sees tasks they own,
      are assigned to via `_assign`, or that target their department
    """
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return ""

    roles = frappe.get_roles(user)

    if "Projects Manager" in roles:
        return ""

    conditions = []

    # User can see tasks they own
    conditions.append(f'`tabTask`.owner = {frappe.db.escape(user)}')

    # User can see tasks assigned to them (via _assign JSON field)
    conditions.append(f'`tabTask`._assign LIKE {frappe.db.escape(f"%{user}%")}')

    # Department-based access via the linked Employee record
    try:
        employee = frappe.db.get_value("Employee", {"user_id": user}, ["department", "name"], as_dict=True)

        if employee and employee.department:
            conditions.append(
                f'`tabTask`.department = {frappe.db.escape(employee.department)}'
            )
            if frappe.db.has_column("Task", "assigned_department"):
                conditions.append(
                    f'`tabTask`.assigned_department = {frappe.db.escape(employee.department)}'
                )
    except Exception as e:
        frappe.log_error(f"Task permission query error for user {user}: {str(e)}", "Task Permission Error")

    return "(" + " OR ".join(conditions) + ")"


def has_permission(doc, ptype, user):
    """
    Check if user has permission to access the task:
    - Administrator and Projects Manager always pass
    - Anyone else passes for tasks they own, are assigned to via `_assign`,
      or that target their department
    """
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return True

    roles = frappe.get_roles(user)

    if "Projects Manager" in roles:
        return True

    if doc.owner == user:
        return True

    if doc._assign:
        try:
            assigned_users = json.loads(doc._assign) if isinstance(doc._assign, str) else doc._assign
            if user in assigned_users:
                return True
        except Exception:
            pass

    try:
        employee = frappe.db.get_value("Employee", {"user_id": user}, ["department"], as_dict=True)

        if employee and employee.department:
            if doc.get("department") == employee.department:
                return True
            if doc.get("assigned_department") == employee.department:
                return True
    except Exception as e:
        frappe.log_error(f"Task has_permission error for user {user}: {str(e)}", "Task Permission Error")

    return False

def send_notification_on_task_status_change(doc, method):
    # Only proceed if status has actually changed
        # 🚫 Skip if this is a new Task (on insert)
    if doc.status == "Open":
        return
    if not doc.has_value_changed('status'):
        return

    recipients = set()  # Use set to automatically handle duplicates

    # Add the task owner as recipient
    if doc.owner:
        recipients.add(doc.owner)

    # Add the assigned users as recipients
    if hasattr(doc, '_assign') and doc._assign:
        try:
            assigned_users = json.loads(doc._assign) if isinstance(doc._assign, str) else doc._assign
            for user_email in assigned_users:
                if user_email:  # Skip empty strings
                    recipients.add(user_email)
        except:
            pass

    # Convert to list and filter out None/empty values
    recipients = list(filter(None, recipients))

    if not recipients:
        return

    # Debug print to see unique recipients
    print(f"Unique recipients: {recipients}")

    # Create notifications for each unique recipient
    for recipient in recipients:
        try:
            notification = frappe.new_doc("Notification Log")
            notification.for_user = recipient
            notification.from_user = frappe.session.user
            notification.subject = f"Task {doc.subject} Status Updated to {doc.status}"
            notification.email_content = f'The status of Task {doc.name} {doc.subject} has been updated to {doc.status}.'
            notification.document_type = "Task"
            notification.document_name = doc.name
            notification.type = "Alert"
            notification.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Notification created for {recipient}")
        except Exception as e:
            frappe.log_error(str(e), "Task Notification Assignment Parsing Error")



def send_task_due_reminders():
    """Send reminders for tasks due today or tomorrow."""
    today = frappe.utils.today()
    tomorrow = frappe.utils.add_days(today, 1)

    # Fetch upcoming tasks
    tasks = frappe.get_all(
        "Task",
        filters=[
            ["exp_end_date", "in", [today, tomorrow]],
            ["status", "not in", ["Completed", "Cancelled", "Closed"]]
        ],
        fields=["name", "subject", "exp_end_date", "owner", "_assign"]
    )
    for task in tasks:
        recipients = set()

        # Add task owner
        if task.owner:
            recipients.add(task.owner)

        # Add assigned users
        if task._assign:
            try:
                assigned_users = json.loads(task._assign) if isinstance(task._assign, str) else task._assign
                recipients.update(filter(None, assigned_users))
            except Exception as e:
                frappe.log_error(str(e), "Reminder Assignment Parse Error")

        recipients = list(filter(None, recipients))

        if not recipients:
            continue


        for recipient in recipients:
            try:
                # Create in-app notification
                notification = frappe.new_doc("Notification Log")
                notification.for_user = recipient
                notification.from_user = "Administrator"  # Fixed user for scheduler
                notification.subject = _("Reminder due date : {0}").format(task.subject)
                notification.email_content = _("The status of Task {0} {1} due date in {2}.").format(task.name, task.subject, task.exp_end_date)
                notification.document_type = "Task"
                notification.document_name = task.name
                notification.type = "Alert"
                notification.insert(ignore_permissions=True)

            except Exception as e:
                frappe.log_error(str(e), "Task Reminder Notification Error")

    frappe.db.commit()

def disable_changes(doc, method):
    old_status = frappe.db.get_value(doc.doctype, doc.name, "status")

    if old_status in ["Completed", "Cancelled"] and frappe.session.user != "Administrator":
        frappe.publish_realtime(
            event='msgprint',
            message="Completed and Cancelled Tasks cannot be changed",
            user="Administrator"
        )
        # Prevent further changes to the document by raising an exception
        frappe.throw("You cannot modify a task that is 'Completed' or 'Cancelled'")
    else :
        return


@frappe.whitelist()
def debug_task_permissions(user=None):
    """Debug function to check task permission setup for a user.
    Call from console: frappe.call('custom_fsf.scripts.tasks.debug_task_permissions')
    """
    if not user:
        user = frappe.session.user

    result = {
        "user": user,
        "roles": frappe.get_roles(user),
        "employee": None,
        "department": None,
        "has_assigned_department_column": frappe.db.has_column("Task", "assigned_department"),
        "tasks_visible": []
    }

    # Check employee record
    employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "department", "employee_name"], as_dict=True)
    if employee:
        result["employee"] = employee.name
        result["department"] = employee.department

    # Check what tasks user can see
    if employee and employee.department:
        dept_tasks = frappe.db.sql("""
            SELECT name, subject, department, owner, _assign
            FROM `tabTask`
            WHERE department = %s
            LIMIT 5
        """, employee.department, as_dict=True)
        result["tasks_in_department"] = dept_tasks

    return result
