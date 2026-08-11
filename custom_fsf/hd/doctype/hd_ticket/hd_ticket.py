# Copyright (c) 2025, FSF and contributors
# For license information, please see license.txt

"""
Help Desk Ticket System for FSF Custom App

This module provides comprehensive ticket management functionality including:
- Ticket lifecycle management (creation, assignment, resolution, closure)
- SLA tracking and evaluation (with business day support)
- Assignment history logging
- Notifications for stakeholders (in-app and email)
- Permission-based filtering
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date, get_datetime, time_diff_in_seconds


# Weekend days in Saudi Arabia: Friday (4) and Saturday (5) per Python weekday()
SA_WEEKEND_DAYS = (4, 5)
AGENT_ROLES = {"HD Agent", "HD Manager"}
AGENT_ONLY_FIELDS = (
	"ticket_type",
	"category",
	"priority",
	"assigned_team",
	"assigned_to",
	"resolution",
)

def add_business_days(start_date, days):
	"""Add business days to a date, skipping Saudi weekends (Fri-Sat).

	Args:
		start_date: The starting datetime.
		days: Number of business days to add.

	Returns:
		datetime: The resulting datetime after adding business days.
	"""
	current = get_datetime(start_date)
	added = 0
	while added < days:
		current = add_to_date(current, days=1)
		if current.weekday() not in SA_WEEKEND_DAYS:
			added += 1
	return current


def is_business_day(dt):
	"""Check if a given datetime falls on a business day (Sun-Thu)."""
	return get_datetime(dt).weekday() not in SA_WEEKEND_DAYS


def has_agent_role(user=None):
	"""Check whether a user has any help desk agent-level role."""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	return bool(roles.intersection(AGENT_ROLES))


def is_active_team_member(team, user, reference_date=None):
	"""Return True when user is an active team member for the given date."""
	if not team or not user:
		return False

	reference_date = reference_date or frappe.utils.today()
	return bool(
		frappe.db.sql(
			"""
			SELECT name
			FROM `tabHD Team Member`
			WHERE team = %(team)s
				AND user = %(user)s
				AND is_active = 1
				AND (start_date IS NULL OR start_date <= %(reference_date)s)
				AND (end_date IS NULL OR end_date >= %(reference_date)s)
			LIMIT 1
			""",
			{
				"team": team,
				"user": user,
				"reference_date": reference_date,
			},
		)
	)


def get_user_active_teams(user, reference_date=None):
	"""Get all currently active teams for a user."""
	reference_date = reference_date or frappe.utils.today()
	rows = frappe.db.sql(
		"""
		SELECT team
		FROM `tabHD Team Member`
		WHERE user = %(user)s
			AND is_active = 1
			AND (start_date IS NULL OR start_date <= %(reference_date)s)
			AND (end_date IS NULL OR end_date >= %(reference_date)s)
		""",
		{"user": user, "reference_date": reference_date},
		as_dict=True,
	)
	return [row.team for row in rows]


def get_user_active_teams_members(team, reference_date=None):
	"""Get all active members (user emails) of a specific team."""
	reference_date = reference_date or frappe.utils.today()
	rows = frappe.db.sql(
		"""
		SELECT user
		FROM `tabHD Team Member`
		WHERE team = %(team)s
			AND is_active = 1
			AND (start_date IS NULL OR start_date <= %(reference_date)s)
			AND (end_date IS NULL OR end_date >= %(reference_date)s)
		""",
		{"team": team, "reference_date": reference_date},
		as_dict=True,
	)
	return [row.user for row in rows]


def get_employee_department(user):
	"""Get department from Employee mapped to a user."""
	if not user:
		return None

	return frappe.db.get_value("Employee", {"user_id": user}, "department")


def get_user_language(user):
	"""Return preferred language for a user, falling back to current locale."""
	if not user:
		return frappe.local.lang or "en"
	return frappe.db.get_value("User", user, "language") or frappe.local.lang or "en"


@frappe.whitelist()
def get_requester_department(requester=None):
	"""Return employee department for a requester (used by form UX)."""
	requester = requester or frappe.session.user
	return get_employee_department(requester)


class HDTicket(Document):
	"""Main HD Ticket document class."""

	def before_insert(self):
		"""Set default values before first save."""
		self.requester = self.requester or frappe.session.user
		self.created_by = frappe.session.user
		self.channel = self.channel or "Portal"

		# Set default type and category if not specified
		if not self.ticket_type:
			default_type = frappe.db.get_value("HD Ticket Type", {"type_name": "Unspecified"})
			if default_type:
				self.ticket_type = default_type

		if not self.category:
			default_category = frappe.db.get_value("HD Ticket Category", {"category_name": "Unspecified"})
			if default_category:
				self.category = default_category

		# Set default priority if not specified
		if not self.priority:
			default_priority = frappe.db.get_value("HD Ticket Priority", {"priority_name": "Medium"})
			if default_priority:
				self.priority = default_priority

	def before_save(self):
		"""Validation and processing before save."""
		self.updated_by = frappe.session.user

		# Track assignment changes (before status change so auto In Progress works)
		if self.has_value_changed("assigned_to") or self.has_value_changed("assigned_team"):
			self._handle_assignment_change()

		# Track status changes for SLA
		if self.has_value_changed("status"):
			self._handle_status_change()

		# Recalculate SLA if priority changes after SLA has started
		if (
			self.has_value_changed("priority")
			and self.sla_start_time
			and self.status not in ("Resolved", "Closed")
		):
			self._recalculate_sla()

	def after_insert(self):
		"""Actions after ticket creation."""
		# Notify assigned agent if ticket is assigned on creation
		if self.assigned_to and not getattr(self.flags, "assignee_notified", False):
			self._notify_assignee()

	def on_update(self):
		"""Actions after ticket update."""
		# Check if status changed
		if self.has_value_changed("status"):
			self._notify_requester_status_change()

		# Notify requester on reassignment when status didn't change
		elif getattr(self.flags, "assignment_changed", False):
			self._notify_requester_assignment()

	def validate(self):
		"""Validate ticket data."""
		self._validate_new_ticket_restrictions()
		self._validate_status_change()
		self._validate_status_transitions()
		self._validate_in_progress_requires_assignment()
		self._validate_subject_description_immutable()
		self._validate_agent_only_fields()
		self._validate_assignment()
		self._validate_closed_ticket()
		self._validate_internal_comments_not_deleted()
		self._validate_close_transition()


	def _validate_status_change(self):
		"""Prevent non-agent users from changing ticket status."""
		if not self.get_doc_before_save():
			return
		if getattr(self.flags, "allow_auto_status_change", False):
			return
		old_status = self.get_doc_before_save().status
		if old_status != self.status and not has_agent_role():
			frappe.throw(_("Only agents can change ticket status."))

	def _validate_new_ticket_restrictions(self):
		"""Harden insert path so requesters cannot bypass agent-only controls."""
		if self.get_doc_before_save() or has_agent_role():
			return

		if (self.status or "Open") != "Open":
			frappe.throw(_("New tickets must start with status Open."))

		if self.assigned_to or self.assigned_team:
			frappe.throw(_("Only agents can assign tickets."))

		if self.resolution:
			frappe.throw(_("Resolution notes can only be added by agents during ticket handling."))

		if self.internal_comments:
			frappe.throw(_("Internal comments are agent-only."))

		if self.assignment_history:
			frappe.throw(_("Assignment history is system-managed and cannot be set manually."))

		system_fields = [
			"sla_start_time",
			"sla_due_date",
			"sla_status",
			"resolution_time_minutes",
			"resolved_date",
			"resolved_by",
			"assigned_date",
			"assigned_by",
		]
		if any(self.get(field) for field in system_fields):
			frappe.throw(_("System tracking fields cannot be set during ticket creation."))

	def _validate_status_transitions(self):
		"""Enforce valid status transition paths on the backend."""
		old_doc = self.get_doc_before_save()
		if not old_doc or old_doc.status == self.status:
			return

		valid_transitions = {
			"Open": {"In Progress"},
			"In Progress": {"Resolved", "Need More Info", "Waiting Approval"},
			"Need More Info": {"In Progress"},
			"Waiting Approval": {"In Progress"},
			"Resolved": {"In Progress", "Closed"},
			"Closed": {"In Progress"},
		}

		allowed = valid_transitions.get(old_doc.status, set())
		if self.status not in allowed:
			frappe.throw(
				_("Cannot change status from {0} to {1}. Allowed transitions: {2}").format(
					old_doc.status, self.status, ", ".join(sorted(allowed)) or _("None")
				)
			)

	def _validate_in_progress_requires_assignment(self):
		"""A ticket can only move to "In Progress" once it has been assigned
		to a team or an individual agent."""
		old_doc = self.get_doc_before_save()
		old_status = old_doc.status if old_doc else None
		if self.status != "In Progress" or old_status == "In Progress":
			return

		if not (self.assigned_team or self.assigned_to):
			frappe.throw(
				_("Please assign this ticket to a team or an agent before moving it to In Progress")
			)

	def _validate_agent_only_fields(self):
		"""Allow only agents to update classification/assignment fields after creation."""
		if not self.get_doc_before_save() or has_agent_role():
			return

		changed_fields = [field for field in AGENT_ONLY_FIELDS if self.has_value_changed(field)]
		if changed_fields:
			frappe.throw(_("Only agents can update ticket classification or assignment fields."))

	def _validate_subject_description_immutable(self):
		"""Prevent anyone from editing subject or description after ticket creation."""
		if not self.get_doc_before_save():
			return

		if self.has_value_changed("subject"):
			frappe.throw(_("Ticket subject cannot be changed after creation."))

		if self.has_value_changed("description"):
			frappe.throw(_("Ticket description cannot be changed after creation."))

	def _validate_assignment(self):
		"""Validate that assigned_to is a member of assigned_team if both are set."""
		if self.assigned_team and self.assigned_to:
			if not is_active_team_member(self.assigned_team, self.assigned_to):
				frappe.throw(_("Assigned agent must be a member of the selected team."))

	def _validate_closed_ticket(self):
		"""Prevent modifications to closed tickets by non-agents."""
		if self.get_doc_before_save():
			old_status = self.get_doc_before_save().status
			if old_status == "Closed" and not has_agent_role():
				frappe.throw(_("Closed tickets cannot be modified."))

	def _validate_close_transition(self):
		"""Allow closing only after resolved state and 1 business day delay."""
		old_doc = self.get_doc_before_save()
		if not old_doc or old_doc.status == self.status or self.status != "Closed":
			return

		if old_doc.status != "Resolved":
			frappe.throw(_("Ticket can only be closed after it is resolved."))

		resolved_on = old_doc.resolved_date or self.resolved_date
		if not resolved_on:
			frappe.throw(_("Resolved Date is required before closing ticket."))

		close_after = add_business_days(resolved_on, 1)
		if get_datetime(now_datetime()) < get_datetime(close_after):
			frappe.throw(_("Ticket can be closed only after 1 business day from resolution."))

	def _validate_internal_comments_not_deleted(self):
		"""Allow editing own comments only; block deletion for audit reliability."""
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		old_snapshot = [
			(row.name, row.comment, row.commented_by, str(row.commented_on))
			for row in (old_doc.internal_comments or [])
		]
		new_snapshot = [
			(row.name, row.comment, row.commented_by, str(row.commented_on))
			for row in (self.internal_comments or [])
		]

		if old_snapshot != new_snapshot and not has_agent_role():
			frappe.throw(_("Only agents can add or edit internal comments."))

		# Only the comment author can edit their own comment
		old_by_name = {row.name: row for row in (old_doc.internal_comments or []) if row.name}
		for row in (self.internal_comments or []):
			if row.name in old_by_name:
				old_row = old_by_name[row.name]
				if row.comment != old_row.comment and row.commented_by != frappe.session.user:
					frappe.throw(_("You can only edit your own comments."))

		old_names = {row.name for row in (old_doc.internal_comments or []) if row.name}
		new_names = {row.name for row in (self.internal_comments or []) if row.name}

		if old_names - new_names:
			frappe.throw(_("Internal comments cannot be deleted. You can edit existing comments instead."))

	def _handle_status_change(self):
		"""Handle status transitions and SLA tracking."""
		old_doc = self.get_doc_before_save()
		old_status = old_doc.status if old_doc else None
		new_status = self.status

		# Start SLA when moving to "In Progress"
		if new_status == "In Progress" and old_status != "In Progress":
			self._start_sla()

		# Evaluate SLA when resolving
		if new_status == "Resolved" and old_status != "Resolved":
			self._evaluate_sla()
			self.resolved_date = now_datetime()
			self.resolved_by = frappe.session.user

		# Reopened ticket should not keep stale resolver identity.
		if new_status == "In Progress" and old_status in {"Resolved", "Closed"}:
			self.resolved_by = None

	def _start_sla(self):
		"""Start SLA timer and calculate due date."""
		if not self.sla_start_time:
			self.sla_start_time = now_datetime()

		if self.priority:
			self._calculate_sla_due_date()

	def _calculate_sla_due_date(self):
		"""Calculate SLA due date based on priority.

		Uses calendar hours for short SLAs (< 24 hours) and
		business days (Sun-Thu) for longer SLAs (>= 24 hours).
		"""
		if not self.priority:
			return

		resolution_hours = frappe.db.get_value(
			"HD Ticket Priority",
			self.priority,
			"resolution_time_hours"
		)
		if resolution_hours:
			start_time = self.sla_start_time or now_datetime()

			if resolution_hours >= 24:
				# Convert to business days for multi-day SLAs
				business_days = int(resolution_hours / 24)
				self.sla_due_date = add_business_days(start_time, business_days)
			else:
				# Use calendar hours for intra-day SLAs (Urgent, High)
				self.sla_due_date = add_to_date(start_time, hours=resolution_hours)

			self.sla_status = "Pending"

	def _recalculate_sla(self):
		"""Recalculate SLA when priority changes."""
		if self.sla_start_time and self.priority:
			self._calculate_sla_due_date()

	def _evaluate_sla(self):
		"""Evaluate SLA fulfillment on resolution."""
		now = now_datetime()

		# Solving duration starts when work actually starts ("In Progress").
		start_time = self.sla_start_time or self.creation
		self.resolution_time_minutes = max(
			0,
			int(
				time_diff_in_seconds(now, get_datetime(start_time)) / 60
			),
		)

		# SLA evaluation: compare resolution moment against SLA due date
		if not self.sla_start_time or not self.sla_due_date:
			return

		if get_datetime(now) <= get_datetime(self.sla_due_date):
			self.sla_status = "Fulfilled"
		else:
			self.sla_status = "Breached"

	def _handle_assignment_change(self):
		"""Log assignment changes, update related fields, and auto-transition status."""
		old_doc = self.get_doc_before_save()
		old_assigned_to = old_doc.assigned_to if old_doc else None
		old_assigned_team = old_doc.assigned_team if old_doc else None

		assignment_changed = self.assigned_to != old_assigned_to or self.assigned_team != old_assigned_team
		if not assignment_changed:
			return

		# Log unassignment when both agent and team are cleared
		if not (self.assigned_to or self.assigned_team):
			self.append("assignment_history", {
				"assigned_to": None,
				"assigned_team": None,
				"assigned_by": frappe.session.user,
				"assigned_date": now_datetime(),
				"notes": _("Unassigned by {0}").format(frappe.session.user),
			})
			return

		self.assigned_date = now_datetime()
		self.assigned_by = frappe.session.user
		self.flags.assignment_changed = True

		# Auto-transition to "In Progress" when assigned from "Open"
		if self.status == "Open":
			self.status = "In Progress"

		# Add to assignment history
		notes = getattr(self, "_reassign_notes", None) or _("Assigned by {0}").format(frappe.session.user)
		self.append("assignment_history", {
			"assigned_to": self.assigned_to,
			"assigned_team": self.assigned_team,
			"assigned_by": frappe.session.user,
			"assigned_date": now_datetime(),
			"notes": notes
		})

		# Notify new assignee when assignment changed to a new user
		if self.assigned_to and self.assigned_to != old_assigned_to:
			self._notify_assignee()
			self.flags.assignee_notified = True

		# Notify team members when assigned to a team without a specific agent
		if not self.assigned_to and self.assigned_team and self.assigned_team != old_assigned_team:
			self._notify_team_assignment()

	def _ensure_agent_action_allowed(self):
		"""Enforce agent-only actions for whitelisted methods."""
		if not has_agent_role():
			frappe.throw(_("Only agents can perform this action."), frappe.PermissionError)

	def _notify_assignee(self):
		"""Send in-app notification and email to assigned agent."""
		if not self.assigned_to:
			return

		recipient = self.assigned_to
		recipient_lang = get_user_language(recipient)
		subject = _("Ticket {0} has been assigned to you", lang=recipient_lang).format(self.name)

		# In-app notification
		try:
			from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

			notification = frappe._dict({
				"subject": subject,
				"from_user": frappe.session.user,
				"type": "Alert",
				"document_type": self.doctype,
				"document_name": self.name
			})
			make_notification_logs(notification, [recipient])
		except Exception:
			frappe.log_error("Failed to send assignment notification", "HD Ticket Notification Error")

		# Email notification
		try:
			frappe.sendmail(
				recipients=[recipient],
				subject=subject,
				message=_(
					"<p>Ticket <strong>{0}</strong> has been assigned to you.</p>"
					"<p><strong>Subject:</strong> {1}</p>"
					"<p><strong>Priority:</strong> {2}</p>"
					"<p><strong>Requester:</strong> {3}</p>"
					"<p><a href='{4}'>View Ticket</a></p>"
				, lang=recipient_lang).format(
					self.name,
					self.subject,
					self.priority or _("Not set", lang=recipient_lang),
					self.requester,
					frappe.utils.get_url_to_form(self.doctype, self.name)
				),
				reference_doctype=self.doctype,
				reference_name=self.name
			)
		except Exception:
			frappe.log_error("Failed to send assignment email", "HD Ticket Email Error")

	def _notify_team_assignment(self):
		"""Notify all active members of assigned team when ticket is assigned to team only."""
		if not self.assigned_team:
			return

		members = get_user_active_teams_members(self.assigned_team)
		if not members:
			return

		# Exclude the user who made the assignment
		recipients = [m for m in members if m != frappe.session.user]
		if not recipients:
			return

		for recipient in recipients:
			recipient_lang = get_user_language(recipient)
			subject = _("Ticket {0} has been assigned to your team {1}", lang=recipient_lang).format(
				self.name, self.assigned_team
			)

			# In-app notification
			try:
				from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

				notification = frappe._dict({
					"subject": subject,
					"from_user": frappe.session.user,
					"type": "Alert",
					"document_type": self.doctype,
					"document_name": self.name,
				})
				make_notification_logs(notification, [recipient])
			except Exception:
				frappe.log_error("Failed to send team assignment notification", "HD Ticket Notification Error")

			# Email notification
			try:
				frappe.sendmail(
					recipients=[recipient],
					subject=subject,
					message=_(
						"<p>Ticket <strong>{0}</strong> has been assigned to team <strong>{1}</strong>.</p>"
						"<p><strong>Subject:</strong> {2}</p>"
						"<p><strong>Priority:</strong> {3}</p>"
						"<p><strong>Requester:</strong> {4}</p>"
						"<p><a href='{5}'>View Ticket</a></p>"
					, lang=recipient_lang).format(
						self.name,
						self.assigned_team,
						self.subject,
						self.priority or _("Not set", lang=recipient_lang),
						self.requester,
						frappe.utils.get_url_to_form(self.doctype, self.name),
					),
					reference_doctype=self.doctype,
					reference_name=self.name,
				)
			except Exception:
				frappe.log_error("Failed to send team assignment email", "HD Ticket Email Error")

	def _get_assignee_display(self, lang=None):
		"""Return display name for the current assignee: agent full name or team name."""
		if self.assigned_to:
			return frappe.db.get_value("User", self.assigned_to, "full_name") or self.assigned_to
		if self.assigned_team:
			return self.assigned_team
		return ""

	def _build_assignee_line(self, lang=None):
		"""Build HTML line for assigned-to display in emails."""
		assignee = self._get_assignee_display(lang=lang)
		if not assignee:
			return ""
		return _(
			"<p><strong>Assigned To:</strong> {0}</p>", lang=lang
		).format(assignee)

	def _notify_requester_status_change(self):
		"""Notify requester via in-app notification and email when ticket status changes."""
		if not self.requester:
			return

		recipient = self.requester
		recipient_lang = get_user_language(recipient)
		localized_status = _(self.status, lang=recipient_lang)
		subject = _("Ticket {0} status changed to {1}", lang=recipient_lang).format(
			self.name, localized_status
		)

		# In-app notification — include assignee when present
		assignee = self._get_assignee_display(lang=recipient_lang)
		in_app_subject = subject
		if assignee:
			in_app_subject = _("Ticket {0} status changed to {1} - Assigned to {2}", lang=recipient_lang).format(
				self.name, localized_status, assignee
			)

		try:
			from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

			notification = frappe._dict({
				"subject": in_app_subject,
				"from_user": frappe.session.user,
				"type": "Alert",
				"document_type": self.doctype,
				"document_name": self.name
			})
			make_notification_logs(notification, [recipient])
		except Exception:
			frappe.log_error("Failed to send status change notification", "HD Ticket Notification Error")

		# Email notification
		try:
			frappe.sendmail(
				recipients=[recipient],
				subject=subject,
				message=_(
					"<p>Your ticket <strong>{0}</strong> status has been updated.</p>"
					"<p><strong>Subject:</strong> {1}</p>"
					"<p><strong>New Status:</strong> {2}</p>"
				, lang=recipient_lang).format(
					self.name,
					self.subject,
					localized_status,
				) + self._build_assignee_line(lang=recipient_lang) + _(
					"<p><a href='{0}'>View Ticket</a></p>", lang=recipient_lang
				).format(
					frappe.utils.get_url_to_form(self.doctype, self.name)
				),
				reference_doctype=self.doctype,
				reference_name=self.name
			)
		except Exception:
			frappe.log_error("Failed to send status change email", "HD Ticket Email Error")

	def _notify_requester_assignment(self):
		"""Notify requester when ticket is reassigned (without status change)."""
		if not self.requester:
			return

		assignee = self._get_assignee_display()
		if not assignee:
			return

		recipient = self.requester
		recipient_lang = get_user_language(recipient)
		subject = _("Ticket {0} has been assigned to {1}", lang=recipient_lang).format(
			self.name, assignee
		)

		# In-app notification
		try:
			from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

			notification = frappe._dict({
				"subject": subject,
				"from_user": frappe.session.user,
				"type": "Alert",
				"document_type": self.doctype,
				"document_name": self.name
			})
			make_notification_logs(notification, [recipient])
		except Exception:
			frappe.log_error("Failed to send assignment notification to requester", "HD Ticket Notification Error")

		# Email notification
		try:
			frappe.sendmail(
				recipients=[recipient],
				subject=subject,
				message=_(
					"<p>Your ticket <strong>{0}</strong> has been reassigned.</p>"
					"<p><strong>Subject:</strong> {1}</p>"
				, lang=recipient_lang).format(
					self.name,
					self.subject,
				) + self._build_assignee_line(lang=recipient_lang) + _(
					"<p><a href='{0}'>View Ticket</a></p>", lang=recipient_lang
				).format(
					frappe.utils.get_url_to_form(self.doctype, self.name)
				),
				reference_doctype=self.doctype,
				reference_name=self.name
			)
		except Exception:
			frappe.log_error("Failed to send assignment email to requester", "HD Ticket Email Error")

	@frappe.whitelist()
	def add_internal_comment(self, comment):
		"""Add internal comment to ticket (agent use only)."""
		self._ensure_agent_action_allowed()
		self.append("internal_comments", {
			"comment": comment,
			"commented_by": frappe.session.user,
			"commented_on": now_datetime(),
		})
		self.save(ignore_permissions=True)
		return {"status": "success", "message": _("Comment added successfully")}

	@frappe.whitelist()
	def reassign_ticket(self, new_agent=None, new_team=None, notes=None):
		"""Reassign ticket to a different agent/team."""
		self._ensure_agent_action_allowed()

		if not new_agent and not new_team:
			frappe.throw(_("Please select a new team or a new agent for reassignment."))

		if new_team:
			self.assigned_team = new_team
		if new_agent:
			self.assigned_to = new_agent
		elif new_team and self.assigned_to and not is_active_team_member(new_team, self.assigned_to):
			# Keep assignment valid when only team is changed.
			self.assigned_to = None
			notes = (notes or "") + _(" (Agent cleared - not a member of team {0})").format(new_team)

		# Store notes so _handle_assignment_change() can use them
		self._reassign_notes = notes

		self.save()
		return {"status": "success", "message": _("Ticket reassigned successfully")}


@frappe.whitelist()
def add_internal_comment(ticket, comment):
	"""Whitelisted wrapper so JS frappe.call can invoke by full path."""
	doc = frappe.get_doc("HD Ticket", ticket)
	return doc.add_internal_comment(comment)


@frappe.whitelist()
def reassign_ticket(ticket, new_agent=None, new_team=None, notes=None):
	"""Whitelisted wrapper so JS frappe.call can invoke by full path."""
	doc = frappe.get_doc("HD Ticket", ticket)
	return doc.reassign_ticket(new_agent=new_agent, new_team=new_team, notes=notes)


def hd_ticket_permission_query(user):
	"""
	Permission query to filter tickets:
	- Requesters see only their own tickets
	- HD Agents and HD Managers see all tickets
	"""
	if not user:
		user = frappe.session.user

	roles = set(frappe.get_roles(user))

	# Agent/Manager roles can see all tickets in list view.
	if roles.intersection(AGENT_ROLES):
		return ""

	conditions = []

	# Requester can see their own tickets
	conditions.append(f"`tabHD Ticket`.requester = {frappe.db.escape(user)}")

	if not conditions:
		return "1=0"  # No access

	return "(" + " OR ".join(conditions) + ")"


def hd_ticket_has_permission(doc, ptype, user):
	"""Check if user has permission to access the ticket."""
	if not user:
		user = frappe.session.user

	roles = set(frappe.get_roles(user))

	# Agent/Manager roles have full document access.
	if roles.intersection(AGENT_ROLES):
		return True

	# Requester can access their own tickets
	if doc.requester == user:
		return True

	return False


def auto_close_resolved_tickets():
	"""
	Auto-close resolved tickets after 1 business day.
	Runs as a scheduled task (hourly). The add_business_days() math already
	accounts for Saudi weekends (Fri-Sat), so there is no need to skip
	running on non-business days.
	"""
	now = now_datetime()

	resolved_tickets = frappe.get_all("HD Ticket",
		filters={
			"status": "Resolved",
			"resolved_date": ["is", "set"]
		},
		fields=["name", "resolved_date"]
	)

	for ticket_data in resolved_tickets:
		try:
			resolved_dt = get_datetime(ticket_data.resolved_date)
			# Calculate 1 business day after resolution
			close_after = add_business_days(resolved_dt, 1)

			if get_datetime(now) >= close_after:
				ticket = frappe.get_doc("HD Ticket", ticket_data.name)
				ticket.status = "Closed"
				ticket.save(ignore_permissions=True)
				frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Error auto-closing ticket {ticket_data.name}: {str(e)}",
				"HD Ticket Auto-Close Error")


def check_and_notify_overdue_tickets():
	"""
	Mark tickets as SLA breached when due date is exceeded and notify assigned agent once.
	Runs hourly.
	"""
	now = now_datetime()

	overdue_rows = frappe.db.sql(
		"""
		SELECT name
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Resolved', 'Closed')
			AND sla_due_date IS NOT NULL
			AND sla_due_date < %(now)s
			AND IFNULL(sla_status, '') IN ('', 'Pending')
		""",
		{"now": now},
		as_dict=True,
	)

	for row in overdue_rows:
		try:
			ticket = frappe.get_doc("HD Ticket", row.name)
			frappe.db.set_value(
				"HD Ticket",
				ticket.name,
				"sla_status",
				"Breached",
				update_modified=False,
			)
			_notify_assignee_sla_breach(ticket)
		except Exception as e:
			frappe.log_error(
				f"Error updating SLA breach for ticket {row.name}: {str(e)}",
				"HD Ticket SLA Breach Error",
			)


def _notify_assignee_sla_breach(ticket):
	"""Notify assigned agent that SLA end date has been exceeded."""
	if not ticket.assigned_to:
		return

	recipient = ticket.assigned_to
	recipient_lang = get_user_language(recipient)
	subject = _("Ticket {0} exceeded SLA due date", lang=recipient_lang).format(ticket.name)

	try:
		from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

		notification = frappe._dict({
			"subject": subject,
			"from_user": "Administrator",
			"type": "Alert",
			"document_type": "HD Ticket",
			"document_name": ticket.name,
		})
		make_notification_logs(notification, [recipient])
	except Exception:
		frappe.log_error("Failed to send SLA breach notification", "HD Ticket Notification Error")

	try:
		frappe.sendmail(
			recipients=[recipient],
			subject=subject,
			message=_(
				"<p>Ticket <strong>{0}</strong> exceeded its SLA due date.</p>"
				"<p><strong>Subject:</strong> {1}</p>"
				"<p><strong>SLA Due:</strong> {2}</p>"
				"<p><a href='{3}'>View Ticket</a></p>"
			, lang=recipient_lang).format(
				ticket.name,
				ticket.subject,
				frappe.utils.format_datetime(ticket.sla_due_date) if ticket.sla_due_date else _("Not set", lang=recipient_lang),
				frappe.utils.get_url_to_form("HD Ticket", ticket.name),
			),
			reference_doctype="HD Ticket",
			reference_name=ticket.name,
		)
	except Exception:
		frappe.log_error("Failed to send SLA breach email", "HD Ticket Email Error")


def auto_progress_on_requester_comment(doc, method):
	"""When the requester adds a comment on a ticket awaiting "Need More Info",
	automatically move the ticket back to "In Progress"."""
	if doc.reference_doctype != "HD Ticket" or not doc.reference_name:
		return
	if doc.comment_type != "Comment":
		return

	try:
		ticket = frappe.get_doc("HD Ticket", doc.reference_name)
	except frappe.DoesNotExistError:
		return

	if ticket.status != "Need More Info":
		return

	commenter = doc.comment_email or doc.owner
	if commenter != ticket.requester:
		return

	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")
		ticket.reload()
		ticket.status = "In Progress"
		ticket.flags.ignore_permissions = True
		ticket.flags.allow_auto_status_change = True
		ticket.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"HD Ticket Status Auto-Update",
		)
	finally:
		frappe.set_user(original_user)


def notify_requester_on_comment(doc, method):
	"""Unified comment notification for HD Tickets.

	Sends an in-app + email notification to every relevant party on a ticket
	comment, ALWAYS excluding the commenter themselves:

	- The requester is always notified (unless they are the commenter).
	- The assigned agent is notified (unless they are the commenter).
	- If no individual agent is set, every active member of the assigned team
	  is notified (minus the commenter).

	This guarantees: requester sees all agent/admin replies; agents/team see
	the requester's replies; an admin (or any user) who comments never
	receives their own notification.
	"""
	if doc.reference_doctype != "HD Ticket" or not doc.reference_name:
		return
	if doc.comment_type != "Comment":
		return

	try:
		ticket = frappe.get_doc("HD Ticket", doc.reference_name)
	except frappe.DoesNotExistError:
		return

	# Figure out who actually wrote the comment. Try every available signal
	# and normalize — Frappe stores User name (= email in most cases) in
	# different fields depending on the entry path.
	commenter_candidates = {
		(doc.comment_email or "").strip().lower(),
		(doc.owner or "").strip().lower(),
		(frappe.session.user or "").strip().lower(),
	}
	commenter_candidates.discard("")

	# Build recipient set
	recipients = set()

	# 1. Requester always gets notified (except on closed tickets — they
	#    cannot reply anyway, and we still let agents see closed-ticket
	#    comments via the agent branch below).
	if ticket.requester and ticket.status != "Closed":
		recipients.add(ticket.requester)

	# 2. Assigned individual agent (if any).
	if ticket.assigned_to:
		recipients.add(ticket.assigned_to)

	# 3. EVERY active member of the assigned team (in addition to assigned_to).
	#    If an agent is assigned individually AND the team exists, we still
	#    notify every other team member so the team stays in the loop.
	if ticket.assigned_team:
		try:
			for member in get_user_active_teams_members(ticket.assigned_team):
				if member:
					recipients.add(member)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				"HD Ticket Comment Notify (team lookup)",
			)

	# Never notify the commenter themselves — match case-insensitively across
	# every candidate identity.
	recipients = {
		r for r in recipients
		if r and r.strip().lower() not in commenter_candidates
	}

	if not recipients:
		return

	ticket_url = frappe.utils.get_url_to_form("HD Ticket", ticket.name)
	commenter = doc.comment_email or doc.owner or frappe.session.user

	# In-app notifications — one per recipient, localized.
	try:
		from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

		for recipient in recipients:
			recipient_lang = get_user_language(recipient)
			notification = frappe._dict({
				"subject": _("New reply on Ticket {0}", lang=recipient_lang).format(ticket.name),
				"from_user": commenter,
				"type": "Alert",
				"document_type": "HD Ticket",
				"document_name": ticket.name,
			})
			make_notification_logs(notification, [recipient])
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"HD Ticket Comment Notify (in-app)",
		)

	# Email notifications — also per recipient, localized.
	try:
		for recipient in recipients:
			recipient_lang = get_user_language(recipient)
			subject = _("New reply on Ticket {0}", lang=recipient_lang).format(ticket.name)
			if recipient == ticket.requester:
				body_key = (
					"<p>Your ticket <strong>{0}</strong> has a new reply.</p>"
					"<p><strong>Subject:</strong> {1}</p>"
					"<p><a href='{2}'>View Ticket</a></p>"
				)
			else:
				body_key = (
					"<p>A new comment was added to ticket <strong>{0}</strong>.</p>"
					"<p><strong>Subject:</strong> {1}</p>"
					"<p><a href='{2}'>View Ticket</a></p>"
				)
			frappe.sendmail(
				recipients=[recipient],
				subject=subject,
				message=_(body_key, lang=recipient_lang).format(
					ticket.name, ticket.subject, ticket_url
				),
				reference_doctype="HD Ticket",
				reference_name=ticket.name,
			)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"HD Ticket Comment Notify (email)",
		)


def validate_hd_ticket_comment(doc, method):
	"""Block requester replies after ticket is closed."""
	if doc.reference_doctype != "HD Ticket" or not doc.reference_name:
		return
	if doc.comment_type != "Comment":
		return

	try:
		ticket = frappe.get_doc("HD Ticket", doc.reference_name)
	except frappe.DoesNotExistError:
		return

	if ticket.status != "Closed":
		return

	commenter = doc.comment_email or doc.owner
	if has_agent_role(commenter):
		return

	frappe.throw(_("Closed tickets do not accept requester replies. Please contact support to reopen."))


@frappe.whitelist()
def get_team_members(doctype, txt, searchfield, start, page_len, filters):
	"""Get team members for assignment dropdown."""
	filters = filters or {}
	team = filters.get("team")

	conditions = [
		"tm.is_active = 1",
		"(tm.start_date IS NULL OR tm.start_date <= %(reference_date)s)",
		"(tm.end_date IS NULL OR tm.end_date >= %(reference_date)s)",
		"(tm.user LIKE %(txt)s OR u.full_name LIKE %(txt)s)",
	]
	params = {
		"reference_date": frappe.utils.today(),
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len,
	}

	if team and team != "%":
		conditions.append("tm.team = %(team)s")
		params["team"] = team

	where_clause = " AND ".join(conditions)
	return frappe.db.sql(
		f"""
		SELECT DISTINCT tm.user, u.full_name
		FROM `tabHD Team Member` tm
		JOIN `tabUser` u ON tm.user = u.name
		WHERE {where_clause}
		ORDER BY u.full_name
		LIMIT %(start)s, %(page_len)s
		""",
		params,
	)


@frappe.whitelist()
def get_agents(doctype, txt, searchfield, start, page_len, filters):
	"""Get users with HD Agent or HD Manager role."""
	return frappe.db.sql(
		"""
		SELECT DISTINCT u.name, u.full_name
		FROM `tabUser` u
		JOIN `tabHas Role` hr ON hr.parent = u.name
		WHERE hr.role IN ('HD Agent', 'HD Manager')
			AND u.enabled = 1
			AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
		ORDER BY u.full_name
		LIMIT %(start)s, %(page_len)s
		""",
		{"txt": f"%{txt}%", "start": start, "page_len": page_len},
	)


@frappe.whitelist()
def get_my_tickets(filters=None):
	"""Get tickets for the current user (requester view)."""
	user = frappe.session.user

	base_filters = {"requester": user}
	if filters:
		base_filters.update(frappe.parse_json(filters))

	return frappe.get_all("HD Ticket",
		filters=base_filters,
		fields=[
			"name",
			"subject",
			"status",
			"priority",
			"creation",
			"modified",
			"assigned_to",
			"resolved_by",
			"sla_status",
			"sla_due_date",
			"resolution_time_minutes",
		],
		order_by="creation DESC"
	)


@frappe.whitelist()
def get_dashboard_stats(period="This Month", agent=None):
	"""Get dashboard statistics for help desk.

	Args:
		period: Time period filter - "Today", "This Week", "This Month", or "All Time".
		agent: Optional agent (user) filter to see stats for a specific agent.
	"""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "HD Agent" not in roles and "HD Manager" not in roles:
		frappe.throw(_("Not authorized to view dashboard"))

	# Date filter based on period
	if period == "Today":
		date_filter = [">=", frappe.utils.today()]
	elif period == "This Week":
		date_filter = [">=", frappe.utils.add_days(frappe.utils.today(), -7)]
	elif period == "This Month":
		date_filter = [">=", frappe.utils.add_months(frappe.utils.today(), -1)]
	else:
		date_filter = None

	filters = {}
	if date_filter:
		filters["creation"] = date_filter

	# Agent filter
	if agent:
		filters["assigned_to"] = agent

	# Total tickets
	total = frappe.db.count("HD Ticket", filters)

	# Resolved tickets
	resolved_filters = filters.copy()
	resolved_filters["status"] = ["in", ["Resolved", "Closed"]]
	resolved = frappe.db.count("HD Ticket", resolved_filters)

	# SLA fulfilled
	sla_fulfilled_filters = filters.copy()
	sla_fulfilled_filters["sla_status"] = "Fulfilled"
	sla_fulfilled = frappe.db.count("HD Ticket", sla_fulfilled_filters)

	# Tickets with SLA (for percentage calculation)
	sla_set_filters = filters.copy()
	sla_set_filters["sla_status"] = ["in", ["Fulfilled", "Breached"]]
	tickets_with_sla = frappe.db.count("HD Ticket", sla_set_filters)

	# Average resolution time from In Progress start to completion.
	avg_conditions = [
		"status IN ('Resolved', 'Closed')",
		"resolved_date IS NOT NULL",
		"sla_start_time IS NOT NULL",
		"TIMESTAMPDIFF(SECOND, sla_start_time, resolved_date) >= 60",
	]
	avg_params = {}

	if date_filter:
		avg_conditions.append("creation >= %(date_from)s")
		avg_params["date_from"] = date_filter[1]

	if agent:
		avg_conditions.append("assigned_to = %(agent)s")
		avg_params["agent"] = agent

	where_clause = " AND ".join(avg_conditions)
	avg_resolution = frappe.db.sql(f"""
		SELECT AVG(TIMESTAMPDIFF(MINUTE, sla_start_time, resolved_date)) as avg_time
		FROM `tabHD Ticket`
		WHERE {where_clause}
	""", avg_params, as_dict=True)[0].get("avg_time") or 0

	return {
		"total_tickets": total,
		"resolved_tickets": resolved,
		"resolved_percentage": round((resolved / total * 100) if total else 0, 1),
		"sla_fulfilled": sla_fulfilled,
		"sla_percentage": round((sla_fulfilled / tickets_with_sla * 100) if tickets_with_sla else 0, 1),
		"avg_resolution_minutes": round(avg_resolution, 0)
	}


@frappe.whitelist()
def get_resolved_pct():
	"""Get percentage of resolved tickets (for KPI number card)."""
	total = frappe.db.count("HD Ticket")
	if not total:
		return 0
	resolved = frappe.db.count("HD Ticket", {"status": ["in", ["Resolved", "Closed"]]})
	return round((resolved / total * 100), 1)


@frappe.whitelist()
def get_sla_fulfilled_pct():
	"""Get percentage of SLA fulfilled tickets (for KPI number card)."""
	tickets_with_sla = frappe.db.count("HD Ticket", {"sla_status": ["in", ["Fulfilled", "Breached"]]})
	if not tickets_with_sla:
		return 0
	fulfilled = frappe.db.count("HD Ticket", {"sla_status": "Fulfilled"})
	return round((fulfilled / tickets_with_sla * 100), 1)


@frappe.whitelist()
def get_avg_resolution_time():
	"""Get average resolution time in hours (for KPI number card)."""
	result = frappe.db.sql("""
		SELECT AVG(TIMESTAMPDIFF(MINUTE, sla_start_time, resolved_date)) as avg_time
		FROM `tabHD Ticket`
		WHERE status IN ('Resolved', 'Closed')
		AND resolved_date IS NOT NULL
		AND sla_start_time IS NOT NULL
		AND TIMESTAMPDIFF(SECOND, sla_start_time, resolved_date) >= 60
	""", as_dict=True)[0].get("avg_time") or 0
	# Return in hours rounded to 1 decimal
	return round(result / 60, 1)
