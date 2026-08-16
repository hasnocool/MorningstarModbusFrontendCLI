"""Minimal async Server-Sent Events parser used by the API client."""

from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass
import json


@dataclass(frozen=True, slots=True)
class SSEEvent:
    event: str
    data: str
    event_id: str | None = None
    retry_ms: int | None = None

    def json(self) -> object:
        return json.loads(self.data)


async def parse_sse(lines: AsyncIterable[str]) -> AsyncIterator[SSEEvent]:
    """Parse an asynchronous stream of decoded SSE lines."""

    event = "message"
    data: list[str] = []
    event_id: str | None = None
    retry_ms: int | None = None

    async for raw_line in lines:
        line = raw_line.rstrip("\r")
        if line == "":
            if data:
                yield SSEEvent(
                    event=event,
                    data="\n".join(data),
                    event_id=event_id,
                    retry_ms=retry_ms,
                )
            event = "message"
            data = []
            retry_ms = None
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]
        if field == "event":
            event = value or "message"
        elif field == "data":
            data.append(value)
        elif field == "id":
            if "\x00" not in value:
                event_id = value
        elif field == "retry":
            try:
                retry_ms = int(value)
            except ValueError:
                pass

    if data:
        yield SSEEvent(event=event, data="\n".join(data), event_id=event_id, retry_ms=retry_ms)
