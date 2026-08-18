"""v0.9 keyboard command palette and searchable operator workspaces."""

from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, Input, Static

from morningstar_tui.state.models import SiteState
from morningstar_tui.views.base import DashboardView


@dataclass(frozen=True, slots=True)
class PaletteCommand:
    action: str
    label: str
    keys: str
    group: str
    keywords: str = ""


class CommandChosen(Message):
    """Posted when a command-palette action is selected."""

    def __init__(self, action: str) -> None:
        super().__init__()
        self.action = action


COMMANDS = (
    PaletteCommand("show_overview", "Open command-center overview", "1", "SYSTEM", "site telemetry status"),
    PaletteCommand("show_system", "Open full system/site details", "S", "SYSTEM", "metric catalog energy health baselines"),
    PaletteCommand("show_power", "Open power and energy flow", "3", "SYSTEM", "energy ledger currents residuals"),
    PaletteCommand("show_forecast", "Open forecast", "5", "INTELLIGENCE", "prediction solar float"),
    PaletteCommand("show_incidents", "Open incidents", "4", "INTELLIGENCE", "alerts evidence health"),
    PaletteCommand("show_controllers", "Open controller inventory", "2", "CONTROLLER", "hardware devices"),
    PaletteCommand("show_telemetry", "Open full live telemetry", "V", "CONTROLLER", "values registers normalized live"),
    PaletteCommand("show_controller_detail", "Open data integrity / energy", "D", "CONTROLLER", "coverage gaps reconciliation"),
    PaletteCommand("show_diagnostics", "Open controller diagnostics", "X", "CONTROLLER", "polling charge cycle health samples"),
    PaletteCommand("show_history", "Open history", "6", "HISTORY", "chart telemetry"),
    PaletteCommand("show_events", "Open events", "7", "HISTORY", "timeline"),
    PaletteCommand("show_investigation", "Open investigation", "8", "HISTORY", "time cursor forensic"),
    PaletteCommand("show_topology", "Open topology / components", "G", "SITE", "graph relationships components readyedge"),
    PaletteCommand("show_noc", "Open multi-site NOC", "9", "FLEET", "network operations"),
    PaletteCommand("show_fleet", "Open fleet comparison", "F", "FLEET", "90 day long term analytics"),
    PaletteCommand("refresh_site", "Refresh selected site", "R", "ACTION", "reload"),
    PaletteCommand("refresh_fleet", "Refresh fleet analytics", "Shift+R", "ACTION", "reload all controllers"),
    PaletteCommand("investigate_now", "Investigate current time", "T", "ACTION", "forensic cursor"),
)


class CommandPaletteView(DashboardView):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._matches: list[PaletteCommand] = list(COMMANDS)

    def compose(self) -> ComposeResult:
        yield Static("COMMAND PALETTE", classes="view-title")
        yield Static(
            "Workspaces are grouped by system, controller, history, site and fleet. Type to filter; Enter runs the highlighted command.",
            classes="hint",
        )
        yield Input(placeholder="Search commands, data or workspace…", id="command-query")
        yield DataTable(id="command-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#command-table", DataTable).add_columns("Group", "Command", "Keys")
        self.refresh_commands("")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "command-query":
            self.refresh_commands(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "command-query":
            action = self.selected_action()
            if action:
                self.post_message(CommandChosen(action))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "command-table":
            action = self.selected_action()
            if action:
                self.post_message(CommandChosen(action))

    def refresh_commands(self, query: str) -> None:
        words = [part.lower() for part in query.split() if part.strip()]
        matches = []
        for command in COMMANDS:
            haystack = f"{command.group} {command.label} {command.action} {command.keywords}".lower()
            if all(word in haystack for word in words):
                matches.append(command)
        self._matches = matches
        table = self.query_one("#command-table", DataTable)
        table.clear(columns=False)
        for command in matches:
            table.add_row(command.group, command.label, command.keys)

    def selected_action(self) -> str | None:
        table = self.query_one("#command-table", DataTable)
        row = table.cursor_row
        if 0 <= row < len(self._matches):
            return self._matches[row].action
        return None

    def focus_query(self, *, clear: bool = False) -> None:
        field = self.query_one("#command-query", Input)
        if clear:
            field.value = ""
        field.focus()

    def refresh_state(self, state: SiteState, all_states: list[SiteState]) -> None:
        del state, all_states
