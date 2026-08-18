"""v0.9 full live telemetry explorer for normalized system and selected controller data."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.explorer import scalar_rows
from morningstar_tui.views.base import DashboardView


class TelemetryView(DashboardView):
    """Render substantially more live data than the compact overview cards."""

    def compose(self) -> ComposeResult:
        yield Static("LIVE TELEMETRY EXPLORER", classes="view-title")
        yield Static(
            "System values are normalized API semantics. Controller values preserve the selected controller's detailed payload.",
            classes="hint",
        )
        yield Static("SYSTEM NORMALIZED TELEMETRY", classes="view-title")
        yield DataTable(id="telemetry-system-table", zebra_stripes=True, cursor_type="row")
        yield Static("SELECTED CONTROLLER TELEMETRY", classes="view-title")
        yield Static("Select a controller in view 2 for controller-level data.", id="telemetry-controller-label", classes="hint")
        yield DataTable(id="telemetry-controller-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        for selector in ("#telemetry-system-table", "#telemetry-controller-table"):
            self.query_one(selector, DataTable).add_columns("Metric / path", "Value", "Unit", "Quality / source")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        self._fill("#telemetry-system-table", state.latest, max_rows=350)
        uid = state.selected_controller_uid
        table = self.query_one("#telemetry-controller-table", DataTable)
        if not uid:
            self.query_one("#telemetry-controller-label", Static).update(
                "No controller selected. Open Controllers (2), highlight one, then press Enter."
            )
            table.clear(columns=False)
            return
        bundle = state.controller_integrity.get(uid)
        self.query_one("#telemetry-controller-label", Static).update(f"Controller: {uid}")
        if bundle is None:
            table.clear(columns=False)
            table.add_row("loading", "controller data is being hydrated", "", "")
            return
        self._fill("#telemetry-controller-table", bundle.latest, max_rows=500)

    def _fill(self, selector: str, payload: object, *, max_rows: int) -> None:
        table = self.query_one(selector, DataTable)
        table.clear(columns=False)
        values = scalar_rows(payload, max_rows=max_rows)
        if not values:
            table.add_row("—", "No data returned by API", "", "")
            return
        for path, value, unit, quality in values:
            table.add_row(path, value, unit, quality)
