from __future__ import annotations
import random
import time
from typing import Callable
from src.core.models import SolverState
from src.core.objective import calculate_objective
from src.core.moves import get_random_successor

DEFAULT_STOCHASTIC_MAX_ITERATION = 50


def stochastic_hill_climbing(
    initial_state: SolverState,
    max_iterations: int = DEFAULT_STOCHASTIC_MAX_ITERATION,
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
    while iteration < max_iterations:
        iteration += 1
        
        successor = get_random_successor(current_state, valid_only=True)
        score = calculate_objective(successor, objective_type=objective_type, strict=strict)
        if score > current_val:
            current_val = score
            current_state = successor

        yield {
            "iteration": iteration,
            "objective_value": current_val,
            "state": {k: v.to_dict() for k, v in current_state.placements.items()},
            "duration": time.perf_counter() - start_time,
            "message": f"Step {iteration}: Stochastic transition result to best neighbor ({current_val:.1f})",
        }
