# Copyright (c) 2025, FSF and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTeamMember(Document):
	def validate(self):
		self.validate_dates()
		self.validate_duplicate()

	def after_insert(self):
		"""Auto-assign HD Agent role to the user when added as a team member."""
		self._ensure_hd_agent_role()

	def on_update(self):
		"""Manage HD Agent role based on membership status changes."""
		if self.has_value_changed("is_active"):
			if self.is_active:
				self._ensure_hd_agent_role()
			else:
				self._remove_hd_agent_role_if_no_active_memberships()

	def _ensure_hd_agent_role(self):
		"""Add HD Agent role to the user if they don't already have it."""
		if not self.user or not self.is_active:
			return

		user_doc = frappe.get_doc("User", self.user)
		existing_roles = [r.role for r in user_doc.roles]

		if "HD Agent" not in existing_roles:
			user_doc.append("roles", {"role": "HD Agent"})
			user_doc.save(ignore_permissions=True)

	def _remove_hd_agent_role_if_no_active_memberships(self):
		"""Remove HD Agent role if the user has no other active team memberships."""
		if not self.user:
			return

		other_active = frappe.db.exists("HD Team Member", {
			"user": self.user,
			"is_active": 1,
			"name": ["!=", self.name],
		})
		if other_active:
			return

		user_doc = frappe.get_doc("User", self.user)
		user_doc.roles = [r for r in user_doc.roles if r.role != "HD Agent"]
		user_doc.save(ignore_permissions=True)

	def validate_dates(self):
		"""Validate that end_date is after start_date if both are set."""
		if self.start_date and self.end_date:
			if self.end_date < self.start_date:
				frappe.throw(_("End Date cannot be before Start Date"))

	def validate_duplicate(self):
		"""Check for duplicate active team membership."""
		if self.is_active:
			existing = frappe.db.exists("HD Team Member", {
				"team": self.team,
				"user": self.user,
				"is_active": 1,
				"name": ["!=", self.name]
			})
			if existing:
				frappe.throw(_("User {0} is already an active member of team {1}").format(
					self.user, self.team
				))


def deactivate_expired_team_members():
	"""Daily scheduler task: deactivate members whose end_date has passed and notify them."""
	today = frappe.utils.today()
	expired_members = frappe.get_all(
		"HD Team Member",
		filters={
			"is_active": 1,
			"end_date": ["<", today],
		},
		fields=["name", "user", "team", "end_date"],
	)

	for member_data in expired_members:
		try:
			member = frappe.get_doc("HD Team Member", member_data.name)
			member.is_active = 0
			member.save(ignore_permissions=True)
			_notify_membership_expired(member_data.user, member_data.team, member_data.end_date)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				f"Error deactivating expired team member {member_data.name}",
				"HD Team Member Expiry Error",
			)


def _notify_membership_expired(user, team, end_date):
	"""Send in-app notification and email to a user whose team membership expired."""
	subject = _("Your membership in team {0} expired on {1}").format(
		team, frappe.utils.formatdate(end_date)
	)

	try:
		from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

		notification = frappe._dict({
			"subject": subject,
			"from_user": "Administrator",
			"type": "Alert",
			"document_type": "HD Team",
			"document_name": team,
		})
		make_notification_logs(notification, [user])
	except Exception:
		frappe.log_error("Failed to send membership expiry notification", "HD Team Member Notification Error")

	try:
		frappe.sendmail(
			recipients=[user],
			subject=subject,
			message=_(
				"<p>Your membership in team <strong>{0}</strong> expired on <strong>{1}</strong> "
				"and has been deactivated.</p>"
				"<p>If you believe this is an error, please contact your team manager.</p>"
			).format(team, frappe.utils.formatdate(end_date)),
		)
	except Exception:
		frappe.log_error("Failed to send membership expiry email", "HD Team Member Email Error")
