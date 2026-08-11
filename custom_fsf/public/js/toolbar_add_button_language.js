frappe.after_ajax(() => {
	const LANG_ID = "custom-lang-switcher";
	const STYLE_ID = "custom-lang-switcher-style";

	// Inject a stylesheet once so the color rule wins regardless of nav-link
	// defaults or inline-style cache quirks.
	if (!document.getElementById(STYLE_ID)) {
		const style = document.createElement("style");
		style.id = STYLE_ID;
		style.textContent = `
			#custom-lang-switcher .nav-link,
			#custom-lang-switcher .nav-link span,
			#custom-lang-switcher .nav-link svg {
				color: #f9fafb !important;
				stroke: #f9fafb !important;
				fill: none !important;
			}
		`;
		document.head.appendChild(style);
	}

	const inject = () => {
		// Remove any previously-injected switcher (including the old
		// non-navbar-nav version that used to be appended directly to <header>).
		const existing = document.getElementById(LANG_ID);
		if (existing) {
			if (existing.tagName === "LI") return; // already placed correctly
			existing.remove();
		}

		// Insert the switcher as a sibling <li> inside the existing navbar-nav
		// so it sits on the same flex row as the notifications bell, help menu,
		// and user avatar — vertically centered with them automatically.
		const navbar_nav = document.querySelector(
			"header.navbar.navbar-expand .navbar-collapse ul.navbar-nav"
		);
		if (!navbar_nav) {
			return;
		}

		const currentLang = frappe.boot.user.language;
		const targetLang = currentLang === "ar" ? "en" : "ar";
		const label = currentLang === "ar" ? "English" : "عربي";

		const li = document.createElement("li");
		li.id = LANG_ID;
		li.className = "nav-item d-none d-lg-block";

		const btn = document.createElement("button");
		btn.className = "btn-reset nav-link";
		btn.setAttribute("aria-label", "Language Switcher");
		btn.style.cssText = `
			display: inline-flex;
			align-items: center;
			gap: 4px;
			background: none;
			border: none;
			color: #f9fafb !important;
			font-size: 13px;
			font-weight: 500;
			cursor: pointer;
		`;

		btn.innerHTML = `
			<span style="color:#f9fafb;">${label}</span>
			<svg class="es-icon icon-xs" style="color:#f9fafb; stroke:#f9fafb;"><use href="#es-line-translate"></use></svg>
		`;

		btn.onclick = () => {
			frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "User",
					name: frappe.session.user,
					fieldname: "language",
					value: targetLang
				},
				callback: () => {
					frappe.msgprint(__('Language updated. Reloading...'));
					setTimeout(() => location.reload(), 1000);
				}
			});
		};

		li.appendChild(btn);

		// Insert just before the user-avatar dropdown so it appears next to it.
		const user_li = navbar_nav.querySelector("li.dropdown-navbar-user");
		if (user_li) {
			navbar_nav.insertBefore(li, user_li);
		} else {
			navbar_nav.appendChild(li);
		}
	};

	inject();

	const observer = new MutationObserver(inject);
	observer.observe(document.body, { childList: true, subtree: true });
});
