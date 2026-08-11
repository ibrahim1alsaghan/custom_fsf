# apps/custom_fsf/custom_fsf/utils/log_retention_reminder.py
import calendar
from datetime import date
import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

# ----- you can change this default to "30" or keep "last"
DEFAULT_TARGET_DAY = "last"  # "last" or a number string like "30"

def _get_system_managers() -> list[str]:
    return frappe.get_all(
        "Has Role",
        filters={"role": "System Manager"},
        pluck="parent",
        distinct=True
    )

def _compose_notification():
    subject = _("Reminder: Logs may be deleted soon by retention rules")
    message = _(
        "Some system logs may be automatically deleted according to retention settings. "
        "If you wish to keep any of them, please export them before month-end."
    )
    return subject, message

def _notify_system_managers():
    users = _get_system_managers()
    if not users:
        return "No System Managers found"

    subject, message = _compose_notification()
    payload = frappe._dict({
        "subject": subject,
        "from_user": frappe.session.user if frappe.session.user else "Administrator",
        "type": "Alert",
        "email_content": message,
        "link": "",  # you can point to a custom "Export Logs" page
    })
    make_notification_logs(payload, users)
    return f"Sent to {len(users)} System Managers"

def _is_target_day(today: date, target_day: str | None = None) -> bool:
    raw = (target_day or DEFAULT_TARGET_DAY).strip().lower()
    last_day = calendar.monthrange(today.year, today.month)[1]
    if raw == "last":
        return today.day == last_day
    try:
        d = int(raw)
        d = min(max(1, d), last_day)  # clamp 31 into Feb, etc.
        return today.day == d
    except Exception:
        return today.day == last_day

# ---------- public entry points ----------

def send_log_retention_reminder():
    """Unconditional send — call this to force-send any time."""
    return _notify_system_managers()

def send_if_today_is_target_day(target_day: str | None = None):
    """Send only if today matches the configured target_day ('last' or '30', etc.)."""
    today = now_datetime().date()
    if _is_target_day(today, target_day):
        return _notify_system_managers()
    return f"Skipped: today={today} is not target day"
