from typing import List, Dict, Any, Optional

from dash import Dash, dcc, html, Input, Output, State, ALL, MATCH, callback, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.core.models import ORIENTATION_NAMES


def create_custom_number_input(prefix_id, label, default_val=5, min_val=1, max_val=20):
    return html.Div([
        dbc.Label(label, className="fw-bold fs-7 mb-1 text-secondary"),
        dbc.InputGroup([
            dbc.Button("-", id=f"{prefix_id}-btn-dec", color="outline-secondary", size="sm"),
            dbc.Input(id=f"{prefix_id}-num-input", type="number", value=default_val, min=min_val, max=max_val, size="sm", className="text-center fw-bold"),
            dbc.Button("+", id=f"{prefix_id}-btn-inc", color="outline-secondary", size="sm"),
        ], size="sm", className="mb-2"),
        dcc.Slider(
            id=f"{prefix_id}-slider",
            min=min_val,
            max=max_val,
            step=1,
            value=default_val,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": False}
        )
    ], className="mb-3 p-2 border rounded bg-light")



def create_package_input_table(num_rows: int, packages_data: Optional[List[Dict[str, Any]]] = None):
    headers = [
        "#", "Package ID", "Fragile", "Orientation",
        "Width (W)", "Length (L)", "Height (H)", "Weight", "Value", "ETA"
    ]
    
    ori_options = [{"label": ORIENTATION_NAMES[i], "value": i} for i in range(6)]
    
    rows = []
    for i in range(num_rows):
        pkg = None
        if packages_data and i < len(packages_data):
            pkg = packages_data[i]
            
        pkg_id = pkg.get("id") if pkg else f"Package_{i+1}"
        is_fragile = bool(pkg.get("is_fragile", False)) if pkg else False
        ori = int(pkg.get("orientation", 0)) if pkg else 0
        w = float(pkg.get("w", 2.0)) if pkg else 2.0
        l = float(pkg.get("l", 3.0)) if pkg else 3.0
        h = float(pkg.get("h", 2.0)) if pkg else 2.0
        weight = float(pkg.get("weight", 10.0)) if pkg else 10.0
        val = float(pkg.get("value", 50.0)) if pkg else 50.0
        eta = float(pkg.get("eta", 1.0)) if pkg else 1.0
        
        row_cells = [
            html.Td(f"#{i+1}", className="fw-bold align-middle text-center text-muted"),
            html.Td(dbc.Input(id={"type": "t1-text", "index": i}, type="text", value=pkg_id, size="sm", style={"minWidth": "100px"})),
            html.Td(dcc.Dropdown(
                id={"type": "t1-bool", "index": i},
                options=[{"label": "True", "value": True}, {"label": "False", "value": False}],
                value=is_fragile, clearable=False, style={"minWidth": "80px"}
            )),
            html.Td(dcc.Dropdown(
                id={"type": "t1-choice", "index": i},
                options=ori_options,
                value=ori, clearable=False, style={"minWidth": "140px"}
            )),
            html.Td(dbc.Input(id={"type": "t1-float-1", "index": i}, type="number", step=0.1, min=0.1, value=w, size="sm", style={"minWidth": "65px"})),
            html.Td(dbc.Input(id={"type": "t1-float-2", "index": i}, type="number", step=0.1, min=0.1, value=l, size="sm", style={"minWidth": "65px"})),
            html.Td(dbc.Input(id={"type": "t1-float-3", "index": i}, type="number", step=0.1, min=0.1, value=h, size="sm", style={"minWidth": "65px"})),
            html.Td(dbc.Input(id={"type": "t1-float-4", "index": i}, type="number", step=0.1, min=0.1, value=weight, size="sm", style={"minWidth": "65px"})),
            html.Td(dbc.Input(id={"type": "t1-float-5", "index": i}, type="number", step=0.1, min=0.0, value=val, size="sm", style={"minWidth": "65px"})),
            html.Td(dbc.Input(id={"type": "t1-float-6", "index": i}, type="number", step=1, min=1, value=eta, size="sm", style={"minWidth": "60px"})),
        ]
        rows.append(html.Tr(row_cells))
        
    return dbc.Table([
        html.Thead(html.Tr([html.Th(h, className="text-center fs-8 py-1") for h in headers]), className="table-light"),
        html.Tbody(rows)
    ], bordered=True, hover=True, size="sm", className="bg-white align-middle fs-8 mb-0")



