import sys
import base64
import json
import random
import threading
import time
import math
import uuid
import traceback
from typing import Dict, Optional, Any, Tuple, List, Generator
from pathlib import Path

from dash import Dash, html, Input, Output, State, ALL, callback, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.core.models import Package, Truck, ProblemInstance, Placement, SolverState
from src.core.objective import calculate_objective, evaluate_state
from src.core.moves import get_all_successors, get_random_successor, generate_initial_state
from src.core.validator import validate_state

from src.app.scene import render_scene_3d
from src.app.interface import create_package_input_table, create_truck_input_table

from src.algorithms.hill_climbing.steepest_ascent import steepest_ascent_hill_climbing
from src.algorithms.hill_climbing.sideways_move import sideways_hill_climbing, DEFAULT_MAX_SIDEWAYS_MOVE
from src.algorithms.hill_climbing.stochastic import stochastic_hill_climbing, DEFAULT_STOCHASTIC_MAX_ITERATION
from src.algorithms.hill_climbing.random_restart import random_restart_hill_climbing, DEFAULT_MAX_RESTART
from src.algorithms.simulated_annealing.simulated_annealing import simulated_annealing, DEFAULT_COOLING_RATE, DEFAULT_INITIAL_TEMP


DEFAULT_PACKAGES = [
    Package(id="RusdiPackage", w=3.0, l=4.0, h=1.0, weight=5.0, value=60.0, is_fragile=False, eta=3.0, orientation=0),
    Package(id="FragileGlass", w=2.0, l=3.0, h=2.0, weight=8.0, value=90.0, is_fragile=True, eta=1.0, orientation=0),
    Package(id="HeavyMachinery", w=4.0, l=6.0, h=2.0, weight=120.0, value=150.0, is_fragile=False, eta=5.0, orientation=2),
    Package(id="ElectronicsBox", w=2.0, l=2.0, h=1.0, weight=10.0, value=120.0, is_fragile=True, eta=2.0, orientation=0),
    Package(id="TextilesBundle", w=3.0, l=5.0, h=2.0, weight=15.0, value=45.0, is_fragile=False, eta=4.0, orientation=1),
]


DEFAULT_TRUCKS = [
    Truck(id="Truck_1", w=10.0, l=20.0, h=5.0, max_capacity=500.0),
    Truck(id="Truck_2", w=8.0, l=16.0, h=4.0, max_capacity=350.0),
]

RANDOMIZER_MIN_PACKAGES = 5
RANDOMIZER_MAX_PACKAGES = 50
RANDOMIZER_MAX_TRUCKS = 10

def evaluate_solution(
    placements: Dict[str, Placement],
    packages: List[Package],
    trucks: List[Truck],
    objective_type: str = "default",
) -> Tuple[float, Dict[str, Any]]:
    c_trucks = trucks if isinstance(trucks, list) else [trucks]
    c_pkgs = {p.id: p for p in packages} if isinstance(packages, list) else packages
    c_plcs = {
        pid: (p if isinstance(p, Placement) else Placement.from_dict(p))
        for pid, p in placements.items()
    }
    st = SolverState(trucks=c_trucks, packages=c_pkgs, placements=c_plcs)
    return evaluate_state(st, objective_type)


def run_solver(
    algorithm_name: str,
    packages: List[Package],
    trucks: List[Truck],
    strict: bool = False,
    objective_type: str = "default",
    params: Optional[Dict[str, Any]] = {}
) -> Generator[Dict[str, Any], None, None]:

    if algorithm_name != "hc_random_restart":
        initial_state = generate_initial_state(trucks, packages)
        curr_state = initial_state.clone()

    # 1. Steepest Ascent Hill-Climbing
    if algorithm_name == "hc_steepest":
        for iteration_result in steepest_ascent_hill_climbing(initial_state, strict=strict, objective_type=objective_type):
            yield iteration_result

    # 2. Hill-Climbing with Sideways Move
    elif algorithm_name == "hc_sideways":
        for iteration_result in sideways_hill_climbing(
            initial_state,
            max_sideways_moves=params.get('max_sideways_moves', DEFAULT_MAX_SIDEWAYS_MOVE),
            strict=strict,
            objective_type=objective_type
        ):
            yield iteration_result

    # 3. Stochastic Hill-Climbing
    elif algorithm_name == "hc_stochastic":
        for iteration_result in stochastic_hill_climbing(
            initial_state,
            max_iterations=params.get("max_iterations", DEFAULT_STOCHASTIC_MAX_ITERATION),
            strict=strict,
            objective_type=objective_type
        ):
            yield iteration_result

    # 4. Random Restart Hill-Climbing
    elif algorithm_name == "hc_random_restart":
        for iteration_result in random_restart_hill_climbing(
            trucks,
            packages,
            max_restarts=params.get("max_restarts", DEFAULT_MAX_RESTART),
            strict=strict,
            objective_type=objective_type
        ):
            yield iteration_result

    # 5. Simulated Annealing
    elif algorithm_name == "simulated_annealing":
        for iteration_result in simulated_annealing(
            initial_state,
            initial_temp=params.get("initial_temp", DEFAULT_INITIAL_TEMP),
            cooling_rate=params.get("cooling_rate", DEFAULT_COOLING_RATE),
            max_iterations=params.get("max_iterations", -1),
            strict=strict,
            objective_type=objective_type
        ):
            yield iteration_result
        




# ==============================================================================
# Background Solver Job State (thread-safe)
# ==============================================================================
_solver_jobs = {}       # job_id -> {"status": "running"|"done"|"error", "result": {...}}
_solver_lock = threading.Lock()
_MAX_FINISHED_JOBS = 5  # Keep at most this many finished jobs to prevent memory leaks


def _cleanup_old_jobs():
    """Remove oldest finished jobs if we exceed the limit."""
    finished = [(k, v) for k, v in _solver_jobs.items() if v.get("status") != "running"]
    if len(finished) > _MAX_FINISHED_JOBS:
        # Sort by completion order (oldest first) and remove extras
        for k, _ in finished[:-_MAX_FINISHED_JOBS]:
            del _solver_jobs[k]


