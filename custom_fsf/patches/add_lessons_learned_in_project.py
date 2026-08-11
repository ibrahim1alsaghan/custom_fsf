import frappe


def execute():
    # Ensure DocType exists before wiring anything
    if not frappe.db.exists("DocType", "Lessons Learned"):
        return

    # Add a Link in Project's connections so it shows under Linked Docs
    try:
        meta = frappe.get_meta("Project")
        ll_link = {
            "group": "References",
            "link_doctype": "Lessons Learned",
            "link_fieldname": "project",
        }
        links = list(meta.links or [])
        if ll_link not in links:
            links.append(ll_link)
            frappe.db.set_value("DocType", "Project", "links", frappe.as_json(links))
    except Exception:
        # Non-fatal; dashboard buttons will still work
        pass



