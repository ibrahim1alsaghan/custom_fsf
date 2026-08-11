// Copyright (c) 2025, FSF and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Ticket", {
	setup(frm) {
		// Filter assigned_to by team members
		frm.set_query("assigned_to", function() {
			if (frm.doc.assigned_team) {
				return {
					query: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.get_team_members",
					filters: {
						team: frm.doc.assigned_team
					}
				};
			}
			return {
				query: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.get_agents",
			};
		});

		// Filter ticket_type to active only
		frm.set_query("ticket_type", function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});

		// Filter category to active only
		frm.set_query("category", function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});

		// Filter priority to active only
		frm.set_query("priority", function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});

		// Filter assigned_team to active only
		frm.set_query("assigned_team", function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});

	},

	refresh(frm) {
		// Check if user is an agent
		const is_agent = frappe.user.has_role("HD Agent") ||
			frappe.user.has_role("HD Manager");
		const is_requester_new_ticket = !is_agent && frm.is_new();

		// Minimal create UX for requester: show only Subject, Description, Attachment.
		frm.toggle_display("section_basic", true);
		frm.toggle_display("subject", true);
		frm.toggle_display("section_description", true);
		frm.toggle_display("description", true);
		frm.toggle_display("section_attachments", true);
		frm.toggle_display("attachments", true);

		frm.toggle_display("requester", !is_requester_new_ticket);
		frm.toggle_display("department", !is_requester_new_ticket);
		frm.toggle_display("status", !is_requester_new_ticket);
		frm.toggle_display("channel", !is_requester_new_ticket);
		frm.toggle_display("section_classification", !is_requester_new_ticket);
		frm.toggle_display("ticket_type", !is_requester_new_ticket);
		frm.toggle_display("category", !is_requester_new_ticket);
		frm.toggle_display("priority", !is_requester_new_ticket);
		frm.toggle_display("section_resolution", !is_requester_new_ticket);
		frm.toggle_display("resolution", !is_requester_new_ticket);

		// Hide internal comments and assignment sections for non-agents
		frm.toggle_display("section_internal", is_agent);
		frm.toggle_display("section_history", is_agent);
		frm.toggle_display("section_assignment", is_agent);
		frm.toggle_display("section_sla", is_agent);

		// Keep requester UX aligned with backend guardrails.
		const restrict_agent_fields = !is_agent && !frm.is_new();
		frm.set_df_property("ticket_type", "read_only", restrict_agent_fields ? 1 : 0);
		frm.set_df_property("category", "read_only", restrict_agent_fields ? 1 : 0);
		frm.set_df_property("priority", "read_only", restrict_agent_fields ? 1 : 0);
		frm.set_df_property("assigned_team", "read_only", restrict_agent_fields ? 1 : 0);
		frm.set_df_property("assigned_to", "read_only", restrict_agent_fields ? 1 : 0);
		frm.set_df_property("resolution", "read_only", restrict_agent_fields ? 1 : 0);
		frm.set_df_property("department", "read_only", frm.is_new() ? 0 : 1);

		// Show department immediately for requester on new tickets (before first save).
		if (frm.is_new() && !frm.doc.department && !is_requester_new_ticket) {
			sync_department_from_requester(frm);
		}

		// Lock subject and description after creation (nobody can edit)
		if (!frm.is_new()) {
			frm.set_df_property("subject", "read_only", 1);
			frm.set_df_property("description", "read_only", 1);
		}

		// Render internal comments timeline for agents on saved tickets
		if (!frm.is_new() && is_agent) {
			render_internal_comments_timeline(frm);
		}

		// Agent buttons
		if (!frm.is_new() && is_agent) {
			// Add internal comment button
			frm.add_custom_button(__("Add Internal Comment"), function() {
				frappe.prompt({
					fieldname: "comment",
					fieldtype: "Text Editor",
					label: __("Comment"),
					reqd: 1
				}, function(values) {
					frappe.call({
						method: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.add_internal_comment",
						args: { ticket: frm.doc.name, comment: values.comment },
						callback: function(r) {
							if (r.message && r.message.status === "success") {
								frappe.show_alert({
									message: r.message.message,
									indicator: "green"
								});
								frm.reload_doc();
							}
						}
					});
				}, __("Add Internal Comment"), __("Add"));
			}, __("Actions"));

			// Reassign button
			frm.add_custom_button(__("Reassign"), function() {
				frappe.prompt([
					{
						fieldname: "new_agent",
						fieldtype: "Link",
						options: "User",
						label: __("New Agent"),
						get_query: () => ({
							query: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.get_team_members",
							filters: { team: "%" }
						})
					},
					{
						fieldname: "new_team",
						fieldtype: "Link",
						options: "HD Team",
						label: __("New Team"),
						filters: { is_active: 1 }
					},
					{
						fieldname: "notes",
						fieldtype: "Small Text",
						label: __("Notes")
					}
				], function(values) {
					if (!values.new_agent && !values.new_team) {
						frappe.msgprint(__("Please select a new team or a new agent."));
						return;
					}

					frappe.call({
						method: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.reassign_ticket",
						args: Object.assign({ ticket: frm.doc.name }, values),
						callback: function(r) {
							if (r.message && r.message.status === "success") {
								frappe.show_alert({
									message: r.message.message,
									indicator: "green"
								});
								frm.reload_doc();
							}
						}
					});
				}, __("Reassign Ticket"), __("Reassign"));
			}, __("Actions"));

			// Quick status change buttons (temporarily toggle read_only off to set value)
			if (frm.doc.status === "Open") {
				frm.add_custom_button(__("Start Working"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "In Progress");
					frm.save();
				}, __("Status"));
			}

			if (frm.doc.status === "In Progress") {
				frm.add_custom_button(__("Resolve"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "Resolved");
					frm.save();
				}, __("Status"));

				frm.add_custom_button(__("Need More Info"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "Need More Info");
					frm.save();
				}, __("Status"));

				frm.add_custom_button(__("Waiting Approval"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "Waiting Approval");
					frm.save();
				}, __("Status"));
			}

			if (frm.doc.status === "Need More Info" || frm.doc.status === "Waiting Approval") {
				frm.add_custom_button(__("Resume Work"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "In Progress");
					frm.save();
				}, __("Status"));
			}

			if (frm.doc.status === "Resolved") {
				frm.dashboard.add_indicator(__("Auto-close will run after 1 business day"), "orange");

				frm.add_custom_button(__("Reopen"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "In Progress");
					frm.save();
				}, __("Status"));
			}

			if (frm.doc.status === "Closed") {
				frm.add_custom_button(__("Reopen"), function() {
					frm.toggle_enable("status", true);
					frm.set_value("status", "In Progress");
					frm.save();
				}, __("Status"));
			}
		}

		// SLA indicator
		if (frm.doc.sla_status) {
			let indicator_color = "blue";
			let indicator_class = "alert-info";
			if (frm.doc.sla_status === "Fulfilled") {
				indicator_color = "green";
				indicator_class = "alert-success";
			}
			if (frm.doc.sla_status === "Breached") {
				indicator_color = "red";
				indicator_class = "alert-danger";
			}
			if (frm.doc.sla_status === "Pending") {
				// Check if SLA is about to breach
				if (frm.doc.sla_due_date) {
					const due = moment(frm.doc.sla_due_date);
					const now = moment();
					const hours_left = due.diff(now, "hours");
					if (hours_left < 0) {
						indicator_color = "red";
						indicator_class = "alert-danger";
					} else if (hours_left < 2) {
						indicator_color = "orange";
						indicator_class = "alert-warning";
					}
				}
			}

			frm.dashboard.set_headline_alert(
				`<div class="alert ${indicator_class}">
					<strong>${__("SLA Status")}:</strong> ${__(frm.doc.sla_status)}
					${frm.doc.sla_due_date ? ` | <strong>${__("Due")}:</strong> ${frappe.datetime.str_to_user(frm.doc.sla_due_date)}` : ""}
				</div>`
			);
		}

		// Show elapsed/resolve time indicator based on ticket status.
		if (frm.doc.status === "In Progress" && frm.doc.sla_start_time) {
			const started_at = frappe.datetime.str_to_obj(frm.doc.sla_start_time);
			const elapsed_minutes = Math.max(
				0,
				Math.floor((new Date().getTime() - started_at.getTime()) / 60000)
			);
			frm.dashboard.add_indicator(
				__("Working Time: {0}", [format_duration_minutes(elapsed_minutes)]),
				"blue"
			);
		}

		if (
			(frm.doc.status === "Resolved" || frm.doc.status === "Closed")
		) {
			let completed_minutes = frm.doc.resolution_time_minutes;
			if (frm.doc.sla_start_time && frm.doc.resolved_date) {
				const started_at = frappe.datetime.str_to_obj(frm.doc.sla_start_time);
				const resolved_at = frappe.datetime.str_to_obj(frm.doc.resolved_date);
				completed_minutes = Math.max(
					0,
					Math.floor((resolved_at.getTime() - started_at.getTime()) / 60000)
				);
			}

			if (completed_minutes !== null && completed_minutes !== undefined) {
				frm.dashboard.add_indicator(
					__("Resolution Time: {0}", [format_duration_minutes(completed_minutes)]),
					"blue"
				);
			}
		}

		// Field is labeled in hours; store stays in minutes, so render converted display value.
		render_solving_duration_hours(frm);
	},

	assigned_team(frm) {
		// Clear assigned_to when team changes
		frm.set_value("assigned_to", "");
	},

	priority(frm) {
		// Show SLA info when priority is selected
		if (frm.doc.priority) {
			frappe.db.get_value("HD Ticket Priority", frm.doc.priority, "resolution_time_hours")
				.then(r => {
					if (r.message && r.message.resolution_time_hours) {
						const hours = r.message.resolution_time_hours;
						let display;
						if (hours >= 24) {
							const days = Math.floor(hours / 24);
							display = __("SLA Resolution Time: {0} business day(s)", [days]);
						} else {
							display = __("SLA Resolution Time: {0} hours", [hours]);
						}
						frappe.show_alert({
							message: display,
							indicator: "blue"
						});
					}
				});
		}
	},

	requester(frm) {
		sync_department_from_requester(frm);
	}
});



