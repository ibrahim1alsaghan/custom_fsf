# apps/custom_fsf/custom_fsf/overrides/asset_depreciation.py

import frappe
from frappe import _
from erpnext.assets.doctype.asset.depreciation import scrap_asset as original_scrap_asset
from erpnext.assets.doctype.asset.asset import Asset

@frappe.whitelist()
def scrap_asset(asset_name):
    doc = frappe.get_doc("Asset", asset_name)

    if doc.custodian:
        frappe.throw(
            _("Cannot scrap asset '{0}' because it has a custodian assigned ({1}). Please clear the custodian first.")
            .format(doc.name, doc.custodian)
        )

    return original_scrap_asset(asset_name)


@frappe.whitelist()
def sell_asset(asset_name):
    asset = frappe.get_doc("Asset", asset_name)

    if asset.custodian:
        frappe.throw(
            _("Cannot sell asset '{0}' because it has a custodian assigned ({1}). Please clear the custodian first.")
            .format(asset.name, asset.custodian)
        )

    frappe.throw(_("Selling flow not implemented. Please use your custom flow here."))

@frappe.whitelist()
def return_asset(asset_name):
	asset = frappe.get_doc("Asset", asset_name)

	if not asset.custodian:
		frappe.throw(_("Asset already has no custodian."))

	asset.db_set("custodian", None)

	frappe.db.commit()

	# Add log entry
	from erpnext.assets.doctype.asset_activity.asset_activity import add_asset_activity
	add_asset_activity(asset.name, _("Asset returned by clearing custodian"))