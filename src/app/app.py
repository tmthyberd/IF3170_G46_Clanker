import os
import sys
from pathlib import Path

from src.core.models import Package, Truck, Placement
from src.app.interface import create_top_section, create_left_section, create_right_section, create_center_section
import src.app.callback

from dash import Dash, dcc, html, Input, ALL
import dash_bootstrap_components as dbc


DEBUG = (os.environ.get('debug', 'false') == 'true')

if __name__ == '__main__':
    app = Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            dbc.icons.FONT_AWESOME
        ],
        suppress_callback_exceptions=False
    )

    app.title = "Local Search"

    app.layout = dbc.Container([
        dcc.Store(id="store-app-mode", storage_type="session", data="input"),
        dcc.Store(id="store-t1-rows", storage_type="session", data=5),
        dcc.Store(id="store-t2-rows", storage_type="session", data=2),
        dcc.Store(id="store-parsed-file-data", storage_type="session"),
        dcc.Store(id="store-history", storage_type="memory"),
        dcc.Store(id="store-instance-cache", storage_type="memory"),
        dcc.Store(id="store-left-open", storage_type="session", data=True),
        dcc.Store(id="store-right-open", storage_type="session", data=False),
        dcc.Store(id="store-solver-job-id", storage_type="memory"),
        dcc.Interval(id="solver-poll-interval", interval=500, disabled=True, n_intervals=0),
        
        html.Div(
            id="floating-left-container",
            children=[
                dbc.Button([html.I(className="fas fa-chevron-right me-1"), " Config"],
                        id="btn-floating-open-left", color="primary", size="sm",
                        className="floating-tab-left shadow")
            ],
            style={"display": "none"}
        ),
        html.Div(
            id="floating-right-container",
            children=[
                dbc.Button(["Analytics ", html.I(className="fas fa-chevron-left ms-1")],
                        id="btn-floating-open-right", color="primary", size="sm",
                        className="floating-tab-right shadow")
            ],
            style={"display": "none"}
        ),
        
        dcc.Interval(id="animation-interval", interval=350, disabled=True, n_intervals=0),
        
        dbc.Row(dbc.Col(create_top_section(), width=12), className="mt-2"),
        
        dbc.Row([
            dbc.Col(create_left_section(), id="col-left", width=12, lg=3, className="mb-3 mb-lg-0 layout-col panel-slider panel-left-open"),
            dbc.Col(create_center_section(), id="col-center", width=12, lg=6, className="mb-3 mb-lg-0 layout-col"),
            dbc.Col(create_right_section(), id="col-right", width=12, lg=3, className="layout-col panel-slider panel-right-open")
        ], id="main-layout-row", className="g-3 align-items-stretch me-0 ms-0")
    ], fluid=True, className="pb-4 bg-light")

    app.run(debug=DEBUG)
