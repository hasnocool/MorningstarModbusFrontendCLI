"""Controller inventory and health view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import text
from morningstar_tui.views.base import DashboardView


class ControllersView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("CONTROLLERS", classes="view-title")
        yield Static(
            "Physical controller inventory uses controller_uid; endpoint changes should not create duplicates.",
            classes="hint",
        )
        yield DataTable(id="controllers-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#controllers-table", DataTable).add_columns(
            "Controller UID", "Status", "Model", "Transport", "Endpoint", "Identity"
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        table = self.query_one("#controllers-table", DataTable)
        table.clear(columns=False)
        for item in state.controllers:
            table.add_row(
                text(item.get("controller_uid") or item.get("controller_id")),
                text(item.get("status") or item.get("state") or item.get("online")),
                text(item.get("model") or item.get("model_name") or item.get("product")),
                text(item.get("transport") or item.get("transport_type")),
                text(item.get("endpoint") or item.get("device") or item.get("host") or item.get("port")),
                text(item.get("identity_confidence") or item.get("confidence") or item.get("serial_number")),
            )
