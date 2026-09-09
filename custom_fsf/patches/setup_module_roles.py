"""Create module-specific roles (Asset Manager) and grant Custom DocPerm
rows so each business role works standalone — without users needing to
layer cross-module standard roles (Accounts User, Stock Manager, HR User,
etc.) just to make Link fields and permission queries resolve.

Asset visibility for non-managers rides on the plain "Employee" role:
every employee sees only the assets where they are custodian, plus their
direct reports' assets (Employee.reports_to). The old "Asset User" role is
disposed of by this patch.

Because Custom DocPerm rows replace a doctype's standard permissions rather
than adding to them, the patch also preserves/restores those standard rows and
gives System Manager full rights across the app — see "Admin coverage" below.

Idempotent: safe to re-run on every migrate.
"""

import frappe
from frappe.permissions import setup_custom_perms


ASSET_ROLES = [
    {
        "role_name": "Asset Manager",
        "description": "Full management of Assets, Asset Categories, and Asset Movements",
    },
]


FULL = {
    "read": 1, "write": 1, "create": 1, "delete": 1,
    "submit": 1, "cancel": 1, "amend": 1,
    "export": 1, "print": 1, "report": 1, "share": 1,
}
WRITE = {"read": 1, "write": 1, "create": 1, "export": 1, "print": 1, "report": 1}
READ = {"read": 1, "export": 1, "print": 1, "report": 1}


# Each grant: role -> [(doctype, perms), ...].
# Adding/removing pairs here is the single source of truth for module-role
# coverage. The patch only inserts rows that don't already exist.
ASSET_GRANTS = {
    "Asset Manager": [
        ("Asset", FULL),
        ("Asset Movement", FULL),
        ("Asset Category", FULL),
        ("Asset Repair", FULL),
        ("Asset Value Adjustment", FULL),
        # Stock + accounting dependencies for creating an Asset:
        # - Item / Item Group: Asset.item_code link, and creating new fixed-asset items
        # - Location: Asset.location link
        # - Cost Center: Asset.cost_center link
        # - Department: Asset.department link + Assets workspace department chart
        # - User: any link to User (audit fields, dashboard widgets)
        ("Item", WRITE),
        ("Item Group", WRITE),
        ("Location", WRITE),
        ("Cost Center", READ),
        ("Department", READ),
        ("User", READ),
        # Asset.custodian and Asset Movement.to_employee are Links to
        # Employee — without read, the custodian dropdown returns nothing,
        # so assets can't be assigned or reassigned.
        ("Employee", READ),
    ],
    # Custodians and department managers (via Employee.reports_to) only get
    # the Asset list, row-filtered by scripts/assets.py. No Item, Asset
    # Category, Asset Movement, or dashboard access.
    "Employee": [
        ("Asset", READ),
    ],
}

HD_GRANTS = {
    "HD Manager": [("User", READ), ("Department", READ), ("Comment", WRITE)],
    "HD Agent": [("User", READ), ("Department", READ), ("Comment", WRITE)],
}

# Custom DocPerms on Employee (Projects roles below) REPLACE the standard
# DocType permissions entirely — wiping out the read/write that ERPNext
# ships for HR Manager, and leaving System Manager with no Employee perm at
# all. Re-grant both so they work standalone.
HR_GRANTS = {
    "HR Manager": [("Employee", WRITE), ("Department", WRITE)],
    "System Manager": [("Employee", WRITE)],
}

PROJECTS_GRANTS = {
    "Projects Manager": [("User", READ), ("Department", READ), ("Employee", READ)],
    "Projects User": [("User", READ), ("Employee", READ), ("Department", READ)],
    # Plain Employees (without Projects User) need read on Task so they can
    # see tasks they own / are assigned to / target their department.
    # The permission_query in scripts/tasks.py applies the row-level filter.
    "Employee": [("Task", READ), ("User", READ)],
}


# Every System User needs User read to view their own profile (/app/user/<email>).
# Frappe gates the profile page on User read perm even when viewing yourself.
# Without this, clicking your own avatar → My Profile returns 403.
USER_PROFILE_GRANTS = {
    "Document Manger": [("User", READ)],
    "Document Viewer": [("User", READ)],
    "Audit Viewer": [("User", READ)],
}


