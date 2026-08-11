# Copyright (c) 2025, ibrahim alsaghan and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
import io
import os


class Library(Document):
	def increment_download_counter(self):
		"""Increment the download counter for this library document"""
		if not self.download_counter:
			self.download_counter = 0
		self.download_counter += 1
		self.save(ignore_permissions=True)
		frappe.db.commit()
		return self.download_counter


def library_permission_query(user):
    roles = frappe.get_roles(user)

    if "System Manager" in roles or "Document Manger" in roles:
        return ""

    # Document Viewer and any Employee see Confidential + Global.
    # Pure portal / external users (no Employee role) fall back to Global only.
    if "Document Viewer" in roles or "Employee" in roles:
        allowed = ["Confidential", "Global"]
    else:
        allowed = ["Global"]

    allowed_escaped = ", ".join([frappe.db.escape(c) for c in allowed])
    return f"""(`tabLibrary`.`classification` IN ({allowed_escaped}))"""

def library_has_permission(doc, user):
    roles = frappe.get_roles(user)

    if "System Manager" in roles or "Document Manger" in roles:
        return True

    classification = doc.classification

    if "Document Viewer" in roles or "Employee" in roles:
        return classification in ["Confidential", "Global"]

    # Default: only allow Global
    return classification == "Global"


@frappe.whitelist()
def increment_download_counter(docname):
    """Server-side method to increment download counter (kept for backwards compatibility)"""
    doc = frappe.get_doc("Library", docname)
    return doc.increment_download_counter()


@frappe.whitelist()
def download_library_file(docname: str, view: str = None):
    """Download or view the library file.

    - Checks Library permissions.
    - For Confidential PDFs, returns a watermarked copy with "CONFIDENTIAL" watermark.
    - For Top Secret PDFs, returns a watermarked copy with personalized watermark (name + email).
    - For all other files, streams the original file.
    
    Args:
        docname: The Library document name
        view: If "1" or "true", returns PDF inline for iframe viewing. Otherwise downloads the file.
    """
    doc = frappe.get_doc("Library", docname)

    if not library_has_permission(doc, frappe.session.user):
        frappe.throw(frappe._("Not permitted to download this document"), frappe.PermissionError)

    if not doc.file:
        frappe.throw(frappe._("No file attached to this Library record"))

    file_url = doc.file

    # Find the underlying File document
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = file_doc.get_full_path()

    # Only increment counter on actual downloads, not when viewing in iframe
    is_viewing = view and str(view).lower() in ("1", "true")
    if not is_viewing:
        doc.increment_download_counter()

    classification = (doc.classification or "").strip().lower()
    is_pdf = file_url.lower().endswith(".pdf")
    
    is_confidential_pdf = classification == "confidential" and is_pdf
    is_top_secret_pdf = classification == "top secret" and is_pdf

    filename = file_doc.file_name or os.path.basename(file_path)

    if not (is_confidential_pdf or is_top_secret_pdf):
        # Just stream the original file
        if is_viewing:
            return _send_file_inline(file_path, filename)
        return _send_file(file_path, filename)

    # Try to generate a watermarked PDF copy on the fly
    try:
        # Get user info for personalized watermark (used for both Confidential and Top Secret)
        user = frappe.get_doc("User", frappe.session.user)
        user_name = user.full_name or user.name
        user_email = user.email or frappe.session.user
        
        if is_top_secret_pdf:
            watermarked_bytes = _generate_top_secret_watermarked_pdf(file_path, user_name, user_email)
            suffix = "_top_secret"
        else:
            # Confidential also gets personalized watermark
            watermarked_bytes = _generate_confidential_watermarked_pdf(file_path, user_name, user_email)
            suffix = "_confidential"
    except ImportError:
        # Required libraries not available: do NOT fall back to original PDF for sensitive documents
        frappe.log_error("pypdf and reportlab are required for Library PDF watermarking")
        frappe.throw(
            frappe._("Unable to generate secure watermarked PDF. Please contact the system administrator."),
            frappe.ValidationError,
        )
    except Exception as e:
        # Any unexpected error: log and do NOT fall back to original PDF for sensitive documents
        frappe.log_error(f"Error while generating watermarked Library PDF: {e}")
        frappe.throw(
            frappe._("An error occurred while generating a secure watermarked PDF. Please try again later or contact support."),
            frappe.ValidationError,
        )

    # Stream the in‑memory watermarked PDF
    if is_viewing:
        # Return inline for iframe viewing (prevents download/print bypass)
        # Use 'download' type with display_content_as='inline' for inline viewing
        frappe.local.response.filename = _append_suffix_to_filename(filename, suffix)
        frappe.local.response.filecontent = watermarked_bytes
        frappe.local.response.type = "download"
        frappe.local.response.content_type = "application/pdf"
        frappe.local.response.display_content_as = "inline"
    else:
        # Return as download
        frappe.local.response.filename = _append_suffix_to_filename(filename, suffix)
        frappe.local.response.filecontent = watermarked_bytes
        frappe.local.response.type = "download"


