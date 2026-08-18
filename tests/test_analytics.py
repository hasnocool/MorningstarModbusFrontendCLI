"""Pure regression tests for v0.6-v0.8 analytics helpers."""

from morningstar_tui.util.analytics import (
    coverage_percent,
    energy_difference_percent,
    gap_counts,
    rows,
)


def test_coverage_prefers_daily_evidence() -> None:
    payload = {
        "daily_evidence": {"coverage_percent": 98.5},
        "realtime": {"coverage_percent": 80},
    }
    assert coverage_percent(payload) == 98.5


def test_gap_counts_uses_duration_days() -> None:
    payload = {
        "gaps": [
            {"status": "recovered", "duration_days": 2},
            {"status": "missing", "duration_days": 1},
        ]
    }
    assert gap_counts(payload) == {"recovered": 2, "partial": 0, "missing": 1}


def test_energy_difference_can_be_derived() -> None:
    payload = {"controller_reported_wh": 1000, "integrated_output_wh": 950}
    assert energy_difference_percent(payload) == -5.0


def test_rows_accepts_envelope_or_list() -> None:
    assert rows({"items": [{"x": 1}]}, "items") == [{"x": 1}]
    assert rows([{"x": 2}]) == [{"x": 2}]