# Workspace sidebar visibility. The workspace JSONs ship with `roles: []`
# meaning "open to all" — but someone has set role restrictions through the
# desk UI that persist in `Has Role` rows on the workspace. This grants the
# module roles the corresponding workspace shortcut so users can discover
# their section in the sidebar (otherwise they'd need the direct URL).
WORKSPACE_GRANTS = {
    "Assets": ["Asset Manager", "Employee"],
    "Document Library": ["Document Manger", "Document Viewer", "Employee"],
    # LMS desk workspace contains "Create Course / LMS Settings / Setup Home
    # Page / Signups+Enrollments charts" — admin content. Restrict it to LMS
    # admins. Pure students still consume LMS via the public /lms/courses
    # portal; they don't need (or want) the desk workspace.
    "LMS": ["Course Creator", "Moderator", "System Manager"],
}


# Standard ERPNext reports that ship gated on Accounts User / Stock Manager etc.
# Mirror the docperm grants so module-role users can run them without stacking
# cross-module roles. (parenttype="Report" stores role grants in `Has Role`.)
REPORT_GRANTS = {
    "Fixed Asset Register": ["Asset Manager"],
    "Project Summary": ["Projects Manager"],
}


# Dashboard chart visibility. Charts currently with empty roles[] are
# wide-open — anyone with read on the underlying doctype sees them. Gate
# them at the chart level to match the module-role model so a user who
# shouldn't see Asset analytics doesn't get them in their dashboard.
CHART_GRANTS = {
    "Action Logged": ["Audit Viewer", "System Manager"],
    "Assets": ["Asset Manager"],
    "Assets Custodian": ["Asset Manager"],
    "Assets Distribution": ["Asset Manager"],
    "Assets Status": ["Asset Manager"],
    "Asset Value Analytics": ["Asset Manager"],
    "Category-wise Asset Value": ["Asset Manager"],
    "Location-wise Asset Value": ["Asset Manager"],
    "File Category": ["Document Manger", "Document Viewer"],
    "File Classification": ["Document Manger", "Document Viewer", "Employee", "System Manager"],
    "Issues": ["Projects Manager", "HD Manager"],
    "Project Summary": ["Projects Manager"],
    "Projects Budget": ["Projects Manager"],
    "Uploaded Documents": ["Document Manger", "Document Viewer"],
    "Completed Tasks": ["Projects Manager", "Projects User"],
    "Tasks": ["Projects Manager", "Projects User", "Employee"],
    "Login": ["System Manager"],
    "Failed Login Attempts": ["System Manager", "Audit Viewer"],
}

# ---------------------------------------------------------------------------
# Admin coverage
# ---------------------------------------------------------------------------
# A Custom DocPerm row REPLACES a doctype's standard permissions wholesale:
# frappe.permissions.get_valid_perms() reads DocPerm rows only for doctypes
# that have no Custom DocPerm row at all. So the single `("User", READ)`
# grant above deletes ERPNext's "System Manager can create/write User"
# permission for everyone — Administrator included, because the desk builds
# its can_create / can_write lists from roles
# (frappe.utils.user.UserPermissions.build_perm_map), and that path has no
# Administrator bypass. The symptom on a fresh install is an admin who can
# open the User list but cannot add or edit a user.
#
# _ensure_custom_docperm() now snapshots the standard rows before adding the
# first custom one, so new sites never lose them; _backfill_standard_perms()
# below repairs sites migrated before that fix.
#
# ADMIN_GRANTS is the belt-and-braces half of the same problem: it gives
# System Manager explicit full rights on every doctype this app owns or
# touches. The app's own doctypes need it independently of the Custom
# DocPerm issue — the HD DocType JSONs only list HD Manager / HD Agent /
# Employee, and Audit Log only lists Audit Viewer, so System Manager has no
# access to them at all as shipped.
APP_DOCTYPES = [
    # "custom fsf" module
    "Announcement",
    "Audit Log",
    "Client Evaluation Form",
    "Events",
    "Lessons Learned",
    "Library",
    "News",
    "Project Recommendation",
    "Security Alerts",
    # "HD" module
    "HD Team",
    "HD Team Member",
    "HD Ticket",
    "HD Ticket Category",
    "HD Ticket Priority",
    "HD Ticket Type",
]


def _touched_doctypes():
    """Every doctype the grant tables above convert to Custom DocPerm, i.e.
    every doctype whose standard permissions this app replaces."""
    seen = []
    for grants in (ASSET_GRANTS, HD_GRANTS, HR_GRANTS, PROJECTS_GRANTS, USER_PROFILE_GRANTS):
        for pairs in grants.values():
            for doctype, _perms in pairs:
                if doctype not in seen:
                    seen.append(doctype)
    # custom_fsf.patches.set_audit_log_permissions adds a Custom DocPerm row
    # for Audit Viewer, replacing Audit Log's standard System Manager perms.
    if "Audit Log" not in seen:
        seen.append("Audit Log")
    return seen


