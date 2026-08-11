import frappe
import random
import string
from frappe.utils.password import update_password as set_user_password
from frappe.utils import get_fullname
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
import re
from frappe import _

def generate_strong_password(length=12):
    characters = string.ascii_letters + string.digits + '@#$!%*?&'
    while True:
        password = ''.join(random.choice(characters) for _ in range(length))
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in '@#$!%*?&' for c in password)):
            return password

def after_insert_user(doc, method):
    # Make sure the user document is committed to the database
    frappe.db.commit()
    
    # Generate a strong password
    random_password = generate_strong_password()
    
    try:
        # Use the correct import path for update_password
        # This directly updates the password hash in the database
        set_user_password(doc.name, random_password)
        
        # Make sure user is enabled and active
        frappe.db.set_value("User", doc.name, "enabled", 1)
        
        # Clear any reset password key
        frappe.db.set_value("User", doc.name, "reset_password_key", "")
        
        # Commit the changes
        frappe.db.commit()
        
        # Store the password temporarily for testing (remove in production)
        print(f"SUCCESS: Generated password for {doc.email}: {random_password}")
        
        # For testing, also save the password in a doctype you can access
        # save_password_for_testing(doc.name, doc.email, random_password)
        
    except Exception as e:
        print(f"ERROR setting password for {doc.email}: {str(e)}")
        frappe.log_error(f"Failed to set password for {doc.email}: {str(e)}", 
                         "User Password Setting Error")

# def save_password_for_testing(username, email, password):
#     """Save password in a doctype for testing purposes"""
#     try:
#         # Create a temporary record to store the password
#         temp_doc = frappe.get_doc({
#             "doctype": "Note",
#             "title": f"TEMP PASSWORD - {email}",
#             "content": f"""
# USERNAME: {username}
# EMAIL: {email}
# PASSWORD: {password}

# DELETE THIS NOTE AFTER TESTING!
# Created: {frappe.utils.now_datetime()}
#             """,
#             "public": 1  # Make it public for easy access
#         })
#         temp_doc.insert(ignore_permissions=True)
#         frappe.db.commit()
        
#         print(f"Password saved in Note: {temp_doc.name}")
#     except Exception as e:
#         print(f"Error saving test password: {str(e)}")

@frappe.whitelist()
def update_project_costs_summary(doc, method):
    # Total Invoiced → from Purchase Invoices
    total_invoiced = frappe.db.sql("""
        SELECT SUM(grand_total)
        FROM `tabPurchase Invoice`
        WHERE project = %s AND docstatus = 1
    """, (doc.name,))[0][0] or 0

    # Total Paid → from Payment Entry Reference, use allocated_amount not paid_amount
    total_paid = frappe.db.sql("""
        SELECT SUM(per.allocated_amount)
        FROM `tabPayment Entry Reference` per
        JOIN `tabPurchase Invoice` pi ON per.reference_name = pi.name
        WHERE per.reference_doctype = 'Purchase Invoice'
        AND per.docstatus = 1
        AND pi.project = %s
    """, (doc.name,))[0][0] or 0

    total_outstanding = total_invoiced - total_paid

    doc.costs_total_invoiced = total_invoiced
    doc.costs_total_paid = total_paid
    doc.costs_outstanding_balance = total_outstanding


@frappe.whitelist()
def get_project_cost_summary(project):
    # Do raw calculations right here
    total_invoiced = frappe.db.sql("""
        SELECT SUM(grand_total)
        FROM `tabPurchase Invoice`
        WHERE project = %s AND docstatus = 1
    """, (project,))[0][0] or 0

    total_paid = frappe.db.sql("""
        SELECT SUM(per.allocated_amount)
        FROM `tabPayment Entry Reference` per
        JOIN `tabPurchase Invoice` pi ON per.reference_name = pi.name
        WHERE per.reference_doctype = 'Purchase Invoice'
        AND per.docstatus = 1
        AND pi.project = %s
    """, (project,))[0][0] or 0

    total_outstanding = total_invoiced - total_paid

    return {
        "value": frappe.db.get_value("Project", project, "project_value") or 0,
        "invoiced": total_invoiced,
        "paid": total_paid,
        "outstanding": total_outstanding
    }