def _run_solver_in_thread(job_id, algo_name, packages, trucks, strict, objective_type, params, instance_cache):
    """Run the solver generator in a background thread and store results."""
    try:
        start_time = time.time()
        generator = run_solver(
            algorithm_name=algo_name,
            packages=packages,
            trucks=trucks,
            strict=strict,
            objective_type=objective_type,
            params=params
        )
        history = list(generator)
        duration = time.time() - start_time

        with _solver_lock:
            _solver_jobs[job_id] = {
                "status": "done",
                "history": history,
                "instance_cache": instance_cache,
                "duration": duration,
            }
            _cleanup_old_jobs()
    except Exception as e:
        traceback.print_exc()
        with _solver_lock:
            _solver_jobs[job_id] = {
                "status": "error",
                "error": str(e),
            }
            _cleanup_old_jobs()


# 1. Sync Row Count Controls with File Upload and Randomize
@callback(
    [Output("rows-t1-num-input", "value"),
     Output("rows-t1-slider", "value"),
     Output("store-t1-rows", "data")],
    [Input("rows-t1-btn-dec", "n_clicks"),
     Input("rows-t1-btn-inc", "n_clicks"),
     Input("rows-t1-num-input", "value"),
     Input("rows-t1-slider", "value"),
     Input("store-parsed-file-data", "data"),
     Input("btn-randomize", "n_clicks")],
    [State("store-t1-rows", "data")]
)
def sync_t1_rows(dec_clicks, inc_clicks, input_val, slider_val, parsed_file, randomize_clicks, current_rows):
    if not callback_context.triggered:
        val = current_rows or 5
        return val, val, val
        
    trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "store-parsed-file-data" and parsed_file and "packages" in parsed_file:
        val = max(1, len(parsed_file["packages"]))
        return val, val, val
        
    val = current_rows or 5
    if trigger_id == "rows-t1-btn-dec":
        val = max(1, (input_val or val) - 1)
    elif trigger_id == "rows-t1-btn-inc":
        val = min(25, (input_val or val) + 1)
    elif trigger_id == "rows-t1-slider":
        val = slider_val or val
    elif trigger_id == "rows-t1-num-input":
        val = max(1, min(25, input_val or val))
        
    return val, val, val


@callback(
    [Output("rows-t2-num-input", "value"),
     Output("rows-t2-slider", "value"),
     Output("store-t2-rows", "data")],
    [Input("rows-t2-btn-dec", "n_clicks"),
     Input("rows-t2-btn-inc", "n_clicks"),
     Input("rows-t2-num-input", "value"),
     Input("rows-t2-slider", "value"),
     Input("store-parsed-file-data", "data"),
     Input("btn-randomize", "n_clicks")],
    [State("store-t2-rows", "data")]
)
def sync_t2_rows(dec_clicks, inc_clicks, input_val, slider_val, parsed_file, randomize_clicks, current_rows):
    ctx = callback_context
    if not ctx.triggered:
        val = current_rows or 2
        return val, val, val
        
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "store-parsed-file-data" and parsed_file and "trucks" in parsed_file:
        val = max(1, len(parsed_file["trucks"]))
        return val, val, val
        
    val = current_rows or 2
    if trigger_id == "rows-t2-btn-dec":
        val = max(1, (input_val or val) - 1)
    elif trigger_id == "rows-t2-btn-inc":
        val = min(10, (input_val or val) + 1)
    elif trigger_id == "rows-t2-slider":
        val = slider_val or val
    elif trigger_id == "rows-t2-num-input":
        val = max(1, min(10, input_val or val))
        
    return val, val, val


# 2. File Upload Handler
@callback(
    [Output("store-parsed-file-data", "data"),
     Output("upload-feedback", "children")],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")]
)
def handle_file_upload(contents, filename):
    if contents is None:
        return no_update, no_update
        
    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string).decode("utf-8")
        parsed = json.loads(decoded)
        
        instance = ProblemInstance.from_dict(parsed)
        feedback = dbc.Alert(
            [html.I(className="fas fa-check-circle me-2"), f"Loaded '{filename}': {len(instance.packages)} packages, {len(instance.trucks)} trucks"],
            color="success", className="py-1 px-2 fs-8 mb-2"
        )
        return instance.to_dict(), feedback
    except Exception as e:
        traceback.print_exc()
        feedback = dbc.Alert(
            [html.I(className="fas fa-exclamation-triangle me-2"), f"Parse error: {str(e)}"],
            color="danger", className="py-1 px-2 fs-8 mb-2"
        )
        return None, feedback


# 2b. Randomize Input Generator
@callback(
    [Output("store-parsed-file-data", "data", allow_duplicate=True),
     Output("upload-feedback", "children", allow_duplicate=True)],
    [Input("btn-randomize", "n_clicks")],
    prevent_initial_call=True
)
def randomize_input(n_clicks):
    if not n_clicks:
        return no_update, no_update
    
    # Randomly pick number of packages and trucks
    num_packages = random.randint(RANDOMIZER_MIN_PACKAGES, RANDOMIZER_MAX_PACKAGES)
    num_trucks = random.randint(1, RANDOMIZER_MAX_TRUCKS)
    
    packages = []
    for i in range(num_packages):
        rng_suffix = random.randint(100, 9999)
        pkg = {
            "id": f"Package_{rng_suffix}",
            "w": round(random.uniform(1.0, 8.0), 1),
            "l": round(random.uniform(1.0, 8.0), 1),
            "h": round(random.uniform(1.0, 5.0), 1),
            "weight": round(random.uniform(1.0, 100.0), 1),
            "value": round(random.uniform(5.0, 200.0), 1),
            "is_fragile": random.random() < 0.25,
            "eta": float(random.randint(1, 7)),
            "orientation": random.randint(0, 5),
        }
        packages.append(pkg)
    
    trucks = []
    for i in range(num_trucks):
        truck = {
            "id": f"Truck_{i + 1}",
            "w": round(random.uniform(5.0, 15.0), 1),
            "l": round(random.uniform(10.0, 30.0), 1),
            "h": round(random.uniform(3.0, 8.0), 1),
            "max_capacity": round(random.uniform(200.0, 1000.0), 0),
        }
        trucks.append(truck)
    
    data = {"packages": packages, "trucks": trucks}
    feedback = dbc.Alert(
        [html.I(className="fas fa-dice me-2"),
         f"Randomized: {num_packages} packages, {num_trucks} trucks"],
        color="warning", className="py-1 px-2 fs-8 mb-2"
    )
    return data, feedback


