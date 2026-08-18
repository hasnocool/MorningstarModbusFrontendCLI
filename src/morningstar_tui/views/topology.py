"""v0.9 component graph, electrical relationships and transport topology view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.util.explorer import compact_mapping, record_rows
from morningstar_tui.util.formatting import text
from morningstar_tui.views.base import DashboardView


class TopologyView(DashboardView):
    def compose(self) -> ComposeResult:
        yield Static("TOPOLOGY / COMPONENT GRAPH", classes="view-title")
        yield Static(
            "Electrical relationships retain API confidence/evidence. Transport proximity is not treated as proof of wiring.",
            classes="hint",
        )
        yield Static("Loading topology…", id="topology-summary", classes="panel")
        yield Static("COMPONENTS", classes="view-title")
        yield DataTable(id="topology-components", zebra_stripes=True, cursor_type="row")
        yield Static("RELATIONSHIPS", classes="view-title")
        yield DataTable(id="topology-relationships", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#topology-components", DataTable).add_columns(
            "Component", "Type", "Status", "Controller / serial", "Evidence"
        )
        self.query_one("#topology-relationships", DataTable).add_columns(
            "Source", "Relationship", "Target", "Confidence", "Evidence"
        )

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del all_states
        details = state.site_details
        summary_payload = details.topology or details.component_graph
        self.query_one("#topology-summary", Static).update(
            f"Site: {state.name} · {state.system_uid}\n\n{compact_mapping(summary_payload, limit=36)}"
        )
        components = record_rows(details.components, "components")
        if not components:
            components = record_rows(details.component_graph, "components", "nodes")
        relationships = record_rows(details.relationships, "relationships")
        if not relationships:
            relationships = record_rows(details.component_graph, "relationships", "edges")
        self._components(components)
        self._relationships(relationships)

    def _components(self, rows: list[dict[str, object]]) -> None:
        table = self.query_one("#topology-components", DataTable)
        table.clear(columns=False)
        for item in rows[:300]:
            identity = item.get("controller_uid") or item.get("serial_number") or item.get("serial")
            table.add_row(
                text(item.get("component_uid") or item.get("uid") or item.get("id") or item.get("name")),
                text(item.get("component_type") or item.get("type") or item.get("kind")),
                text(item.get("status") or item.get("state")),
                text(identity),
                text(item.get("evidence") or item.get("source") or item.get("provenance")),
            )
        if not rows:
            table.add_row("—", "No components returned", "", "", "")

    def _relationships(self, rows: list[dict[str, object]]) -> None:
        table = self.query_one("#topology-relationships", DataTable)
        table.clear(columns=False)
        for item in rows[:400]:
            table.add_row(
                text(item.get("source") or item.get("source_uid") or item.get("from")),
                text(item.get("relationship") or item.get("relationship_type") or item.get("type")),
                text(item.get("target") or item.get("target_uid") or item.get("to")),
                text(item.get("confidence") or item.get("quality")),
                text(item.get("evidence") or item.get("source_evidence") or item.get("provenance")),
            )
        if not rows:
            table.add_row("—", "No relationships returned", "", "", "")
