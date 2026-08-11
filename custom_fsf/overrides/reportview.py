from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.desk import reportview as frappe_reportview
from frappe.model import optional_fields


# Valid database fieldname:
#
#   name
#   modified
#   custom_department
#
# Invalid:
#
#   '
#   count(name)
#   modified; select ...
#   (select ...)
FIELDNAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Used to remove an optional ASC or DESC from ORDER BY.
ORDER_DIRECTION_PATTERN = re.compile(
    r"\s+(asc|desc)\s*$",
    flags=re.IGNORECASE,
)

MAX_PARAMETER_LENGTH = 500
MAX_FIELDS = 10


def _invalid_query_parameter() -> None:
    """
    Return a generic validation error without reflecting attacker input.
    """

    frappe.throw(
        _("Invalid sorting or grouping parameter."),
        frappe.ValidationError,
    )


def _get_valid_columns(doctype: str) -> set[str]:
    """
    Return actual database columns for the requested DocType.
    """

    if not isinstance(doctype, str) or not doctype.strip():
        _invalid_query_parameter()

    try:
        meta = frappe.get_meta(doctype.strip())
        # optional_fields (_assign, _liked_by, _seen, ...) are real table
        # columns the desk sorts/groups by (e.g. "Group By: Assigned To")
        # but are not returned by get_valid_columns(), so allow them too.
        return set(meta.get_valid_columns()) | set(optional_fields)
    except Exception:
        _invalid_query_parameter()

    # This is unreachable, but keeps static type checkers happy.
    return set()


def _extract_fieldname(
    expression: str,
    *,
    doctype: str,
) -> str:
    """
    Accept either:

        modified
        `modified`
        `tabList Filter`.`modified`

    Reject fields qualified with another table.
    """

    # Backticks are acceptable for quoting table/column names.
    normalized = expression.replace("`", "").strip()

    if not normalized:
        _invalid_query_parameter()

    if "." not in normalized:
        fieldname = normalized
    else:
        table_name, fieldname = normalized.rsplit(".", 1)

        table_name = table_name.strip()
        fieldname = fieldname.strip()

        expected_table = f"tab{doctype}"

        if table_name != expected_table:
            _invalid_query_parameter()

    if not FIELDNAME_PATTERN.fullmatch(fieldname):
        _invalid_query_parameter()

    return fieldname


def _validate_query_clause(
    value: object,
    *,
    doctype: str,
    allow_direction: bool,
) -> None:
    """
    Validate ORDER BY or GROUP BY using an allowlist of real columns.

    ORDER BY examples accepted:

        modified
        modified desc
        creation asc
        status asc, modified desc
        `tabList Filter`.`modified` desc

    GROUP BY examples accepted:

        status
        owner
        `tabList Filter`.`modified`
    """

    if value is None or value == "":
        return

    if not isinstance(value, str):
        _invalid_query_parameter()

    if len(value) > MAX_PARAMETER_LENGTH:
        _invalid_query_parameter()

    terms = value.split(",")

    if not terms or len(terms) > MAX_FIELDS:
        _invalid_query_parameter()

    valid_columns = _get_valid_columns(doctype)

    for raw_term in terms:
        term = raw_term.strip()

        if not term:
            _invalid_query_parameter()

        if allow_direction:
            direction_match = ORDER_DIRECTION_PATTERN.search(term)

            if direction_match:
                # Remove the final ASC/DESC before validating the field.
                term = term[: direction_match.start()].strip()
        else:
            # GROUP BY must not contain sorting directions.
            if ORDER_DIRECTION_PATTERN.search(term):
                _invalid_query_parameter()

        fieldname = _extract_fieldname(
            term,
            doctype=doctype,
        )

        if fieldname not in valid_columns:
            _invalid_query_parameter()


def _validate_reportview_request() -> None:
    """
    Validate the request-controlled SQL structure before Frappe processes it.
    """

    doctype = frappe.form_dict.get("doctype")

    if not isinstance(doctype, str) or not doctype.strip():
        _invalid_query_parameter()

    doctype = doctype.strip()

    _validate_query_clause(
        frappe.form_dict.get("order_by"),
        doctype=doctype,
        allow_direction=True,
    )

    _validate_query_clause(
        frappe.form_dict.get("group_by"),
        doctype=doctype,
        allow_direction=False,
    )


@frappe.whitelist()
@frappe.read_only()
def get():
    _validate_reportview_request()
    return frappe_reportview.get()


@frappe.whitelist()
@frappe.read_only()
def get_list():
    _validate_reportview_request()
    return frappe_reportview.get_list()


@frappe.whitelist()
@frappe.read_only()
def get_count():
    _validate_reportview_request()
    return frappe_reportview.get_count()