def _admin_grants():
    doctypes = APP_DOCTYPES + [dt for dt in _touched_doctypes() if dt not in APP_DOCTYPES]
    return {"System Manager": [(dt, FULL) for dt in doctypes]}


BACKFILL_FLAG = "custom_fsf_standard_docperm_backfill"


def _backfill_standard_perms():
    """One-shot repair for sites that already ran the earlier version of this
    patch and lost their standard permissions.

    For each doctype this app converted to Custom DocPerm, copy back any
    standard DocPerm row that has no Custom DocPerm counterpart. Runs once
    and then records a flag, so a permission an admin deliberately removes
    later in Role Permission Manager is not resurrected on the next migrate.
    """
    if frappe.db.get_default(BACKFILL_FLAG):
        return

    skip = {"name", "creation", "modified", "modified_by", "owner", "idx", "doctype"}

    for doctype in _touched_doctypes():
        if not frappe.db.exists("DocType", doctype):
            continue
        if not frappe.db.exists("Custom DocPerm", {"parent": doctype}):
            continue  # still on standard perms — nothing was replaced

        existing = {
            (r.role, r.permlevel, r.if_owner)
            for r in frappe.get_all(
                "Custom DocPerm",
                filters={"parent": doctype},
                fields=["role", "permlevel", "if_owner"],
            )
        }
        for row in frappe.get_all("DocPerm", filters={"parent": doctype}, fields="*"):
            if (row.role, row.permlevel, row.if_owner) in existing:
                continue
            if not frappe.db.exists("Role", row.role):
                continue
            doc = frappe.new_doc("Custom DocPerm")
            doc.update({k: v for k, v in row.items() if k not in skip})
            doc.parenttype = "DocType"
            doc.parentfield = "permissions"
            doc.insert(ignore_permissions=True)
            print(f"✅ Restored standard '{row.role}' perm on '{doctype}'")

    frappe.db.set_default(BACKFILL_FLAG, "1")


# Note: Number Cards have no `roles` table in this Frappe version, so the
# asset dashboard cards (Total Assets, Asset Value, ...) can't be gated with
# Has Role rows. They're gated in code instead — see
# custom_fsf/overrides/number_card.py (every Asset-based card is manager-only).


def _ensure_role(role_name, description):
    if frappe.db.exists("Role", role_name):
        return
    frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
            "disabled": 0,
            "is_custom": 0,
            "description": description,
        }
    ).insert(ignore_permissions=True)
    print(f"✅ Created role '{role_name}'")


def _applicable(parent, perms):
    """Drop submit/cancel/amend for doctypes that aren't submittable, so a
    FULL grant stays valid on plain doctypes (Item, User, Library, ...)."""
    if not perms.get("submit"):
        return perms
    if frappe.db.get_value("DocType", parent, "is_submittable"):
        return perms
    return {k: v for k, v in perms.items() if k not in ("submit", "cancel", "amend")}


def _ensure_custom_docperm(parent, role, perms, upgrade=False):
    if not frappe.db.exists("DocType", parent):
        # ERPNext / target app not installed on this site — skip silently.
        return
    if not frappe.db.exists("Role", role):
        return

    perms = _applicable(parent, perms)

    existing = frappe.db.get_value(
        "Custom DocPerm",
        {"parent": parent, "role": role, "permlevel": 0},
    )
    if existing:
        if not upgrade:
            return
        # Widen the existing row rather than skipping it, so a role that was
        # granted read-only earlier still ends up with the rights asked for
        # here. Rights are only ever added, never taken away.
        doc = frappe.get_doc("Custom DocPerm", existing)
        added = [k for k, v in perms.items() if v and not doc.get(k)]
        if not added:
            return
        for key in added:
            doc.set(key, 1)
        doc.save(ignore_permissions=True)
        print(f"✅ Widened '{role}' perm on '{parent}' ({', '.join(added)})")
        return

    # A Custom DocPerm row REPLACES the doctype's standard permissions
    # wholesale (frappe.permissions.get_valid_perms), so copy the standard
    # rows across before adding the first custom one — exactly what
    # frappe.permissions.add_permission does. Without this, adding a single
    # read row for, say, Document Viewer on `User` silently deletes
    # ERPNext's "System Manager can create/write User" permission.
    setup_custom_perms(parent)

    doc = {
        "doctype": "Custom DocPerm",
        "parent": parent,
        "parenttype": "DocType",
        "parentfield": "permissions",
        "role": role,
        "permlevel": 0,
    }
    doc.update(perms)
    frappe.get_doc(doc).insert(ignore_permissions=True)
    print(f"✅ Granted '{role}' perm on '{parent}'")


