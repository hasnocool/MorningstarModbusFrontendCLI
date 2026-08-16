# tests/test_sse.py
from __future__ import annotations

import pytest

from morningstar_tui.api.sse import parse_sse


async def _lines(values: list[str]):
    for value in values:
        yield value


@pytest.mark.asyncio
async def test_parse_sse_event_and_id() -> None:
    events = [
        event
        async for event in parse_sse(
            _lines(
                [
                    ": heartbeat",
                    "id: 42",
                    "event: telemetry",
                    'data: {"battery_voltage_v":13.4}',
                    "",
                ]
            )
        )
    ]
    assert len(events) == 1
    assert events[0].event == "telemetry"
    assert events[0].event_id == "42"
    assert events[0].json() == {"battery_voltage_v": 13.4}


@pytest.mark.asyncio
async def test_parse_multiline_data() -> None:
    events = [event async for event in parse_sse(_lines(["data: one", "data: two", ""]))]
    assert events[0].data == "one\ntwo"
