import frappe
from frappe import _
from frappe.utils import (
	now_datetime, getdate, today, add_months, add_days,
	get_datetime, date_diff
)


@frappe.whitelist()
def get_dashboard_data(period="This Month", agent=None):
	"""Return all data needed for the HD Dashboard page."""
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection({"HD Agent", "HD Manager"}):
		frappe.throw(_("Not authorized to view dashboard"), frappe.PermissionError)

	current_range, previous_range = _get_date_ranges(period)

	base_filters = {}
	if agent:
		base_filters["assigned_to"] = agent

	kpis = _get_kpis(current_range, previous_range, base_filters)
	tickets_trend = _get_tickets_trend(current_range, base_filters)
	feedback_trend = _get_feedback_trend(current_range, base_filters)
	tickets_by_team = _get_distribution("assigned_team", current_range, base_filters)
	tickets_by_type = _get_distribution("ticket_type", current_range, base_filters)
	tickets_by_status = _get_distribution("status", current_range, base_filters)
	tickets_by_priority = _get_distribution("priority", current_range, base_filters)
	tickets_by_department = _get_distribution("department", current_range, base_filters)

	return {
		"kpis": kpis,
		"tickets_trend": tickets_trend,
		"feedback_trend": feedback_trend,
		"tickets_by_team": tickets_by_team,
		"tickets_by_type": tickets_by_type,
		"tickets_by_status": tickets_by_status,
		"tickets_by_priority": tickets_by_priority,
		"tickets_by_department": tickets_by_department,
	}


def _get_date_ranges(period):
	"""Return (current_from, current_to) and (prev_from, prev_to) date tuples."""
	today_date = getdate(today())

	if period == "Today":
		current_from = today_date
		current_to = today_date
		prev_from = add_days(today_date, -1)
		prev_to = add_days(today_date, -1)
	elif period == "This Week":
		current_from = add_days(today_date, -6)
		current_to = today_date
		prev_from = add_days(today_date, -13)
		prev_to = add_days(today_date, -7)
	elif period == "This Month":
		current_from = add_months(today_date, -1)
		current_to = today_date
		prev_from = add_months(today_date, -2)
		prev_to = add_months(today_date, -1)
	elif period == "This Quarter":
		current_from = add_months(today_date, -3)
		current_to = today_date
		prev_from = add_months(today_date, -6)
		prev_to = add_months(today_date, -3)
	else:  # All Time
		current_from = None
		current_to = today_date
		prev_from = None
		prev_to = None

	return (current_from, current_to), (prev_from, prev_to)


def _build_filters(date_range, base_filters):
	"""Build frappe ORM filters dict from date range and base filters."""
	filters = dict(base_filters)
	if date_range[0]:
		filters["creation"] = ["between", [date_range[0], date_range[1]]]
	return filters


def _get_kpis(current_range, previous_range, base_filters):
	"""Calculate KPI values and deltas compared to previous period."""
	cur = _calc_period_stats(current_range, base_filters)
	prev = _calc_period_stats(previous_range, base_filters)

	def delta(cur_val, prev_val, suffix="%"):
		if not prev_val:
			return {"value": 0, "text": ""}
		change = cur_val - prev_val
		pct = round((change / prev_val) * 100, 1) if prev_val else 0
		direction = "up" if change >= 0 else "down"
		arrow = "\u2191" if change >= 0 else "\u2193"
		return {
			"value": pct,
			"text": f"{arrow} {abs(pct)}{suffix}",
			"direction": direction,
		}

	avg_res_minutes_cur = cur["avg_completion_minutes"]
	avg_res_minutes_prev = prev["avg_completion_minutes"]
	if (
		avg_res_minutes_cur is not None
		and avg_res_minutes_prev is not None
		and cur.get("avg_completion_source") == prev.get("avg_completion_source")
	):
		res_delta_minutes = round(avg_res_minutes_cur - avg_res_minutes_prev, 1)
		res_direction = "up" if res_delta_minutes >= 0 else "down"
		res_arrow = "\u2191" if res_delta_minutes >= 0 else "\u2193"
		if abs(res_delta_minutes) >= 1440:
			res_delta_text = f"{res_arrow} {round(abs(res_delta_minutes) / 1440, 1)} " + _("days")
		elif abs(res_delta_minutes) >= 60:
			res_delta_text = f"{res_arrow} {round(abs(res_delta_minutes) / 60, 1)} " + _("hrs")
		else:
			res_delta_text = f"{res_arrow} {round(abs(res_delta_minutes), 0)} " + _("mins")
	else:
		res_direction = "neutral"
		res_delta_text = ""
		res_delta_minutes = 0

	return {
		"total_tickets": {
			"value": cur["total"],
			"delta": delta(cur["total"], prev["total"]),
		},
		"resolved_pct": {
			"value": cur["resolved_pct"],
			"delta": delta(cur["resolved_pct"], prev["resolved_pct"]),
		},
		"sla_fulfilled_pct": {
			"value": cur["sla_pct"],
			"delta": delta(cur["sla_pct"], prev["sla_pct"]),
		},
		"avg_resolution_minutes": {
			"value": avg_res_minutes_cur,
			"source": cur.get("avg_completion_source"),
			"delta": {
				"value": res_delta_minutes,
				"text": res_delta_text,
				"direction": res_direction,
			},
		},
	}


