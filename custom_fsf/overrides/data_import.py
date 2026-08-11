import json

import frappe
from frappe import _


def _errored_rows(importer, data_import):
    """Header row + every failed data row, mirroring frappe's
    Importer.export_errored_rows() row selection."""
    import_log = (
        frappe.get_all(
            "Data Import Log",
            fields=["row_indexes", "success"],
            filters={"data_import": data_import.name},
            order_by="log_index",
        )
        or []
    )

    row_indexes = []
    for log in import_log:
        if not log.get("success"):
            row_indexes.extend(json.loads(log.get("row_indexes") or "[]"))
    row_indexes = sorted(set(row_indexes))

    header_row = [col.header_title for col in importer.import_file.columns]
    rows = [header_row]
    rows += [row.data for row in importer.import_file.data if row.row_number in row_indexes]
    return rows


@frappe.whitelist()
def download_errored_template(data_import_name):
    """Export the failed import rows in the SAME format the file was uploaded
    in: .xlsx upload → .xlsx download, otherwise CSV.

    Frappe's stock `download_errored_template` always returns CSV, so an Excel
    import comes back as CSV — annoying to fix and re-upload. This override
    returns xlsx for xlsx/xls uploads so the user keeps working in Excel.
    Registered via override_whitelisted_methods in hooks.py.
    """
    data_import = frappe.get_doc("Data Import", data_import_name)
    importer = data_import.get_importer()
    rows = _errored_rows(importer, data_import)

    filename = _(data_import.reference_doctype)
    file_path = (data_import.import_file or "").lower()

    if file_path.endswith((".xlsx", ".xls")):
        # Build with explicit column widths. make_xlsx writes dates in a long
        # format (dd-MM-yyyy HH:mm:ss) into narrow default columns, so Excel
        # shows "#######". build_xlsx_response can't pass widths, so call
        # make_xlsx + provide_binary_file directly with auto-fit widths.
        from frappe.desk.utils import provide_binary_file
        from frappe.utils.xlsxutils import make_xlsx

        xlsx = make_xlsx(rows, filename, column_widths=_auto_column_widths(rows))
        provide_binary_file(filename, "xlsx", xlsx.getvalue())
    else:
        from frappe.utils.csvutils import build_csv_response

        build_csv_response(rows, filename)


def _auto_column_widths(rows, min_width=12, max_width=50):
    """Width per column = longest cell in that column (+padding), clamped.
    Keeps date columns wide enough that Excel doesn't render them as '#######'."""
    if not rows:
        return []
    ncols = max(len(r) for r in rows)
    widths = []
    for i in range(ncols):
        longest = max(
            (len(str(r[i])) for r in rows if i < len(r) and r[i] is not None),
            default=0,
        )
        widths.append(min(max(longest + 2, min_width), max_width))
    return widths
