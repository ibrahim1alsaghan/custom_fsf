import frappe
from frappe.utils import today

no_cache = True

def get_context(context):
    context.no_cache = 1
    context.no_header = True
    context.no_footer = True

    # Fetch alerts for the landing page
    context.alerts = get_alerts_data()

    return context

def get_alerts_data():
    try:
        alerts = frappe.db.sql("""
            SELECT name,
                warning_name_en,
                warning_name_ar,
                warning_source,
                warning_source_logo,
                warning_date,
                severity_level,
                warning_link
            FROM `tabSecurity Alerts`
            ORDER BY `warning_date` DESC
            LIMIT 6
        """, as_dict=True)
        return alerts
    except Exception:
        return []

@frappe.whitelist(allow_guest=True)
def get_alerts():
    alerts = frappe.db.sql("""
        SELECT name,
            warning_name_en,
            warning_name_ar,
            warning_source,
            warning_description_en,
            warning_description_ar,
            warning_number,
            warning_link,
            warning_date,
            severity_level,
            recommendations,
            recommendations_ar,
            warning_source_logo
        FROM `tabSecurity Alerts`
        ORDER BY `warning_date` DESC
        LIMIT 3
    """, as_dict=True)

    for alert in alerts:
        alert_name = alert.get('name')
        sectors = frappe.db.sql("""
            SELECT name_en, name_ar
            FROM `tabSector`
            WHERE parent = %s
        """, (alert_name,), as_dict=True)

        alert['target_sectors_en'] = [s.get('name_en') for s in sectors if s.get('name_en')]
        alert['target_sectors_ar'] = [s.get('name_ar') for s in sectors if s.get('name_ar')]

    return alerts

@frappe.whitelist(allow_guest=True)
def get_news():
    news = frappe.db.sql("""
        SELECT name, title, image, url, description, date
        FROM `tabNews`
        WHERE enabled = 1
        ORDER BY `date` DESC
        LIMIT 3
    """, as_dict=True)

    return news

@frappe.whitelist(allow_guest=True)
def get_events():
    today_date = today()
    events = frappe.db.sql("""
        SELECT
            event_title,
            event_description,
            event_link,
            event_date_gregorian,
            event_date_hijri,
            event_image
        FROM `tabEvents`
        WHERE event_date_gregorian >= %s
        ORDER BY event_date_gregorian ASC
        LIMIT 8
    """, (today_date,), as_dict=True)
    return events
