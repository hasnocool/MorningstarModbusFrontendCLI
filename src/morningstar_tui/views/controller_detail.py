"""v0.6 controller drill-down, data-integrity and energy reconciliation console."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import ControllerIntegrityBundle, SiteState
from morningstar_tui.util.analytics import (
    coverage_day_rows,
    coverage_percent,
    energy_daily_rows,
    energy_difference_percent,
    energy_integrated_wh,
    energy_reported_wh,
    gap_counts,
    realtime_coverage_percent,
    rows,
)
from morningstar_tui.util.formatting import (
    first,
    fmt_age,
    fmt_energy_wh,
    fmt_number,
    fmt_percent,
    metric,
    text,
)
from morningstar_tui.views.base import DashboardView


class ControllerDetailView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("CONTROLLER OPERATIONS", classes="view-title")
        yield Static(
            "v0.6: live identity + evidence coverage + recovered gaps + controller-vs-local energy. Esc returns to the previous view.",
            classes="hint",
        )
        yield Static("Select a controller from view 2 and press Enter.", id="controller-summary", classes="panel")
        yield Static("", id="coverage-calendar", classes="panel")
        yield Static("HISTORY GAPS", classes="view-title")
        yield DataTable(id="controller-gaps-table", zebra_stripes=True, cursor_type="row")
        yield Static("ENERGY VERIFICATION — 30 DAYS", classes="view-title")
        yield DataTable(id="controller-energy-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#controller-gaps-table", DataTable).add_columns(
            "From", "To", "Days", "Status", "Recoverability"
        )
        self.query_one("#controller-energy-table", DataTable).add_columns(
            "Date", "Controller", "Local", "Δ", "Samples", "Skipped"
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        uid = state.selected_controller_uid
        if not uid:
            self.query_one("#controller-summary", Static).update(
                "No controller selected. Open Controllers (2), highlight a row, and press Enter."
            )
            self._clear_tables()
            return
        bundle = state.controller_integrity.get(uid)
        if bundle is None:
            self.query_one("#controller-summary", Static).update(
                f"{uid}\nLoading controller evidence asynchronously…"
            )
            self.query_one("#coverage-calendar", Static).update("")
            self._clear_tables()
            return
        self.query_one("#controller-summary", Static).update(_summary(uid, bundle))
        self.query_one("#coverage-calendar", Static).update(_coverage_calendar(bundle))
        self._render_gaps(bundle)
        self._render_energy(bundle)

    def _clear_tables(self) -> None:
        self.query_one("#controller-gaps-table", DataTable).clear(columns=False)
        self.query_one("#controller-energy-table", DataTable).clear(columns=False)

    def _render_gaps(self, bundle: ControllerIntegrityBundle) -> None:
        table = self.query_one("#controller-gaps-table", DataTable)
        table.clear(columns=False)
        for item in rows(bundle.gaps, "gaps", "intervals", "items", "data"):
            table.add_row(
                text(item.get("from") or item.get("start") or item.get("date")),
                text(item.get("to") or item.get("end") or item.get("date")),
                text(item.get("duration_days") or item.get("days") or 1),
                text(item.get("status") or item.get("state")),
                text(item.get("recoverability") or item.get("source")),
            )

    def _render_energy(self, bundle: ControllerIntegrityBundle) -> None:
        table = self.query_one("#controller-energy-table", DataTable)
        table.clear(columns=False)
        daily = energy_daily_rows(bundle.energy_daily_30d)
        for item in reversed(daily[-30:]):
            table.add_row(
                text(item.get("date") or item.get("day")),
                fmt_energy_wh(item.get("controller_reported_wh")),
                fmt_energy_wh(item.get("integrated_output_wh")),
                fmt_percent(item.get("difference_percent")),
                text(item.get("output_power_sample_count") or item.get("sample_count")),
                _seconds(item.get("skipped_between_sample_seconds") or item.get("skipped_seconds")),
            )


def _summary(uid: str, bundle: ControllerIntegrityBundle) -> str:
    detail = bundle.detail
    counts = gap_counts(bundle.gaps)
    coverage = coverage_percent(bundle.coverage)
    realtime = realtime_coverage_percent(bundle.coverage)
    reported_30 = energy_reported_wh(bundle.energy_summary_30d)
    integrated_30 = energy_integrated_wh(bundle.energy_summary_30d)
    delta_30 = energy_difference_percent(bundle.energy_summary_30d)
    reported_90 = energy_reported_wh(bundle.energy_summary_90d)
    latest = bundle.latest
    lines = [
        f"{text(detail.get('model') or detail.get('model_name') or detail.get('product'), 'Morningstar controller')}  {uid}",
        f"Status: {text(detail.get('status') or detail.get('state') or detail.get('online'))}   Serial: {text(detail.get('serial_number') or detail.get('serial'))}   Firmware: {text(detail.get('firmware') or detail.get('firmware_version'))}",
        f"Battery: {fmt_number(metric(latest, 'battery_voltage_v'), 'V', 2)}   Solar: {fmt_number(metric(latest, 'solar_input_power_w'), 'W', 0)}   Charge: {fmt_number(metric(latest, 'battery_charge_current_a'), 'A', 1)}   Stage: {text(metric(latest, 'charge_state'))}",
        "",
        f"Evidence: daily {fmt_percent(coverage)}   live {fmt_percent(realtime)}   recovered {counts['recovered']}d   partial {counts['partial']}d   missing {counts['missing']}d",
        f"Energy 30d: controller {fmt_energy_wh(reported_30)}   local {fmt_energy_wh(integrated_30)}   Δ {fmt_percent(delta_30)}",
        f"Energy 90d: controller {fmt_energy_wh(reported_90)}   cache age {fmt_age(bundle.loaded_at)}",
    ]
    if bundle.error:
        lines.append(f"Error: {bundle.error}")
    sync = first(
        bundle.coverage,
        "retained_history_sync.completed_at",
        "retained_history_sync.finished_at",
        "last_retained_sync_at",
    )
    if sync:
        lines.append(f"Last retained-history sync: {text(sync)}")
    return "\n".join(lines)


def _coverage_calendar(bundle: ControllerIntegrityBundle) -> str:
    days = coverage_day_rows(bundle.coverage)
    if not days:
        return "COVERAGE CALENDAR\nDay-level rows are not present in this API response; summary percentages above remain authoritative."
    cells: list[str] = []
    legend = "█ live  ▓ recovered  ▒ partial  · missing"
    for item in days[-90:]:
        status = str(
            item.get("status")
            or item.get("state")
            or item.get("coverage_state")
            or item.get("evidence")
            or ""
        ).lower()
        glyph = _coverage_glyph(status, item)
        raw_date = item.get("date") or item.get("day")
        label = _day_label(raw_date)
        cells.append(f"{label}{glyph}")
    lines = ["COVERAGE — LAST 90 DAYS", legend]
    for index in range(0, len(cells), 15):
        lines.append(" ".join(cells[index : index + 15]))
    return "\n".join(lines)


def _coverage_glyph(status: str, item: dict[str, Any]) -> str:
    if "recover" in status:
        return "▓"
    if "partial" in status:
        return "▒"
    if "missing" in status or "none" in status:
        return "·"
    if "live" in status or "realtime" in status or item.get("has_live_samples"):
        return "█"
    if item.get("controller_record_complete"):
        return "▓"
    return "·"


def _day_label(value: object) -> str:
    if not value:
        return "??"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return f"{parsed.day:02d}"
    except ValueError:
        raw = str(value)
        return raw[-2:] if len(raw) >= 2 else raw


def _seconds(value: object) -> str:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return "—"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
