# tests/test_sparkline.py
from morningstar_tui.util.sparkline import sparkline


def test_sparkline_preserves_small_series() -> None:
    rendered = sparkline([0.0, 1.0, 2.0, 3.0], width=10)
    assert len(rendered) == 4
    assert rendered[0] != rendered[-1]


def test_sparkline_downsamples() -> None:
    rendered = sparkline([float(value) for value in range(100)], width=20)
    assert len(rendered) == 20
