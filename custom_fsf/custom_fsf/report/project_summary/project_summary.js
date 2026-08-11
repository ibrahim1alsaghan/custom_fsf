// Copyright (c) 2025, ibrahim alsaghan and contributors
// For license information, please see license.txt

frappe.query_reports["Project Summary"] = {
	filters: [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				"",
				"Open",
				"Completed",
				"Cancelled",
			],
		},
		{
			fieldname: "project_type",
			label: __("Project Type"),
			fieldtype: "Link",
			options: "Project Type",
		},
		{
			fieldname: "priority",
			label: __("Priority"),
			fieldtype: "Select",
			options: [
				"",
				"Low",
				"Medium",
				"High",
				"Urgent",
			],
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "expected_start_date",
			label: __("Expected Start Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "expected_end_date",
			label: __("Expected End Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "project_template",
			label: __("Project Template"),
			fieldtype: "Link",
			options: "Project Template",
		},
	],
};
