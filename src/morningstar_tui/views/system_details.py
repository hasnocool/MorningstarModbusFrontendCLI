"""v0.9 expanded system/site metadata, health, energy and metric catalog view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.explorer import compact_mapping, record_rows, scalar_rows
from morningstar_tui.util.formatting import text
from morningstar_tui.views.base import DashboardView


class SystemDetailsView(DashboardView):
    """Expose API system data that is too detailed for the command-center overview."""

    def compose(self) -> ComposeResult:
        yield Static("SYSTEM / SITE DETAILS", classes="view-title")
        yield Static(
            "Source-backed system metadata, normalized metric catalog, energy summary, health and baselines.",
            classes="hint",
        )
        yield Static("Loading system metadata…", id="system-detail-summary", classes="panel")
        yield Static("NORMALIZED METRIC CATALOG", classes="view-title")
        yield DataTable(id="system-metrics-table", zebra_stripes=True, cursor_type="row")
        yield Static("SYSTEM ENERGY", classes="view-title")
        yield DataTable(id="system-energy-table", zebra_stripes=True)
        yield Static("HEALTH / BASELINES", classes="view-title")
        yield DataTable(id="system-health-table", zebra_stripes=True)

    def on_mount(self) -> None:
        self.query_one("#system-metrics-table", DataTable).add_columns(
            "Metric", "Aggregation / authority", "Unit", "Description"
        )
        self.query_one("#system-energy-table", DataTable).add_columns("Field", "Value", "Unit", "Quality")
        self.query_one("#system-health-table", DataTable).add_columns("Field", "Value", "Unit", "Quality")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        details = state.site_details
        summary = [
            f"Site: {state.name}   system_uid: {state.system_uid}   API: {state.base_url}",
            "",
            compact_mapping(state.system, limit=24),
        ]
        if details.error:
            summary.append(f"\nExtended-data error: {details.error}")
        self.query_one("#system-detail-summary", Static).update("\n".join(summary))
        self._metrics(details.metrics_catalog)
        self._key_value_table("#system-energy-table", details.energy)
        combined = {
            "health": state.health,
            "health_score": state.health_score,
            "baselines": state.baselines,
        }
        self._key_value_table("#system-health-table", combined, max_rows=180)

    def _metrics(self, payload: object) -> None:
        table = self.query_one("#system-metrics-table", DataTable)
        table.clear(columns=False)
        rows = record_rows(payload, "metrics", "catalog")
        if rows:
            for item in rows[:250]:
                table.add_row(
                    text(item.get("name") or item.get("metric") or item.get("semantic")),
                    text(item.get("aggregation") or item.get("authority") or item.get("strategy")),
                    text(item.get("unit")),
                    text(item.get("description") or item.get("meaning") or item.get("label")),
                )
            return
        for path, value, unit, quality in scalar_rows(payload, max_rows=250):
            table.add_row(path, quality, unit, value)

    def _key_value_table(self, selector: str, payload: object, *, max_rows: int = 120) -> None:
        table = self.query_one(selector, DataTable)
        table.clear(columns=False)
        for path, value, unit, quality in scalar_rows(payload, max_rows=max_rows):
            table.add_row(path, value, unit, quality)
