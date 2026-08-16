"""In-memory read models shared by the runtime and Textual views."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class InvestigationBundle:
    cursor: datetime
    start: datetime
    end: datetime
    histories: dict[str, object] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class SiteState:
    name: str
    base_url: str
    system_uid: str = "sys_default"
    online: bool = False
    stream_online: bool = False
    latency_ms: float | None = None
    last_error: str | None = None
    last_update: datetime | None = None
    system: dict[str, Any] = field(default_factory=dict)
    latest: dict[str, Any] = field(default_factory=dict)
    controllers: list[dict[str, Any]] = field(default_factory=list)
    power_flow: dict[str, Any] = field(default_factory=dict)
    energy_ledger: dict[str, Any] = field(default_factory=dict)
    health: dict[str, Any] = field(default_factory=dict)
    health_score: dict[str, Any] = field(default_factory=dict)
    baselines: dict[str, Any] = field(default_factory=dict)
    incidents: list[dict[str, Any]] = field(default_factory=list)
    forecast: dict[str, Any] = field(default_factory=dict)
    forecast_accuracy: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    history: object = field(default_factory=dict)
    history_metric: str = "solar_input_power_w"
    history_window: str = "24h"
    investigation: InvestigationBundle | None = None

    def touch(self) -> None:
        self.last_update = datetime.now(UTC)
