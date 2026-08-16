"""Async-safe state store for concurrent REST and SSE producers."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from morningstar_tui.state.models import ControllerIntegrityBundle, InvestigationBundle, SiteState

StateCallback = Callable[[str], None]


class StateStore:
    """Protect mutable site snapshots with an asyncio lock."""

    def __init__(self, states: list[SiteState]) -> None:
        self._states = {state.name: state for state in states}
        self._lock = asyncio.Lock()
        self._callback: StateCallback | None = None

    def set_callback(self, callback: StateCallback | None) -> None:
        self._callback = callback

    async def names(self) -> tuple[str, ...]:
        async with self._lock:
            return tuple(self._states)

    async def snapshot(self, name: str) -> SiteState:
        async with self._lock:
            return deepcopy(self._states[name])

    async def snapshots(self) -> list[SiteState]:
        async with self._lock:
            return [deepcopy(value) for value in self._states.values()]

    async def patch(self, name: str, **changes: Any) -> None:
        async with self._lock:
            state = self._states[name]
            for key, value in changes.items():
                setattr(state, key, value)
            state.touch()
        self._notify(name)

    async def telemetry(self, name: str, payload: dict[str, Any]) -> None:
        await self.patch(name, latest=payload, online=True, stream_online=True, last_error=None)

    async def event(self, name: str, event: dict[str, Any], *, limit: int = 500) -> None:
        async with self._lock:
            state = self._states[name]
            state.events.insert(0, event)
            del state.events[limit:]
            state.stream_online = True
            state.online = True
            state.last_error = None
            state.touch()
        self._notify(name)

    async def investigation(self, name: str, bundle: InvestigationBundle) -> None:
        await self.patch(name, investigation=bundle)

    async def select_controller(self, name: str, controller_uid: str | None) -> None:
        await self.patch(name, selected_controller_uid=controller_uid)

    async def controller_integrity(
        self,
        name: str,
        controller_uid: str,
        bundle: ControllerIntegrityBundle,
    ) -> None:
        """Atomically update one controller cache entry without losing concurrent writers."""

        async with self._lock:
            state = self._states[name]
            state.controller_integrity[controller_uid] = bundle
            state.touch()
        self._notify(name)

    def _notify(self, name: str) -> None:
        if self._callback is not None:
            self._callback(name)
