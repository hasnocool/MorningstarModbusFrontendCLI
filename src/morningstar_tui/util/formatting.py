"""Defensive formatting helpers for evolving API payloads."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any


def nested(payload: object, path: str) -> object | None:
    current = payload
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def first(payload: object, *paths: str) -> object | None:
    for path in paths:
        value = nested(payload, path)
        if value is not None:
            return value
    return None


def recursive_find(payload: object, key: str) -> object | None:
    """Find the first exact key in a bounded JSON-like structure."""

    queue: list[object] = [payload]
    seen = 0
    while queue and seen < 5000:
        current = queue.pop(0)
        seen += 1
        if isinstance(current, Mapping):
            if key in current:
                value = current[key]
                if isinstance(value, Mapping) and "value" in value:
                    return value["value"]
                return value
            queue.extend(current.values())
        elif isinstance(current, list):
            queue.extend(current)
    return None


def metric(payload: object, name: str) -> object | None:
    return first(
        payload,
        name,
        f"metrics.{name}",
        f"metrics.{name}.value",
        f"values.{name}",
        f"values.{name}.value",
    ) or recursive_find(payload, name)


def number(value: object | None) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, Mapping) and "value" in value:
        return number(value["value"])
    return None


def text(value: object | None, default: str = "—") -> str:
    if value is None:
        return default
    if isinstance(value, Mapping) and "value" in value:
        return text(value["value"], default)
    if isinstance(value, list):
        return ", ".join(text(item, "") for item in value) or default
    return str(value)


def fmt_number(value: object | None, unit: str = "", digits: int = 1) -> str:
    numeric = number(value)
    if numeric is None:
        return "—"
    suffix = f" {unit}" if unit else ""
    return f"{numeric:.{digits}f}{suffix}"


def fmt_energy_wh(value: object | None) -> str:
    numeric = number(value)
    if numeric is None:
        return "—"
    if abs(numeric) >= 1000:
        return f"{numeric / 1000:.2f} kWh"
    return f"{numeric:.0f} Wh"


def fmt_percent(value: object | None, *, ratio: bool = False) -> str:
    numeric = number(value)
    if numeric is None:
        return "—"
    if ratio:
        numeric *= 100
    return f"{numeric:.1f}%"


def fmt_age(value: object | None) -> str:
    parsed = parse_time(value)
    if parsed is None:
        return "—"
    seconds = max(0, int((datetime.now(UTC) - parsed).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def parse_time(value: object | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def event_summary(event: Mapping[str, Any]) -> str:
    for key in ("message", "summary", "detail", "description", "event_type", "type"):
        if event.get(key):
            return text(event[key])
    return "event"


def values_from_history(payload: object) -> list[float]:
    points: Iterable[object]
    if isinstance(payload, list):
        points = payload
    elif isinstance(payload, Mapping):
        points = next(
            (
                value
                for key in ("points", "history", "samples", "data", "buckets")
                if isinstance((value := payload.get(key)), list)
            ),
            [],
        )
    else:
        return []
    values: list[float] = []
    for point in points:
        if isinstance(point, Mapping):
            candidate = first(point, "value", "avg", "average", "mean", "last", "value.value")
        else:
            candidate = point
        numeric = number(candidate)
        if numeric is not None:
            values.append(numeric)
    return values
