// Fix Arabic time-ago abbreviations (pretty_date.js)
// MariaDB case-insensitive collation prevents using Translation doctype
// for "{0} m" vs "{0} M", so we fix it client-side.
$(document).on("startup", function () {
	if (frappe.boot.lang === "ar") {
		Object.assign(frappe._messages, {
			"now": "الآن",
			"{0} m": "{0} د",
			"{0} h": "{0} س",
			"{0} d": "{0} ي",
			"{0} w": "{0} أ",
			"{0} M": "{0} ش",
			"{0} y": "{0} سن",
		});
	}
});