def create_truck_input_table(num_rows: int, trucks_data: Optional[List[Dict[str, Any]]] = None):
    headers = ["#", "Width (W)", "Length (L)", "Height (H)", "Max Capacity"]
    
    rows = []
    for i in range(num_rows):
        truck = None
        if trucks_data and i < len(trucks_data):
            truck = trucks_data[i]
            
        w = float(truck.get("w", 10.0)) if truck else 10.0
        l = float(truck.get("l", 20.0)) if truck else 20.0
        h = float(truck.get("h", 5.0)) if truck else 5.0
        cap = float(truck.get("max_capacity", 500.0)) if truck else 500.0
        
        row_cells = [
            html.Td(f"Truck #{i+1}", className="fw-bold align-middle text-center text-muted"),
            html.Td(dbc.Input(id={"type": "t2-float-1", "index": i}, type="number", step=0.1, min=1.0, value=w, size="sm", style={"minWidth": "80px"})),
            html.Td(dbc.Input(id={"type": "t2-float-2", "index": i}, type="number", step=0.1, min=1.0, value=l, size="sm", style={"minWidth": "80px"})),
            html.Td(dbc.Input(id={"type": "t2-float-3", "index": i}, type="number", step=0.1, min=1.0, value=h, size="sm", style={"minWidth": "80px"})),
            html.Td(dbc.Input(id={"type": "t2-float-4", "index": i}, type="number", step=1.0, min=1.0, value=cap, size="sm", style={"minWidth": "90px"})),
        ]
        rows.append(html.Tr(row_cells))
        
    return dbc.Table([
        html.Thead(html.Tr([html.Th(h, className="text-center fs-8 py-1") for h in headers]), className="table-light"),
        html.Tbody(rows)
    ], bordered=True, hover=True, size="sm", className="bg-white align-middle fs-8 mb-0")



def create_top_section():
    return dbc.Card(
        dbc.CardBody(
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.H5("Mejiro Express Packing Optimizer", className="mb-0 fw-bold text-primary"),
                        html.Small("Optimize Packing in Truck using Local Search techniques", className="text-muted d-block")
                    ]),
                    width=12, md=4, className="d-flex align-items-center mb-2 mb-md-0"
                ),
                dbc.Col(
                    dbc.ButtonGroup(
                        [
                            dbc.Button([html.I(className="fas fa-edit me-2"), "Input"], id="btn-mode-input", color="primary", active=True, style={"width": "140px"}),
                            dbc.Button([html.I(className="fas fa-cubes me-2"), "Result"], id="btn-mode-result", color="secondary", active=False, style={"width": "140px"}),
                        ],
                        className="justify-content-center shadow-xs"
                    ),
                    width=12, md=4, className="d-flex justify-content-center align-items-center mb-2 mb-md-0"
                ),
                dbc.Col(
                    html.Div(id="top-status-badge", children=[
                        dbc.Badge("Mode: Setup", color="info", className="p-2 fs-7")
                    ], className="text-md-end text-center"),
                    width=12, md=4, className="d-flex justify-content-md-end justify-content-center align-items-center"
                )
            ])
        ),
        className="mb-3 shadow-sm border-0 bg-white"
    )


