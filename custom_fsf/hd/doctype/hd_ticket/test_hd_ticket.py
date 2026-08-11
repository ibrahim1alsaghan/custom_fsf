# Copyright (c) 2026, ibrahim alsaghan and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime, today

from custom_fsf.hd.doctype.hd_ticket.hd_ticket import get_team_members
from custom_fsf.patches.create_hd_default_data import execute as create_hd_default_data


def ensure_role(role_name):
	if frappe.db.exists("Role", role_name):
		return

	frappe.get_doc({
		"doctype": "Role",
		"role_name": role_name,
	}).insert(ignore_permissions=True)


def ensure_user(email, roles):
	default_name = email.split("@")[0].replace(".", " ").title()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": default_name,
			"full_name_arabic": default_name,
			"enabled": 1,
			"send_welcome_email": 0,
			"user_type": "System User",
		})
		try:
			user.insert(ignore_permissions=True)
		except frappe.TimestampMismatchError:
			# after_insert_user hook uses frappe.db.set_value + commit which
			# desynchronises the in-memory modified timestamp; the LMS
			# after_insert hook then fails on check_if_latest.  The user
			# record is already committed, so we can safely continue.
			pass

	# Always load a fresh copy so we have the latest modified timestamp.
	user = frappe.get_doc("User", email)

	existing_roles = {entry.role for entry in user.roles}
	for role in roles:
		if role not in existing_roles:
			user.append("roles", {"role": role})

	user.enabled = 1
	user.user_type = "System User"
	if hasattr(user, "full_name_arabic") and not user.full_name_arabic:
		user.full_name_arabic = user.full_name or user.first_name or default_name
	user.save(ignore_permissions=True)
	return user.name


def ensure_department(department_name):
	existing = frappe.db.get_value("Department", {"department_name": department_name}, "name")
	if existing:
		return existing

	dept = frappe.get_doc({
		"doctype": "Department",
		"department_name": department_name,
	})
	dept.insert(ignore_permissions=True)
	return dept.name


def ensure_employee(user, department):
	default_company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
		"Company", {}, "name"
	)
	if not default_company:
		frappe.throw("No default company found for employee test setup")

	employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if employee_name:
		employee = frappe.get_doc("Employee", employee_name)
		employee.department = department
		employee.status = "Active"
		employee.save(ignore_permissions=True)
		return employee.name

	employee = frappe.get_doc({
		"doctype": "Employee",
		"first_name": user.split("@")[0],
		"company": default_company,
		"user_id": user,
		"date_of_birth": "1990-01-01",
		"date_of_joining": today(),
		"department": department,
		"gender": "Male",
		"company_email": user,
		"prefered_contact_email": "Company Email",
		"prefered_email": user,
		"status": "Active",
	})
	employee.insert(ignore_permissions=True)
	return employee.name


def ensure_team(team_name):
	if frappe.db.exists("HD Team", team_name):
		return team_name

	team = frappe.get_doc({
		"doctype": "HD Team",
		"team_name": team_name,
		"description": "Test team for HD ticket tests",
		"is_active": 1,
	})
	team.insert(ignore_permissions=True)
	return team.name


def ensure_team_member(team, user, start_date=None, end_date=None, is_active=1):
	existing = frappe.db.get_value(
		"HD Team Member",
		{"team": team, "user": user, "is_active": is_active},
		"name",
	)

	if existing:
		member = frappe.get_doc("HD Team Member", existing)
	else:
		member = frappe.get_doc({
			"doctype": "HD Team Member",
			"naming_series": "HDM-.YYYY.-.#####",
			"team": team,
			"user": user,
			"role": "Member",
			"is_active": is_active,
		})

	if start_date:
		member.start_date = start_date
	if end_date:
		member.end_date = end_date

	if member.is_new():
		member.insert(ignore_permissions=True)
	else:
		member.save(ignore_permissions=True)

	return member.name


