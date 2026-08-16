"""Unicode sparkline rendering with no plotting dependency."""

from __future__ import annotations

from collections.abc import Sequence

_BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(values: Sequence[float], *, width: int = 60) -> str:
    if not values or width <= 0:
        return ""
    sampled = _sample(values, width)
    low = min(sampled)
    high = max(sampled)
    if high == low:
        return _BLOCKS[len(_BLOCKS) // 2] * len(sampled)
    span = high - low
    result: list[str] = []
    for value in sampled:
        fraction = (value - low) / span
        index = min(len(_BLOCKS) - 1, int(round(fraction * (len(_BLOCKS) - 1))))
        result.append(_BLOCKS[index])
    return "".join(result)


def _sample(values: Sequence[float], width: int) -> list[float]:
    if len(values) <= width:
        return list(values)
    output: list[float] = []
    for index in range(width):
        start = int(index * len(values) / width)
        end = max(start + 1, int((index + 1) * len(values) / width))
        bucket = values[start:end]
        output.append(sum(bucket) / len(bucket))
    return output
