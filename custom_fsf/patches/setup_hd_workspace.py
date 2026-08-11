"""
Set up Help Desk workspaces with proper role-based visibility.

Creates two workspaces:
- "Help Desk" (all users): Only shows "My Tickets" for requesters
- "Help Desk Admin" (HD Agent, HD Manager, System Manager): Shows all
  tickets, dashboard, and lookup management links
"""

import json
import frappe


def execute():
	"""Set up both Help Desk workspaces."""
	setup_requester_workspace()
	setup_admin_workspace()
	frappe.db.commit()


def setup_requester_workspace():
	"""Set up the requester-facing Help Desk workspace (visible to all)."""
	workspace_name = "Help Desk"

	if frappe.db.exists("Workspace", workspace_name):
		ws = frappe.get_doc("Workspace", workspace_name)
	else:
		ws = frappe.new_doc("Workspace")
		ws.label = workspace_name

	ws.module = "HD"
	ws.icon = "support"
	ws.indicator_color = "blue"
	ws.is_hidden = 0
	ws.public = 1
	ws.sequence_id = 15
	ws.title = "Help Desk"

	# No role restriction - visible to all desk users
	ws.roles = []

	# Clear and rebuild shortcuts
	ws.shortcuts = []
	ws.append("shortcuts", {
		"label": "My Tickets",
		"link_to": "HD Ticket",
		"type": "DocType",
		"doc_view": "List",
		"color": "#ED64A6",
	})

	# Clear and rebuild links - must start with Card Break
	ws.links = []
	ws.append("links", {
		"type": "Card Break",
		"label": "My Tickets",
	})
	ws.append("links", {
		"type": "Link",
		"label": "My Tickets",
		"link_to": "HD Ticket",
		"link_type": "DocType",
		"onboard": 1,
	})

	# Content JSON: shortcut + card referencing the Card Break label
	ws.content = json.dumps([
		{
			"id": "s_my",
			"type": "shortcut",
			"data": {"shortcut_name": "My Tickets", "col": 12},
		},
		{
			"id": "c_my",
			"type": "card",
			"data": {"card_name": "My Tickets", "col": 12},
		},
	])

	ws.save(ignore_permissions=True)


def setup_admin_workspace():
	"""Set up the admin Help Desk workspace (agents/managers only)."""
	workspace_name = "Help Desk Admin"

	if frappe.db.exists("Workspace", workspace_name):
		ws = frappe.get_doc("Workspace", workspace_name)
	else:
		ws = frappe.new_doc("Workspace")
		ws.label = workspace_name

	ws.module = "HD"
	ws.icon = "setting-gear"
	ws.indicator_color = "orange"
	ws.is_hidden = 0
	ws.public = 1
	ws.sequence_id = 16
	ws.title = "Help Desk Admin"

	# Restrict to agent/manager roles only
	ws.roles = []
	for role in ("HD Agent", "HD Manager", "System Manager"):
		ws.append("roles", {"role": role})

	# Clear and rebuild shortcuts
	ws.shortcuts = []
	ws.append("shortcuts", {
		"label": "All Tickets",
		"link_to": "HD Ticket",
		"type": "DocType",
		"doc_view": "List",
		"color": "#4299E1",
	})
	ws.append("shortcuts", {
		"label": "HD Dashboard",
		"link_to": "hd-dashboard",
		"type": "Page",
		"color": "#38B2AC",
	})

	# Clear and rebuild links - Card Break required before each group
	ws.links = []

	# Group 1: Tickets
	ws.append("links", {
		"type": "Card Break",
		"label": "Tickets",
	})
	ws.append("links", {
		"type": "Link",
		"label": "All Tickets",
		"link_to": "HD Ticket",
		"link_type": "DocType",
		"onboard": 1,
	})
	ws.append("links", {
		"type": "Link",
		"label": "Dashboard",
		"link_to": "hd-dashboard",
		"link_type": "Page",
		"onboard": 1,
	})

	# Group 2: Lookups
	ws.append("links", {
		"type": "Card Break",
		"label": "Lookups",
	})
	ws.append("links", {
		"type": "Link",
		"label": "Teams",
		"link_to": "HD Team",
		"link_type": "DocType",
	})
	ws.append("links", {
		"type": "Link",
		"label": "Team Members",
		"link_to": "HD Team Member",
		"link_type": "DocType",
	})
	ws.append("links", {
		"type": "Link",
		"label": "Ticket Types",
		"link_to": "HD Ticket Type",
		"link_type": "DocType",
	})
	ws.append("links", {
		"type": "Link",
		"label": "Categories",
		"link_to": "HD Ticket Category",
		"link_type": "DocType",
	})
	ws.append("links", {
		"type": "Link",
		"label": "Priorities",
		"link_to": "HD Ticket Priority",
		"link_type": "DocType",
	})

	# Content JSON: shortcuts + cards (card_name must match Card Break labels)
	ws.content = json.dumps([
		{
			"id": "s_all",
			"type": "shortcut",
			"data": {"shortcut_name": "All Tickets", "col": 6},
		},
		{
			"id": "s_dash",
			"type": "shortcut",
			"data": {"shortcut_name": "HD Dashboard", "col": 6},
		},
		{
			"id": "c_tickets",
			"type": "card",
			"data": {"card_name": "Tickets", "col": 4},
		},
		{
			"id": "c_lookups",
			"type": "card",
			"data": {"card_name": "Lookups", "col": 4},
		},
	])

	ws.save(ignore_permissions=True)
