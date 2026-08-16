"""System power-flow and energy-ledger view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import fmt_number, metric
from morningstar_tui.views.base import DashboardView
from morningstar_tui.widgets import MetricCard


class PowerFlowView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("POWER FLOW", classes="view-title")
        with Horizontal(classes="metric-row"):
            yield MetricCard(id="pf-solar")
            yield MetricCard(id="pf-charge")
            yield MetricCard(id="pf-battery")
            yield MetricCard(id="pf-load")
        yield Static(id="pf-diagram", classes="panel")
        yield Static(id="pf-ledger", classes="panel")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        source = state.power_flow or state.latest
        solar = metric(source, "solar_input_power_w") or metric(state.latest, "solar_input_power_w")
        charge = metric(source, "system_charge_power_w") or metric(source, "charge_output_power_w")
        battery = metric(source, "battery_net_power_w")
        load = metric(source, "dc_load_power_w") or metric(source, "load_power_w")
        self.query_one("#pf-solar", MetricCard).set_metric("PV input", fmt_number(solar, "W", 0))
        self.query_one("#pf-charge", MetricCard).set_metric("Charge power", fmt_number(charge, "W", 0))
        self.query_one("#pf-battery", MetricCard).set_metric("Battery net", fmt_number(battery, "W", 0))
        self.query_one("#pf-load", MetricCard).set_metric("DC load", fmt_number(load, "W", 0))
        self.query_one("#pf-diagram", Static).update(
            "[b]Electrical flow[/b]\n\n"
            f"PV {fmt_number(solar, 'W', 0):>10}  ───▶  controllers  ───▶  "
            f"battery {fmt_number(battery, 'W', 0):>10}\n"
            f"{'':29}└──────────────▶  loads {fmt_number(load, 'W', 0):>10}\n\n"
            "Values remain unknown when the API cannot defend the derivation."
        )
        ledger_keys = (
            "daily_charge_wh",
            "system_daily_charge_wh",
            "external_source_charge_wh",
            "battery_discharge_wh",
            "load_consumption_wh",
            "unaccounted_energy_wh",
        )
        lines = ["[b]Energy ledger[/b]"]
        for key in ledger_keys:
            value = metric(state.energy_ledger, key)
            lines.append(f"{key:30} {fmt_number(value, 'Wh', 1)}")
        self.query_one("#pf-ledger", Static).update("\n".join(lines))