# 3. Dynamic Table Generation
@callback(
    [Output("table-1-wrapper", "children"),
     Output("table-2-wrapper", "children")],
    [Input("store-t1-rows", "data"),
     Input("store-t2-rows", "data"),
     Input("store-parsed-file-data", "data"),
     Input("btn-randomize", "n_clicks")]
)
def render_tables(t1_rows, t2_rows, parsed_file, randomize_clicks):
    t1_rows = t1_rows if t1_rows is not None else 5
    t2_rows = t2_rows if t2_rows is not None else 2
    
    packages_data = [p.to_dict() for p in DEFAULT_PACKAGES]
    trucks_data = [t.to_dict() for t in DEFAULT_TRUCKS]
    
    if parsed_file:
        if "packages" in parsed_file:
            packages_data = parsed_file["packages"]
        if "trucks" in parsed_file:
            trucks_data = parsed_file["trucks"]
            
    t1_html = create_package_input_table(t1_rows, packages_data)
    t2_html = create_truck_input_table(t2_rows, trucks_data)
    return t1_html, t2_html


# 4. Dynamic Algorithm Parameters Panel
@callback(
    Output("algo-params-container", "children"),
    Input("config-dropdown-1", "value")
)
def render_algo_params(selected_algo):
    if selected_algo == "hc_steepest":
        return [
            dbc.Alert(
                [html.I(className="fas fa-mountain me-2"), "Steepest Ascent runs independently over all valid successors until local peak (stops iff max f(s') <= f(s))."],
                color="primary", className="py-2 px-2 fs-8 mb-0"
            )
        ]
    elif selected_algo == "hc_sideways":
        return [
            html.Div([
                dbc.Label("Max Sideways Moves", className="fw-bold fs-8 mb-1"),
                dbc.Checkbox(
                    id={"type": "algo-checkbox", "key": "hc_no_max_sideways"},
                    label="No Maximum Sideways Move",
                    value=False,
                    className="fs-8 mb-1"
                ),
                dbc.Input(
                    id={"type": "algo-param", "key": "max_sideways_moves"},
                    type="number",
                    value=500,
                    min=1,
                    max=10000,
                    size="sm",
                    disabled=False
                )
            ])
        ]
    elif selected_algo == "hc_random_restart":
        return [
            dbc.Label("Max Restarts", className="fw-bold fs-8 mb-1"),
            dbc.Input(id={"type": "algo-param", "key": "max_restarts"}, type="number", value=5, min=1, max=50, size="sm"),
            dbc.FormText("Runs independent Steepest Ascent on each restart.", className="fs-9 text-muted")
        ]
    elif selected_algo == "simulated_annealing":
        return [
            dbc.Label("Initial Temp (T0)", className="fw-bold fs-8 mb-1"),
            dbc.Input(id={"type": "algo-param", "key": "initial_temp"}, type="number", value=1000.0, min=10.0, step=50.0, size="sm"),
            dbc.Label("Cooling Rate (alpha)", className="fw-bold fs-8 mt-2 mb-1"),
            dbc.Input(id={"type": "algo-param", "key": "cooling_rate"}, type="number", value=0.95, min=0.5, max=0.999, step=0.01, size="sm"),
            html.Div([
                dbc.Label("Max Iterations", className="fw-bold fs-8 mt-2 mb-1"),
                dbc.Checkbox(
                    id={"type": "algo-checkbox", "key": "sa_no_max_iter"},
                    label="No Max Iterations (run until T <= T_min)",
                    value=False,
                    className="fs-8 mb-1"
                ),
                dbc.Input(
                    id={"type": "algo-param", "key": "max_iterations"},
                    type="number",
                    value=300,
                    min=10,
                    max=10000,
                    size="sm",
                    disabled=False
                )
            ])
        ]
    else:  # Stochastic
        return [
            dbc.Label("Max Iterations", className="fw-bold fs-8 mb-1"),
            dbc.Input(id={"type": "algo-param", "key": "max_iterations"}, type="number", value=100, min=5, max=1000, size="sm")
        ]


@callback(
    Output({"type": "algo-param", "key": "max_iterations"}, "disabled"),
    Input({"type": "algo-checkbox", "key": "sa_no_max_iter"}, "value"),
    prevent_initial_call=True
)
def toggle_sa_max_iter_disabled(checked_val):
    if isinstance(checked_val, list):
        return bool(checked_val and checked_val[0])
    return bool(checked_val)


@callback(
    Output({"type": "algo-param", "key": "max_sideways_moves"}, "disabled"),
    Input({"type": "algo-checkbox", "key": "hc_no_max_sideways"}, "value"),
    prevent_initial_call=True
)
def toggle_hc_sideways_disabled(checked_val):
    if isinstance(checked_val, list):
        return bool(checked_val and checked_val[0])
    return bool(checked_val)


