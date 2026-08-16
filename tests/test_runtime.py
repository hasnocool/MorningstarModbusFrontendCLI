# tests/test_runtime.py
from morningstar_tui.config import SiteConfig
from morningstar_tui.state.runtime import _resolve_system


def test_resolve_system_by_name_or_uid() -> None:
    systems = [
        {"system_uid": "sys_a", "name": "alpha"},
        {"system_uid": "sys_b", "name": "beta"},
    ]
    assert _resolve_system(SiteConfig("a", "http://x", system="beta"), systems) == "sys_b"
    assert _resolve_system(SiteConfig("a", "http://x", system="sys_a"), systems) == "sys_a"
