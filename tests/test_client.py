# tests/test_client.py
from __future__ import annotations

import httpx
import pytest

from morningstar_tui.api.client import MorningstarAPIClient
from morningstar_tui.config import SiteConfig


@pytest.mark.asyncio
async def test_client_systems_and_latest() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/systems":
            return httpx.Response(200, json=[{"system_uid": "sys_default", "name": "default"}])
        if request.url.path == "/v1/systems/sys_default/latest":
            return httpx.Response(200, json={"metrics": {"battery_voltage_v": {"value": 13.4}}})
        return httpx.Response(404, json={"detail": "missing"})

    client = MorningstarAPIClient(SiteConfig(name="test", base_url="http://test"))
    await client._client.aclose()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test")
    try:
        systems = await client.systems()
        latest = await client.latest("sys_default")
    finally:
        await client.close()
    assert systems[0]["system_uid"] == "sys_default"
    assert latest["metrics"]["battery_voltage_v"]["value"] == 13.4


@pytest.mark.asyncio
async def test_history_uses_api_from_to_aliases() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params.multi_items()))
        return httpx.Response(200, json={"points": []})

    client = MorningstarAPIClient(SiteConfig(name="test", base_url="http://test"))
    await client._client.aclose()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test")
    try:
        await client.history(
            "sys_default",
            "solar_input_power_w",
            start="2026-08-15T00:00:00+00:00",
            end="2026-08-16T00:00:00+00:00",
        )
    finally:
        await client.close()
    assert seen["from"] == "2026-08-15T00:00:00+00:00"
    assert seen["to"] == "2026-08-16T00:00:00+00:00"
    assert "start" not in seen
    assert "end" not in seen