function sync_department_from_requester(frm) {
	const requester = frm.doc.requester || frappe.session.user;
	if (!requester) return;

	frappe.call({
		method: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.get_requester_department",
		args: { requester: requester },
		callback: function(r) {
			if (r.message) {
				frm.set_value("department", r.message);
			}
		}
	});
}

function format_duration_minutes(total_minutes) {
	const minutes_int = Math.max(0, Math.round(Number(total_minutes) || 0));
	const hours = Math.floor(minutes_int / 60);
	const minutes = minutes_int % 60;
	if (hours > 0) {
		return `${hours} ${__("hours")} ${minutes} ${__("minutes")}`;
	}
	return `${minutes} ${__("minutes")}`;
}

function render_solving_duration_hours(frm) {
	const field = frm.fields_dict.resolution_time_minutes;
	if (!field || !field.$wrapper) return;

	const raw_minutes = Number(frm.doc.resolution_time_minutes);
	const value_el = field.$wrapper.find(".control-value");
	if (!value_el || !value_el.length) return;

	if (frm.doc.resolution_time_minutes === null || frm.doc.resolution_time_minutes === undefined || Number.isNaN(raw_minutes)) {
		return;
	}

	const hours = raw_minutes / 60;
	// Display in 0.5-hour units for SLA field UX (e.g., 5 minutes -> 0.5).
	const rounded_half_hour = hours > 0 ? Math.max(0.5, Math.ceil(hours * 2) / 2) : 0;
	const hours_text = Number.isInteger(rounded_half_hour)
		? String(rounded_half_hour)
		: rounded_half_hour.toFixed(1).replace(/\.?0+$/, "");
	value_el.text(hours_text);
}

