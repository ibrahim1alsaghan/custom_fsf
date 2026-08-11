frappe.pages["hd-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Dashboard"),
		single_column: true,
	});

	page.main.addClass("hd-dashboard");
	new HDDashboard(page);
};

class HDDashboard {
	constructor(page) {
		this.page = page;
		this.filters = { period: "This Month", agent: null };
		this.charts = {};
		this.render_skeleton();
		this.setup_filters();
		this.fetch_and_render();
	}

	setup_filters() {
		const wrapper = this.page.main.find("#hd-dashboard-filters");
		if (!wrapper.length) return;

		this.period_filter = frappe.ui.form.make_control({
			parent: wrapper.find(".filter-period").get(0),
			df: {
				fieldname: "period",
				label: __("Period"),
				fieldtype: "Select",
				options: "This Month\nThis Week\nToday\nThis Quarter\nAll Time",
				default: "This Month",
				change: () => {
					this.filters.period = this.period_filter.get_value();
					this.fetch_and_render();
				},
			},
			render_input: true,
		});
		this.period_filter.set_value(this.filters.period);

		this.agent_filter = frappe.ui.form.make_control({
			parent: wrapper.find(".filter-agent").get(0),
			df: {
				fieldname: "agent",
				label: __("Agent"),
				fieldtype: "Link",
				options: "User",
				change: () => {
					this.filters.agent = this.agent_filter.get_value();
					this.fetch_and_render();
				},
				get_query: () => {
					return {
						query: "custom_fsf.hd.doctype.hd_ticket.hd_ticket.get_agents",
					};
				},
			},
			render_input: true,
		});
		this.agent_filter.set_value(this.filters.agent || "");

		wrapper.find(".filter-clear").on("click", () => {
			this.filters = { period: "This Month", agent: null };
			this.period_filter.set_value(this.filters.period);
			this.agent_filter.set_value("");
			this.fetch_and_render();
		});
	}

	render_skeleton() {
		this.page.main.html(`
				<div class="hd-filters" id="hd-dashboard-filters">
					<div class="hd-filter-control filter-period"></div>
					<div class="hd-filter-control filter-agent"></div>
					<button class="btn btn-default filter-clear" title="${__("Clear Filters")}" aria-label="${__("Clear Filters")}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
				</div>
				<div class="hd-kpi-row">
					<div class="hd-kpi-card" id="kpi-tickets"></div>
					<div class="hd-kpi-card" id="kpi-resolved"></div>
					<div class="hd-kpi-card" id="kpi-sla"></div>
					<div class="hd-kpi-card" id="kpi-resolution-time"></div>
				</div>
				<div class="hd-chart-row">
					<div class="hd-chart-card">
						<div class="chart-title">${__("Tickets Trend")}</div>
					<div class="chart-subtitle" id="trend-subtitle"></div>
					<div id="chart-tickets-trend"></div>
				</div>
				<div class="hd-chart-card">
					<div class="chart-title">${__("Feedback Trend")}</div>
					<div class="chart-subtitle" id="feedback-subtitle"></div>
					<div id="chart-feedback-trend"></div>
				</div>
			</div>
			<div class="hd-chart-row">
				<div class="hd-chart-card">
					<div class="chart-title">${__("Tickets by Status")}</div>
					<div class="chart-subtitle">${__("Distribution of Tickets by Status")}</div>
					<div id="chart-by-status"></div>
				</div>
				<div class="hd-chart-card">
					<div class="chart-title">${__("Tickets by Priority")}</div>
					<div class="chart-subtitle">${__("Distribution of Tickets by Priority")}</div>
					<div id="chart-by-priority"></div>
				</div>
			</div>
			<div class="hd-chart-row">
				<div class="hd-chart-card">
					<div class="chart-title">${__("Tickets by Department")}</div>
					<div class="chart-subtitle">${__("Distribution of Tickets by Department")}</div>
					<div id="chart-by-department"></div>
				</div>
				<div class="hd-chart-card">
					<div class="chart-title">${__("Tickets by Team")}</div>
					<div class="chart-subtitle">${__("Distribution of Tickets by Team")}</div>
					<div id="chart-by-team"></div>
				</div>
			</div>
			<div class="hd-chart-row hd-chart-row-single">
				<div class="hd-chart-card">
					<div class="chart-title">${__("Tickets by Type")}</div>
					<div class="chart-subtitle">${__("Distribution of Tickets by Type")}</div>
					<div id="chart-by-type"></div>
				</div>
			</div>
		`);
	}

	fetch_and_render() {
		frappe.call({
			method: "custom_fsf.hd.page.hd_dashboard.hd_dashboard.get_dashboard_data",
			args: {
				period: this.filters.period,
				agent: this.filters.agent || null,
			},
			callback: (r) => {
				if (r.message) {
					this.data = r.message;
					this.render_kpis();
					this.render_tickets_trend();
					this.render_feedback_trend();
					this.render_donut("chart-by-status", this.data.tickets_by_status);
					this.render_donut("chart-by-priority", this.data.tickets_by_priority);
					this.render_donut("chart-by-department", this.data.tickets_by_department);
					this.render_donut("chart-by-team", this.data.tickets_by_team);
					this.render_donut("chart-by-type", this.data.tickets_by_type);
				}
			},
		});
	}

