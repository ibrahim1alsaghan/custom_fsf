import frappe


LIST_HTML = """
<style>
  table { width: 100%; border-collapse: collapse; }
  th, td { font-size: 12px; padding: 6px 8px; border: 1px solid #e5e7eb; }
  th { background: #f9fafb; text-align: left; }
</style>

{% set rows = (docs if docs is defined else [doc]) %}
<h3>Lessons Learned</h3>
<table>
  <thead>
    <tr>
      <th style="width: 25%">Title</th>
      <th style="width: 15%">Project</th>
      <th style="width: 15%">Phase</th>
      <th style="width: 10%">Impact</th>
      <th style="width: 10%">Category</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    {% for r in rows %}
    <tr>
      <td>{{ r.title }}</td>
      <td>{{ r.project }}</td>
      <td>{{ r.project_phase }}</td>
      <td>{{ r.impact }}</td>
      <td>{{ r.category }}</td>
      <td>{{ (r.description or "-") | striptags | truncate(180) }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
"""


def execute():
    if not frappe.db.exists("DocType", "Lessons Learned"):
        return
    name = "Lessons Learned - List"
    exists = frappe.db.exists("Print Format", name)
    if exists:
        pf = frappe.get_doc("Print Format", name)
        pf.custom_format = 1
        pf.print_format_type = "Jinja"
        pf.disabled = 0
        pf.raw_printing = 0
        pf.html = LIST_HTML
        pf.doc_type = "Lessons Learned"
        pf.save(ignore_permissions=True)
        return

    pf = frappe.get_doc({
        "doctype": "Print Format",
        "name": name,
        "doc_type": "Lessons Learned",
        "custom_format": 1,
        "print_format_type": "Jinja",
        "disabled": 0,
        "raw_printing": 0,
        "html": LIST_HTML,
    })
    pf.insert(ignore_permissions=True)