def create_left_section():
    return dbc.Card([
        dbc.CardHeader([
            html.Span([html.I(className="fas fa-sliders-h me-2 text-primary"), "Configuration"], className="fw-bold text-dark"),
            dbc.Button(html.I(className="fas fa-chevron-left"), id="btn-left-close", size="sm", color="link", className="panel-close-btn", title="Slide Left to Hide")
        ], className="card-header-light d-flex justify-content-between align-items-center"),
        dbc.CardBody([
            # File Upload
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt me-2 fa-lg"),
                    html.Span("Drag & Drop or "), html.A("Select JSON File", className="fw-bold text-decoration-underline")
                ]),
                style={
                    "width": "100%", "height": "56px", "lineHeight": "56px",
                    "borderWidth": "2px", "borderStyle": "dashed", "borderRadius": "8px",
                    "textAlign": "center", "cursor": "pointer", "fontSize": "13px"
                },
                className="mb-2 border-primary text-primary bg-light"
            ),
            html.Div(id="upload-feedback", className="mb-2"),
            
            # Number Inputs: Packages count & Trucks count
            create_custom_number_input("rows-t1", "Packages Count (Table 1)", default_val=5, min_val=1, max_val=25),
            create_custom_number_input("rows-t2", "Trucks Count (Table 2)", default_val=2, min_val=1, max_val=10),
            
            # Dropdown 1: Algorithm Selection
            dbc.Label([html.I(className="fas fa-brain me-1 text-primary"), " Local Search Algorithm"], className="fw-bold fs-7 mb-1"),
            dcc.Dropdown(
                id="config-dropdown-1",
                options=[
                    {"label": "Steepest Ascent Hill-Climbing", "value": "hc_steepest"},
                    {"label": "Stochastic Hill-Climbing", "value": "hc_stochastic"},
                    {"label": "Hill-Climbing (Sideways Move)", "value": "hc_sideways"},
                    {"label": "Random Restart Hill-Climbing", "value": "hc_random_restart"},
                    {"label": "Simulated Annealing", "value": "simulated_annealing"},
                    {"label": "Genetic Algorithm", "value": "genetic_algorithm"},
                ],
                value="hc_steepest",
                clearable=False,
                className="mb-2 fs-7"
            ),
            dbc.Checkbox(
                id="algo-strict-checkbox",
                label="strict",
                value=False,
                className="fs-7 mb-2"
            ),
            
            # Dynamic Algorithm Parameters Container
            html.Div(id="algo-params-container", className="mb-3 p-2 border rounded bg-white fs-7"),
            
            dbc.Button([html.I(className="fas fa-dice me-2"), "Randomize Input"], id="btn-randomize", color="outline-warning", size="sm", className="w-100 mb-3"),
            
            # Dropdown 2: Objective Function
            dbc.Label([html.I(className="fas fa-bullseye me-1 text-danger"), " Objective Function"], className="fw-bold fs-7 mb-1"),
            dcc.Dropdown(
                id="config-dropdown-2",
                options=[
                    {"label": "Total Value", "value": "default"},
                    {"label": "Volume", "value": "volume"},
                    {"label": "ETA", "value": "eta"},
                    {"label": "Total Value + Volume", "value": "bonus_volume"},
                    {"label": "Total Value + Nearest ETA", "value": "bonus_eta"},
                    {"label": "Total Value + Volume + Nearest ETA", "value": "bonus_volume_eta"},
                ],
                value="default",
                clearable=False,
                className="mb-3 fs-7"
            ),
            
            # Submit / Solve Button
            dbc.Button([html.I(className="fas fa-play me-2"), "Solve Optimization"], id="btn-solve", color="success", size="md", className="w-100 py-2 fw-bold shadow-sm"),
            
            # Export JSON helper
            dbc.Input(
                id="export-filename-input",
                type="text",
                placeholder="bin_packing_instance.json",
                value="bin_packing_instance.json",
                size="sm",
                className="mt-3 mb-1 fs-8"
            ),
            dbc.Button([html.I(className="fas fa-download me-2"), "Export Config as JSON"], id="btn-export-json", color="outline-info", size="sm", className="w-100"),
            dcc.Download(id="download-json")
        ])
    ], className="shadow-sm h-100 border-0")


