"""v0.8 fleet comparison and long-term controller analytics."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.analytics import (
    aggregate,
    coverage_percent,
    energy_difference_percent,
    energy_reported_wh,
    weighted_average,
)
from morningstar_tui.util.formatting import first, fmt_energy_wh, fmt_number, fmt_percent, text
from morningstar_tui.views.base import DashboardView


class FleetView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("FLEET COMPARISON / LONG-TERM ANALYTICS", classes="view-title")
        yield Static(
            "v0.8 compares API sites and controllers using 90-day evidence coverage plus 30/90-day controller energy summaries. Refresh with R if source data changes.",
            classes="hint",
        )
        yield Static("SITE COMPARISON", classes="view-title")
        yield DataTable(id="fleet-sites-table", zebra_stripes=True, cursor_type="row")
        yield Static("CONTROLLER COMPARISON", classes="view-title")
        yield DataTable(id="fleet-controllers-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#fleet-sites-table", DataTable).add_columns(
            "Site",
            "API",
            "Controllers",
            "Health",
            "Data 90d",
            "Energy 30d",
            "Energy 90d",
            "Energy Δ 30d",
            "Incidents",
        )
        self.query_one("#fleet-controllers-table", DataTable).add_columns(
            "Site",
            "Controller",
            "Model",
            "Data 90d",
            "Energy 30d",
            "Energy 90d",
            "Energy Δ 30d",
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del state
        sites = self.query_one("#fleet-sites-table", DataTable)
        controllers = self.query_one("#fleet-controllers-table", DataTable)
        sites.clear(columns=False)
        controllers.clear(columns=False)

        for site in all_states:
            bundles = list(site.controller_integrity.values())
            coverages = [(coverage_percent(bundle.coverage), 1.0) for bundle in bundles]
            reported_30 = aggregate(
                [energy_reported_wh(bundle.energy_summary_30d) for bundle in bundles]
            )
            reported_90 = aggregate(
                [energy_reported_wh(bundle.energy_summary_90d) for bundle in bundles]
            )
            deltas = [
                energy_difference_percent(bundle.energy_summary_30d) for bundle in bundles
            ]
            present_deltas = [value for value in deltas if value is not None]
            mean_delta = sum(present_deltas) / len(present_deltas) if present_deltas else None
            sites.add_row(
                site.name,
                "UP" if site.online else "DOWN",
                str(len(site.controllers)),
                fmt_number(first(site.health_score, "score", "health_score", "total"), "/100", 0),
                fmt_percent(weighted_average(coverages)) if bundles else "loading…",
                fmt_energy_wh(reported_30),
                fmt_energy_wh(reported_90),
                fmt_percent(mean_delta),
                str(len(site.incidents)),
            )

            model_by_uid = {
                str(item.get("controller_uid")): text(
                    item.get("model") or item.get("model_name") or item.get("product")
                )
                for item in site.controllers
                if item.get("controller_uid")
            }
            for uid, bundle in site.controller_integrity.items():
                controllers.add_row(
                    site.name,
                    uid,
                    model_by_uid.get(uid, text(bundle.detail.get("model") or bundle.detail.get("model_name"))),
                    fmt_percent(coverage_percent(bundle.coverage)),
                    fmt_energy_wh(energy_reported_wh(bundle.energy_summary_30d)),
                    fmt_energy_wh(energy_reported_wh(bundle.energy_summary_90d)),
                    fmt_percent(energy_difference_percent(bundle.energy_summary_30d)),
                )