def _calc_period_stats(date_range, base_filters):
	"""Calculate stats for a specific period."""
	filters = _build_filters(date_range, base_filters)

	total = frappe.db.count("HD Ticket", filters) or 0

	resolved_filters = dict(filters)
	resolved_filters["status"] = ["in", ["Resolved", "Closed"]]
	resolved = frappe.db.count("HD Ticket", resolved_filters) or 0

	sla_fulfilled_filters = dict(filters)
	sla_fulfilled_filters["sla_status"] = "Fulfilled"
	sla_fulfilled = frappe.db.count("HD Ticket", sla_fulfilled_filters) or 0

	sla_set_filters = dict(filters)
	sla_set_filters["sla_status"] = ["in", ["Fulfilled", "Breached"]]
	tickets_with_sla = frappe.db.count("HD Ticket", sla_set_filters) or 0

	# Average completion KPI:
	# - If there are active in-progress tickets, show live average elapsed time.
	# - Otherwise show completed average time (Resolved/Closed).
	in_progress_conditions = ["status = 'In Progress'"]
	in_progress_params = {}
	if date_range[0]:
		in_progress_conditions.append("creation BETWEEN %(from_date)s AND %(to_date)s")
		in_progress_params["from_date"] = date_range[0]
		in_progress_params["to_date"] = date_range[1]
	if base_filters.get("assigned_to"):
		in_progress_conditions.append("assigned_to = %(agent)s")
		in_progress_params["agent"] = base_filters["assigned_to"]
	in_progress_conditions.append("sla_start_time IS NOT NULL")
	in_progress_conditions.append("TIMESTAMPDIFF(SECOND, sla_start_time, NOW()) >= 0")

	in_progress_where = " AND ".join(in_progress_conditions)
	in_progress_avg = frappe.db.sql(
		f"SELECT AVG(TIMESTAMPDIFF(MINUTE, sla_start_time, NOW())) as v FROM `tabHD Ticket` WHERE {in_progress_where}",
		in_progress_params,
		as_dict=True,
	)[0].get("v")

	completed_conditions = [
		"status IN ('Resolved', 'Closed')",
		"resolved_date IS NOT NULL",
		"sla_start_time IS NOT NULL",
	]
	completed_params = {}
	if date_range[0]:
		completed_conditions.append("creation BETWEEN %(from_date)s AND %(to_date)s")
		completed_params["from_date"] = date_range[0]
		completed_params["to_date"] = date_range[1]
	if base_filters.get("assigned_to"):
		completed_conditions.append("assigned_to = %(agent)s")
		completed_params["agent"] = base_filters["assigned_to"]
	completed_conditions.append("TIMESTAMPDIFF(SECOND, sla_start_time, resolved_date) >= 60")

	completed_where = " AND ".join(completed_conditions)
	completed_avg = frappe.db.sql(
		f"SELECT AVG(TIMESTAMPDIFF(MINUTE, sla_start_time, resolved_date)) as v FROM `tabHD Ticket` WHERE {completed_where}",
		completed_params,
		as_dict=True,
	)[0].get("v")

	avg_completion = completed_avg
	avg_source = "closed" if completed_avg is not None else None
	if in_progress_avg is not None:
		avg_completion = in_progress_avg
		avg_source = "in_progress"

	return {
		"total": total,
		"resolved": resolved,
		"resolved_pct": round((resolved / total * 100) if total else 0, 1),
		"sla_fulfilled": sla_fulfilled,
		"sla_pct": round((sla_fulfilled / tickets_with_sla * 100) if tickets_with_sla else 0, 1),
		"avg_completion_minutes": avg_completion,
		"avg_completion_source": avg_source,
	}


