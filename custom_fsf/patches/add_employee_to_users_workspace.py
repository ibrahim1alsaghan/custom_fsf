"""Add an Employee shortcut to the "Users" workspace.

The Users workspace is HR Manager's home (see setup_workspaces.py), but it
only ships shortcuts for User / Role Profile / Role — there is no sidebar
path to the Employee list at all. DocType shortcuts auto-hide for users
without read permission on the target, so adding Employee here only
surfaces it for HR staff and System Managers.

Idempotent: safe to re-run on every migrate.
"""

import json

import frappe


def execute():
    if not frappe.db.exists("Workspace", "Users"):
        return

    ws = frappe.get_doc("Workspace", "Users")

    if any(s.type == "DocType" and s.link_to == "Employee" for s in ws.shortcuts):
        return

    ws.append(
        "shortcuts",
        {"type": "DocType", "link_to": "Employee", "label": "Employee", "color": "Grey"},
    )

    content = json.loads(ws.content or "[]")
    block = {
        "id": frappe.generate_hash(length=10),
        "type": "shortcut",
        "data": {"shortcut_name": "Employee", "col": 3},
    }
    shortcut_indexes = [i for i, b in enumerate(content) if b.get("type") == "shortcut"]
    if shortcut_indexes:
        content.insert(shortcut_indexes[-1] + 1, block)
    else:
        content.append(block)
    ws.content = json.dumps(content)

    ws.flags.ignore_permissions = True
    ws.save()
    frappe.db.commit()
    print("✅ Added Employee shortcut to the Users workspace")
