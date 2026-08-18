"""Regression tests for generic API payload exploration."""

from morningstar_tui.util.explorer import compact_mapping, record_rows, scalar_rows


def test_scalar_rows_preserves_wrapper_metadata() -> None:
    payload = {
        "metrics": {
            "battery_voltage_v": {
                "value": 13.42,
                "unit": "V",
                "quality": "complete",
                "source": "controller:abc",
            }
        }
    }

    assert scalar_rows(payload) == [
        ("metrics.battery_voltage_v", "13.42", "V", "complete · controller:abc")
    ]


def test_scalar_rows_flattens_nested_lists_and_scalars() -> None:
    payload = {
        "faults": ["overcurrent", "overtemp"],
        "status": {"online": True, "attempts": 3},
        "power": {"value": 0, "unit": "W", "quality": "complete"},
    }

    rows = scalar_rows(payload)

    assert ("faults[0]", "overcurrent", "", "") in rows
    assert ("faults[1]", "overtemp", "", "") in rows
    assert ("status.online", "yes", "", "") in rows
    assert ("status.attempts", "3", "", "") in rows
    assert ("power", "0", "W", "complete") in rows


def test_record_rows_supports_common_envelopes() -> None:
    assert record_rows({"components": [{"id": "battery"}]}, "components") == [
        {"id": "battery"}
    ]
    assert record_rows([{"id": "controller"}, "ignored"]) == [{"id": "controller"}]


def test_compact_mapping_includes_quality_and_unit() -> None:
    rendered = compact_mapping(
        {"battery_net_current_a": {"value": -4.2, "unit": "A", "quality": "complete"}}
    )

    assert "battery_net_current_a" in rendered
    assert "-4.2 A [complete]" in rendered
