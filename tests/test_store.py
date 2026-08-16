# tests/test_store.py
from __future__ import annotations

import asyncio

import pytest

from morningstar_tui.state.models import SiteState
from morningstar_tui.state.store import StateStore


@pytest.mark.asyncio
async def test_store_concurrent_patch_is_consistent() -> None:
    store = StateStore([SiteState(name="local", base_url="http://test")])

    async def writer(index: int) -> None:
        await store.patch("local", latency_ms=float(index), online=True)

    await asyncio.gather(*(writer(index) for index in range(50)))
    state = await store.snapshot("local")
    assert state.online is True
    assert state.latency_ms is not None
    assert 0 <= state.latency_ms <= 49
