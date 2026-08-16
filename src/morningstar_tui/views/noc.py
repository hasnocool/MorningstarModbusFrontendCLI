"""Multi-site NOC with v0.6 observability-integrity indicators."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.analytics import coverage_percent, energy_difference_percent, weighted_average
from morningstar_tui.util.formatting import first, fmt_number, fmt_percent, metric, text
from morningstar_tui.views.base import DashboardView


class NOCView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("MULTI-SITE NOC", classes="view-title")
        yield Static(
            "System health and observability health are separate. Fleet enrichment is lazy; use F for full long-term comparison.",
            classes="hint",
        )
        yield DataTable(id="noc-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#noc-table", DataTable).add_columns(
            "Site",
            "API",
            "SSE",
            "Health",
            "Solar",
            "Battery",
            "Incidents",
            "Data",
            "Energy Δ",
            "Latency",
            "System",
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        table = self.query_one("#noc-table", DataTable)
        table.clear(columns=False)
        for item in all_states:
            marker = "▶ " if item.name == state.name else "  "
            score = first(item.health_score, "score", "health_score", "total")
            integrity = list(item.controller_integrity.values())
            data_quality = weighted_average(
                [(coverage_percent(bundle.coverage), 1.0) for bundle in integrity]
            )
            energy_deltas = [
                energy_difference_percent(bundle.energy_summary_30d) for bundle in integrity
            ]
            present_deltas = [value for value in energy_deltas if value is not None]
            energy_delta = sum(present_deltas) / len(present_deltas) if present_deltas else None
            table.add_row(
                marker + item.name,
                "UP" if item.online else "DOWN",
                "LIVE" if item.stream_online else "—",
                fmt_number(score, "/100", 0),
                fmt_number(metric(item.latest, "solar_input_power_w"), "W", 0),
                fmt_number(metric(item.latest, "battery_voltage_v"), "V", 2),
                str(len(item.incidents)),
                fmt_percent(data_quality) if integrity else "…",
                fmt_percent(energy_delta) if integrity else "…",
                fmt_number(item.latency_ms, "ms", 0),
                text(item.system_uid),
            )
