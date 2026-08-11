# Copyright (c) 2025, FSF and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class HDTicketInternalComment(Document):
	def before_insert(self):
		self._set_audit_defaults()

	def validate(self):
		self._set_audit_defaults()

	def _set_audit_defaults(self):
		if not self.commented_by:
			self.commented_by = frappe.session.user
		if not self.commented_on:
			self.commented_on = now_datetime()
