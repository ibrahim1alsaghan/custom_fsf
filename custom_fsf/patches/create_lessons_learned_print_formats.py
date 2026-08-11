import frappe


DETAIL_HTML = """
<style>
  .ll-card { padding: 12px 16px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 10px; }
  .ll-h1 { font-size: 20px; font-weight: 600; margin: 0 0 6px 0; }
  .ll-muted { color: #6b7280; font-size: 12px; }
  .ll-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
  .ll-label { color: #6b7280; font-size: 12px; }
  .ll-val { font-size: 14px; font-weight: 500; }
  .ll-section { margin-top: 14px; }
  .page-break { page-break-after: always; }
</style>

{% set many = (docs if docs is defined else []) %}
{% if many and many|length > 1 %}
  {# Bulk print: render each with a page break #}
  {% for d in many %}
  <div class="ll-card">
    <div class="ll-h1">{{ d.title }}</div>
    <div class="ll-muted">Lessons Learned • {{ d.name }}</div>
    <div class="ll-grid">
      <div>
        <div class="ll-label">Project</div>
        <div class="ll-val">{{ d.project or "-" }}</div>
      </div>
      <div>
        <div class="ll-label">Project Phase</div>
        <div class="ll-val">{{ d.project_phase or "-" }}</div>
      </div>
      <div>
        <div class="ll-label">Impact</div>
        <div class="ll-val">{{ d.impact or "-" }}</div>
      </div>
      <div>
        <div class="ll-label">Category</div>
        <div class="ll-val">{{ d.category or "-" }}</div>
      </div>
    </div>
    <div class="ll-section">
      <div class="ll-label">Description</div>
      <div class="ll-val">{{ (d.description or "-") | safe }}</div>
    </div>
  </div>
  {% if not loop.last %}<div class="page-break"></div>{% endif %}
  {% endfor %}
{% else %}
  {# Single print: use "doc" #}
  <div class="ll-card">
    <div class="ll-h1">{{ doc.title }}</div>
    <div class="ll-muted">Lessons Learned • {{ doc.name }}</div>
    <div class="ll-grid">
      <div>
        <div class="ll-label">Project</div>
        <div class="ll-val">{{ doc.project or "-" }}</div>
      </div>
      <div>
        <div class="ll-label">Project Phase</div>
        <div class="ll-val">{{ doc.project_phase or "-" }}</div>
      </div>
      <div>
        <div class="ll-label">Impact</div>
        <div class="ll-val">{{ doc.impact or "-" }}</div>
      </div>
      <div>
        <div class="ll-label">Category</div>
        <div class="ll-val">{{ doc.category or "-" }}</div>
      </div>
    </div>
    <div class="ll-section">
      <div class="ll-label">Description</div>
      <div class="ll-val">{{ (doc.description or "-") | safe }}</div>
    </div>
  </div>
{% endif %}
"""


def upsert_print_format(name: str, html: str):
    exists = frappe.db.exists("Print Format", name)
    if exists:
        pf = frappe.get_doc("Print Format", name)
        pf.custom_format = 1
        pf.print_format_type = "Jinja"
        pf.disabled = 0
        pf.raw_printing = 0
        pf.html = html
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
        "html": html,
    })
    pf.insert(ignore_permissions=True)


def execute():
    if not frappe.db.exists("DocType", "Lessons Learned"):
        return
    upsert_print_format("Lessons Learned - Detail", DETAIL_HTML)



