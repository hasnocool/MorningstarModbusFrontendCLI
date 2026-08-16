"""v0.5 multi-site terminal NOC view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import first, fmt_number, metric, text
from morningstar_tui.views.base import DashboardView


class NOCView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("MULTI-SITE NOC", classes="view-title")
        yield Static(
            "Use Tab / Shift+Tab to change active site. Compact, low-bandwidth and alert-only modes are CLI/config options.",
            classes="hint",
        )
        yield DataTable(id="noc-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#noc-table", DataTable).add_columns(
            "Site", "API", "SSE", "Health", "Solar", "Battery", "Incidents", "Latency", "System"
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        table = self.query_one("#noc-table", DataTable)
        table.clear(columns=False)
        for item in all_states:
            marker = "▶ " if item.name == state.name else "  "
            score = first(item.health_score, "score", "health_score", "total")
            table.add_row(
                marker + item.name,
                "UP" if item.online else "DOWN",
                "LIVE" if item.stream_online else "—",
                fmt_number(score, "/100", 0),
                fmt_number(metric(item.latest, "solar_input_power_w"), "W", 0),
                fmt_number(metric(item.latest, "battery_voltage_v"), "V", 2),
                str(len(item.incidents)),
                fmt_number(item.latency_ms, "ms", 0),
                text(item.system_uid),
            )