function render_internal_comments_timeline(frm) {
	const wrapper = frm.fields_dict.internal_comments_html;
	if (!wrapper) return;

	const comments = (frm.doc.internal_comments || []).slice().sort(
		(a, b) => new Date(a.commented_on) - new Date(b.commented_on)
	);

	let html = `<style>
		.hd-comments-timeline { padding: 0; }
		.hd-comment-entry {
			display: flex;
			gap: 12px;
			padding: 12px 0;
			border-bottom: 1px solid var(--border-color);
		}
		.hd-comment-entry:last-child { border-bottom: none; }
		.hd-comment-avatar {
			flex-shrink: 0;
			width: 32px;
			height: 32px;
			border-radius: 50%;
			background: var(--bg-blue);
			color: var(--text-on-blue);
			display: flex;
			align-items: center;
			justify-content: center;
			font-weight: 600;
			font-size: 13px;
		}
		.hd-comment-body { flex: 1; min-width: 0; }
		.hd-comment-header {
			display: flex;
			align-items: center;
			gap: 8px;
			margin-bottom: 4px;
		}
		.hd-comment-author { font-weight: 600; font-size: 13px; }
		.hd-comment-time { color: var(--text-muted); font-size: 12px; }
		.hd-comment-edit-btn {
			margin-left: auto;
			cursor: pointer;
			color: var(--text-muted);
			font-size: 12px;
		}
		.hd-comment-edit-btn:hover { color: var(--text-color); }
		.hd-comment-text { font-size: 13px; line-height: 1.5; }
		.hd-comment-text img { max-width: 100%; }
		.hd-comments-empty {
			color: var(--text-muted);
			font-size: 13px;
			padding: 12px 0;
		}
	</style>`;

	html += `<div class="hd-comments-timeline">`;

	if (!comments.length) {
		html += `<div class="hd-comments-empty">${__("No internal comments yet.")}</div>`;
	}

	comments.forEach(function(c) {
		const full_name = frappe.user.full_name(c.commented_by) || c.commented_by;
		const initials = full_name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
		const time_ago = frappe.datetime.prettyDate(c.commented_on);
		const abs_time = frappe.datetime.str_to_user(c.commented_on);
		const is_own = c.commented_by === frappe.session.user;

		html += `<div class="hd-comment-entry">
			<div class="hd-comment-avatar">${initials}</div>
			<div class="hd-comment-body">
				<div class="hd-comment-header">
					<span class="hd-comment-author">${frappe.utils.escape_html(full_name)}</span>
					<span class="hd-comment-time" title="${abs_time}">${time_ago}</span>
					${is_own ? `<span class="hd-comment-edit-btn" data-name="${c.name}" title="${__("Edit")}">
						<svg class="icon icon-sm"><use href="#icon-edit"></use></svg>
					</span>` : ""}
				</div>
				<div class="hd-comment-text">${c.comment}</div>
			</div>
		</div>`;
	});

	html += `</div>`;

	wrapper.$wrapper.html(html);

	// Bind edit handlers
	wrapper.$wrapper.find(".hd-comment-edit-btn").on("click", function() {
		const row_name = $(this).data("name");
		const row = frm.doc.internal_comments.find(r => r.name === row_name);
		if (!row) return;

		const d = new frappe.ui.Dialog({
			title: __("Edit Internal Comment"),
			fields: [{
				fieldname: "comment",
				fieldtype: "Text Editor",
				label: __("Comment"),
				reqd: 1,
				default: row.comment
			}],
			primary_action_label: __("Save"),
			primary_action(values) {
				row.comment = values.comment;
				frm.dirty();
				frm.save().then(() => {
					d.hide();
					render_internal_comments_timeline(frm);
				});
			}
		});
		d.show();
	});
}
