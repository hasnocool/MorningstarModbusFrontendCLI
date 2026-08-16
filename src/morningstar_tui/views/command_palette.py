"""v0.7 keyboard command palette and searchable operator actions."""

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
    keywords: str = ""


class CommandChosen(Message):
    """Posted when a command-palette action is selected."""

    def __init__(self, action: str) -> None:
        super().__init__()
        self.action = action


COMMANDS = (
    PaletteCommand("show_overview", "Open site overview", "1", "site telemetry status"),
    PaletteCommand("show_controllers", "Open controller inventory", "2", "hardware devices"),
    PaletteCommand("show_power", "Open power flow", "3", "energy ledger topology"),
    PaletteCommand("show_incidents", "Open incidents", "4", "alerts evidence"),
    PaletteCommand("show_forecast", "Open forecast", "5", "prediction solar float"),
    PaletteCommand("show_history", "Open history", "6", "chart telemetry"),
    PaletteCommand("show_events", "Open events", "7", "timeline"),
    PaletteCommand("show_investigation", "Open investigation", "8", "time cursor forensic"),
    PaletteCommand("show_noc", "Open multi-site NOC", "9", "network operations"),
    PaletteCommand("show_controller_detail", "Open selected controller operations", "D", "coverage gaps energy"),
    PaletteCommand("show_fleet", "Open fleet comparison", "F", "90 day long term analytics"),
    PaletteCommand("refresh_site", "Refresh selected site", "R", "reload"),
    PaletteCommand("refresh_fleet", "Refresh fleet analytics", "Shift+R", "reload all controllers"),
    PaletteCommand("investigate_now", "Investigate current time", "T", "forensic cursor"),
)


class CommandPaletteView(DashboardView):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._matches: list[PaletteCommand] = list(COMMANDS)

    def compose(self) -> ComposeResult:
        yield Static("COMMAND PALETTE", classes="view-title")
        yield Static(
            "Type to filter commands. Enter runs the highlighted command; Esc returns.",
            classes="hint",
        )
        yield Input(placeholder="Search commands…", id="command-query")
        yield DataTable(id="command-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self.query_one("#command-table", DataTable).add_columns("Command", "Keys")
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
            haystack = f"{command.label} {command.action} {command.keywords}".lower()
            if all(word in haystack for word in words):
                matches.append(command)
        self._matches = matches
        table = self.query_one("#command-table", DataTable)
        table.clear(columns=False)
        for command in matches:
            table.add_row(command.label, command.keys)

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