def _apply_grants(grants, upgrade=False):
    for role, pairs in grants.items():
        for doctype, perms in pairs:
            _ensure_custom_docperm(doctype, role, perms, upgrade=upgrade)


def _ensure_has_role(parent, parenttype, role, parentfield="roles"):
    """Generic helper for parented Has Role rows (workspaces, reports, etc.)."""
    if not frappe.db.exists(parenttype, parent):
        return
    if not frappe.db.exists("Role", role):
        return
    if frappe.db.exists("Has Role", {
        "parent": parent, "parenttype": parenttype, "role": role,
    }):
        return
    frappe.get_doc({
        "doctype": "Has Role",
        "parent": parent,
        "parenttype": parenttype,
        "parentfield": parentfield,
        "role": role,
    }).db_insert()
    print(f"✅ Granted '{role}' {parenttype} access to '{parent}'")


def _apply_workspace_grants(grants):
    for workspace, roles in grants.items():
        for role in roles:
            _ensure_has_role(workspace, "Workspace", role)


def _apply_report_grants(grants):
    for report, roles in grants.items():
        for role in roles:
            _ensure_has_role(report, "Report", role)


def _apply_chart_grants(grants):
    for chart, roles in grants.items():
        for role in roles:
            _ensure_has_role(chart, "Dashboard Chart", role)


def _dispose_asset_user_role():
    """The 'Asset User' role was merged into 'Employee' (custodian/manager
    visibility now keys off the Employee record alone). Remove every trace:
    doc perms, role assignments, workspace/report/chart grants, the Role."""
    if not frappe.db.exists("Role", "Asset User"):
        return

    frappe.db.delete("Custom DocPerm", {"role": "Asset User"})
    frappe.db.delete("Has Role", {"role": "Asset User"})

    frappe.delete_doc("Role", "Asset User", ignore_permissions=True, force=True)
    frappe.clear_cache()
    print("✅ Disposed 'Asset User' role (merged into 'Employee')")


def execute():
    for role in ASSET_ROLES:
        _ensure_role(role["role_name"], role["description"])

    _dispose_asset_user_role()

    _apply_grants(ASSET_GRANTS)
    _apply_grants(HD_GRANTS)
    _apply_grants(HR_GRANTS)
    _apply_grants(PROJECTS_GRANTS)
    _apply_grants(USER_PROFILE_GRANTS)

    # Put back whatever the grants above displaced (one-shot), then make sure
    # System Manager holds full rights everywhere this app reaches.
    _backfill_standard_perms()
    _apply_grants(_admin_grants(), upgrade=True)

    _apply_workspace_grants(WORKSPACE_GRANTS)
    _apply_report_grants(REPORT_GRANTS)
    _apply_chart_grants(CHART_GRANTS)

    # Drop orphan Has Role rows once inserted against Number Cards — the
    # doctype has no roles table, so they were never read by anything.
    frappe.db.delete("Has Role", {"parenttype": "Number Card"})

    # Portal Settings.default_portal_home defaults to "/app" on ERPNext sites,
    # which overrides the `home_page = "landing"` hook for ANY non-Guest user
    # (see frappe.website.utils.get_home_page). Users without desk access
    # (HD Manager, Document Viewer, Audit Viewer, plain Employee, etc.) then
    # get a 403 "Not Permitted" page when they visit `/`. Force it to the
    # landing route so the hook value is honored.
    current = frappe.db.get_single_value("Portal Settings", "default_portal_home")
    if current != "landing":
        frappe.db.set_single_value("Portal Settings", "default_portal_home", "landing")
        print("✅ Set Portal Settings.default_portal_home = 'landing'")

    _fix_user_types_for_desk_roles()
    _remove_employee_self_restrictions()
    _set_assets_as_home_for_asset_users()

    # Permission rows are read through a cache keyed by doctype+user; without
    # this the desk keeps serving the pre-patch perms until the next restart.
    frappe.clear_cache()
    frappe.db.commit()


# Roles that get Assets as their desk home page. Asset Manager + Employee are
# the asset-facing users; System Manager is included so admins (who can see
# every workspace, Assets included) also home on Assets rather than the stock
# ERPNext "Home". Users without any of these keep their own default.
ASSET_HOME_ROLES = ("Asset Manager", "Employee", "System Manager")


