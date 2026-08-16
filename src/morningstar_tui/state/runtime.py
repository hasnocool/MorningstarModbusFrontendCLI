"""Concurrent multi-site runtime for REST, SSE and on-demand controller analytics."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
import json
from typing import Any

from morningstar_tui.api import APIError, MorningstarAPIClient, SSEEvent
from morningstar_tui.config import AppConfig, SiteConfig
from morningstar_tui.state.models import ControllerIntegrityBundle, InvestigationBundle, SiteState
from morningstar_tui.state.store import StateStore


_WINDOW_DELTAS = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "180d": timedelta(days=180),
    "1y": timedelta(days=365),
}
_WINDOW_RESOLUTION = {
    "1h": "1m",
    "6h": "5m",
    "24h": "5m",
    "7d": "1h",
    "30d": "1h",
    "180d": "1d",
    "1y": "1d",
}
_CONTROLLER_CACHE_SECONDS = 45.0


class DashboardRuntime:
    """Supervise each configured API site without blocking the Textual event loop."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.clients = {
            site.name: MorningstarAPIClient(
                site,
                timeout_seconds=config.dashboard.request_timeout_seconds,
            )
            for site in config.sites
        }
        self.sites = {site.name: site for site in config.sites}
        self.store = StateStore(
            [
                SiteState(
                    name=site.name,
                    base_url=site.base_url,
                    system_uid=site.system,
                    history_metric=config.dashboard.history_metric,
                    history_window=config.dashboard.history_window,
                )
                for site in config.sites
            ]
        )
        self._stop = asyncio.Event()
        self._controller_slots = asyncio.Semaphore(6)

    async def close(self) -> None:
        self._stop.set()
        await asyncio.gather(*(client.close() for client in self.clients.values()), return_exceptions=True)

    async def run(self) -> None:
        async with asyncio.TaskGroup() as group:
            for site in self.config.sites:
                group.create_task(self._site_worker(site), name=f"site:{site.name}")

    async def refresh_site(self, name: str, *, intelligence: bool = True) -> None:
        site = self.sites[name]
        client = self.clients[name]
        try:
            systems, latency = await client.timed_get_json("/v1/systems")
            system_uid = _resolve_system(site, systems)
            common: tuple[Awaitable[Any], ...] = (
                client.system(system_uid),
                client.latest(system_uid),
                client.controllers(system_uid),
                client.power_flow(system_uid),
                client.energy_ledger(system_uid),
                client.health(system_uid),
                client.events(system_uid, limit=200),
            )
            results = await asyncio.gather(*(_safe(item, None) for item in common))
            system, latest, controllers, power_flow, ledger, health, events = results
            changes: dict[str, Any] = {
                "system_uid": system_uid,
                "online": True,
                "latency_ms": latency,
                "last_error": None,
                "system": system or {},
                "latest": latest or {},
                "controllers": controllers or [],
                "power_flow": power_flow or {},
                "energy_ledger": ledger or {},
                "health": health or {},
                "events": events or [],
            }
            if intelligence:
                extras = await asyncio.gather(
                    _safe(client.health_score(system_uid), {}),
                    _safe(client.baselines(system_uid), {}),
                    _safe(client.incidents(system_uid), []),
                    _safe(client.forecast(system_uid), {}),
                    _safe(client.forecast_accuracy(system_uid), {}),
                )
                (
                    changes["health_score"],
                    changes["baselines"],
                    changes["incidents"],
                    changes["forecast"],
                    changes["forecast_accuracy"],
                ) = extras
            await self.store.patch(name, **changes)
        except Exception as exc:
            await self.store.patch(name, online=False, stream_online=False, last_error=str(exc))

    async def fetch_history(self, name: str, metric: str, window: str) -> None:
        state = await self.store.snapshot(name)
        delta = _WINDOW_DELTAS[window]
        end = datetime.now(UTC)
        start = end - delta
        client = self.clients[name]
        try:
            history = await client.history(
                state.system_uid,
                metric,
                start=start.isoformat(),
                end=end.isoformat(),
                resolution=_WINDOW_RESOLUTION[window],
                max_points=2500,
            )
            await self.store.patch(name, history=history, history_metric=metric, history_window=window)
        except Exception as exc:
            await self.store.patch(name, last_error=f"history: {exc}")

    async def investigate(self, name: str, cursor: datetime, *, minutes: int = 30) -> None:
        state = await self.store.snapshot(name)
        start = cursor - timedelta(minutes=minutes)
        end = cursor + timedelta(minutes=minutes)
        metrics = (
            "solar_input_power_w",
            "charge_output_power_w",
            "battery_voltage_v",
            "battery_charge_current_a",
            "charge_state",
        )
        client = self.clients[name]
        calls = [
            _safe(
                client.history(
                    state.system_uid,
                    metric,
                    start=start.isoformat(),
                    end=end.isoformat(),
                    resolution="1m",
                    max_points=1000,
                ),
                {},
            )
            for metric in metrics
        ]
        try:
            results = await asyncio.gather(*calls)
            events = await _safe(
                client.events(
                    state.system_uid,
                    start=start.isoformat(),
                    end=end.isoformat(),
                    limit=500,
                ),
                [],
            )
            bounded_events = [event for event in events if _event_in_range(event, start, end)]
            bundle = InvestigationBundle(
                cursor=cursor,
                start=start,
                end=end,
                histories=dict(zip(metrics, results, strict=True)),
                events=bounded_events,
            )
        except Exception as exc:
            bundle = InvestigationBundle(cursor=cursor, start=start, end=end, error=str(exc))
        await self.store.investigation(name, bundle)

    async def select_controller(self, name: str, controller_uid: str) -> None:
        await self.store.select_controller(name, controller_uid)

    async def fetch_controller_integrity(
        self,
        name: str,
        controller_uid: str,
        *,
        force: bool = False,
        select: bool = True,
    ) -> ControllerIntegrityBundle:
        """Load v0.6 controller evidence lazily and cache it for rapid TUI navigation."""

        if select:
            await self.store.select_controller(name, controller_uid)
        state = await self.store.snapshot(name)
        cached = state.controller_integrity.get(controller_uid)
        if cached is not None and not force:
            age = (datetime.now(UTC) - cached.loaded_at).total_seconds()
            if age <= _CONTROLLER_CACHE_SECONDS:
                return cached

        client = self.clients[name]
        end_day = datetime.now(UTC).date()
        start_30d = (end_day - timedelta(days=30)).isoformat()
        start_90d = (end_day - timedelta(days=90)).isoformat()
        end = (end_day + timedelta(days=1)).isoformat()

        async with self._controller_slots:
            try:
                (
                    detail,
                    latest,
                    health_score,
                    charge_cycle,
                    charge_forecast,
                    coverage,
                    gaps,
                    retained_summary,
                    energy_daily_30d,
                    energy_summary_30d,
                    energy_summary_90d,
                ) = await asyncio.gather(
                    _safe(client.controller(controller_uid), {}),
                    _safe(client.controller_latest(controller_uid), {}),
                    _safe(client.controller_health_score(controller_uid), {}),
                    _safe(client.controller_charge_cycle(controller_uid), {}),
                    _safe(client.controller_charge_forecast(controller_uid), {}),
                    _safe(client.controller_coverage(controller_uid, start=start_90d, end=end), {}),
                    _safe(client.controller_gaps(controller_uid, start=start_90d, end=end), {}),
                    _safe(client.controller_retained_summary(controller_uid, start=start_90d, end=end), {}),
                    _safe(client.controller_energy_daily(controller_uid, start=start_30d, end=end), {}),
                    _safe(client.controller_energy_summary(controller_uid, start=start_30d, end=end), {}),
                    _safe(client.controller_energy_summary(controller_uid, start=start_90d, end=end), {}),
                )
                bundle = ControllerIntegrityBundle(
                    controller_uid=controller_uid,
                    detail=detail,
                    latest=latest,
                    health_score=health_score,
                    charge_cycle=charge_cycle,
                    charge_forecast=charge_forecast,
                    coverage=coverage,
                    gaps=gaps,
                    retained_summary=retained_summary,
                    energy_daily_30d=energy_daily_30d,
                    energy_summary_30d=energy_summary_30d,
                    energy_summary_90d=energy_summary_90d,
                )
            except Exception as exc:
                bundle = ControllerIntegrityBundle(controller_uid=controller_uid, error=str(exc))

        await self.store.controller_integrity(name, controller_uid, bundle)
        return bundle

    async def hydrate_site_integrity(self, name: str, *, force: bool = False) -> None:
        """Enrich every controller for fleet comparison using bounded async requests."""

        state = await self.store.snapshot(name)
        controller_uids = [
            str(item.get("controller_uid") or "")
            for item in state.controllers
            if item.get("controller_uid")
        ]
        await asyncio.gather(
            *(
                self.fetch_controller_integrity(
                    name,
                    controller_uid,
                    force=force,
                    select=False,
                )
                for controller_uid in controller_uids
            ),
            return_exceptions=True,
        )

    async def hydrate_fleet_integrity(self, *, force: bool = False) -> None:
        await asyncio.gather(
            *(self.hydrate_site_integrity(site.name, force=force) for site in self.config.sites),
            return_exceptions=True,
        )

    async def snapshot_once(self) -> list[SiteState]:
        await asyncio.gather(*(self.refresh_site(site.name) for site in self.config.sites))
        return await self.store.snapshots()

    async def _site_worker(self, site: SiteConfig) -> None:
        delay = self.config.dashboard.reconnect_initial_seconds
        while not self._stop.is_set():
            await self.refresh_site(site.name, intelligence=True)
            state = await self.store.snapshot(site.name)
            if not state.online:
                await _sleep_or_stop(self._stop, delay)
                delay = min(delay * 2, self.config.dashboard.reconnect_max_seconds)
                continue
            delay = self.config.dashboard.reconnect_initial_seconds
            if self.config.dashboard.alert_only:
                await _sleep_or_stop(self._stop, self.config.dashboard.refresh_interval_seconds)
                continue
            try:
                async with asyncio.TaskGroup() as group:
                    group.create_task(self._refresh_loop(site.name), name=f"refresh:{site.name}")
                    group.create_task(self._stream_loop(site.name), name=f"sse:{site.name}")
            except* Exception as errors:
                message = "; ".join(str(item) for item in errors.exceptions)
                await self.store.patch(site.name, stream_online=False, last_error=message)
            await _sleep_or_stop(self._stop, delay)
            delay = min(delay * 2, self.config.dashboard.reconnect_max_seconds)

    async def _refresh_loop(self, name: str) -> None:
        while not self._stop.is_set():
            await _sleep_or_stop(self._stop, self.config.dashboard.refresh_interval_seconds)
            if self._stop.is_set():
                return
            await self.refresh_site(name, intelligence=True)

    async def _stream_loop(self, name: str) -> None:
        state = await self.store.snapshot(name)
        client = self.clients[name]
        async with client.stream_system(state.system_uid) as events:
            await self.store.patch(name, stream_online=True)
            async for event in events:
                if self._stop.is_set():
                    return
                await self._apply_sse(name, event)
        raise APIError("SSE stream ended")

    async def _apply_sse(self, name: str, event: SSEEvent) -> None:
        try:
            payload = event.json()
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        if event.event == "telemetry":
            await self.store.telemetry(name, payload)
            return
        if event.event in {"system_event", "incident_opened", "incident_updated", "incident_resolved"}:
            await self.store.event(name, payload)
            if event.event.startswith("incident_"):
                state = await self.store.snapshot(name)
                incidents = await _safe(self.clients[name].incidents(state.system_uid), state.incidents)
                await self.store.patch(name, incidents=incidents)


async def _safe[T](awaitable: Awaitable[T], default: T) -> T:
    try:
        return await awaitable
    except Exception:
        return default


def _resolve_system(site: SiteConfig, systems: object) -> str:
    if isinstance(systems, dict):
        candidates = systems.get("systems", [])
    elif isinstance(systems, list):
        candidates = systems
    else:
        candidates = []
    wanted = site.system
    for item in candidates:
        if not isinstance(item, dict):
            continue
        uid = str(item.get("system_uid") or "")
        name = str(item.get("name") or "")
        if wanted in {uid, name}:
            return uid or wanted
    if wanted:
        return wanted
    for item in candidates:
        if isinstance(item, dict) and item.get("system_uid"):
            return str(item["system_uid"])
    return "sys_default"


def _event_in_range(event: dict[str, Any], start: datetime, end: datetime) -> bool:
    raw = event.get("observed_at") or event.get("created_at") or event.get("timestamp") or event.get("time")
    if not raw:
        return True
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return start <= parsed.astimezone(UTC) <= end


async def _sleep_or_stop(stop: asyncio.Event, seconds: float) -> None:
    with suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), timeout=seconds)
