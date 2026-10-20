from __future__ import annotations
import random
import time
from typing import Callable, Generator, Any
from src.core.models import SolverState
from src.core.objective import calculate_objective
from src.core.moves import get_all_successors


def steepest_ascent_hill_climbing(
    initial_state: SolverState,
    strict: bool = False,
    objective_type: str = "default"
) -> Generator[Dict[str, Any], None, None]:

    start_time = time.perf_counter()
    current_state = initial_state.clone()
    current_val = calculate_objective(current_state, objective_type=objective_type, strict=strict)

    yield {
        "iteration": 0,
        "objective_value": current_val,
        "state": {k: v.to_dict() for k, v in initial_state.placements.items()},
        "duration": 0.0,
        "message": f"Initial state (Score: {current_val:.1f})",
    }


    iteration = 0
    while True:
        iteration += 1
        
        best_successor_val = float('-inf')
        neighbor = None
        for successor in get_all_successors(current_state, valid_only=True):
            score = calculate_objective(successor, objective_type=objective_type, strict=strict)
            if best_successor_val < score:
                best_successor_val = score
                neighbor = successor

        if neighbor is None or best_successor_val <= current_val:
            break
        
        current_val = best_successor_val
        current_state = neighbor

        yield {
            "iteration": iteration,
            "objective_value": current_val,
            "state": {k: v.to_dict() for k, v in current_state.placements.items()},
            "duration": time.perf_counter() - start_time,
            "message": f"Step {iteration}: Steepest ascent to best neighbor ({current_val:.1f})",
        }