	render_kpis() {
		const k = this.data.kpis;

		this._render_kpi("kpi-tickets", __("Total Tickets"), k.total_tickets.value, k.total_tickets.delta);
		this._render_kpi("kpi-resolved", __("% Resolved"), k.resolved_pct.value + "%", k.resolved_pct.delta);
		this._render_kpi("kpi-sla", __("% SLA Fulfilled"), k.sla_fulfilled_pct.value + "%", k.sla_fulfilled_pct.delta);

		const res_raw = k.avg_resolution_minutes.value;
		const res_num = Number(res_raw);
		let res_display;
		if (res_raw === null || res_raw === undefined || Number.isNaN(res_num)) {
			res_display = "-";
		} else if (res_num >= 1440) {
			res_display = (res_num / 1440).toFixed(1) + " " + __("days");
		} else if (res_num >= 60) {
			res_display = (res_num / 60).toFixed(1) + " " + __("hrs");
		} else {
			res_display = Math.round(res_num) + " " + __("mins");
		}

		const resolution_label = k.avg_resolution_minutes.source === "in_progress"
			? __("Avg. Active Time")
			: __("Avg. Resolution Time");
		this._render_kpi("kpi-resolution-time", resolution_label, res_display, k.avg_resolution_minutes.delta);
	}

	_render_kpi(id, label, value, delta) {
		let delta_class = "neutral";
		if (delta && delta.direction === "up") delta_class = "up";
		if (delta && delta.direction === "down") delta_class = "down";

		// For resolution time, "down" is actually good (faster resolution)
		if (id === "kpi-resolution-time") {
			if (delta && delta.direction === "down") delta_class = "up";
			if (delta && delta.direction === "up") delta_class = "down";
		}

		const delta_text = delta && delta.text ? delta.text : "";

		document.getElementById(id).innerHTML = `
			<div class="kpi-label">${label}</div>
			<div class="kpi-value">${value}</div>
			<div class="kpi-delta ${delta_class}">${delta_text}</div>
		`;
	}

	render_tickets_trend() {
		const t = this.data.tickets_trend;
		const container = document.getElementById("chart-tickets-trend");

		if (!t.labels.length) {
			container.innerHTML = `<div class="chart-placeholder">${__("No ticket data for this period")}</div>`;
			return;
		}

		const total = t.closed.reduce((a, b) => a + b, 0) + t.open.reduce((a, b) => a + b, 0);
		const avg = t.labels.length ? Math.round(total / t.labels.length) : 0;
		document.getElementById("trend-subtitle").textContent =
			__("Average tickets per day is around {0}", [avg]);

		// Destroy previous chart
		if (this.charts.trend) {
			this.charts.trend = null;
			container.innerHTML = "";
		}

		this.charts.trend = new frappe.Chart(container, {
			data: {
				labels: t.labels,
				datasets: [
					{ name: __("Closed"), values: t.closed, chartType: "bar" },
					{ name: __("Open"), values: t.open, chartType: "bar" },
					{ name: __("SLA Fulfilled %"), values: t.sla_pct, chartType: "line" },
				],
				yMarkers: [],
			},
			type: "axis-mixed",
			height: 280,
			colors: ["#3b82f6", "#f472b6", "#22c55e"],
			barOptions: { stacked: true, spaceRatio: 0.4 },
			lineOptions: { dotSize: 4, regionFill: 0 },
			axisOptions: { xIsSeries: true },
			tooltipOptions: {
				formatTooltipY: (d) => d,
			},
		});
	}

	render_feedback_trend() {
		const f = this.data.feedback_trend;
		const container = document.getElementById("chart-feedback-trend");

		if (!f.labels.length) {
			container.innerHTML = `<div class="chart-placeholder">${__("No feedback data for this period")}</div>`;
			document.getElementById("feedback-subtitle").textContent = "";
			return;
		}

		const total_feedback = (f.feedback_count || []).reduce((a, b) => a + b, 0);
		document.getElementById("feedback-subtitle").textContent =
			__("Requester feedback comments: {0}", [total_feedback]);

		if (this.charts.feedback) {
			this.charts.feedback = null;
			container.innerHTML = "";
		}

		const datasets = [
			{ name: __("Feedback Comments"), values: f.feedback_count || [], chartType: "bar" },
		];

		const has_rating = (f.rating || []).some((v) => !!v);
		if (has_rating) {
			datasets.push({ name: __("Avg Rating"), values: f.rating, chartType: "line" });
		}

		this.charts.feedback = new frappe.Chart(container, {
			data: {
				labels: f.labels,
				datasets: datasets,
			},
			type: "axis-mixed",
			height: 280,
			colors: ["#06b6d4", "#f59e0b"],
			axisOptions: { xIsSeries: true },
			lineOptions: { dotSize: 4, regionFill: 0 },
			tooltipOptions: {
				formatTooltipY: (d) => d,
			},
		});
	}

	render_donut(container_id, data) {
		const container = document.getElementById(container_id);

		if (!data || !data.length) {
			container.innerHTML = `<div class="chart-placeholder">${__("No data available")}</div>`;
			return;
		}

		const labels = data.map((d) => `${__(d.label)} (${d.pct}%)`);
		const values = data.map((d) => d.value);

		// Destroy previous chart
		if (this.charts[container_id]) {
			this.charts[container_id] = null;
			container.innerHTML = "";
		}

		this.charts[container_id] = new frappe.Chart(container, {
			data: {
				labels: labels,
				datasets: [{ values: values }],
			},
			type: "donut",
			height: 280,
			colors: ["#06b6d4", "#3b82f6", "#ef4444", "#f59e0b", "#8b5cf6", "#22c55e"],
			tooltipOptions: {
				formatTooltipY: (d) => d + " " + __("tickets"),
			},
		});
	}
}
