"""Controller inventory with v0.6 integrity summaries and drill-down selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.analytics import coverage_percent, energy_difference_percent
from morningstar_tui.util.formatting import fmt_percent, text
from morningstar_tui.views.base import DashboardView


class ControllerActivated(Message):
    """Posted when the operator opens a controller row."""

    def __init__(self, controller_uid: str) -> None:
        super().__init__()
        self.controller_uid = controller_uid


class ControllersView(DashboardView):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._row_uids: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static("CONTROLLERS", classes="view-title")
        yield Static(
            "Enter drills into the highlighted physical controller. Integrity columns are loaded lazily from API v0.6 evidence endpoints.",
            classes="hint",
        )
        yield DataTable(id="controllers-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#controllers-table", DataTable).add_columns(
            "Controller UID",
            "Status",
            "Model",
            "Transport",
            "Endpoint",
            "Identity",
            "Data",
            "Energy Δ",
        )

    def selected_controller_uid(self) -> str | None:
        table = self.query_one("#controllers-table", DataTable)
        row = table.cursor_row
        if 0 <= row < len(self._row_uids):
            return self._row_uids[row]
        return None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "controllers-table":
            return
        uid = self.selected_controller_uid()
        if uid:
            self.post_message(ControllerActivated(uid))

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        table = self.query_one("#controllers-table", DataTable)
        table.clear(columns=False)
        self._row_uids = []
        for item in state.controllers:
            controller_uid = str(item.get("controller_uid") or item.get("controller_id") or "")
            if not controller_uid:
                continue
            self._row_uids.append(controller_uid)
            integrity = state.controller_integrity.get(controller_uid)
            data_quality = fmt_percent(coverage_percent(integrity.coverage)) if integrity else "…"
            energy_delta = (
                fmt_percent(energy_difference_percent(integrity.energy_summary_30d))
                if integrity
                else "…"
            )
            table.add_row(
                controller_uid,
                text(item.get("status") or item.get("state") or item.get("online")),
                text(item.get("model") or item.get("model_name") or item.get("product")),
                text(item.get("transport") or item.get("transport_type")),
                text(item.get("endpoint") or item.get("device") or item.get("host") or item.get("port")),
                text(item.get("identity_confidence") or item.get("confidence") or item.get("serial_number")),
                data_quality,
                energy_delta,
            )
