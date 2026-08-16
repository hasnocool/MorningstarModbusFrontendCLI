"""Expanded system power-flow and energy-ledger workspace."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.explorer import compact_mapping
from morningstar_tui.util.formatting import fmt_number, metric
from morningstar_tui.views.base import DashboardView
from morningstar_tui.widgets import MetricCard


def _first_value(*values: object | None) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


class PowerFlowView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("POWER / ENERGY", classes="view-title")
        with Horizontal(classes="metric-row"):
            yield MetricCard(id="pf-solar")
            yield MetricCard(id="pf-charge")
            yield MetricCard(id="pf-battery")
            yield MetricCard(id="pf-load")
        with Horizontal(classes="metric-row"):
            yield MetricCard(id="pf-system-current")
            yield MetricCard(id="pf-battery-current")
            yield MetricCard(id="pf-load-current")
            yield MetricCard(id="pf-residual")
        yield Static(id="pf-diagram", classes="panel")
        yield Static(id="pf-ledger", classes="panel")
        yield Static(id="pf-evidence", classes="panel")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        source = state.power_flow or state.latest
        solar = _first_value(
            metric(source, "solar_input_power_w"), metric(state.latest, "solar_input_power_w")
        )
        controller_charge = _first_value(
            metric(source, "charge_output_power_w"), metric(state.latest, "charge_output_power_w")
        )
        system_charge = _first_value(metric(source, "system_charge_power_w"), controller_charge)
        battery = metric(source, "battery_net_power_w")
        load = _first_value(metric(source, "dc_load_power_w"), metric(source, "load_power_w"))
        system_current = _first_value(
            metric(source, "system_charge_current_a"), metric(state.latest, "system_charge_current_a")
        )
        battery_current = _first_value(
            metric(source, "battery_net_current_a"), metric(state.latest, "battery_net_current_a")
        )
        load_current = _first_value(
            metric(source, "system_load_current_a"), metric(state.latest, "system_load_current_a")
        )
        residual = _first_value(
            metric(source, "dc_power_residual_w"),
            metric(source, "whole_system_dc_power_residual_w"),
            metric(source, "power_residual_w"),
        )
        self.query_one("#pf-solar", MetricCard).set_metric("PV input", fmt_number(solar, "W", 0))
        self.query_one("#pf-charge", MetricCard).set_metric(
            "System charge",
            fmt_number(system_charge, "W", 0),
            f"controller output {fmt_number(controller_charge, 'W', 0)}",
        )
        self.query_one("#pf-battery", MetricCard).set_metric("Battery net", fmt_number(battery, "W", 0))
        self.query_one("#pf-load", MetricCard).set_metric("DC load", fmt_number(load, "W", 0))
        self.query_one("#pf-system-current", MetricCard).set_metric(
            "System charge I", fmt_number(system_current, "A", 1)
        )
        self.query_one("#pf-battery-current", MetricCard).set_metric(
            "Battery net I", fmt_number(battery_current, "A", 1)
        )
        self.query_one("#pf-load-current", MetricCard).set_metric(
            "Load I", fmt_number(load_current, "A", 1)
        )
        self.query_one("#pf-residual", MetricCard).set_metric("DC residual", fmt_number(residual, "W", 0))
        self.query_one("#pf-diagram", Static).update(
            "[b]Electrical flow[/b]\n\n"
            f"PV {fmt_number(solar, 'W', 0):>10}  ───▶  controllers {fmt_number(controller_charge, 'W', 0):>10}\n"
            f"{'':24}│\n"
            f"{'':24}├──▶ battery net {fmt_number(battery, 'W', 0):>10}\n"
            f"{'':24}└──▶ DC loads    {fmt_number(load, 'W', 0):>10}\n\n"
            f"System charge current {fmt_number(system_current, 'A', 1)}   "
            f"battery net current {fmt_number(battery_current, 'A', 1)}   "
            f"load current {fmt_number(load_current, 'A', 1)}\n"
            "Unknown values stay unknown when the API cannot defend the measurement or derivation."
        )
        ledger_keys = (
            "daily_charge_wh",
            "system_daily_charge_wh",
            "system_daily_charge_ah",
            "system_daily_battery_ah",
            "system_daily_load_ah",
            "external_source_charge_wh",
            "external_source_charge_ah",
            "battery_discharge_wh",
            "load_consumption_wh",
            "conversion_loss_wh",
            "unaccounted_energy_wh",
        )
        lines = ["[b]Energy ledger[/b]"]
        for key in ledger_keys:
            value = metric(state.energy_ledger, key)
            if value is None:
                value = metric(state.site_details.energy, key)
            unit = "Ah" if key.endswith("_ah") else "Wh"
            lines.append(f"{key:32} {fmt_number(value, unit, 1)}")
        self.query_one("#pf-ledger", Static).update("\n".join(lines))
        self.query_one("#pf-evidence", Static).update(
            "[b]Power-flow evidence / provenance[/b]\n" + compact_mapping(state.power_flow, limit=45)
        )
