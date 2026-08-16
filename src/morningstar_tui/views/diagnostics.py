"""v0.9 controller diagnostics, health, charge-cycle and polling workspace."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import ControllerIntegrityBundle, SiteState
from morningstar_tui.util.explorer import scalar_rows
from morningstar_tui.util.formatting import fmt_age
from morningstar_tui.views.base import DashboardView


class DiagnosticsView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("CONTROLLER DIAGNOSTICS", classes="view-title")
        yield Static(
            "Health penalties, charge-cycle evidence, charge forecast, polling performance, history summary, incidents and recent samples.",
            classes="hint",
        )
        yield Static("Select a controller from Controllers (2).", id="diag-summary", classes="panel")
        yield Static("HEALTH SCORE / EVIDENCE", classes="view-title")
        yield DataTable(id="diag-health", zebra_stripes=True)
        yield Static("CHARGE CYCLE / FORECAST", classes="view-title")
        yield DataTable(id="diag-charge", zebra_stripes=True)
        yield Static("POLLING / HISTORY", classes="view-title")
        yield DataTable(id="diag-polling", zebra_stripes=True)
        yield Static("INCIDENTS / RECENT SAMPLES", classes="view-title")
        yield DataTable(id="diag-events", zebra_stripes=True)

    def on_mount(self) -> None:
        for selector in ("#diag-health", "#diag-charge", "#diag-polling", "#diag-events"):
            self.query_one(selector, DataTable).add_columns("Field", "Value", "Unit", "Quality / source")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        uid = state.selected_controller_uid
        if not uid:
            self.query_one("#diag-summary", Static).update(
                "No controller selected. Open Controllers (2), select a row, then press Enter."
            )
            self._clear()
            return
        bundle = state.controller_integrity.get(uid)
        if bundle is None:
            self.query_one("#diag-summary", Static).update(f"{uid}\nLoading diagnostics asynchronously…")
            self._clear()
            return
        self.query_one("#diag-summary", Static).update(
            f"Controller: {uid}   cache age: {fmt_age(bundle.loaded_at)}"
            + (f"\nError: {bundle.error}" if bundle.error else "")
        )
        self._fill("#diag-health", bundle.health_score, max_rows=180)
        self._fill(
            "#diag-charge",
            {"cycle": bundle.charge_cycle, "forecast": bundle.charge_forecast},
            max_rows=220,
        )
        self._fill(
            "#diag-polling",
            {
                "performance": bundle.polling_performance,
                "performance_history": bundle.polling_history,
                "history_summary": bundle.history_summary,
                "retained_history": bundle.retained_summary,
            },
            max_rows=300,
        )
        self._fill(
            "#diag-events",
            {"incidents": bundle.incidents, "samples": bundle.samples},
            max_rows=300,
        )

    def _clear(self) -> None:
        for selector in ("#diag-health", "#diag-charge", "#diag-polling", "#diag-events"):
            self.query_one(selector, DataTable).clear(columns=False)

    def _fill(self, selector: str, payload: object, *, max_rows: int) -> None:
        table = self.query_one(selector, DataTable)
        table.clear(columns=False)
        values = scalar_rows(payload, max_rows=max_rows)
        if not values:
            table.add_row("—", "No data returned by API", "", "")
            return
        for path, value, unit, quality in values:
            table.add_row(path, value, unit, quality)
