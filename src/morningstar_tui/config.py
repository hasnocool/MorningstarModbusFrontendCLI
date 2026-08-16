"""Configuration models and TOML loading for the terminal dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import tomllib


@dataclass(frozen=True, slots=True)
class SiteConfig:
    """One MorningstarModbusAPI endpoint."""

    name: str
    base_url: str
    system: str = "sys_default"
    token: str | None = None
    verify_tls: bool = True

    def normalized(self) -> "SiteConfig":
        return replace(self, base_url=self.base_url.rstrip("/"))


@dataclass(frozen=True, slots=True)
class DashboardConfig:
    """Runtime behavior shared by all configured sites."""

    refresh_interval_seconds: float = 15.0
    reconnect_initial_seconds: float = 1.0
    reconnect_max_seconds: float = 30.0
    request_timeout_seconds: float = 10.0
    history_window: str = "24h"
    history_metric: str = "solar_input_power_w"
    compact: bool = False
    low_bandwidth: bool = False
    alert_only: bool = False


@dataclass(frozen=True, slots=True)
class AppConfig:
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    sites: tuple[SiteConfig, ...] = (
        SiteConfig(name="local", base_url="http://127.0.0.1:8080"),
    )


_ALLOWED_WINDOWS = {"1h", "6h", "24h", "7d", "30d", "180d", "1y"}


def _validate(config: AppConfig) -> AppConfig:
    dashboard = config.dashboard
    if dashboard.refresh_interval_seconds <= 0:
        raise ValueError("dashboard.refresh_interval_seconds must be positive")
    if dashboard.reconnect_initial_seconds <= 0:
        raise ValueError("dashboard.reconnect_initial_seconds must be positive")
    if dashboard.reconnect_max_seconds < dashboard.reconnect_initial_seconds:
        raise ValueError("dashboard.reconnect_max_seconds must be >= reconnect_initial_seconds")
    if dashboard.request_timeout_seconds <= 0:
        raise ValueError("dashboard.request_timeout_seconds must be positive")
    if dashboard.history_window not in _ALLOWED_WINDOWS:
        raise ValueError(f"dashboard.history_window must be one of {sorted(_ALLOWED_WINDOWS)}")
    if not config.sites:
        raise ValueError("at least one [[sites]] entry is required")
    names: set[str] = set()
    normalized: list[SiteConfig] = []
    for site in config.sites:
        if not site.name.strip():
            raise ValueError("site name must not be empty")
        if site.name in names:
            raise ValueError(f"duplicate site name: {site.name}")
        if not site.base_url.startswith(("http://", "https://")):
            raise ValueError(f"site {site.name!r} base_url must use http:// or https://")
        names.add(site.name)
        normalized.append(site.normalized())
    return AppConfig(dashboard=dashboard, sites=tuple(normalized))


def load_config(path: str | None = None) -> AppConfig:
    """Load dashboard configuration before the async UI runtime starts."""

    if path is None:
        return _validate(AppConfig())
    payload = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    dashboard = DashboardConfig(**payload.get("dashboard", {}))
    raw_sites = payload.get("sites", [])
    sites = tuple(SiteConfig(**item) for item in raw_sites)
    return _validate(AppConfig(dashboard=dashboard, sites=sites))


def apply_cli_overrides(
    config: AppConfig,
    *,
    site: str | None = None,
    system: str | None = None,
    compact: bool | None = None,
    low_bandwidth: bool | None = None,
    alert_only: bool | None = None,
) -> AppConfig:
    """Return an immutable configuration with command-line overrides applied."""

    sites = config.sites
    if site is not None:
        matches = tuple(item for item in sites if item.name == site)
        if not matches:
            raise ValueError(f"unknown site {site!r}; configured sites: {', '.join(s.name for s in sites)}")
        sites = matches
    if system is not None:
        sites = tuple(replace(item, system=system) for item in sites)
    dashboard = config.dashboard
    dashboard = replace(
        dashboard,
        compact=dashboard.compact if compact is None else compact,
        low_bandwidth=dashboard.low_bandwidth if low_bandwidth is None else low_bandwidth,
        alert_only=dashboard.alert_only if alert_only is None else alert_only,
    )
    if dashboard.low_bandwidth:
        dashboard = replace(dashboard, refresh_interval_seconds=max(60.0, dashboard.refresh_interval_seconds))
    return _validate(AppConfig(dashboard=dashboard, sites=sites))