def _set_assets_as_home_for_asset_users():
    """Make the desk home button / bare `/app` open the Assets workspace.

    The desk resolves bare `/app` in this order (frappe router.js):
      1. the user's `default_workspace`
      2. a private `home-<user>` workspace
      3. the standard "Home" workspace   <-- always wins otherwise
      4. the first workspace in the list
    Hiding "Home" / reordering the sidebar only affects step 4, which is
    never reached because "Home" exists at step 3. The only override is
    step 1, so point each user's default_workspace at Assets.

    Only fills an empty value, so a user's own choice is respected, and it
    does not trap navigation — it only sets where the home button lands."""
    if not frappe.db.exists("Workspace", "Assets"):
        return

    users = frappe.get_all(
        "Has Role",
        filters={"role": ["in", ASSET_HOME_ROLES], "parenttype": "User"},
        pluck="parent",
        distinct=True,
    )

    for user in users:
        if not frappe.db.exists("User", user):
            continue
        if frappe.db.get_value("User", user, "default_workspace"):
            continue  # respect an explicit choice
        frappe.db.set_value("User", user, "default_workspace", "Assets", update_modified=False)
        print(f"✅ Set Assets as home workspace for '{user}'")


def _remove_employee_self_restrictions():
    """ERPNext pins every user to their own Employee record with an
    auto-created User Permission (employee.py update_user_permissions, on by
    default via the create_user_permission checkbox). User Permissions
    override role perms — even System Manager — so anyone except
    Administrator sees a one-row Employee list. Drop those self-pins and
    stop new ones from being created. No roles are special-cased here:
    Employee visibility is governed purely by role permissions (see
    HR_GRANTS / PROJECTS_GRANTS, adjustable in Role Permission Manager).
    Self-heals on every migrate."""
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter

    # Delete only the auto-created self-pins (a user permission pointing at
    # the user's own Employee record), not deliberate admin-made restrictions.
    self_pins = frappe.db.sql(
        """
        SELECT up.name, up.user
        FROM `tabUser Permission` up
        JOIN `tabEmployee` emp ON emp.name = up.for_value AND emp.user_id = up.user
        WHERE up.allow = 'Employee'
        """,
        as_dict=True,
    )
    for pin in self_pins:
        # delete_doc (not db.delete) so the User Permission controller
        # clears the user's cached permission set.
        frappe.delete_doc("User Permission", pin.name, ignore_permissions=True)
        print(f"✅ Removed self-only Employee restriction for '{pin.user}'")

    # Stop recreation: clear the checkbox on existing employees and default
    # it off for new ones.
    frappe.db.sql(
        "UPDATE `tabEmployee` SET create_user_permission = 0 WHERE create_user_permission = 1"
    )
    make_property_setter(
        "Employee", "create_user_permission", "default", "0", "Text",
        validate_fields_for_doctype=False,
    )


# Roles whose holders MUST be System Users (have desk access). Sourced from
# each role JSON's `desk_access: 1`. If a user holds one of these roles but
# is still a "Website User", they hit "Not Permitted" on /app and on any
# desk page — even though their role is supposed to grant desk access. This
# can happen when users are created/imported in a way that bypasses
# User.validate (data import, raw SQL, custom scripts). Self-heal here.
DESK_ROLES = {
    "Asset Manager",
    "HD Manager", "HD Agent",
    "Document Viewer", "Document Manger", "Document Manager",
    "Audit Viewer",
    "System Manager",
    "Projects Manager", "Projects User",
    "HR Manager", "HR User",
    "Accounts Manager", "Accounts User",
    "Stock Manager", "Stock User",
    "Item Manager",
}


def _fix_user_types_for_desk_roles():
    """Bump any Website User who actually holds a desk-access role up to
    System User, so post-login they can reach /app instead of a 403."""
    rows = frappe.db.sql(
        """
        SELECT DISTINCT u.name
        FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent = u.name AND hr.parenttype = "User"
        WHERE u.enabled = 1
          AND u.user_type = "Website User"
          AND hr.role IN ({placeholders})
        """.format(placeholders=", ".join(["%s"] * len(DESK_ROLES))),
        tuple(DESK_ROLES),
        as_dict=True,
    )
    for row in rows:
        frappe.db.set_value("User", row.name, "user_type", "System User")
        print(f"✅ Promoted '{row.name}' to System User (holds a desk-access role)")
