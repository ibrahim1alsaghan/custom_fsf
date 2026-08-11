frappe.ui.form.on("Library", {
  refresh(frm) {
    render_file_preview(frm);
  },
  file(frm) {
    render_file_preview(frm);
  }
});

function render_file_preview(frm) {
  const file_url = frm.doc.file;
  const wrapper = frm.fields_dict.preview_html.$wrapper;

  if (!file_url) {
    wrapper.html("<p>No file attached.</p>");
    return;
  }

  const ext = file_url.split('.').pop().toLowerCase();
  const full_url = window.location.origin + file_url;

  console.log("📎 File URL:", file_url);
  console.log("📂 File Extension:", ext);

  const office_ext = ["doc", "docx", "xls", "xlsx", "ppt", "pptx"];
  const video_ext = ["mp4", "webm", "ogg"];
  const pdf_ext = ["pdf"];
  const image_ext = ["jpg", "jpeg", "png", "gif", "svg", "webp"];


  let html = "";

  const classification = (frm.doc.classification || "").toLowerCase();
  const is_confidential = classification === "confidential";
  const is_top_secret = classification === "top secret";
  const is_pdf = pdf_ext.includes(ext);

  // For Confidential/Top Secret PDFs, use watermarking endpoint for preview too
  // This prevents users from downloading/printing the original via PDF viewer controls
  const preview_url = ((is_confidential || is_top_secret) && is_pdf)
    ? `/api/method/custom_fsf.custom_fsf.doctype.library.library.download_library_file?docname=${encodeURIComponent(frm.doc.name)}&view=1`
    : file_url;

  if (pdf_ext.includes(ext)) {
    html = `<iframe src="${preview_url}" width="100%" height="600px" style="border:1px solid #ccc;"></iframe>`;
  } else if (image_ext.includes(ext)) {
    html = `<iframe src="${file_url}" width="100%" height="600px" style="border:1px solid #ccc;"></iframe>`;
  } else if (video_ext.includes(ext)) {
    html = `
      <video width="100%" height="400" controls>
        <source src="${file_url}" type="video/${ext}">
        Your browser does not support the video tag.
      </video>
    `;
  } else {
    html = `<p>Preview not available for this file type.</p>`;
  }
  // Decide which URL to use for downloads:
  // - Confidential PDFs: go through server-side watermarking endpoint (CONFIDENTIAL watermark)
  // - Top Secret PDFs: go through server-side watermarking endpoint (personalized watermark)
  // - Everything else: direct file URL
  const download_url = ((is_confidential || is_top_secret) && is_pdf)
    ? `/api/method/custom_fsf.custom_fsf.doctype.library.library.download_library_file?docname=${encodeURIComponent(frm.doc.name)}`
    : file_url;

  html += `
    <div style="margin-top: 10px;">
      <a class="btn btn-primary download-btn" href="${download_url}" target="_blank" download data-docname="${frm.doc.name}">
        Download File
      </a>
    </div>
  `;

  wrapper.html(html);
}

frappe.ui.form.on("Library", {
  refresh: function (frm) {
    const attach_field = frm.fields_dict["file"];

    // Override attach click to restrict file types
    attach_field.on_attach_click = function () {
      attach_field.set_upload_options();

      // Define allowed MIME types
      attach_field.upload_options.restrictions.allowed_file_types = [
        // Documents
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        // Videos
        "video/mp4",
        "video/webm",
        "video/ogg",
        // ✅ Images
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/svg+xml",
        "image/webp"
      ];

      // Launch custom FileUploader with restriction
      attach_field.file_uploader = new frappe.ui.FileUploader(attach_field.upload_options);
    };
  }
});

frappe.ui.form.on('Library', {
  refresh: function(frm) {
    toggle_file_field(frm);
  },
  file: function(frm) {
    toggle_file_field(frm);
  }
});

function toggle_file_field(frm) {
  if (frm.doc.file) {
    // Hide the file field when file is uploaded
    frm.toggle_display('file', false);
  } else {
    // Show the field if no file is attached
    frm.toggle_display('file', true);
  }
}
