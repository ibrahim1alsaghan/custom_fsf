"""Create one Role Profile per business persona, so a new user is set up by
picking a single profile instead of hand-assembling roles.

Each profile bundles the app role with the supporting roles that role needs
to actually function: "Employee" (asset custodian visibility, Task read, HD
Ticket raising) is in every staff profile, and Projects Manager also carries
Projects User because several ERPNext Project/Task perms hang off the latter.

Note on semantics: Frappe's Role Profile is authoritative. RoleProfile.on_update
runs update_all_users(), which REPLACES the roles of every user assigned to the
profile with the profile's own list. So each profile must be complete on its
own — a user assigned "FSF Help Desk Agent" keeps exactly those roles and
nothing else.

Idempotent, and additive: re-running only appends roles that are missing from
an existing profile. It never removes roles someone added by hand, and never
touches profiles it doesn't own.
"""

import frappe


PREFIX = "FSF "

# persona -> roles. Roles that don't exist on a given site (LMS not installed,
# for example) are dropped silently.
ROLE_PROFILES = {
    # Full run of the system: every module role plus the desk admin roles
    # needed to edit workspaces, reports and dashboards.
    "Administrator": [
        "System Manager",
        "Asset Manager",
        "HD Manager",
        "Document Manger",
        "Audit Viewer",
        "Projects Manager",
        "Projects User",
        "HR Manager",
        "HR User",
        "Employee",
        "Workspace Manager",
        "Report Manager",
        "Dashboard Manager",
        "Script Manager",
        "Website Manager",
    ],
    "Asset Manager": ["Asset Manager", "Employee"],
    "Help Desk Manager": ["HD Manager", "Employee"],
    "Help Desk Agent": ["HD Agent", "Employee"],
    "Document Manager": ["Document Manger", "Document Viewer", "Employee"],
    "Document Viewer": ["Document Viewer", "Employee"],
    "Auditor": ["Audit Viewer", "Employee"],
    "Project Manager": ["Projects Manager", "Projects User", "Employee"],
    "Project Member": ["Projects User", "Employee"],
    "HR Manager": ["HR Manager", "HR User", "Employee"],
    # Baseline staff account: own assets + own tasks + raise HD tickets +
    # read the document library.
    "Employee": ["Employee", "Document Viewer"],
    "LMS Instructor": ["Course Creator", "Moderator", "LMS Student"],
    "LMS Student": ["LMS Student"],
}


def _ensure_role_profile(name, roles):
    roles = [r for r in roles if frappe.db.exists("Role", r)]
    if not roles:
        return

    if not frappe.db.exists("Role Profile", name):
        frappe.get_doc(
            {
                "doctype": "Role Profile",
                "role_profile": name,
                "roles": [{"role": r} for r in roles],
            }
        ).insert(ignore_permissions=True)
        print(f"✅ Created Role Profile '{name}' ({len(roles)} roles)")
        return

    doc = frappe.get_doc("Role Profile", name)
    have = {r.role for r in doc.roles}
    missing = [r for r in roles if r not in have]
    if not missing:
        return
    for role in missing:
        doc.append("roles", {"role": role})
    doc.save(ignore_permissions=True)
    print(f"✅ Updated Role Profile '{name}' (added {', '.join(missing)})")


def execute():
    for persona, roles in ROLE_PROFILES.items():
        _ensure_role_profile(PREFIX + persona, roles)

    frappe.db.commit()
