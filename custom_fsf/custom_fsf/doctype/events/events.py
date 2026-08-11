import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from hijridate import Gregorian  # Umm al-Qura


def gregorian_to_hijri_str(value) -> str | None:
    if not value:
        return None
    d = getdate(value)  # str/date/datetime -> date
    h = Gregorian(d.year, d.month, d.day).to_hijri()
    return f"{h.year:04d}-{h.month:02d}-{h.day:02d}"


@frappe.whitelist()
def convert_gregorian_to_hijri(date_str: str | None = None) -> str | None:
    # called from client script
    return gregorian_to_hijri_str(date_str)


class Events(Document):
    def validate(self):
        # canonical: event_date_gregorian (Date)
        # derived: event_date_hijri (Data)
        self.event_date_hijri = gregorian_to_hijri_str(self.event_date_gregorian)
