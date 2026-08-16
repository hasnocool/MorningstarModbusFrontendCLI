"""Small reusable terminal widgets."""

from __future__ import annotations

from textual.widgets import Static


class MetricCard(Static):
    """Compact label/value/unit card updated without reconstructing layout."""

    DEFAULT_CSS = """
    MetricCard {
        border: round $surface-lighten-2;
        padding: 0 1;
        min-width: 18;
        height: 4;
    }
    """

    def set_metric(self, label: str, value: str, detail: str = "") -> None:
        suffix = f"\n[dim]{detail}[/dim]" if detail else ""
        self.update(f"[b]{label}[/b]\n{value}{suffix}")
