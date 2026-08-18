"""Pure defensive helpers for controller and fleet analytics rendering."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from morningstar_tui.util.formatting import first, number


def rows(payload: object, *keys: str) -> list[dict[str, Any]]:
    """Extract a list of mapping rows from evolving API response envelopes."""

    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def coverage_percent(payload: object) -> float | None:
    return number(
        first(
            payload,
            "daily_evidence.coverage_percent",
            "coverage_percent",
            "realtime.coverage_percent",
            "summary.coverage_percent",
        )
    )


def realtime_coverage_percent(payload: object) -> float | None:
    return number(first(payload, "realtime.coverage_percent", "live.coverage_percent"))


def energy_reported_wh(payload: object) -> float | None:
    return number(
        first(
            payload,
            "controller_reported_wh",
            "total_controller_reported_wh",
            "controller.total_wh",
            "summary.controller_reported_wh",
        )
    )


def energy_integrated_wh(payload: object) -> float | None:
    return number(
        first(
            payload,
            "integrated_output_wh",
            "total_integrated_output_wh",
            "local_integrated_wh",
            "summary.integrated_output_wh",
        )
    )


def energy_difference_percent(payload: object) -> float | None:
    explicit = number(
        first(
            payload,
            "difference_percent",
            "energy_difference_percent",
            "summary.difference_percent",
        )
    )
    if explicit is not None:
        return explicit
    reported = energy_reported_wh(payload)
    integrated = energy_integrated_wh(payload)
    if reported in (None, 0) or integrated is None:
        return None
    return (integrated - reported) / reported * 100.0


def gap_counts(payload: object) -> dict[str, int]:
    counts = {"recovered": 0, "partial": 0, "missing": 0}
    for item in rows(payload, "gaps", "intervals", "items", "data"):
        status = str(item.get("status") or item.get("state") or "").lower()
        days = number(item.get("duration_days") or item.get("days") or 1) or 1
        if status in counts:
            counts[status] += max(1, int(days))
    return counts


def coverage_day_rows(payload: object) -> list[dict[str, Any]]:
    return rows(payload, "days", "daily", "coverage", "items", "data")


def energy_daily_rows(payload: object) -> list[dict[str, Any]]:
    return rows(payload, "days", "daily", "energy", "items", "data")


def aggregate(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def weighted_average(pairs: list[tuple[float | None, float]]) -> float | None:
    valid = [(value, weight) for value, weight in pairs if value is not None and weight > 0]
    if not valid:
        return None
    total_weight = sum(weight for _, weight in valid)
    return sum(value * weight for value, weight in valid if value is not None) / total_weight