# 5. Mode Switcher Callback
@callback(
    [Output("store-app-mode", "data"),
     Output("btn-mode-input", "color"),
     Output("btn-mode-input", "active"),
     Output("btn-mode-result", "color"),
     Output("btn-mode-result", "active"),
     Output("input-mode-container", "style"),
     Output("result-mode-container", "style"),
     Output("workspace-header-title", "children"),
     Output("top-status-badge", "children"),
     Output("animation-player-footer", "style")],
    [Input("btn-mode-input", "n_clicks"),
     Input("btn-mode-result", "n_clicks"),
     Input("store-app-mode", "data")],
    [State("store-app-mode", "data")]
)
def switch_mode(btn_in, btn_res, mode_store_trigger, current_mode):
    ctx = callback_context
    mode = current_mode or "input"
    
    if ctx.triggered:
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger == "btn-mode-input":
            mode = "input"
        elif trigger == "btn-mode-result":
            mode = "result"
        elif trigger == "store-app-mode":
            mode = mode_store_trigger or "input"
            
    if mode == "input":
        badge = dbc.Badge("Mode: Setup & Input", color="info", className="p-2 fs-7")
        return (
            "input", "primary", True, "secondary", False,
            {"display": "block", "width": "100%"},
            {"display": "none"},
            "Input Tables Mode", badge,
            {"display": "none"}
        )
    else:
        badge = dbc.Badge("Mode: 3D Visualization", color="success", className="p-2 fs-7")
        return (
            "result", "secondary", False, "primary", True,
            {"display": "none"},
            {"display": "flex", "flexDirection": "column", "flexGrow": "1", "width": "100%", "height": "100%", "minHeight": "560px", "justifyContent": "center", "alignItems": "center"},
            "3D Results & Playback", badge,
            {"display": "block"}
        )


# 5b. Toggle Left & Right Panels Callbacks (Middle Controls & Floating Tabs)
@callback(
    Output("store-left-open", "data"),
    [Input("btn-left-close", "n_clicks"),
     Input("btn-center-toggle-left", "n_clicks"),
     Input("btn-floating-open-left", "n_clicks")],
    [State("store-left-open", "data")],
    prevent_initial_call=True
)
def toggle_left_panel(n_close, n_center, n_float, is_open):
    if is_open is None:
        is_open = True
    return not is_open


@callback(
    Output("store-right-open", "data"),
    [Input("btn-right-close", "n_clicks"),
     Input("btn-center-toggle-right", "n_clicks"),
     Input("btn-floating-open-right", "n_clicks"),
     Input("btn-mode-input", "n_clicks")],
    [State("store-right-open", "data")],
    prevent_initial_call=True
)
def toggle_right_panel(n_close, n_center, n_float, n_mode_input, is_open):
    ctx = callback_context
    if ctx.triggered:
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger == "btn-mode-input":
            return False
    if is_open is None:
        is_open = False
    return not is_open


@callback(
    [Output("col-left", "style"),
     Output("col-left", "className"),
     Output("col-right", "style"),
     Output("col-right", "className"),
     Output("col-right", "lg"),
     Output("col-center", "style"),
     Output("col-center", "lg"),
     Output("floating-left-container", "style"),
     Output("floating-right-container", "style"),
     Output("btn-center-toggle-left", "children"),
     Output("btn-center-toggle-left", "className"),
     Output("btn-center-toggle-right", "children"),
     Output("btn-center-toggle-right", "className")],
    [Input("store-left-open", "data"),
     Input("store-right-open", "data"),
     Input("store-app-mode", "data")]
)
def update_panels_layout(left_open, right_open, app_mode):
    left_open = True if left_open is None else left_open
    right_open = True if right_open is None else right_open
    app_mode = app_mode or "input"

    if left_open:
        left_style = {"display": "block"}
        left_class = "mb-3 mb-lg-0 layout-col panel-slider panel-left-open"
        float_l_style = {"display": "none"}
        btn_l_children = [html.I(className="fas fa-sliders-h me-1 text-primary"), "Config"]
        btn_l_class = "middle-toggle-btn"
    else:
        left_style = {"display": "none"}
        left_class = "mb-3 mb-lg-0 layout-col panel-slider panel-left-closed"
        float_l_style = {"display": "block"}
        btn_l_children = [html.I(className="fas fa-chevron-right me-1 text-primary"), "Show Config"]
        btn_l_class = "middle-toggle-btn bg-primary-subtle text-primary border-primary"

    show_right = right_open and (app_mode != "input")

    if show_right:
        right_style = {"display": "block"}
        right_class = "layout-col panel-slider panel-right-open"
        right_lg = 9 if left_open else 12
        center_style = {"display": "none"}
        center_lg = 0
        float_r_style = {"display": "none"}
        btn_r_children = ["Analytics", html.I(className="fas fa-chart-line ms-1 text-primary")]
        btn_r_class = "middle-toggle-btn"
    else:
        right_style = {"display": "none"}
        right_class = "layout-col panel-slider panel-right-closed"
        right_lg = 0
        center_style = {"display": "block"}
        center_lg = 9 if left_open else 12
        float_r_style = {"display": "block"}
        btn_r_children = ["Show Analytics", html.I(className="fas fa-chevron-left ms-1 text-primary")]
        btn_r_class = "middle-toggle-btn bg-primary-subtle text-primary border-primary"

    return (
        left_style, left_class,
        right_style, right_class,
        right_lg,
        center_style,
        center_lg,
        float_l_style, float_r_style,
        btn_l_children, btn_l_class,
        btn_r_children, btn_r_class
    )


