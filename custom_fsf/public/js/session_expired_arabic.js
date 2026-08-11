// Fix session-timeout messages showing in English.
//
// When a session expires, Frappe's 403 handler calls frappe.msgprint()
// with the English error. We wrap frappe.msgprint to intercept and
// replace it with an Arabic dialog before it renders.

(function () {
	var lang = (frappe.boot && frappe.boot.lang) || document.documentElement.lang;
	if (lang !== "ar") return;

	// Translate titles that go through __() in the 403 handler
	Object.assign(frappe._messages, {
		"Method Not Allowed": "الطريقة غير مسموح بها",
		"Not permitted": "غير مصرح",
		"Not Permitted": "غير مصرح",
	});

	function isSessionExpiredMessage(raw) {
		var msg = $.isPlainObject(raw) ? (raw.message || "") : String(raw || "");
		return msg.indexOf("not permitted to access this resource") !== -1
			|| msg.indexOf("is not whitelisted") !== -1;
	}

	var _original = frappe.msgprint;
	frappe.msgprint = function (msg, title, is_minimizable) {
		if (isSessionExpiredMessage(msg)) {
			showExpiredDialog();
			return;
		}
		return _original.call(this, msg, title, is_minimizable);
	};
	window.msgprint = frappe.msgprint;

	var _shown = false;
	function showExpiredDialog() {
		if (_shown) return;
		_shown = true;
		frappe.hide_msgprint();

		var url = "/login?redirect-to=" +
			encodeURIComponent(window.location.pathname + window.location.search);

		var d = new frappe.ui.Dialog({
			title: "انتهت الجلسة",
			indicator: "orange",
			primary_action_label: "تسجيل الدخول",
			primary_action: function () { window.location.href = url; },
		});
		d.$body.html(
			'<p style="font-size:var(--text-base);text-align:right;">' +
			"انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى للمتابعة.</p>"
		);
		d.show();
		d.$wrapper.on("hidden.bs.modal", function () { window.location.href = url; });
	}

	// Prevent Frappe's cleanup from redirecting while our dialog is up
	$(document).on("startup", function () {
		if (!frappe.app) return;
		var _orig = frappe.app.handle_session_expired;
		frappe.app.handle_session_expired = function () {
			if (_shown) return;
			_orig.call(frappe.app);
		};
	});
})();
