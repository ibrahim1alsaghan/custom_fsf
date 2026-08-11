frappe.ui.form.on("Events", {
	event_date_gregorian(frm) {
	  const v = frm.doc.event_date_gregorian;
  
	  if (!v) {
		frm.set_value("event_date_hijri", null);
		return;
	  }
  
	  frappe.call({
		method: "custom_fsf.custom_fsf.doctype.events.events.convert_gregorian_to_hijri",
		args: { date_str: v },
		callback: (r) => frm.set_value("event_date_hijri", r.message || null),
	  });
	},
  });
  