"""v0.1/v0.2 site command-center overview."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import (
    first,
    fmt_energy_wh,
    fmt_number,
    fmt_percent,
    metric,
    text,
)
from morningstar_tui.views.base import DashboardView
from morningstar_tui.widgets import MetricCard


class OverviewView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("SYSTEM OVERVIEW", classes="view-title")
        with Horizontal(classes="metric-row"):
            yield MetricCard(id="ov-health")
            yield MetricCard(id="ov-solar")
            yield MetricCard(id="ov-battery")
            yield MetricCard(id="ov-stage")
        with Horizontal(classes="metric-row"):
            yield MetricCard(id="ov-energy")
            yield MetricCard(id="ov-forecast")
            yield MetricCard(id="ov-float")
            yield MetricCard(id="ov-incidents")
        with Vertical(classes="panel"):
            yield Static("[b]Connection[/b]", id="ov-connection")
            yield Static("[b]Forecast confidence[/b]", id="ov-confidence")
        yield Static("[b]Controllers[/b]")
        yield DataTable(id="ov-controllers", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#ov-controllers", DataTable)
        table.add_columns("Controller", "Status", "Model", "Last seen")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        score = first(state.health_score, "score", "health_score", "total")
        solar = metric(state.latest, "solar_input_power_w")
        battery = metric(state.latest, "battery_voltage_v")
        stage = metric(state.latest, "charge_state")
        observed_wh = first(
            state.forecast,
            "solar.observed_energy_wh",
            "solar.observed_so_far_wh",
            "observed_energy_wh",
        )
        projected = first(
            state.forecast,
            "solar.projected_end_of_day_wh.p50",
            "solar.projected_eod_wh.p50",
            "solar.projected_end_of_day_energy_wh.p50",
            "solar.projected_energy_wh.p50",
        )
        float_probability = first(
            state.forecast,
            "charge.all_controllers_float_probability",
            "all_controllers_float_probability",
        )
        confidence = first(state.forecast, "confidence", "solar.confidence")
        self.query_one("#ov-health", MetricCard).set_metric("Health", fmt_number(score, "/100", 0))
        self.query_one("#ov-solar", MetricCard).set_metric("Solar", fmt_number(solar, "W", 0))
        self.query_one("#ov-battery", MetricCard).set_metric("Battery", fmt_number(battery, "V", 2))
        self.query_one("#ov-stage", MetricCard).set_metric("Charge stage", text(stage))
        self.query_one("#ov-energy", MetricCard).set_metric("Observed solar", fmt_energy_wh(observed_wh))
        self.query_one("#ov-forecast", MetricCard).set_metric("Forecast EOD", fmt_energy_wh(projected))
        self.query_one("#ov-float", MetricCard).set_metric(
            "Float chance", fmt_percent(float_probability, ratio=True)
        )
        critical = sum(1 for item in state.incidents if str(item.get("severity", "")).lower() == "critical")
        self.query_one("#ov-incidents", MetricCard).set_metric(
            "Active incidents", str(len(state.incidents)), f"{critical} critical"
        )
        status = "ONLINE" if state.online else "OFFLINE"
        stream = "SSE live" if state.stream_online else "SSE down"
        latency = fmt_number(state.latency_ms, "ms", 0)
        error = f" | {state.last_error}" if state.last_error else ""
        self.query_one("#ov-connection", Static).update(
            f"[b]Connection[/b]  {state.name}  {status}  {stream}  REST {latency}{error}"
        )
        self.query_one("#ov-confidence", Static).update(
            f"[b]Forecast confidence[/b]  {text(confidence)}"
        )
        table = self.query_one("#ov-controllers", DataTable)
        table.clear(columns=False)
        for controller in state.controllers:
            uid = text(controller.get("controller_uid") or controller.get("controller_id") or "unknown")
            status_value = text(controller.get("status") or controller.get("state") or controller.get("online"))
            model = text(controller.get("model") or controller.get("model_name") or controller.get("product"))
            last_seen = text(controller.get("last_seen") or controller.get("observed_at") or "—")
            table.add_row(uid, status_value, model, last_seen)
