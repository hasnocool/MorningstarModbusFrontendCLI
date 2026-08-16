"""Defensive helpers for rendering evolving API payloads as terminal tables."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_METADATA_KEYS = {"unit", "quality", "source", "provenance", "observed_at", "timestamp"}


def scalar_rows(payload: object, *, max_rows: int = 400) -> list[tuple[str, str, str, str]]:
    """Flatten JSON-like data into path/value/unit/quality rows without losing wrappers."""

    output: list[tuple[str, str, str, str]] = []

    def walk(value: object, path: str, depth: int) -> None:
        if len(output) >= max_rows or depth > 10:
            return
        if isinstance(value, Mapping):
            if "value" in value and not isinstance(value.get("value"), (Mapping, list)):
                unit = _text(value.get("unit"))
                quality = _text(value.get("quality") or value.get("status"))
                source = _text(value.get("source") or value.get("provenance"))
                suffix = quality if not source else f"{quality} · {source}" if quality else source
                output.append((path or "value", _text(value.get("value")), unit, suffix))
                for key, child in value.items():
                    if key in _METADATA_KEYS or key == "value":
                        continue
                    walk(child, f"{path}.{key}" if path else str(key), depth + 1)
                return
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                walk(child, child_path, depth + 1)
            return
        if isinstance(value, list):
            for index, child in enumerate(value[:100]):
                walk(child, f"{path}[{index}]", depth + 1)
            return
        output.append((path or "value", _text(value), "", ""))

    walk(payload, "", 0)
    return output[:max_rows]


def record_rows(payload: object, *keys: str) -> list[dict[str, Any]]:
    """Extract a list of object rows from either a direct array or common envelopes."""

    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    candidates = (*keys, "items", "data", "results", "rows")
    for key in candidates:
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def compact_mapping(payload: object, *, limit: int = 40) -> str:
    """Render a compact newline key/value block for metadata panels."""

    lines: list[str] = []
    for path, value, unit, quality in scalar_rows(payload, max_rows=limit):
        rendered = f"{value} {unit}".strip()
        if quality:
            rendered = f"{rendered} [{quality}]"
        lines.append(f"{path:36} {rendered}")
    return "\n".join(lines) if lines else "No data returned by API."


def _text(value: object | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)