class TestHDTicket(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

		# Ensure foundational lookup data is available for every test run.
		create_hd_default_data()
		ensure_role("HD Agent")
		ensure_role("HD Manager")

		cls.requester = ensure_user("hd.requester@example.com", ["Employee"])
		cls.agent = ensure_user("hd.agent@example.com", ["Employee", "HD Agent"])
		cls.future_agent = ensure_user("hd.future.agent@example.com", ["Employee"])

		cls.department = ensure_department("HD Test Department")
		cls.agent_department = ensure_department("HD Agent Department")
		ensure_employee(cls.requester, cls.department)
		ensure_employee(cls.agent, cls.agent_department)
		ensure_employee(cls.future_agent, cls.agent_department)

		cls.team = ensure_team("HD Test Team")
		ensure_team_member(cls.team, cls.agent)
		ensure_team_member(cls.team, cls.future_agent, start_date=add_to_date(today(), days=2))

	def tearDown(self):
		frappe.set_user("Administrator")

	def _create_ticket(self, requester=None):
		requester = requester or self.requester
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": f"HD Test Ticket {frappe.generate_hash(length=8)}",
			"description": "Test ticket description",
			"requester": requester,
			"priority": "Medium",
			"ticket_type": "Unspecified",
			"category": "Unspecified",
			"channel": "Portal",
			"status": "Open",
		})
		ticket.insert(ignore_permissions=True)
		return ticket

	def _resolve_and_close_ticket(self, ticket_name):
		ticket = frappe.get_doc("HD Ticket", ticket_name)
		ticket.status = "In Progress"
		ticket.save(ignore_permissions=True)

		ticket.reload()
		ticket.status = "Resolved"
		ticket.save(ignore_permissions=True)

		ticket.reload()
		ticket.resolved_date = add_to_date(now_datetime(), days=-7)
		ticket.save(ignore_permissions=True)

		ticket.reload()
		ticket.status = "Closed"
		ticket.save(ignore_permissions=True)
		ticket.reload()
		return ticket

	def test_requester_cannot_change_agent_only_fields(self):
		ticket = self._create_ticket()
		frappe.set_user(self.requester)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.priority = "High"

		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_requester_can_create_ticket_with_priority(self):
		frappe.set_user(self.requester)
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": f"Requester Priority Test {frappe.generate_hash(length=8)}",
			"description": "Requester can set priority on create",
			"priority": "Medium",
			"channel": "Portal",
			"status": "Open",
		})
		ticket.insert()
		self.assertEqual(ticket.priority, "Medium")
		self.assertEqual(ticket.requester, self.requester)

	def test_requester_cannot_set_assignment_or_in_progress_on_create(self):
		frappe.set_user(self.requester)
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": f"Requester Insert Guard {frappe.generate_hash(length=8)}",
			"description": "Requester should not create assigned/in-progress ticket",
			"priority": "Medium",
			"status": "In Progress",
			"assigned_to": self.agent,
		})

		with self.assertRaises(frappe.ValidationError):
			ticket.insert()

	def test_requester_cannot_reassign_via_api_method(self):
		ticket = self._create_ticket()
		frappe.set_user(self.requester)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		with self.assertRaises(frappe.PermissionError):
			doc.reassign_ticket(new_team=self.team)

	def test_assignment_to_team_only_sets_in_progress_and_logs_history(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.assigned_team = self.team
		doc.save(ignore_permissions=True)
		doc.reload()

		self.assertEqual(doc.status, "In Progress")
		self.assertTrue(doc.assigned_date)
		self.assertGreaterEqual(len(doc.assignment_history), 1)
		self.assertEqual(doc.assignment_history[-1].assigned_team, self.team)
		self.assertFalse(doc.assignment_history[-1].assigned_to)

	def test_close_requires_one_business_day_after_resolved(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.status = "In Progress"
		doc.save(ignore_permissions=True)

		doc.reload()
		doc.status = "Resolved"
		doc.save(ignore_permissions=True)

		doc.reload()
		doc.status = "Closed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

		doc.reload()
		doc.resolved_date = add_to_date(now_datetime(), days=-7)
		doc.save(ignore_permissions=True)

		doc.reload()
		doc.status = "Closed"
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.status, "Closed")

	def test_requester_reply_blocked_on_closed_ticket(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)
		ticket = self._resolve_and_close_ticket(ticket.name)

		frappe.set_user(self.requester)
		comment = frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Comment",
			"content": "Any update?",
			"reference_doctype": "HD Ticket",
			"reference_name": ticket.name,
		})

		with self.assertRaises(frappe.ValidationError):
			comment.insert(ignore_permissions=True)

	def test_get_team_members_team_filter_honors_membership_dates(self):
		rows = get_team_members("HD Ticket", "", "user", 0, 100, {"team": self.team})
		users = {row[0] for row in rows}

		self.assertIn(self.agent, users)
		self.assertNotIn(self.future_agent, users)

	def test_department_is_derived_from_requester_employee(self):
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": f"HD Test Dept {frappe.generate_hash(length=8)}",
			"description": "Department sync test",
			"requester": self.requester,
			"department": self.agent_department,  # wrong on purpose, should be overridden
			"priority": "Medium",
			"ticket_type": "Unspecified",
			"category": "Unspecified",
			"channel": "Portal",
			"status": "Open",
		})
		ticket.insert(ignore_permissions=True)
		ticket.reload()
		self.assertEqual(ticket.department, self.department)

	def test_agent_cannot_edit_description(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.description = "Changed by agent"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_internal_comment_auto_sets_user_and_time(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.add_internal_comment("Internal check note")
		doc.reload()

		last_comment = doc.internal_comments[-1]
		self.assertEqual(last_comment.comment, "Internal check note")
		self.assertEqual(last_comment.commented_by, self.agent)
		self.assertTrue(last_comment.commented_on)

	def test_internal_comment_editable_but_not_deletable(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.add_internal_comment("First note")
		doc.reload()
		self.assertEqual(len(doc.internal_comments), 1)

		# Editing existing comment is allowed
		doc.internal_comments[0].comment = "Updated note"
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.internal_comments[0].comment, "Updated note")

		# Deleting existing comment is blocked
		doc.internal_comments = []
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_requester_cannot_edit_internal_comments(self):
		ticket = self._create_ticket()
		frappe.set_user(self.agent)
		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.add_internal_comment("Agent private note")

		frappe.set_user(self.requester)
		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.internal_comments[0].comment = "Requester changed it"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_status_transition_open_to_resolved_blocked(self):
		"""Direct Open→Resolved should be rejected by _validate_status_transitions."""
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.status = "Resolved"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_valid_status_transitions(self):
		"""Open→In Progress→Resolved happy path should succeed."""
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.status = "In Progress"
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.status, "In Progress")

		doc.status = "Resolved"
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.status, "Resolved")
		self.assertEqual(doc.resolved_by, self.agent)

		doc.status = "In Progress"
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertIsNone(doc.resolved_by)

	def test_unassignment_logs_history(self):
		"""Clearing assignment creates an 'Unassigned' history entry."""
		ticket = self._create_ticket()
		frappe.set_user(self.agent)

		doc = frappe.get_doc("HD Ticket", ticket.name)
		doc.assigned_team = self.team
		doc.assigned_to = self.agent
		doc.save(ignore_permissions=True)
		doc.reload()
		history_count_before = len(doc.assignment_history)

		doc.assigned_team = None
		doc.assigned_to = None
		doc.save(ignore_permissions=True)
		doc.reload()

		self.assertEqual(len(doc.assignment_history), history_count_before + 1)
		last_entry = doc.assignment_history[-1]
		self.assertIn("Unassigned", last_entry.notes or "")

	def test_team_member_deactivation_removes_role(self):
		"""Deactivating a member with no other active teams removes HD Agent role."""
		test_user_email = "hd.role.test@example.com"
		ensure_user(test_user_email, ["Employee"])
		dept = ensure_department("HD Role Test Dept")
		ensure_employee(test_user_email, dept)
		test_team = ensure_team("HD Role Test Team")
		member_name = ensure_team_member(test_team, test_user_email)

		# User should now have HD Agent role (added by after_insert)
		user_roles = {r.role for r in frappe.get_doc("User", test_user_email).roles}
		self.assertIn("HD Agent", user_roles)

		# Deactivate the membership
		member = frappe.get_doc("HD Team Member", member_name)
		member.is_active = 0
		member.save(ignore_permissions=True)

		# HD Agent role should be removed since no other active memberships
		user_roles = {r.role for r in frappe.get_doc("User", test_user_email).roles}
		self.assertNotIn("HD Agent", user_roles)

	def test_dashboard_requires_agent_role(self):
		"""Non-agent gets PermissionError on dashboard API."""
		from custom_fsf.hd.doctype.hd_ticket.hd_ticket import get_dashboard_stats

		frappe.set_user(self.requester)
		with self.assertRaises(Exception):
			get_dashboard_stats()
