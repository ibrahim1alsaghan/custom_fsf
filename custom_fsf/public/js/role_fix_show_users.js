frappe.ui.form.on("Role", {
	refresh(frm) {
		// Try to remove the broken core button (different versions expose different helpers)
		try {
			frm.remove_custom_button(__("Show Users"));
		} catch (e) {}

		try {
			frm.page.remove_inner_button(__("Show Users"));
		} catch (e) {}

		// Add the fixed button
		frm.add_custom_button(__("Show Users"), async () => {
			if (!frm.doc?.name) return;

			try {
				const r = await frappe.call({
					method: "custom_fsf.utils.get_users_with_role",
					args: {
						role: frm.doc.name,
						enabled_only: 1
					}
				});

				const users = (r && r.message) || [];

				if (!users.length) {
					frappe.msgprint({
						title: __("No Users Found"),
						message: __("No enabled users currently have the role {0}.", [frm.doc.name]),
						indicator: "orange"
					});
					return;
				}

				// Route to normal User List (NOT report view) and filter by name IN users
				frappe.route_options = {
					name: ["in", users]
				};
				frappe.set_route("List", "User");
			} catch (err) {
				console.error(err);
				frappe.msgprint({
					title: __("Error"),
					message: __("Could not load users for this role. Check console/server logs."),
					indicator: "red"
				});
			}
		});
	}
});