def _get_tickets_trend(date_range, base_filters):
	"""Get daily ticket trend data for the stacked bar + line chart."""
	conditions = ["1=1"]
	params = {}

	if date_range[0]:
		conditions.append("creation BETWEEN %(from_date)s AND %(to_date)s")
		params["from_date"] = date_range[0]
		params["to_date"] = date_range[1]
	if base_filters.get("assigned_to"):
		conditions.append("assigned_to = %(agent)s")
		params["agent"] = base_filters["assigned_to"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT
			DATE(creation) as day,
			SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as closed,
			SUM(CASE WHEN status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as open_count,
			SUM(CASE WHEN sla_status = 'Fulfilled' THEN 1 ELSE 0 END) as sla_ok,
			SUM(CASE WHEN sla_status IN ('Fulfilled', 'Breached') THEN 1 ELSE 0 END) as sla_total
		FROM `tabHD Ticket`
		WHERE {where}
		GROUP BY DATE(creation)
		ORDER BY DATE(creation)
	""", params, as_dict=True)

	labels = []
	closed_vals = []
	open_vals = []
	sla_pct_vals = []

	for r in rows:
		labels.append(frappe.utils.formatdate(r.day, "d MMM"))
		closed_vals.append(r.closed or 0)
		open_vals.append(r.open_count or 0)
		sla_pct = round((r.sla_ok / r.sla_total * 100) if r.sla_total else 0, 1)
		sla_pct_vals.append(sla_pct)

	return {
		"labels": labels,
		"closed": closed_vals,
		"open": open_vals,
		"sla_pct": sla_pct_vals,
	}


def _get_feedback_trend(date_range, base_filters):
	"""Get requester feedback trend from ticket conversation comments."""
	conditions = [
		"c.reference_doctype = 'HD Ticket'",
		"c.comment_type = 'Comment'",
		"(c.comment_email = t.requester OR c.owner = t.requester)",
	]
	params = {}

	if date_range[0]:
		conditions.append("c.creation BETWEEN %(from_date)s AND %(to_date)s")
		params["from_date"] = date_range[0]
		params["to_date"] = date_range[1]
	if base_filters.get("assigned_to"):
		conditions.append("t.assigned_to = %(agent)s")
		params["agent"] = base_filters["assigned_to"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT DATE(c.creation) as day, COUNT(*) as feedback_count
		FROM `tabComment` c
		INNER JOIN `tabHD Ticket` t ON t.name = c.reference_name
		WHERE {where}
		GROUP BY DATE(c.creation)
		ORDER BY DATE(c.creation)
		""",
		params,
		as_dict=True,
	)

	labels = []
	feedback_count = []
	for row in rows:
		labels.append(frappe.utils.formatdate(row.day, "d MMM"))
		feedback_count.append(row.feedback_count or 0)

	return {
		"labels": labels,
		"feedback_count": feedback_count,
		"rating": [],
	}


ALLOWED_DISTRIBUTION_FIELDS = {"assigned_team", "ticket_type", "category", "status", "priority", "channel", "department"}


def _get_distribution(field, date_range, base_filters):
	"""Get ticket distribution by a given field (team, type, etc.)."""
	if field not in ALLOWED_DISTRIBUTION_FIELDS:
		frappe.throw(_("Invalid distribution field: {0}").format(field))

	conditions = [f"`{field}` IS NOT NULL", f"`{field}` != ''"]
	params = {}

	if date_range[0]:
		conditions.append("creation BETWEEN %(from_date)s AND %(to_date)s")
		params["from_date"] = date_range[0]
		params["to_date"] = date_range[1]
	if base_filters.get("assigned_to"):
		conditions.append("assigned_to = %(agent)s")
		params["agent"] = base_filters["assigned_to"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT `{field}` as label, COUNT(*) as value
		FROM `tabHD Ticket`
		WHERE {where}
		GROUP BY `{field}`
		ORDER BY value DESC
	""", params, as_dict=True)

	display_map = _get_distribution_display_map(field, [row.label for row in rows if row.label])

	total = sum(r.value for r in rows) or 1
	result = []
	for r in rows:
		pct = round(r.value / total * 100)
		result.append({
			"label": display_map.get(r.label, r.label),
			"value": r.value,
			"pct": pct,
		})

	return result


def _get_distribution_display_map(field, names):
	"""Return user-friendly labels for link-based distribution values."""
	if not names:
		return {}

	link_field_map = {
		"assigned_team": ("HD Team", "team_name", "team_name"),
		"ticket_type": ("HD Ticket Type", "type_name_ar", "type_name"),
		"priority": ("HD Ticket Priority", "priority_name_ar", "priority_name"),
		"category": ("HD Ticket Category", "category_name_ar", "category_name"),
		"department": ("Department", "department_name", "department_name"),
	}
	config = link_field_map.get(field)
	if not config:
		return {}

	doctype, ar_field, default_field = config
	meta = frappe.get_meta(doctype)
	fields = ["name"]
	if meta.has_field(default_field) and default_field != "name":
		fields.append(default_field)
	if meta.has_field(ar_field) and ar_field not in fields:
		fields.append(ar_field)

	if len(fields) == 1:
		return {}

	use_ar = (frappe.local.lang or "").lower().startswith("ar")
	rows = frappe.get_all(
		doctype,
		filters={"name": ["in", list(set(names))]},
		fields=fields,
	)

	label_map = {}
	for row in rows:
		display = row.get(default_field) or row.name
		if use_ar and row.get(ar_field):
			display = row.get(ar_field)
		label_map[row.name] = display

	return label_map
