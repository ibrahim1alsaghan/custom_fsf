import frappe
from frappe import whitelist

# @frappe.whitelist(allow_guest=True)
# def get_courses():
#     return frappe.get_all(
#         "LMS Course",
#         fields=[
#             "name", "title", "description",
#             "image", "rating", "lessons"
#         ],
#         filters={"published": 1},
#         limit=6
#     )

from lms.lms.utils import get_courses, get_batches, get_enrollment_details

@frappe.whitelist(allow_guest=False)
def fetch_courses():
    filters = {
        "published": 1,
        "upcoming": 0,
        "disable_self_learning": 0
    }

    return get_courses(
            filters=filters,
            start=0,
            page_length=4,  # Top 4 popular courses
        )
    

@frappe.whitelist(allow_guest=True)
def fetch_batch():
    return get_batches()



@frappe.whitelist(allow_guest=True)
def fetch_enrollment():
    courses = get_courses()
    courses = courses[:4]
    return get_enrollment_details(courses)