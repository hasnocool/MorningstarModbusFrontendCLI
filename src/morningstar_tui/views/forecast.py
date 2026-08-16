"""v0.3 predictive operations view."""

from __future__ import annotations

from collections.abc import Mapping

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import first, fmt_energy_wh, fmt_percent, number, text
from morningstar_tui.util.sparkline import sparkline
from morningstar_tui.views.base import DashboardView
from morningstar_tui.widgets import MetricCard


class ForecastView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("PREDICTIVE OPERATIONS", classes="view-title")
        with Horizontal(classes="metric-row"):
            yield MetricCard(id="fc-observed")
            yield MetricCard(id="fc-p50")
            yield MetricCard(id="fc-float")
            yield MetricCard(id="fc-confidence")
        yield Static(id="fc-curve", classes="panel")
        yield Static(id="fc-charge", classes="panel")
        yield Static(id="fc-accuracy", classes="panel")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        forecast = state.forecast
        observed = first(
            forecast,
            "solar.energy.observed_input_wh",
            "solar.observed_energy_wh",
            "solar.observed_so_far_wh",
        )
        p50 = first(
            forecast,
            "solar.energy.eod_p50_wh",
            "solar.projected_end_of_day_wh.p50",
            "solar.projected_eod_wh.p50",
            "solar.projected_end_of_day_energy_wh.p50",
        )
        probability = first(forecast, "charge.all_controllers_float_probability")
        confidence = first(forecast, "confidence", "solar.confidence")
        self.query_one("#fc-observed", MetricCard).set_metric("Observed", fmt_energy_wh(observed))
        self.query_one("#fc-p50", MetricCard).set_metric("Projected P50", fmt_energy_wh(p50))
        self.query_one("#fc-float", MetricCard).set_metric(
            "All Float chance", fmt_percent(probability, ratio=True)
        )
        self.query_one("#fc-confidence", MetricCard).set_metric("Confidence", text(confidence))

        curve = first(forecast, "solar.curve")
        observed_curve: list[float] = []
        p10_curve: list[float] = []
        p50_curve: list[float] = []
        p90_curve: list[float] = []
        if isinstance(curve, list):
            for point in curve:
                if not isinstance(point, Mapping):
                    continue
                for target, key in (
                    (observed_curve, "observed_w"),
                    (p10_curve, "p10_w"),
                    (p50_curve, "p50_w"),
                    (p90_curve, "p90_w"),
                ):
                    value = number(point.get(key))
                    if value is not None:
                        target.append(value)
        self.query_one("#fc-curve", Static).update(
            "[b]Today's solar curve[/b]\n"
            f"observed {sparkline(observed_curve, width=72) or '—'}\n"
            f"P10      {sparkline(p10_curve, width=72) or '—'}\n"
            f"P50      {sparkline(p50_curve, width=72) or '—'}\n"
            f"P90      {sparkline(p90_curve, width=72) or '—'}"
        )
        charge = first(forecast, "charge.controllers")
        lines = ["[b]Charge outlook[/b]"]
        if isinstance(charge, list):
            for item in charge:
                if not isinstance(item, Mapping):
                    continue
                uid = text(item.get("controller_uid"))
                stage = text(item.get("current_state") or item.get("current_charge_state"))
                chance = fmt_percent(item.get("float_probability"), ratio=True)
                expected = text(item.get("expected_float_at") or item.get("median_first_float_time"))
                lines.append(f"{uid:20} {stage:12} Float {chance:8} expected {expected}")
        if len(lines) == 1:
            lines.append("insufficient evidence")
        self.query_one("#fc-charge", Static).update("\n".join(lines))
        accuracy = state.forecast_accuracy
        self.query_one("#fc-accuracy", Static).update(
            "[b]Backtest calibration[/b]\n"
            f"evaluated days: {text(first(accuracy, 'evaluated_days', 'count'))}\n"
            f"median P50 APE: {fmt_percent(first(accuracy, 'median_absolute_error_percent', 'median_absolute_percentage_error', 'median_ape'))}\n"
            f"mean P50 APE: {fmt_percent(first(accuracy, 'mean_absolute_error_percent', 'mean_absolute_percentage_error', 'mean_ape'))}\n"
            f"P10-P90 coverage: {fmt_percent(first(accuracy, 'p10_p90_interval_coverage', 'interval_coverage', 'p10_p90_coverage'), ratio=True)}"
        )