def notify_new_custodian_on_submit(doc, method):
    # Skip during bulk Data Import: sending a custodian notification for every
    # imported asset adds a DB lookup + Notification Log write per row (the
    # cost that makes large imports time out) and floods custodians with
    # hundreds of alerts they didn't trigger.
    if frappe.flags.in_import:
        return

    if not doc.custodian:
        return

    user_id = frappe.db.get_value("Employee", doc.custodian, "user_id")
    if not user_id:
        return

    asset_name = doc.asset_name or doc.name
    subject = _("You've been assigned as custodian for asset '{0}'").format(asset_name)

    notification = frappe._dict({
        "subject": subject,
        "from_user": frappe.session.user if frappe.session.user else "Administrator",
        "type": "Alert",
        "document_type": doc.doctype,
        "document_name": doc.name
    })

    make_notification_logs(notification, [user_id])


_ALNUM_50 = re.compile(r"^[A-Za-z0-9]{1,50}$")

def valid_alphanumeric(v: str) -> bool:
    if not v:            # field optional -> allow empty
        return True
    v = v.strip()
    return bool(_ALNUM_50.fullmatch(v))

def validate_contract_etimad(doc, method=None):
    for field, label in (("contract_number", _("Contract Number")),
                         ("etimad_number",   _("Etimad Number"))):
        v = (doc.get(field) or "").strip()
        if not valid_alphanumeric(v):
            frappe.throw(
                _("{0} must be alphanumeric (A–Z, a–z, 0–9).")
                .format(label),
                title=_("Invalid {0}").format(label)
            )

@frappe.whitelist()
def get_project_managers():
    """Get users with Project Manager role for assignee field"""
    users = frappe.get_all(
        "Has Role",
        filters={"role": "Projects Manager", "parenttype": "User"},
        pluck="parent",
    )
    return {"filters": [["User", "name", "in", users]]}


SAUDI_MOBILE_REGEX = re.compile(r"^(05\d{8}|9665\d{8})$")

def _validate_mobile(value: str, label: str, errors: list) -> str:
    """Validate Saudi mobile number: 05XXXXXXXX or 9665XXXXXXXX"""
    if not value:
        return value
    value = value.strip()
    # Normalize 05 → 9665
    if value.startswith("05"):
        value = "966" + value[1:]
    if not SAUDI_MOBILE_REGEX.match(value):
        errors.append(_("Invalid {0}. Use 05XXXXXXXX or 9665XXXXXXXX").format(_(label)))
    return value

def validate_user(doc, method=None):
    errors = []
    doc.mobile_no = _validate_mobile(doc.mobile_no, "Mobile No", errors)
    doc.phone = _validate_mobile(doc.phone, "Phone", errors)
    if errors:
        frappe.throw("<br>".join(errors))

@frappe.whitelist()
def get_users_with_role(role: str, enabled_only: int = 1):
	"""
	Return list of User IDs that have a given role. (enabled only)
	"""
	if not role:
		return []

	#only for people who can read users list for security purposes
	if not frappe.has_permission("User", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	enabled_only = 1 if str(enabled_only) in ("1", "true", "True") else 0

	#use the 'tabHas Role' child table for User.roles
	users = frappe.db.sql_list(
		"""
		select distinct u.name
		from `tabUser` u
		inner join `tabHas Role` hr
			on hr.parent = u.name
			and hr.parenttype = 'User'
			and hr.parentfield = 'roles'
		where hr.role = %(role)s
		  and (%(enabled_only)s = 0 or u.enabled = 1)
		order by u.name
		""",
		{"role": role, "enabled_only": enabled_only},
	)

	return users


def ensure_dependencies():
    """Check and install missing dependencies after app install."""
    import subprocess
    import os
    
    bench_path = frappe.utils.get_bench_path()
    requirements_file = os.path.join(bench_path, "apps", "custom_fsf", "requirements.txt")
    
    if os.path.exists(requirements_file):
        pip_path = os.path.join(bench_path, "env", "bin", "pip")
        try:
            subprocess.check_call([pip_path, "install", "-r", requirements_file, "--quiet"])
            print("custom_fsf: Dependencies installed successfully")
        except Exception as e:
            print(f"custom_fsf: Warning - Could not install dependencies: {e}")
    else:
        print("custom_fsf: No requirements.txt found, skipping dependency check")
