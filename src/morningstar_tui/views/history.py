"""v0.2 multi-resolution historical telemetry view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import values_from_history
from morningstar_tui.util.sparkline import sparkline
from morningstar_tui.views.base import DashboardView


class HistoryView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("HISTORY", classes="view-title")
        yield Static(
            "Use [ and ] to change window; use m to cycle metrics. Storage-v2/rollups are consumed through the API.",
            classes="hint",
        )
        yield Static(id="history-chart", classes="panel tall")
        yield Static(id="history-stats", classes="panel")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        values = values_from_history(state.history)
        if values:
            minimum, maximum = min(values), max(values)
            average = sum(values) / len(values)
        else:
            minimum = maximum = average = 0.0
        self.query_one("#history-chart", Static).update(
            f"[b]{state.history_metric} — {state.history_window}[/b]\n\n"
            f"{sparkline(values, width=90) or 'No history loaded yet.'}"
        )
        self.query_one("#history-stats", Static).update(
            f"points {len(values)}  |  min {minimum:.2f}  |  avg {average:.2f}  |  max {maximum:.2f}"
        )
