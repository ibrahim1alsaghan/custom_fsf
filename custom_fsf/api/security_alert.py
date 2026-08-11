import os
import re

import frappe
import requests
from frappe.utils import getdate
from frappe.utils import strip_html

API_URL = "https://backend.nca.gov.sa/api/public/alert?size=5&page=0&sort=warningNumber,desc"
NCA_BACKEND = "https://backend.nca.gov.sa"
NCA_CDN = "https://cdn.nca.gov.sa/api"
ALERT_DETAIL_URL = "https://nca.gov.sa/ar/cert/{alert_id}/"


def _clean_text(html):
    """Strip HTML tags and clean up &nbsp; entities."""
    text = strip_html(html or "")
    text = text.replace("&nbsp;", " ").replace("\xa0", " ")
    text = re.sub(r" {2,}", " ", text).strip()
    return text


def _download_logo(logo_url, warning_number):
    """Download vendor logo from NCA and save to public files. Returns local file URL or empty string."""
    if not logo_url:
        return ""
    try:
        resp = requests.get(logo_url, timeout=15)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        ext = "png"
        if "svg" in content_type:
            ext = "svg"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = "jpg"

        filename = f"vendor_logo_{warning_number}.{ext}"
        public_files = frappe.get_site_path("public", "files")
        file_path = os.path.join(public_files, filename)

        with open(file_path, "wb") as f:
            f.write(resp.content)

        return f"/files/{filename}"
    except Exception:
        return ""


def fetch_nca_alerts(force_update=False):
    """Fetch alerts from NCA API. Pass force_update=True to re-process all existing alerts."""
    r = requests.get(API_URL, timeout=30, headers={"Accept": "application/json"})
    r.raise_for_status()

    alerts = r.json().get("content", [])
    inserted = 0
    updated = 0

    for a in alerts:
        warning_number = (a.get("warningNumber") or "").strip()
        if not warning_number:
            continue

        existing = frappe.db.exists("Security Alerts", {"warning_number": warning_number})

        if existing and not force_update:
            continue

        desc_en = _clean_text(a.get("bodyEn"))
        desc_ar = _clean_text(a.get("bodyAr"))
        rec_en  = _clean_text(a.get("preventiveMeasuresEn"))
        rec_ar  = _clean_text(a.get("preventiveMeasuresAr"))

        nca_id = a.get("id")
        detail_url = ALERT_DETAIL_URL.format(alert_id=nca_id) if nca_id else ""

        # Download vendor logo locally
        vendor = a.get("vendor") or {}
        vendor_image = vendor.get("image") or {}
        external_link = vendor_image.get("externalLink") or ""
        remote_logo_url = f"{NCA_CDN}/{external_link}" if external_link else ""

        local_logo_url = _download_logo(remote_logo_url, warning_number)
        warning_source = vendor.get("nameEn") or vendor.get("nameAr") or ""

        if existing:
            # Update existing record
            doc_name = frappe.db.get_value("Security Alerts", {"warning_number": warning_number}, "name")
            frappe.db.set_value("Security Alerts", doc_name, {
                "warning_description_en": desc_en,
                "warning_description_ar": desc_ar,
                "recommendations": rec_en,
                "recommendations_ar": rec_ar,
                "warning_link": detail_url,
                "warning_source_logo": local_logo_url or remote_logo_url,
            })
            updated += 1
        else:
            # Insert new
            doc = frappe.get_doc({
                "doctype": "Security Alerts",
                "warning_number": warning_number,
                "warning_date": getdate(a.get("warningDate")) if a.get("warningDate") else None,
                "warning_name_en": a.get("titleEn"),
                "warning_name_ar": a.get("titleAr"),
                "severity_level": a.get("severityLevel"),
                "warning_description_en": desc_en,
                "warning_description_ar": desc_ar,
                "recommendations": rec_en,
                "recommendations_ar": rec_ar,
                "warning_source": warning_source,
                "warning_link": detail_url,
                "warning_source_logo": local_logo_url or remote_logo_url,
            })

            for s in (a.get("sectors") or []):
                doc.append("target_sectors", {
                    "id": str(s.get("id") or ""),
                    "name_en": s.get("nameEn"),
                    "name_ar": s.get("nameAr"),
                })

            doc.insert(ignore_permissions=True)
            inserted += 1

    frappe.db.commit()
    return {"ok": True, "inserted": inserted, "updated": updated}
