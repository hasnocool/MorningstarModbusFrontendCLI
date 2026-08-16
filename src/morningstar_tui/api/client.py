"""Non-blocking HTTP/SSE client for MorningstarModbusAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
import time
from typing import Any

import httpx

from morningstar_tui.api.sse import SSEEvent, parse_sse
from morningstar_tui.config import SiteConfig

JSON = dict[str, Any] | list[Any]


class APIError(RuntimeError):
    """Raised when the Morningstar API cannot satisfy a request."""


class MorningstarAPIClient:
    """Typed-enough async facade over the API's read-only resources."""

    def __init__(self, site: SiteConfig, *, timeout_seconds: float = 10.0) -> None:
        headers = {"Accept": "application/json"}
        if site.token:
            headers["Authorization"] = f"Bearer {site.token}"
        self.site = site
        self._client = httpx.AsyncClient(
            base_url=site.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout_seconds),
            verify=site.verify_tls,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_json(self, path: str, **params: object) -> JSON:
        try:
            response = await self._client.get(path, params={k: v for k, v in params.items() if v is not None})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise APIError(f"GET {path} failed: {exc}") from exc
        payload = response.json()
        if not isinstance(payload, (dict, list)):
            raise APIError(f"GET {path} returned non-object JSON")
        return payload

    async def timed_get_json(self, path: str, **params: object) -> tuple[JSON, float]:
        started = time.perf_counter()
        payload = await self.get_json(path, **params)
        return payload, (time.perf_counter() - started) * 1000.0

    async def systems(self) -> list[dict[str, Any]]:
        payload = await self.get_json("/v1/systems")
        return payload if isinstance(payload, list) else list(payload.get("systems", []))

    async def system(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}"))

    async def controllers(self, system_uid: str) -> list[dict[str, Any]]:
        payload = await self.get_json(f"/v1/systems/{system_uid}/controllers")
        return payload if isinstance(payload, list) else list(payload.get("controllers", []))

    async def latest(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/latest"))

    async def power_flow(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/power-flow"))

    async def energy_ledger(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/energy-ledger"))

    async def health(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/health"))

    async def topology(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/topology"))

    async def events(self, system_uid: str, *, start: str | None = None, end: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        payload = await self.get_json(f"/v1/systems/{system_uid}/events", **{"from": start, "to": end, "limit": limit})
        return payload if isinstance(payload, list) else list(payload.get("events", []))

    async def incidents(self, system_uid: str, *, state: str | None = "active", limit: int = 500) -> list[dict[str, Any]]:
        payload = await self.get_json(f"/v1/systems/{system_uid}/incidents", state=state, limit=limit)
        return payload if isinstance(payload, list) else list(payload.get("incidents", []))

    async def health_score(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/health-score"))

    async def baselines(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/baselines"))

    async def forecast(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/forecast"))

    async def forecast_accuracy(self, system_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/systems/{system_uid}/forecast/accuracy"))

    async def history(self, system_uid: str, metric: str, *, start: str | None = None, end: str | None = None, resolution: str = "5m", max_points: int = 2500) -> JSON:
        return await self.get_json(f"/v1/systems/{system_uid}/history", **{"metric": metric, "from": start, "to": end, "resolution": resolution, "max_points": max_points})

    async def controller(self, controller_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}"))

    async def controller_latest(self, controller_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/latest"))

    async def controller_health_score(self, controller_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/health-score"))

    async def controller_charge_cycle(self, controller_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/charge-cycle"))

    async def controller_charge_forecast(self, controller_uid: str) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/charge-forecast"))

    async def controller_coverage(self, controller_uid: str, *, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/history/coverage", **{"from": start, "to": end}))

    async def controller_gaps(self, controller_uid: str, *, start: str | None = None, end: str | None = None) -> JSON:
        return await self.get_json(f"/v1/controllers/{controller_uid}/history/gaps", **{"from": start, "to": end})

    async def controller_retained_summary(self, controller_uid: str, *, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/history/controller-daily/summary", **{"from": start, "to": end}))

    async def controller_energy_daily(self, controller_uid: str, *, start: str | None = None, end: str | None = None, max_gap_seconds: int = 300) -> JSON:
        return await self.get_json(f"/v1/controllers/{controller_uid}/energy/daily", **{"from": start, "to": end, "max_gap_seconds": max_gap_seconds})

    async def controller_energy_summary(self, controller_uid: str, *, start: str | None = None, end: str | None = None, max_gap_seconds: int = 300) -> dict[str, Any]:
        return _object(await self.get_json(f"/v1/controllers/{controller_uid}/energy/summary", **{"from": start, "to": end, "max_gap_seconds": max_gap_seconds}))

    @asynccontextmanager
    async def stream_system(self, system_uid: str) -> AsyncIterator[AsyncIterator[SSEEvent]]:
        """Open the native system SSE stream without blocking the event loop."""
        try:
            async with self._client.stream("GET", f"/v1/systems/{system_uid}/stream", headers={"Accept": "text/event-stream"}, timeout=None) as response:
                response.raise_for_status()
                yield parse_sse(response.aiter_lines())
        except httpx.HTTPError as exc:
            raise APIError(f"SSE stream failed: {exc}") from exc


def _object(payload: JSON) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise APIError("API returned an array where an object was expected")
    return payload


def iso(value: datetime) -> str:
    return value.isoformat()
