"""v0.3 persistent incident command center."""

from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import event_summary, fmt_age, text
from morningstar_tui.views.base import DashboardView


class IncidentsView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("INCIDENT COMMAND CENTER", classes="view-title")
        yield Static(id="incident-summary", classes="panel")
        yield DataTable(id="incidents-table", zebra_stripes=True, cursor_type="row")
        yield Static(id="incident-evidence", classes="panel")

    def on_mount(self) -> None:
        table = self.query_one("#incidents-table", DataTable)
        table.add_columns("Severity", "Category", "Finding", "Controller", "Age", "Count")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        counts = {level: 0 for level in ("critical", "warning", "info")}
        table = self.query_one("#incidents-table", DataTable)
        table.clear(columns=False)
        for item in state.incidents:
            severity = str(item.get("severity") or "info").lower()
            counts[severity] = counts.get(severity, 0) + 1
            table.add_row(
                severity.upper(),
                text(item.get("category")),
                event_summary(item),
                text(item.get("controller_uid") or item.get("scope_uid") or "system"),
                fmt_age(item.get("opened_at") or item.get("first_seen") or item.get("created_at")),
                text(item.get("occurrence_count") or item.get("count") or 1),
            )
        self.query_one("#incident-summary", Static).update(
            f"active {len(state.incidents)}  |  critical {counts.get('critical', 0)}  |  "
            f"warning {counts.get('warning', 0)}  |  info {counts.get('info', 0)}"
        )
        if state.incidents:
            evidence = state.incidents[0].get("evidence") or state.incidents[0]
            rendered = json.dumps(evidence, indent=2, sort_keys=True, default=str)[:5000]
            self.query_one("#incident-evidence", Static).update(f"[b]Evidence[/b]\n{rendered}")
        else:
            self.query_one("#incident-evidence", Static).update("No active incident evidence.")
