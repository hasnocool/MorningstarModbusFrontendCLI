"""Dashboard content views from v0.1 through v0.5."""

from morningstar_tui.views.controllers import ControllersView
from morningstar_tui.views.events import EventsView
from morningstar_tui.views.forecast import ForecastView
from morningstar_tui.views.history import HistoryView
from morningstar_tui.views.incidents import IncidentsView
from morningstar_tui.views.investigation import InvestigationView
from morningstar_tui.views.noc import NOCView
from morningstar_tui.views.overview import OverviewView
from morningstar_tui.views.power_flow import PowerFlowView

__all__ = [
    "ControllersView",
    "EventsView",
    "ForecastView",
    "HistoryView",
    "IncidentsView",
    "InvestigationView",
    "NOCView",
    "OverviewView",
    "PowerFlowView",
]
