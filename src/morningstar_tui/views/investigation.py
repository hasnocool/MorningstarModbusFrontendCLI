"""v0.4 historical investigation/time-travel console."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.formatting import event_summary, text, values_from_history
from morningstar_tui.util.sparkline import sparkline
from morningstar_tui.views.base import DashboardView


class InvestigationView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("INVESTIGATION / TIME TRAVEL", classes="view-title")
        yield Static(
            "Press t to jump to now; -/+ shifts 5 minutes; PageUp/PageDown shifts one hour.",
            classes="hint",
        )
        yield Static(id="inv-cursor", classes="panel")
        yield Static(id="inv-series", classes="panel tall")
        yield Static(id="inv-events", classes="panel")

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        bundle = state.investigation
        if bundle is None:
            self.query_one("#inv-cursor", Static).update("Press t to load a historical investigation window.")
            self.query_one("#inv-series", Static).update("")
            self.query_one("#inv-events", Static).update("")
            return
        self.query_one("#inv-cursor", Static).update(
            f"cursor {bundle.cursor.isoformat()}\nwindow {bundle.start.isoformat()} → {bundle.end.isoformat()}"
        )
        if bundle.error:
            self.query_one("#inv-series", Static).update(bundle.error)
            return
        lines = ["[b]Correlated telemetry[/b]"]
        for metric_name, payload in bundle.histories.items():
            values = values_from_history(payload)
            lines.append(f"{metric_name:28} {sparkline(values, width=62) or '—'}")
        self.query_one("#inv-series", Static).update("\n".join(lines))
        event_lines = ["[b]Events in window[/b]"]
        for event in bundle.events[:30]:
            event_lines.append(
                f"{text(event.get('observed_at') or event.get('timestamp')):25} "
                f"{text(event.get('event_type') or event.get('type')):22} {event_summary(event)}"
            )
        if len(event_lines) == 1:
            event_lines.append("none")
        self.query_one("#inv-events", Static).update("\n".join(event_lines))
