"""Dashboard content views from v0.1 through v0.8."""

from morningstar_tui.views.command_palette import CommandChosen, CommandPaletteView
from morningstar_tui.views.controller_detail import ControllerDetailView
from morningstar_tui.views.controllers import ControllerActivated, ControllersView
from morningstar_tui.views.events import EventsView
from morningstar_tui.views.fleet import FleetView
from morningstar_tui.views.forecast import ForecastView
from morningstar_tui.views.history import HistoryView
from morningstar_tui.views.incidents import IncidentsView
from morningstar_tui.views.investigation import InvestigationView
from morningstar_tui.views.noc import NOCView
from morningstar_tui.views.overview import OverviewView
from morningstar_tui.views.power_flow import PowerFlowView

__all__ = [
    "CommandChosen",
    "CommandPaletteView",
    "ControllerActivated",
    "ControllerDetailView",
    "ControllersView",
    "EventsView",
    "FleetView",
    "ForecastView",
    "HistoryView",
    "IncidentsView",
    "InvestigationView",
    "NOCView",
    "OverviewView",
    "PowerFlowView",
]