# 6a. Start Solver (non-blocking) - launches background thread and returns immediately
@callback(
    [Output("store-solver-job-id", "data"),
     Output("solver-poll-interval", "disabled", allow_duplicate=True),
     Output("solver-poll-interval", "n_intervals", allow_duplicate=True),
     Output("btn-solve", "disabled"),
     Output("btn-solve", "children", allow_duplicate=True)],
    [Input("btn-solve", "n_clicks")],
    [State({"type": "t1-text", "index": ALL}, "value"),
     State({"type": "t1-bool", "index": ALL}, "value"),
     State({"type": "t1-choice", "index": ALL}, "value"),
     State({"type": "t1-float-1", "index": ALL}, "value"),
     State({"type": "t1-float-2", "index": ALL}, "value"),
     State({"type": "t1-float-3", "index": ALL}, "value"),
     State({"type": "t1-float-4", "index": ALL}, "value"),
     State({"type": "t1-float-5", "index": ALL}, "value"),
     State({"type": "t1-float-6", "index": ALL}, "value"),
     State({"type": "t2-float-1", "index": ALL}, "value"),
     State({"type": "t2-float-2", "index": ALL}, "value"),
     State({"type": "t2-float-3", "index": ALL}, "value"),
     State({"type": "t2-float-4", "index": ALL}, "value"),
     State("config-dropdown-1", "value"),
     State("algo-strict-checkbox", "value"),
     State("config-dropdown-2", "value"),
     State({"type": "algo-param", "key": ALL}, "value"),
     State({"type": "algo-param", "key": ALL}, "id"),
     State({"type": "algo-checkbox", "key": ALL}, "value"),
     State({"type": "algo-checkbox", "key": ALL}, "id")],
    prevent_initial_call=True
)
def start_solver_callback(n_clicks,
                        t1_names, t1_bools, t1_oris,
                        t1_w, t1_l, t1_h, t1_wt, t1_val, t1_eta,
                        t2_w, t2_l, t2_h, t2_cap,
                        algo_name, strict_val, objective_type,
                        algo_param_vals, algo_param_ids,
                        algo_checkbox_vals, algo_checkbox_ids):
    if not n_clicks:
        return (no_update,) * 5

    strict = bool(strict_val)

    # 0. Collect algorithm parameters
    params = {}
    if algo_param_vals and algo_param_ids:
        for p_id, p_val in zip(algo_param_ids, algo_param_vals):
            if p_val is not None:
                params[p_id["key"]] = p_val

    if algo_checkbox_vals and algo_checkbox_ids:
        for c_id, c_val in zip(algo_checkbox_ids, algo_checkbox_vals):
            is_checked = bool(c_val[0]) if isinstance(c_val, list) and c_val else bool(c_val)
            if c_id.get("key") == "sa_no_max_iter" and is_checked:
                params["max_iterations"] = -1
            elif c_id.get("key") == "hc_no_max_sideways" and is_checked:
                params["max_sideways_moves"] = -1

    # 1. Parse Packages from Table 1
    packages = []
    num_pkgs = len(t1_names)
    for i in range(num_pkgs):
        pkg_id = t1_names[i] or f"Package_{i+1}"
        pkg = Package(
            id=pkg_id,
            w=float(t1_w[i] or 1.0),
            l=float(t1_l[i] or 1.0),
            h=float(t1_h[i] or 1.0),
            weight=float(t1_wt[i] or 1.0),
            value=float(t1_val[i] or 10.0),
            is_fragile=bool(t1_bools[i]),
            eta=float(t1_eta[i] or 1.0),
            orientation=int(t1_oris[i] or 0)
        )
        packages.append(pkg)

    # 2. Parse Trucks from Table 2
    trucks = []
    num_trucks = len(t2_w)
    for i in range(num_trucks):
        truck = Truck(
            id=f"Truck_{i+1}",
            w=float(t2_w[i] or 10.0),
            l=float(t2_l[i] or 20.0),
            h=float(t2_h[i] or 5.0),
            max_capacity=float(t2_cap[i] or 500.0)
        )
        trucks.append(truck)

    instance_cache = {
        "packages": [p.to_dict() for p in packages],
        "trucks": [t.to_dict() for t in trucks],
        "algo_name": algo_name,
        "objective_type": objective_type,
        "strict": strict
    }

    # 3. Launch solver in a background thread
    job_id = str(uuid.uuid4())
    with _solver_lock:
        _solver_jobs[job_id] = {"status": "running"}

    thread = threading.Thread(
        target=_run_solver_in_thread,
        args=(job_id, algo_name, packages, trucks, strict, objective_type, params, instance_cache),
        daemon=True
    )
    thread.start()

    # 4. Return immediately with loading state
    loading_btn = [
        dbc.Spinner(size="sm", spinner_class_name="me-2"),
        "Solving…"
    ]
    return (job_id, False, 0, True, loading_btn)


# 6b. Poll Solver Completion - checks background thread every 500ms
@callback(
    [Output("store-history", "data"),
     Output("store-instance-cache", "data"),
     Output("store-app-mode", "data", allow_duplicate=True),
     Output("animation-slider", "max"),
     Output("animation-slider", "value"),
     Output("metric-duration", "children"),
     Output("animation-interval", "disabled", allow_duplicate=True),
     Output("animation-interval", "n_intervals", allow_duplicate=True),
     Output("btn-anim-play-pause", "children", allow_duplicate=True),
     Output("btn-anim-play-pause", "color", allow_duplicate=True),
     Output("btn-anim-play-pause", "title", allow_duplicate=True),
     Output("solver-poll-interval", "disabled"),
     Output("btn-solve", "disabled", allow_duplicate=True),
     Output("btn-solve", "children")],
    [Input("solver-poll-interval", "n_intervals")],
    [State("store-solver-job-id", "data")],
    prevent_initial_call=True
)
def poll_solver_callback(n_intervals, job_id):
    if not job_id:
        return (no_update,) * 14

    with _solver_lock:
        job = _solver_jobs.get(job_id)

    if not job or job["status"] == "running":
        # Still running - keep polling, don't update anything else
        return (no_update,) * 14

    # Solver finished - stop polling and restore button
    solve_btn_children = [html.I(className="fas fa-play me-2"), "Solve Optimization"]

    if job["status"] == "error":
        # On error: stop polling, re-enable button, don't change result outputs
        return (no_update, no_update, no_update, no_update, no_update,
                f"Error: {job.get('error', 'Unknown')}", no_update, no_update,
                no_update, no_update, no_update,
                True, False, solve_btn_children)

    # Success - deliver results
    history = job["history"]
    instance_cache = job["instance_cache"]
    duration = job["duration"]
    duration_str = f"{duration:.2f}s"

    max_steps = max(0, len(history) - 1)
    icon_play = html.I(className="fas fa-play")

    return (history, instance_cache, "result", max_steps, max_steps, duration_str,
            True, 0, icon_play, "primary", "Play Animation",
            True, False, solve_btn_children)