def _send_file(path: str, filename: str):
    """Helper to stream a file as a download response."""
    with open(path, "rb") as f:
        data = f.read()

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = data
    frappe.local.response.type = "download"


def _send_file_inline(path: str, filename: str):
    """Helper to stream a file inline for viewing (e.g., in iframe)."""
    with open(path, "rb") as f:
        data = f.read()

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = data
    frappe.local.response.type = "download"
    frappe.local.response.content_type = "application/pdf"
    frappe.local.response.display_content_as = "inline"


def _append_suffix_to_filename(filename: str, suffix: str) -> str:
    """Insert a suffix before the file extension."""
    base, ext = os.path.splitext(filename)
    return f"{base}{suffix}{ext}"


def _generate_confidential_watermarked_pdf(source_path: str, user_name: str, user_email: str) -> bytes:
    """Return a watermarked copy of the given PDF as bytes.

    The watermark includes personalized information in 2 lines:
    - Line 1: CONFIDENTIAL - name
    - Line 2: (email)
    Requires pypdf and reportlab to be installed in the bench environment.
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import Color
    except ImportError:
        # Bubble up to be handled by caller
        raise

    reader = PdfReader(source_path)
    writer = PdfWriter()

    # Format the watermark text as two lines
    line1 = f"CONFIDENTIAL - {user_name}"
    line2 = f"({user_email})"

    for page in reader.pages:
        # Create a temporary in‑memory PDF containing the watermark for this page size
        packet = io.BytesIO()

        # Get the original page size
        media_box = page.mediabox
        width = float(media_box.width)
        height = float(media_box.height)

        c = canvas.Canvas(packet, pagesize=(width, height))
        c.saveState()

        # Semi‑transparent, light text so underlying content remains readable
        try:
            transparent_grey = Color(0.85, 0.85, 0.85, alpha=0.45)
            c.setFillColor(transparent_grey)
            if hasattr(c, "setFillAlpha"):
                c.setFillAlpha(0.50)
        except Exception:
            c.setFillGray(0.9)

        # Calculate font size relative to page size (use smaller dimension for consistency)
        # Use ~3.5% of the smaller dimension, with min 24 and max 60, then make it 25% bigger
        min_dimension = min(width, height)
        base_font_size = max(24, min(60, min_dimension * 0.035))
        font_size = base_font_size * 1.25  # 25% bigger
        c.setFont("Helvetica-Bold", font_size)

        # Line spacing relative to font size (with extra spacing for readability)
        line_spacing = font_size * 0.75  # Increased spacing between lines

        # Draw 1 watermark on the main diagonal (45 degrees, top-left to bottom-right)
        c.saveState()
        c.translate(width / 2.0, height / 2.0)
        c.rotate(45)
        # Draw first line (CONFIDENTIAL - name)
        c.drawCentredString(0, line_spacing / 2, line1)
        # Draw second line (email)
        c.drawCentredString(0, -line_spacing / 2, line2)
        c.restoreState()

        # Draw 1 horizontal watermark at the top center
        c.saveState()
        top_y = height * 0.9  # Position near top (90% from bottom, 10% from top)
        c.drawCentredString(width / 2.0, top_y + line_spacing / 2, line1)
        c.drawCentredString(width / 2.0, top_y - line_spacing / 2, line2)
        c.restoreState()

        # Draw 1 horizontal watermark at the bottom center
        c.saveState()
        bottom_y = height * 0.1  # Position near bottom (10% from bottom)
        c.drawCentredString(width / 2.0, bottom_y + line_spacing / 2, line1)
        c.drawCentredString(width / 2.0, bottom_y - line_spacing / 2, line2)
        c.restoreState()

        # Draw 1 vertical watermark on the left side
        c.saveState()
        left_x = width * 0.1  # Position near left (10% from left)
        c.translate(left_x, height / 2.0)
        c.rotate(90)  # Rotate 90 degrees for vertical text
        # Draw first line (CONFIDENTIAL - name)
        c.drawCentredString(0, line_spacing / 2, line1)
        # Draw second line (email)
        c.drawCentredString(0, -line_spacing / 2, line2)
        c.restoreState()

        c.restoreState()
        c.save()

        packet.seek(0)
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]

        page.merge_page(watermark_page)
        writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream.read()


def _generate_top_secret_watermarked_pdf(source_path: str, user_name: str, user_email: str) -> bytes:
    """Return a watermarked copy of the given PDF as bytes.

    The watermark includes personalized information in 2 lines:
    - Line 1: name
    - Line 2: (email)
    Requires pypdf and reportlab to be installed in the bench environment.
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import Color
    except ImportError:
        # Bubble up to be handled by caller
        raise

    reader = PdfReader(source_path)
    writer = PdfWriter()

    # Format the watermark text as two lines
    line1 = f"TOP SECRET - {user_name}"
    line2 = f"({user_email})"

    for page in reader.pages:
        # Create a temporary in‑memory PDF containing the watermark for this page size
        packet = io.BytesIO()

        # Get the original page size
        media_box = page.mediabox
        width = float(media_box.width)
        height = float(media_box.height)

        c = canvas.Canvas(packet, pagesize=(width, height))
        c.saveState()

        # Semi‑transparent, light text so underlying content remains readable
        try:
            transparent_grey = Color(0.85, 0.85, 0.85, alpha=0.45)
            c.setFillColor(transparent_grey)
            if hasattr(c, "setFillAlpha"):
                c.setFillAlpha(0.50)
        except Exception:
            c.setFillGray(0.9)

        # Calculate font size relative to page size (use smaller dimension for consistency)
        # Use ~3.5% of the smaller dimension, with min 24 and max 60, then make it 25% bigger
        min_dimension = min(width, height)
        base_font_size = max(24, min(60, min_dimension * 0.035))
        font_size = base_font_size * 1.25  # 25% bigger
        c.setFont("Helvetica-Bold", font_size)

        # Line spacing relative to font size (with extra spacing for readability)
        line_spacing = font_size * 0.75  # Increased spacing between lines

        # Draw 1 watermark on the main diagonal (45 degrees, top-left to bottom-right)
        c.saveState()
        c.translate(width / 2.0, height / 2.0)
        c.rotate(45)
        # Draw first line (TOP SECRET - name)
        c.drawCentredString(0, line_spacing / 2, line1)
        # Draw second line (email)
        c.drawCentredString(0, -line_spacing / 2, line2)
        c.restoreState()

        # Draw 1 horizontal watermark at the top center
        c.saveState()
        top_y = height * 0.9  # Position near top (90% from bottom, 10% from top)
        c.drawCentredString(width / 2.0, top_y + line_spacing / 2, line1)
        c.drawCentredString(width / 2.0, top_y - line_spacing / 2, line2)
        c.restoreState()

        # Draw 1 horizontal watermark at the bottom center
        c.saveState()
        bottom_y = height * 0.1  # Position near bottom (10% from bottom)
        c.drawCentredString(width / 2.0, bottom_y + line_spacing / 2, line1)
        c.drawCentredString(width / 2.0, bottom_y - line_spacing / 2, line2)
        c.restoreState()

        # Draw 1 vertical watermark on the left side
        c.saveState()
        left_x = width * 0.1  # Position near left (10% from left)
        c.translate(left_x, height / 2.0)
        c.rotate(90)  # Rotate 90 degrees for vertical text
        # Draw first line (TOP SECRET - name)
        c.drawCentredString(0, line_spacing / 2, line1)
        # Draw second line (email)
        c.drawCentredString(0, -line_spacing / 2, line2)
        c.restoreState()

        c.restoreState()
        c.save()

        packet.seek(0)
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]

        page.merge_page(watermark_page)
        writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream.read()
