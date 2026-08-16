# tests/test_config.py
from __future__ import annotations

from pathlib import Path

import pytest

from morningstar_tui.config import apply_cli_overrides, load_config


def test_load_multi_site_config(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        """
[dashboard]
history_window = "7d"

[[sites]]
name = "a"
base_url = "http://one.example/"

[[sites]]
name = "b"
base_url = "https://two.example"
system = "main"
""",
        encoding="utf-8",
    )
    config = load_config(str(path))
    assert config.dashboard.history_window == "7d"
    assert [site.name for site in config.sites] == ["a", "b"]
    assert config.sites[0].base_url == "http://one.example"


def test_site_filter_and_low_bandwidth() -> None:
    config = load_config()
    updated = apply_cli_overrides(config, site="local", low_bandwidth=True)
    assert len(updated.sites) == 1
    assert updated.dashboard.refresh_interval_seconds >= 60


def test_unknown_site_rejected() -> None:
    with pytest.raises(ValueError, match="unknown site"):
        apply_cli_overrides(load_config(), site="missing")