# 7. Animation Playback Controls Callback (Single Play/Pause Toggle)
@callback(
    [Output("animation-slider", "value", allow_duplicate=True),
     Output("animation-interval", "disabled"),
     Output("animation-interval", "interval"),
     Output("btn-anim-play-pause", "children"),
     Output("btn-anim-play-pause", "color"),
     Output("btn-anim-play-pause", "title")],
    [Input("btn-anim-first", "n_clicks"),
     Input("btn-anim-prev", "n_clicks"),
     Input("btn-anim-play-pause", "n_clicks"),
     Input("btn-anim-next", "n_clicks"),
     Input("btn-anim-last", "n_clicks"),
     Input("animation-interval", "n_intervals"),
     Input("anim-speed-dropdown", "value")],
    [State("animation-slider", "value"),
     State("animation-slider", "max"),
     State("animation-interval", "disabled")],
    prevent_initial_call=True
)
def manage_animation(btn_first, btn_prev, btn_play_pause, btn_next, btn_last,
                     n_intervals, speed_interval, current_step, max_step, is_disabled):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update, no_update, no_update
        
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    speed = speed_interval or 350
    curr = current_step if current_step is not None else 0
    max_s = max_step if max_step is not None else 0
    
    icon_play = html.I(className="fas fa-play")
    icon_pause = html.I(className="fas fa-pause")
    
    if trigger == "btn-anim-play-pause":
        if is_disabled:
            # Currently paused -> Start playing
            # If at the end, restart from beginning
            new_step = 0 if curr >= max_s else curr
            if max_s <= 0:
                # Nothing to play
                return no_update, no_update, no_update, no_update, no_update, no_update
            return new_step, False, speed, icon_pause, "warning", "Pause Animation"
        else:
            # Currently playing -> Pause
            return no_update, True, speed, icon_play, "primary", "Play Animation"
            
    elif trigger == "btn-anim-first":
        return 0, True, speed, icon_play, "primary", "Play Animation"
    elif trigger == "btn-anim-prev":
        new_val = max(0, curr - 1)
        return new_val, True, speed, icon_play, "primary", "Play Animation"
    elif trigger == "btn-anim-next":
        new_val = min(max_s, curr + 1)
        return new_val, True, speed, icon_play, "primary", "Play Animation"
    elif trigger == "btn-anim-last":
        return max_s, True, speed, icon_play, "primary", "Play Animation"
    elif trigger == "animation-interval":
        if curr >= max_s:
            # Reached end -> Auto pause
            return max_s, True, speed, icon_play, "primary", "Play Animation"
        return curr + 1, no_update, speed, no_update, no_update, no_update
    elif trigger == "anim-speed-dropdown":
        # Only update speed, preserve everything else
        return no_update, no_update, speed, no_update, no_update, no_update
        
    return no_update, no_update, no_update, no_update, no_update, no_update