def create_center_section():
    return dbc.Card([
        dbc.CardHeader([
            dbc.Button([html.I(className="fas fa-sliders-h me-1"), "Config"], id="btn-center-toggle-left", size="sm", className="middle-toggle-btn", title="Toggle Configuration Sidebar"),
            html.Div([
                html.Span([html.I(className="fas fa-desktop me-2 text-primary"), "Workspace: "], className="fw-bold text-dark"),
                html.Span(id="workspace-header-title", children="Input Tables Mode", className="fw-semibold text-primary")
            ], className="d-flex align-items-center"),
            dbc.Button(["Analytics", html.I(className="fas fa-chart-line ms-1")], id="btn-center-toggle-right", size="sm", className="middle-toggle-btn", title="Toggle Analytics Sidebar")
        ], className="card-header-light d-flex justify-content-between align-items-center"),
        
        dbc.CardBody([
            # Container for Input Tables (Mode: Input)
            html.Div(id="input-mode-container", className="w-100", children=[
                html.Div([
                    html.H6([html.I(className="fas fa-boxes me-2"), "Packages Configuration (Table 1)"], className="fw-bold text-primary mb-1"),
                    html.Small("Specify package dimensions (W, L, H), weight, value, fragility, and initial orientation.", className="text-muted d-block mb-2"),
                ]),
                html.Div(id="table-1-wrapper", className="table-responsive mb-4", style={"maxHeight": "280px", "overflowY": "auto"}),
                
                html.Div([
                    html.H6([html.I(className="fas fa-truck-moving me-2"), "Truck Fleet Configuration (Table 2)"], className="fw-bold text-primary mb-1"),
                    html.Small("Specify container container dimensions (W, L, H) and maximum weight capacity.", className="text-muted d-block mb-2"),
                ]),
                html.Div(id="table-2-wrapper", className="table-responsive mb-2", style={"maxHeight": "200px", "overflowY": "auto"})
            ]),
            
            # Container for 3D Result Canvas (Mode: Result)
            html.Div(
                id="result-mode-container",
                className="w-100 h-100",
                style={"display": "none"},
                children=[
                    dcc.Graph(
                        id="canvas-3d",
                        responsive=True,
                        config={
                            "scrollZoom": True,
                            "displayModeBar": True,
                            "toImageButtonOptions": {"format": "png", "filename": "3d_bin_packing"}
                        },
                        figure=go.Figure(
                            layout=go.Layout(
                                uirevision="truck_scene_revision",
                                autosize=True,
                                scene=dict(
                                    uirevision="truck_scene_revision",
                                    aspectmode="data",
                                    xaxis=dict(visible=False),
                                    yaxis=dict(visible=False),
                                    zaxis=dict(visible=False)
                                ),
                                margin=dict(l=0, r=0, t=0, b=0),
                                annotations=[{
                                    "text": "Belum ada hasil (Klik 'Solve' untuk mendapatkan hasil local search)",
                                    "xref": "paper", "yref": "paper",
                                    "showarrow": False, "font": {"size": 15, "color": "#64748b"}
                                }]
                            )
                        ),
                        style={"width": "100%", "height": "100%", "minHeight": "560px", "flexGrow": "1"}
                    )
                ]
            ),
        ], className="d-flex flex-column flex-grow-1 p-2 w-100 h-100 justify-content-center align-items-center"),
        
        # Bottom Animation Playback Controls (Only shown in Result Mode when results are ready)
        dbc.CardFooter(
            id="animation-player-footer",
            children=[
                html.Div(
                    id="anim-controls-wrapper",
                    children=[
                        dbc.Row([
                            dbc.Col(
                                dbc.ButtonGroup([
                                    dbc.Button(html.I(className="fas fa-fast-backward"), id="btn-anim-first", outline=True, color="secondary", size="sm", title="First Step"),
                                    dbc.Button(html.I(className="fas fa-step-backward"), id="btn-anim-prev", outline=True, color="secondary", size="sm", title="Previous Step"),
                                    dbc.Button(html.I(className="fas fa-play"), id="btn-anim-play-pause", color="primary", size="sm", title="Play Animation"),
                                    dbc.Button(html.I(className="fas fa-step-forward"), id="btn-anim-next", outline=True, color="secondary", size="sm", title="Next Step"),
                                    dbc.Button(html.I(className="fas fa-fast-forward"), id="btn-anim-last", outline=True, color="secondary", size="sm", title="Last Step"),
                                ]),
                                width="auto"
                            ),
                            dbc.Col(
                                html.Span(id="anim-step-badge", children="Step: 0 / 0 | Score: 0.0", className="badge bg-secondary p-2 fs-8 font-monospace"),
                                width="auto", className="d-flex align-items-center"
                            ),
                            dbc.Col(
                                dcc.Slider(id="animation-slider", min=0, max=0, step=1, value=0, marks=None, tooltip={"placement": "top"}),
                                className="d-flex align-items-center"
                            ),
                            dbc.Col([
                                dcc.Dropdown(
                                    id="anim-speed-dropdown",
                                    options=[
                                        {"label": "0.5x", "value": 700},
                                        {"label": "1x", "value": 350},
                                        {"label": "2x", "value": 180},
                                        {"label": "5x", "value": 70},
                                    ],
                                    value=350,
                                    clearable=False,
                                    searchable=False,
                                    style={"width": "75px"},
                                    className="fs-8"
                                )
                            ], width="auto", className="d-flex align-items-center")
                        ], className="align-items-center g-2")
                    ],
                    style={"display": "none"}
                ),

                html.Div(
                    id="anim-no-result-msg",
                    children=[
                        html.Div([
                            html.I(className="fas fa-info-circle me-2 text-primary"),
                            "Configure inputs and click 'Solve Optimization' to generate playback animation."
                        ], className="text-muted fs-8 py-1 text-center")
                    ],
                    style={"display": "block"}
                )
            ],
            className="bg-white border-top py-2",
            style={"display": "none"}
        )
    ], className="shadow-sm h-100 border-0")


