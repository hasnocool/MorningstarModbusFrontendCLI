"""Textual application shell for the v0.5 operations dashboard."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from textual.app import App, ComposeResult
from textual.widgets import ContentSwitcher, Footer, Header

from morningstar_tui.config import AppConfig
from morningstar_tui.state import DashboardRuntime, SiteState
from morningstar_tui.views import (
    ControllersView,
    EventsView,
    ForecastView,
    HistoryView,
    IncidentsView,
    InvestigationView,
    NOCView,
    OverviewView,
    PowerFlowView,
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


class MorningstarTUI(App[None]):
    """Keyboard-first, read-only Morningstar operations console."""

    TITLE = "Morningstar Power Site"
    SUB_TITLE = "MorningstarModbusAPI terminal operations dashboard"

    CSS = """
    Screen {
        layout: vertical;
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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ContentSwitcher(initial="overview", id="views"):
            yield OverviewView(id="overview")
            yield ControllersView(id="controllers")
            yield PowerFlowView(id="power")
            yield IncidentsView(id="incidents")
            yield ForecastView(id="forecast")
            yield HistoryView(id="history")
            yield EventsView(id="events")
            yield InvestigationView(id="investigation")
            yield NOCView(id="noc")
        yield Footer()

    async def on_mount(self) -> None:
        if self.config.dashboard.compact:
            self.screen.add_class("compact")
        if len(self.config.sites) > 1:
            self.query_one("#views", ContentSwitcher).current = "noc"
        self.runtime.store.set_callback(self._state_changed)
        self._runtime_task = asyncio.create_task(self.runtime.run(), name="morningstar-runtime")
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
        self.sub_title = (
            f"{selected.name} · {selected.system_uid} · "
            f"{'online' if selected.online else 'offline'} · "
            f"{'SSE' if selected.stream_online else 'REST'}"
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

    def _show(self, view_id: str) -> None:
        self.query_one("#views", ContentSwitcher).current = view_id
        self._dirty = True

    def action_show_overview(self) -> None:
        self._show("overview")

    def action_show_controllers(self) -> None:
        self._show("controllers")

    def action_show_power(self) -> None:
        self._show("power")

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

    def action_next_site(self) -> None:
        self._selected_site_index += 1
        self._dirty = True

    def action_previous_site(self) -> None:
        self._selected_site_index -= 1
        self._dirty = True

    async def action_refresh_site(self) -> None:
        state = await self._selected_state()
        asyncio.create_task(self.runtime.refresh_site(state.name))

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
