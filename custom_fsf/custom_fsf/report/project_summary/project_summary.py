# Copyright (c) 2025, ibrahim alsaghan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = []

	data = frappe.db.get_all(
		"Project",
		filters=filters,
		fields=[
			"name",
			"project_name",
			"status",
			"percent_complete",
			"expected_start_date",
			"expected_end_date",
			"project_type",
		],
		order_by="expected_end_date",
	)

	for project in data:
		project["total_tasks"] = frappe.db.count("Task", filters={"project": project.name})
		project["completed_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Completed"}
		)
		project["overdue_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Overdue"}
		)
		project["total_issues"] = frappe.db.count("Issue", filters={"project": project.name})
		project["open_issues"] = frappe.db.count(
			"Issue", filters={"project": project.name, "status": "Open"}
		)
		project["resolved_issues"] = frappe.db.count(
			"Issue", filters={"project": project.name, "status": "Resolved"}
		)

	chart = get_chart_data(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"fieldname": "name",
			"label": _("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"width": 200,
		},
		{
			"fieldname": "project_name",
			"label": _("Project Name"),
			"width": 200,
		},
		{
			"fieldname": "project_type",
			"label": _("Type"),
			"fieldtype": "Link",
			"options": "Project Type",
			"width": 120,
		},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 120},
		{"fieldname": "total_tasks", "label": _("Total Tasks"), "fieldtype": "Data", "width": 120},
		{
			"fieldname": "completed_tasks",
			"label": _("Tasks Completed"),
			"fieldtype": "Data",
			"width": 120,
		},
		{"fieldname": "overdue_tasks", "label": _("Tasks Overdue"), "fieldtype": "Data", "width": 120},
		{"fieldname": "total_issues", "label": _("Total Issues"), "fieldtype": "Data", "width": 120},
		{"fieldname": "open_issues", "label": _("Open Issues"), "fieldtype": "Data", "width": 120},
		{"fieldname": "resolved_issues", "label": _("Resolved Issues"), "fieldtype": "Data", "width": 120},
		{"fieldname": "percent_complete", "label": _("Completion"), "fieldtype": "Data", "width": 120},
		{
			"fieldname": "expected_start_date",
			"label": _("Start Date"),
			"fieldtype": "Date",
			"width": 120,
		},
		{"fieldname": "expected_end_date", "label": _("End Date"), "fieldtype": "Date", "width": 120},
	]


def get_chart_data(data):
	labels = []
	total_tasks = []
	completed_tasks = []
	overdue_tasks = []
	total_issues = []
	open_issues = []
	resolved_issues = []

	for project in data:
		labels.append(project.project_name)
		total_tasks.append(project.total_tasks)
		completed_tasks.append(project.completed_tasks)
		overdue_tasks.append(project.overdue_tasks)
		total_issues.append(project.total_issues)
		open_issues.append(project.open_issues)
		resolved_issues.append(project.resolved_issues)

	return {
		"data": {
			"labels": labels[:30],
			"datasets": [
				{"name": _("Overdue Tasks"), "values": overdue_tasks[:30]},
				{"name": _("Completed Tasks"), "values": completed_tasks[:30]},
				{"name": _("Total Tasks"), "values": total_tasks[:30]},
				{"name": _("Open Issues"), "values": open_issues[:30]},
				{"name": _("Resolved Issues"), "values": resolved_issues[:30]},
				{"name": _("Total Issues"), "values": total_issues[:30]},
			],
		},
		"type": "bar",
		"colors": ["#2e7d32", "#4caf50", "#66bb6a", "#ffc107", "#ffeb3b", "#fff176"],
		"barOptions": {"stacked": True},
	}


def get_report_summary(data):
	if not data:
		return None

	avg_completion = sum(project.percent_complete for project in data) / len(data)
	total_tasks = sum([project.total_tasks for project in data])
	total_overdue_tasks = sum([project.overdue_tasks for project in data])
	completed_tasks = sum([project.completed_tasks for project in data])
	total_issues = sum([project.total_issues for project in data])
	open_issues = sum([project.open_issues for project in data])
	resolved_issues = sum([project.resolved_issues for project in data])

	return [
		{
			"value": avg_completion,
			"indicator": "Green" if avg_completion > 50 else "Red",
			"label": _("Average Completion"),
			"datatype": "Percent",
		},
		{
			"value": total_tasks,
			"indicator": "Blue",
			"label": _("Total Tasks"),
			"datatype": "Int",
		},
		{
			"value": completed_tasks,
			"indicator": "Green",
			"label": _("Completed Tasks"),
			"datatype": "Int",
		},
		{
			"value": total_overdue_tasks,
			"indicator": "Green" if total_overdue_tasks == 0 else "Red",
			"label": _("Overdue Tasks"),
			"datatype": "Int",
		},
		{
			"value": total_issues,
			"indicator": "Orange",
			"label": _("Total Issues"),
			"datatype": "Int",
		},
		{
			"value": open_issues,
			"indicator": "Red" if open_issues > 0 else "Green",
			"label": _("Open Issues"),
			"datatype": "Int",
		},
		{
			"value": resolved_issues,
			"indicator": "Green",
			"label": _("Resolved Issues"),
			"datatype": "Int",
		},
	]