def create_right_section():
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Span([html.I(className="fas fa-chart-line me-2 text-primary"), "Analytics & Results"], className="fw-bold text-dark"),
            ], className="d-flex align-items-center"),
            dbc.Button([html.I(className="fas fa-desktop me-1"), "Workspace View"], id="btn-right-close", size="sm", color="outline-primary", className="py-1 px-2 fs-8", title="Switch to Workspace (Tables / 3D Scene)")
        ], className="card-header-light d-flex justify-content-between align-items-center"),
        dbc.CardBody([
            html.Div(id="metrics-summary-container", children=[
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.Small("Best Score", className="text-muted d-block"),
                            html.H5("0.0", id="metric-best-score", className="mb-0 fw-bold text-success")
                        ], className="p-2 text-center")
                    ], className="bg-light border-0 shadow-none mb-2"), width=6, md=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.Small("Duration", className="text-muted d-block"),
                            html.H5("0.00s", id="metric-duration", className="mb-0 fw-bold text-primary")
                        ], className="p-2 text-center")
                    ], className="bg-light border-0 shadow-none mb-2"), width=6, md=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.Small("Packed / Unpacked", className="text-muted d-block"),
                            html.H6("0 / 0", id="metric-packed-count", className="mb-0 fw-bold text-dark")
                        ], className="p-2 text-center")
                    ], className="bg-light border-0 shadow-none mb-2"), width=6, md=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.Small("Total Steps", className="text-muted d-block"),
                            html.H6("0", id="metric-total-steps", className="mb-0 fw-bold text-dark")
                        ], className="p-2 text-center")
                    ], className="bg-light border-0 shadow-none mb-2"), width=6, md=3),
                ], className="g-2"),
                html.Div(id="violations-alert-container", className="mb-2")
            ]),
            
            html.Div([
                dbc.Row([
                    dbc.Col(dbc.Label("Select Graph View:", className="fw-bold fs-8 mb-0 text-muted align-self-center"), width="auto"),
                    dbc.Col(dcc.Dropdown(
                        id="graph-view-selector",
                        options=[
                            {"label": "Objective Value vs Iterations", "value": "objective_curve"},
                            {"label": "Algorithm Metric (SA / GA / Random Restart)", "value": "algo_metric"},
                            {"label": "Truck Capacity Breakdown", "value": "truck_breakdown"},
                        ],
                        value="objective_curve",
                        clearable=False,
                        className="fs-8"
                    ), className="flex-grow-1")
                ], className="align-items-center mb-2 g-2")
            ]),
            
            dcc.Graph(
                id="result-2d-graph",
                responsive=True,
                figure=go.Figure(
                    layout=go.Layout(
                        autosize=True,
                        title=dict(text="Objective Value vs Iterations", font=dict(size=13)),
                        xaxis=dict(title="Iteration", showgrid=True),
                        yaxis=dict(title="Score", showgrid=True),
                        margin=dict(l=40, r=20, t=35, b=35),
                        annotations=[{
                            "text": "Run optimization to plot metrics",
                            "xref": "paper", "yref": "paper",
                            "showarrow": False, "font": {"size": 13, "color": "#94a3b8"}
                        }]
                    )
                ),
                style={"width": "100%", "height": "100%", "minHeight": "600px", "flexGrow": "1"}
            )
        ], className="p-3 d-flex flex-column flex-grow-1")
    ], className="shadow-sm h-100 border-0 d-flex flex-column")