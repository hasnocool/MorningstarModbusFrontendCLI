"""Textual application shell for the v0.9 terminal operations dashboard."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import inspect

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import ContentSwitcher, Footer, Header, Static

from morningstar_tui.config import AppConfig
from morningstar_tui.state import DashboardRuntime, SiteState
from morningstar_tui.views import (
    CommandChosen,
    CommandPaletteView,
    ControllerActivated,
    ControllerDetailView,
    ControllersView,
    DiagnosticsView,
    EventsView,
    FleetView,
    ForecastView,
    HistoryView,
    IncidentsView,
    InvestigationView,
    NOCView,
    OverviewView,
    PowerFlowView,
    SystemDetailsView,
    TelemetryView,
    TopologyView,
)
from morningstar_tui.views.base import DashboardView

_WINDOWS = ("1h", "6h", "24h", "7d", "30d", "180d", "1y")
_METRICS = (
    "solar_input_power_w",
    "charge_output_power_w",
    "battery_voltage_v",
    "battery_charge_current_a",
    "charge_state",
)
_VIEW_LABELS = {
    "overview": "Overview",
    "system": "System details",
    "controllers": "Controllers",
    "telemetry": "Live telemetry",
    "power": "Power & energy",
    "incidents": "Incidents",
    "forecast": "Forecast",
    "history": "History",
    "events": "Events",
    "investigation": "Investigation",
    "topology": "Topology",
    "diagnostics": "Diagnostics",
    "noc": "NOC",
    "controller-detail": "Data integrity",
    "fleet": "Fleet analytics",
    "palette": "Command palette",
}
_CONTROLLER_VIEWS = {"controller-detail", "telemetry", "diagnostics"}


class MorningstarTUI(App[None]):
    """Keyboard-first, read-only Morningstar operations console."""

    TITLE = "Morningstar Power Site"
    SUB_TITLE = "MorningstarModbusAPI terminal operations dashboard"
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        layout: vertical;
    }
    #navigation-bar {
        height: 2;
        padding: 0 1;
        text-style: bold;
        color: $text-muted;
    }
    ContentSwitcher {
        height: 1fr;
    }
    .view-title {
        text-style: bold;
        padding: 1 1 0 1;
        height: 3;
    }
    .hint {
        color: $text-muted;
        padding: 0 1 1 1;
    }
    .metric-row {
        height: 5;
        padding: 0 1;
    }
    .metric-row MetricCard {
        width: 1fr;
        margin: 0 1 0 0;
    }
    .panel {
        border: round $surface-lighten-2;
        margin: 0 1 1 1;
        padding: 1;
        height: auto;
    }
    .tall {
        min-height: 10;
    }
    DataTable {
        margin: 0 1 1 1;
        height: 1fr;
    }
    #command-query {
        margin: 0 1 1 1;
    }
    #controller-gaps-table, #controller-energy-table, #fleet-sites-table, #fleet-controllers-table,
    #telemetry-system-table, #telemetry-controller-table, #system-metrics-table, #system-energy-table,
    #system-health-table, #topology-components, #topology-relationships, #diag-health, #diag-charge,
    #diag-polling, #diag-events {
        min-height: 8;
    }
    .compact #navigation-bar {
        height: 1;
        padding: 0 1;
    }
    .compact .view-title {
        height: 2;
        padding: 0 1;
    }
    .compact .hint {
        padding: 0 1;
    }
    .compact .metric-row {
        height: 3;
    }
    .compact .panel {
        margin: 0 1;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("1", "show_overview", "Overview"),
        ("2", "show_controllers", "Controllers"),
        ("3", "show_power", "Power flow"),
        ("4", "show_incidents", "Incidents"),
        ("5", "show_forecast", "Forecast"),
        ("6", "show_history", "History"),
        ("7", "show_events", "Events"),
        ("8", "show_investigation", "Investigate"),
        ("9", "show_noc", "NOC"),
        ("s", "show_system", "System"),
        ("v", "show_telemetry", "Telemetry"),
        ("g", "show_topology", "Topology"),
        ("x", "show_diagnostics", "Diagnostics"),
        ("d", "show_controller_detail", "Data integrity"),
        ("f", "show_fleet", "Fleet"),
        Binding("ctrl+p", "command_palette", "Commands", priority=True),
        ("/", "command_palette", "Search"),
        Binding("escape", "back", "Back", priority=True),
        ("tab", "next_site", "Next site"),
        ("shift+tab", "previous_site", "Prev site"),
        ("[", "history_previous", "Shorter history"),
        ("]", "history_next", "Longer history"),
        ("m", "history_metric", "History metric"),
        ("t", "investigate_now", "Time travel"),
        ("-", "investigate_back", "-5m"),
        ("+", "investigate_forward", "+5m"),
        ("pageup", "investigate_back_hour", "-1h"),
        ("pagedown", "investigate_forward_hour", "+1h"),
        ("r", "refresh_site", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.runtime = DashboardRuntime(config)
        self._runtime_task: asyncio.Task[None] | None = None
        self._selected_site_index = 0
        self._dirty = True
        self._history_seeded: set[str] = set()
        self._nav_stack: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            "SYSTEM  [1] Overview [S] Details [3] Power [4] Incidents [5] Forecast  |  "
            "CONTROLLER  [2] Inventory [V] Telemetry [D] Data [X] Diagnostics  |  "
            "HISTORY  [6] History [7] Events [8] Investigate  |  SITE/FLEET [G] Topology [9] NOC [F] Fleet",
            id="navigation-bar",
            markup=False,
        )
        with ContentSwitcher(initial="overview", id="views"):
            yield OverviewView(id="overview")
            yield SystemDetailsView(id="system")
            yield ControllersView(id="controllers")
            yield TelemetryView(id="telemetry")
            yield PowerFlowView(id="power")
            yield IncidentsView(id="incidents")
            yield ForecastView(id="forecast")
            yield HistoryView(id="history")
            yield EventsView(id="events")
            yield InvestigationView(id="investigation")
            yield TopologyView(id="topology")
            yield DiagnosticsView(id="diagnostics")
            yield NOCView(id="noc")
            yield ControllerDetailView(id="controller-detail")
            yield FleetView(id="fleet")
            yield CommandPaletteView(id="palette")
        yield Footer()

    async def on_mount(self) -> None:
        if self.config.dashboard.compact:
            self.screen.add_class("compact")
        if len(self.config.sites) > 1:
            self.query_one("#views", ContentSwitcher).current = "noc"
        self.runtime.store.set_callback(self._state_changed)
        self._runtime_task = asyncio.create_task(self.runtime.run(), name="morningstar-runtime")
        self.call_after_refresh(self._start_state_flush_timer)

    def _start_state_flush_timer(self) -> None:
        """Start periodic rendering only after the first complete Textual composition pass."""

        self.set_interval(0.35, self._flush_state)

    async def on_unmount(self) -> None:
        self.runtime.store.set_callback(None)
        await self.runtime.close()
        if self._runtime_task is not None:
            self._runtime_task.cancel()
            await asyncio.gather(self._runtime_task, return_exceptions=True)

    def _state_changed(self, site_name: str) -> None:
        del site_name
        self._dirty = True

    async def _flush_state(self) -> None:
        if not self._dirty:
            return
        self._dirty = False
        states = await self.runtime.store.snapshots()
        if not states:
            return
        self._selected_site_index %= len(states)
        selected = states[self._selected_site_index]
        current = self._current_view()
        breadcrumb = _VIEW_LABELS.get(current, current)
        if current in _CONTROLLER_VIEWS and selected.selected_controller_uid:
            breadcrumb = f"Controllers › {selected.selected_controller_uid} › {breadcrumb}"
        self.sub_title = (
            f"{selected.name} · {selected.system_uid} · "
            f"{'online' if selected.online else 'offline'} · "
            f"{'SSE' if selected.stream_online else 'REST'} · {breadcrumb}"
        )
        for view in self.query(DashboardView):
            view.refresh_state(selected, states)
        if (
            selected.online
            and selected.name not in self._history_seeded
            and not self.config.dashboard.alert_only
        ):
            self._history_seeded.add(selected.name)
            asyncio.create_task(
                self.runtime.fetch_history(
                    selected.name,
                    selected.history_metric,
                    selected.history_window,
                )
            )

    async def _selected_state(self) -> SiteState:
        states = await self.runtime.store.snapshots()
        if not states:
            raise RuntimeError("no configured sites")
        self._selected_site_index %= len(states)
        return states[self._selected_site_index]

    def _current_view(self) -> str:
        return self.query_one("#views", ContentSwitcher).current or "overview"

    def _show(self, view_id: str, *, push: bool = True) -> None:
        switcher = self.query_one("#views", ContentSwitcher)
        current = switcher.current or "overview"
        if current == view_id:
            self._dirty = True
            return
        if push:
            self._nav_stack.append(current)
        switcher.current = view_id
        self._dirty = True

    def action_back(self) -> None:
        switcher = self.query_one("#views", ContentSwitcher)
        if self._nav_stack:
            switcher.current = self._nav_stack.pop()
        elif switcher.current != "overview":
            switcher.current = "overview"
        self._dirty = True

    def action_show_overview(self) -> None:
        self._show("overview")

    def action_show_system(self) -> None:
        self._show("system")
        asyncio.create_task(self._hydrate_site_details())

    def action_show_controllers(self) -> None:
        self._show("controllers")
        asyncio.create_task(self._hydrate_selected_site())

    def action_show_power(self) -> None:
        self._show("power")
        asyncio.create_task(self._hydrate_site_details())

    def action_show_incidents(self) -> None:
        self._show("incidents")

    def action_show_forecast(self) -> None:
        self._show("forecast")

    def action_show_history(self) -> None:
        self._show("history")

    def action_show_events(self) -> None:
        self._show("events")

    def action_show_investigation(self) -> None:
        self._show("investigation")

    def action_show_noc(self) -> None:
        self._show("noc")

    def action_show_topology(self) -> None:
        self._show("topology")
        asyncio.create_task(self._hydrate_site_details())

    async def action_show_controller_detail(self) -> None:
        state, uid = await self._controller_context()
        if uid is None:
            self._show("controllers")
            return
        await self.runtime.select_controller(state.name, uid)
        self._show("controller-detail")
        asyncio.create_task(self.runtime.fetch_controller_integrity(state.name, uid, select=False))

    async def action_show_telemetry(self) -> None:
        state, uid = await self._controller_context()
        if uid is None:
            self._show("controllers")
            return
        await self.runtime.select_controller(state.name, uid)
        self._show("telemetry")
        asyncio.create_task(self.runtime.fetch_controller_integrity(state.name, uid, select=False))

    async def action_show_diagnostics(self) -> None:
        state, uid = await self._controller_context()
        if uid is None:
            self._show("controllers")
            return
        await self.runtime.select_controller(state.name, uid)
        self._show("diagnostics")
        asyncio.create_task(self.runtime.fetch_controller_diagnostics(state.name, uid, select=False))

    def action_show_fleet(self) -> None:
        self._show("fleet")
        asyncio.create_task(self.runtime.hydrate_fleet_integrity())

    def action_command_palette(self) -> None:
        self._show("palette")
        self.call_after_refresh(self.query_one("#palette", CommandPaletteView).focus_query, clear=True)

    async def on_controller_activated(self, message: ControllerActivated) -> None:
        state = await self._selected_state()
        await self.runtime.select_controller(state.name, message.controller_uid)
        self._show("telemetry")
        asyncio.create_task(
            self.runtime.fetch_controller_integrity(
                state.name, message.controller_uid, select=False
            )
        )

    async def on_command_chosen(self, message: CommandChosen) -> None:
        self.action_back()
        await self._dispatch_action(message.action)

    async def _dispatch_action(self, action: str) -> None:
        method = getattr(self, f"action_{action}", None)
        if method is None:
            return
        result = method()
        if inspect.isawaitable(result):
            await result

    async def _controller_context(self) -> tuple[SiteState, str | None]:
        state = await self._selected_state()
        uid = state.selected_controller_uid
        if uid is None:
            uid = self.query_one("#controllers", ControllersView).selected_controller_uid()
        if uid is None and state.controllers:
            uid = str(state.controllers[0].get("controller_uid") or "") or None
        return state, uid

    def action_next_site(self) -> None:
        self._selected_site_index += 1
        self._dirty = True

    def action_previous_site(self) -> None:
        self._selected_site_index -= 1
        self._dirty = True

    async def action_refresh_site(self) -> None:
        state = await self._selected_state()
        asyncio.create_task(self.runtime.refresh_site(state.name))
        current = self._current_view()
        if current in {"controllers", "controller-detail", "telemetry"}:
            asyncio.create_task(self.runtime.hydrate_site_integrity(state.name, force=True))
        if current == "diagnostics" and state.selected_controller_uid:
            asyncio.create_task(
                self.runtime.fetch_controller_diagnostics(
                    state.name,
                    state.selected_controller_uid,
                    force=True,
                    select=False,
                )
            )
        if current in {"system", "topology", "power"}:
            asyncio.create_task(self.runtime.fetch_site_details(state.name, force=True))

    def action_refresh_fleet(self) -> None:
        self._show("fleet")
        asyncio.create_task(self.runtime.hydrate_fleet_integrity(force=True))

    async def _hydrate_selected_site(self) -> None:
        state = await self._selected_state()
        await self.runtime.hydrate_site_integrity(state.name)

    async def _hydrate_site_details(self) -> None:
        state = await self._selected_state()
        await self.runtime.fetch_site_details(state.name)

    async def action_history_previous(self) -> None:
        await self._change_history_window(-1)

    async def action_history_next(self) -> None:
        await self._change_history_window(1)

    async def _change_history_window(self, offset: int) -> None:
        state = await self._selected_state()
        index = _WINDOWS.index(state.history_window) if state.history_window in _WINDOWS else 2
        window = _WINDOWS[(index + offset) % len(_WINDOWS)]
        self._show("history")
        asyncio.create_task(self.runtime.fetch_history(state.name, state.history_metric, window))

    async def action_history_metric(self) -> None:
        state = await self._selected_state()
        index = _METRICS.index(state.history_metric) if state.history_metric in _METRICS else 0
        metric = _METRICS[(index + 1) % len(_METRICS)]
        self._show("history")
        asyncio.create_task(self.runtime.fetch_history(state.name, metric, state.history_window))

    async def action_investigate_now(self) -> None:
        state = await self._selected_state()
        self._show("investigation")
        asyncio.create_task(self.runtime.investigate(state.name, datetime.now(UTC)))

    async def action_investigate_back(self) -> None:
        await self._shift_investigation(timedelta(minutes=-5))

    async def action_investigate_forward(self) -> None:
        await self._shift_investigation(timedelta(minutes=5))

    async def action_investigate_back_hour(self) -> None:
        await self._shift_investigation(timedelta(hours=-1))

    async def action_investigate_forward_hour(self) -> None:
        await self._shift_investigation(timedelta(hours=1))

    async def _shift_investigation(self, delta: timedelta) -> None:
        state = await self._selected_state()
        cursor = state.investigation.cursor if state.investigation else datetime.now(UTC)
        self._show("investigation")
        asyncio.create_task(self.runtime.investigate(state.name, cursor + delta))
