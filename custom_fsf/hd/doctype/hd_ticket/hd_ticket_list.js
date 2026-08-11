frappe.listview_settings["HD Ticket"] = {
	add_fields: ["status", "priority", "resolution_time_minutes", "requester", "assigned_to", "resolved_by"],

	onload: function (listview) {
		// Hide sensitive filter controls from non-agent users. Requesters only
		// ever see their own tickets, so exposing the Requester / Assigned To
		// / Team / Assigned By etc. filters would leak other users' identities
		// through the link autocomplete.
		const AGENT_ROLES = ["HD Manager", "HD Agent"];
		const is_agent = frappe.user_roles && frappe.user_roles.some((r) => AGENT_ROLES.includes(r));
		if (is_agent) return;

		const HIDDEN_FIELDS = [
			"requester",
			"assigned_to",
			"assigned_team",
			"assigned_by",
			"resolved_by",
			"_assign",
			"owner",
		];

		const hide_fields = () => {
			const $page = listview.page && listview.page.wrapper ? $(listview.page.wrapper) : $(document);
			HIDDEN_FIELDS.forEach((fieldname) => {
				$page
					.find(
						`.filter-section [data-fieldname="${fieldname}"],
						 .standard-filter-section [data-fieldname="${fieldname}"],
						 .filter-selector [data-fieldname="${fieldname}"],
						 .page-form [data-fieldname="${fieldname}"]`
					)
					.closest(".frappe-control, .form-group, .standard-filter-item")
					.hide();
			});
			// Also hide the sidebar "Filter By" Assigned/Created-By dropdowns.
			$page.find(".list-sidebar .assigned-to-filter").hide();
		};

		hide_fields();
		// Frappe re-renders the filter section on refresh; re-run then too.
		listview.$result && listview.$result.on("render-complete", hide_fields);
		$(document).on("page-change", hide_fields);
	},

	get_indicator: function (doc) {
		const status_map = {
			"Open": [__("Open"), "orange", "status,=,Open"],
			"In Progress": [__("In Progress"), "blue", "status,=,In Progress"],
			"Need More Info": [__("Need More Info"), "yellow", "status,=,Need More Info"],
			"Waiting Approval": [__("Waiting Approval"), "yellow", "status,=,Waiting Approval"],
			"Resolved": [__("Resolved"), "green", "status,=,Resolved"],
			"Closed": [__("Closed"), "darkgrey", "status,=,Closed"],
		};
		return status_map[doc.status] || [__(doc.status), "grey", "status,=," + doc.status];
	},

	formatters: {
		resolution_time_minutes: function (value) {
			if (!value) return "";
			return (value / 60).toFixed(1);
		},
	},
};
