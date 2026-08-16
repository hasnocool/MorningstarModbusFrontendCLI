# tests/test_app.py
from __future__ import annotations

import pytest

from morningstar_tui.config import apply_cli_overrides, load_config


@pytest.mark.asyncio
async def test_textual_app_mounts(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("textual")
    from morningstar_tui.app import MorningstarTUI

    config = apply_cli_overrides(load_config(), alert_only=True)
    app = MorningstarTUI(config)

    async def idle_runtime() -> None:
        return None

    monkeypatch.setattr(app.runtime, "run", idle_runtime)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.title == "Morningstar Power Site"
        assert app.query_one("#views") is not None