def extract_camera_from_relayout(relayout_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Safely extract 3D camera state from Plotly relayoutData to prevent camera reset/teleport."""
    if not relayout_data:
        return None
    if "scene.camera" in relayout_data and isinstance(relayout_data["scene.camera"], dict):
        cam = relayout_data["scene.camera"]
        if "center" not in cam:
            cam["center"] = {"x": 0, "y": 0, "z": 0}
        return cam
    if "scene" in relayout_data and isinstance(relayout_data["scene"], dict) and "camera" in relayout_data["scene"]:
        cam = relayout_data["scene"]["camera"]
        if "center" not in cam:
            cam["center"] = {"x": 0, "y": 0, "z": 0}
        return cam
    camera = {}
    for comp in ["eye", "center", "up"]:
        sub = {}
        for axis in ["x", "y", "z"]:
            key = f"scene.camera.{comp}.{axis}"
            if key in relayout_data:
                sub[axis] = relayout_data[key]
        if sub:
            camera[comp] = sub
    if "eye" in camera:
        if "center" not in camera:
            camera["center"] = {"x": 0, "y": 0, "z": 0}
        if "up" not in camera:
            camera["up"] = {"x": 0, "y": 0, "z": 1}
        return camera
    return None


# 8. Render 3D Scene, 2D Analytics, and Summary Metrics
@callback(
    [Output("canvas-3d", "figure"),
     Output("result-2d-graph", "figure"),
     Output("anim-step-badge", "children"),
     Output("metric-best-score", "children"),
     Output("metric-packed-count", "children"),
     Output("metric-total-steps", "children"),
     Output("violations-alert-container", "children"),
     Output("anim-controls-wrapper", "style"),
     Output("anim-no-result-msg", "style")],
    [Input("animation-slider", "value"),
     Input("store-history", "data"),
     Input("graph-view-selector", "value")],
    [State("store-instance-cache", "data"),
     State("canvas-3d", "relayoutData")]
)
def update_visuals(slider_step, history, graph_view, instance_cache, relayout_data):
    if not history or not instance_cache:
        empty_3d = go.Figure(layout=go.Layout(
            uirevision="truck_scene_revision",
            scene=dict(
                uirevision="truck_scene_revision",
                xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            annotations=[{"text": "Configure inputs and click 'Solve Optimization'", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 14, "color": "#64748b"}}]
        ))
        empty_2d = go.Figure(layout=go.Layout(
            title=dict(text="Objective Value vs Iterations", font=dict(size=13)),
            margin=dict(l=40, r=20, t=35, b=35),
            annotations=[{"text": "No data yet", "xref": "paper", "yref": "paper", "showarrow": False}]
        ))
        return empty_3d, empty_2d, "Step: 0 / 0", "0.0", "0 / 0", "0", None, {"display": "none"}, {"display": "block"}
        
    packages = [Package.from_dict(p) for p in instance_cache["packages"]]
    trucks = [Truck.from_dict(t) for t in instance_cache["trucks"]]
    objective_type = instance_cache.get("objective_type", "default")
    
    total_steps = len(history)
    step_idx = min(total_steps - 1, max(0, slider_step or 0))
    current_step_data = history[step_idx]
    
    # 1. Parse current placements
    raw_state = current_step_data.get("state") or current_step_data.get("global_best_state", {})
    placements: Dict[str, Placement] = {}
    for pid, pdata in raw_state.items():
        placements[pid] = Placement.from_dict(pdata)
        
    # Evaluate current state metrics
    current_score, metrics = evaluate_solution(placements, packages, trucks, objective_type)
    
    # 2. Render 3D Figure (Preserve user's current camera angle, pan, and zoom)
    user_camera = extract_camera_from_relayout(relayout_data)
    fig_3d = render_scene_3d(trucks, packages, placements, step_info=current_step_data, camera=user_camera)
    
    # Check if Random Restart summary is available
    rr_step = None
    for h in reversed(history):
        if "restart_iter_count" in h or "random_iter_count" in h:
            rr_step = h
            break

    # 3. Render 2D Figure
    fig_2d = go.Figure()
    iterations = [h.get("iteration", i) for i, h in enumerate(history)]
    scores = [h.get("objective_value", h.get("global_best_value", 0.0)) for h in history]
    
    if graph_view == "algo_metric":
        # Check if SA, GA, or Random Restart data is available
        has_sa = any("acceptance_chance" in h for h in history)
        has_ga = any("pop_max" in h for h in history)
        has_rr = rr_step is not None or any("restart_iter_count" in h or "random_iter_count" in h for h in history)
        
        if has_sa:
            probs = [h.get("acceptance_chance", 0.0) for h in history]
            temps = [h.get("temperature", 0.0) for h in history]
            fig_2d.add_trace(go.Scatter(x=iterations, y=probs, mode="markers", name="P = exp(delta(E)/T)", line=dict(color="#f59e0b", width=2)))
            fig_2d.add_trace(go.Scatter(x=iterations, y=temps, mode="lines", name="Temperature (T)", line=dict(color="#06b6d4", dash="dash"), yaxis="y2"))
            fig_2d.update_layout(
                title=dict(text="SA: exp(delta(E)/T) & Temperature vs Iteration", font=dict(size=12)),
                xaxis=dict(title="Iteration", showgrid=True),
                yaxis=dict(title="P = exp(ΔE/T)", range=[-0.05, 1.05], showgrid=True),
                yaxis2=dict(title="Temperature", overlaying="y", side="right", showgrid=False)
            )
        elif has_ga:
            pop_maxs = [h.get("pop_max", 0.0) for h in history]
            pop_avgs = [h.get("pop_avg", 0.0) for h in history]
            fig_2d.add_trace(go.Scatter(x=iterations, y=pop_maxs, mode="lines", name="Max Fitness", line=dict(color="#10b981", width=2)))
            fig_2d.add_trace(go.Scatter(x=iterations, y=pop_avgs, mode="lines", name="Avg Fitness", line=dict(color="#3b82f6", dash="dot")))
            fig_2d.update_layout(title=dict(text="GA: Population Fitness vs Generation", font=dict(size=12)), yaxis_title="Fitness")
        elif has_rr:
            iter_counts = (rr_step.get("restart_iter_count") or rr_step.get("random_iter_count", [])) if rr_step else []
            x_labels = [f"Restart {i+1}" for i in range(len(iter_counts))]
            fig_2d.add_trace(go.Bar(
                x=x_labels,
                y=iter_counts,
                name="Iterations (random_iter_count)",
                marker_color="#2563eb",
                text=iter_counts,
                textposition="auto"
            ))
            fig_2d.update_layout(
                title=dict(text="Random Restart: Iterations per Restart (random_iter_count)", font=dict(size=12)),
                xaxis=dict(title="Restart Run", showgrid=True),
                yaxis=dict(title="Iterations Taken", showgrid=True)
            )
        else:
            fig_2d.add_trace(go.Scatter(x=iterations, y=scores, mode="lines+markers", name="Score", line=dict(color="#2563eb")))
            fig_2d.update_layout(title=dict(text="Objective Value vs Iteration", font=dict(size=12)))

    elif graph_view == "truck_breakdown":
        truck_names = [f"Truck {i+1}" for i in range(len(trucks))]
        used_wts = [metrics["truck_weights"].get(i, 0.0) for i in range(len(trucks))]
        max_caps = [t.max_capacity for t in trucks]
        
        fig_2d.add_trace(go.Bar(x=truck_names, y=used_wts, name="Used Weight (kg)", marker_color="#0284c7"))
        fig_2d.add_trace(go.Bar(x=truck_names, y=max_caps, name="Max Capacity (kg)", marker_color="#94a3b8", opacity=0.4))
        fig_2d.update_layout(barmode="group", title=dict(text="Fleet Capacity Breakdown", font=dict(size=12)), yaxis_title="Weight (kg)")

    else:
        # Default objective curve
        fig_2d.add_trace(go.Scatter(x=iterations, y=scores, mode="lines+markers", name="Objective Score", line=dict(color="#2563eb", width=2.5)))
        # Vertical marker at current step
        curr_it = iterations[step_idx]
        fig_2d.add_vline(x=curr_it, line_width=2, line_dash="dash", line_color="#ef4444")
        fig_2d.update_layout(
            title=dict(text=f"Objective vs Iteration (Step {step_idx}: {current_score:.1f})", font=dict(size=12)),
            xaxis=dict(title="Iteration", showgrid=True),
            yaxis=dict(title="Objective Score", showgrid=True)
        )
        
    fig_2d.update_layout(margin=dict(l=40, r=20, t=35, b=35), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    # 4. Summary Text & Badges
    if current_step_data.get("finished"):
        step_badge = f"{current_step_data.get('finished')} | Score: {current_score:.1f}"
    elif "restart_id" in current_step_data:
        step_badge = f"Restart #{current_step_data.get('restart_id') + 1} | Step: {step_idx} / {total_steps - 1} | Score: {current_score:.1f}"
    else:
        step_badge = f"Step: {step_idx} / {total_steps - 1} | Score: {current_score:.1f}"

    if rr_step and rr_step.get("global_best_value") is not None:
        best_score_str = f"{rr_step.get('global_best_value'):.1f}"
    else:
        best_score_str = f"{max(scores):.1f}"

    packed_str = f"{metrics['packed_count']} / {len(packages)}"
    total_steps_str = str(total_steps - 1)
    
    alerts = []
    if not metrics["is_valid"] and metrics["violations"]:
        alerts.append(dbc.Alert(
            [html.I(className="fas fa-exclamation-triangle me-2"), f"{len(metrics['violations'])} Constraint Violations in current state"],
            color="danger", className="py-1 px-2 fs-8 mb-1"
        ))
    if any("acceptance_chance" in h for h in history):
        stuck_count = sum(1 for h in history if h.get("is_stuck", False))
        stuck_pct = (stuck_count / max(1, total_steps - 1)) * 100
        alerts.append(dbc.Alert(
            [html.I(className="fas fa-temperature-low me-2"), f"SA Stuck in Local Optima: {stuck_count} / {total_steps - 1} times ({stuck_pct:.1f}%)"],
            color="warning" if stuck_count > 0 else "info", className="py-1 px-2 fs-8 mb-1"
        ))
    if rr_step:
        iter_counts = rr_step.get("restart_iter_count") or rr_step.get("random_iter_count", [])
        total_rr_iters = sum(iter_counts)
        avg_rr_iters = total_rr_iters / max(1, len(iter_counts)) if iter_counts else 0
        counts_str = ", ".join(f"R{i+1}: {c}" for i, c in enumerate(iter_counts))
        finished_msg = rr_step.get("finished", "Finished Random Restart")
        global_best = rr_step.get("global_best_value")
        alerts.append(dbc.Alert([
            html.Div([
                html.I(className="fas fa-redo me-2 text-primary"),
                html.Strong(f"{finished_msg} | Total Restarts: {len(iter_counts)}"),
            ], className="fw-semibold mb-1"),
            html.Div([
                html.Span("Iterations per restart (random_iter_count): ", className="fw-bold me-1 text-secondary"),
                html.Span(f"[{counts_str}]", className="font-monospace fw-bold text-primary")
            ], className="fs-8"),
            html.Div([
                html.Span(f"Total Iterations: {total_rr_iters} | Average: {avg_rr_iters:.1f} iters/restart", className="text-muted me-2"),
                html.Span(f"Global Best Score: {global_best:.1f}" if global_best is not None else "", className="fw-bold text-success")
            ], className="fs-8 mt-1")
        ], color="info", className="py-2 px-3 fs-8 mb-2 border-info shadow-xs"))
    violations_alert = html.Div(alerts) if alerts else None
        
    return fig_3d, fig_2d, step_badge, best_score_str, packed_str, total_steps_str, violations_alert, {"display": "block"}, {"display": "none"}


# 9. Export Configuration JSON
@callback(
    Output("download-json", "data"),
    Input("btn-export-json", "n_clicks"),
    [State("export-filename-input", "value"),
     State({"type": "t1-text", "index": ALL}, "value"),
     State({"type": "t1-bool", "index": ALL}, "value"),
     State({"type": "t1-choice", "index": ALL}, "value"),
     State({"type": "t1-float-1", "index": ALL}, "value"),
     State({"type": "t1-float-2", "index": ALL}, "value"),
     State({"type": "t1-float-3", "index": ALL}, "value"),
     State({"type": "t1-float-4", "index": ALL}, "value"),
     State({"type": "t1-float-5", "index": ALL}, "value"),
     State({"type": "t1-float-6", "index": ALL}, "value"),
     State({"type": "t2-float-1", "index": ALL}, "value"),
     State({"type": "t2-float-2", "index": ALL}, "value"),
     State({"type": "t2-float-3", "index": ALL}, "value"),
     State({"type": "t2-float-4", "index": ALL}, "value")],
    prevent_initial_call=True
)
def export_json(n_clicks, filename_val, t1_names, t1_bools, t1_oris, t1_w, t1_l, t1_h, t1_wt, t1_val, t1_eta, t2_w, t2_l, t2_h, t2_cap):
    if not n_clicks:
        return no_update
        
    packages = []
    for i in range(len(t1_names)):
        packages.append({
            "id": t1_names[i] or f"Package_{i+1}",
            "dimensions": {"w": float(t1_w[i] or 1.0), "l": float(t1_l[i] or 1.0), "h": float(t1_h[i] or 1.0)},
            "weight": float(t1_wt[i] or 1.0),
            "value": float(t1_val[i] or 10.0),
            "is_fragile": bool(t1_bools[i]),
            "eta": float(t1_eta[i] or 1.0),
            "orientation": int(t1_oris[i] or 0)
        })
        
    trucks = []
    for i in range(len(t2_w)):
        trucks.append({
            "id": f"Truck_{i+1}",
            "dimensions": {"w": float(t2_w[i] or 10.0), "l": float(t2_l[i] or 20.0), "h": float(t2_h[i] or 5.0)},
            "max_capacity": float(t2_cap[i] or 500.0)
        })
        
    filename = (filename_val or "bin_packing_instance.json").strip()
    if not filename:
        filename = "bin_packing_instance.json"
    if not filename.endswith(".json"):
        filename += ".json"

    data = {"trucks": trucks, "packages": packages}
    return dict(content=json.dumps(data, indent=2), filename=filename)