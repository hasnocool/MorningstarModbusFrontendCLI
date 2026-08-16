"""Base class for dashboard content views."""

from __future__ import annotations

from textual.containers import VerticalScroll

from morningstar_tui.state.models import SiteState


class DashboardView(VerticalScroll):
    """A view that can render the selected site's immutable snapshot."""

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del state, all_states
