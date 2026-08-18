"""Expanded controller inventory with integrity summaries and workspace selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.analytics import coverage_percent, energy_difference_percent
from morningstar_tui.util.formatting import fmt_age, fmt_percent, text
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
            "Enter opens full live telemetry. D = data integrity/energy, X = diagnostics. Integrity columns hydrate asynchronously.",
            classes="hint",
        )
        yield DataTable(id="controllers-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#controllers-table", DataTable).add_columns(
            "Controller UID",
            "Status",
            "Model",
            "Serial",
            "Firmware",
            "Transport",
            "Endpoint",
            "Identity",
            "Last seen",
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
            detail = integrity.detail if integrity else {}
            data_quality = fmt_percent(coverage_percent(integrity.coverage)) if integrity else "…"
            energy_delta = (
                fmt_percent(energy_difference_percent(integrity.energy_summary_30d))
                if integrity
                else "…"
            )
            last_seen = (
                item.get("last_seen")
                or item.get("observed_at")
                or detail.get("last_seen")
                or detail.get("observed_at")
            )
            table.add_row(
                controller_uid,
                text(item.get("status") or item.get("state") or item.get("online")),
                text(item.get("model") or item.get("model_name") or item.get("product") or detail.get("model")),
                text(item.get("serial_number") or item.get("serial") or detail.get("serial_number") or detail.get("serial")),
                text(item.get("firmware") or item.get("firmware_version") or detail.get("firmware") or detail.get("firmware_version")),
                text(item.get("transport") or item.get("transport_type") or detail.get("transport")),
                text(item.get("endpoint") or item.get("device") or item.get("host") or item.get("port") or detail.get("endpoint")),
                text(item.get("identity_confidence") or item.get("confidence") or detail.get("identity_confidence")),
                fmt_age(last_seen) if last_seen else "—",
                data_quality,
                energy_delta,
            )
