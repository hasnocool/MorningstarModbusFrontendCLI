"""Unified chronological event stream view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import event_summary, text
from morningstar_tui.views.base import DashboardView


class EventsView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("EVENT TIMELINE", classes="view-title")
        yield DataTable(id="events-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#events-table", DataTable).add_columns(
            "Time", "Type", "Controller", "Summary", "Source"
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        table = self.query_one("#events-table", DataTable)
        table.clear(columns=False)
        for item in state.events[:500]:
            table.add_row(
                text(item.get("observed_at") or item.get("created_at") or item.get("timestamp")),
                text(item.get("event_type") or item.get("type")),
                text(item.get("controller_uid") or item.get("source_uid")),
                event_summary(item),
                text(item.get("source") or item.get("provenance")),
            )
