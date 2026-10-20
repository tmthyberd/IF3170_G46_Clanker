from __future__ import annotations
import random
import time
from typing import Callable, Set, Tuple, Generator, Any, Dict
from src.core.models import SolverState
from src.core.objective import calculate_objective
from src.core.moves import get_all_successors


DEFAULT_MAX_SIDEWAYS_MOVE = 500


def sideways_hill_climbing(
    initial_state: SolverState,
    max_sideways_moves: int = DEFAULT_MAX_SIDEWAYS_MOVE,
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
        "sideways_count": 0,
        "message": f"Initial state (Score: {current_val:.1f})",
    }

    tracker: Set[Tuple] = set()
    tracker.add(current_state.signature)

    iteration = 0
    total_sideways = 0
    while True:
        iteration += 1
        
        best_successor_val = float('-inf')
        neighbor = None
        for successor in get_all_successors(current_state, valid_only=True):
            if successor.signature in tracker:
                continue

            score = calculate_objective(successor, objective_type=objective_type, strict=strict)
            if best_successor_val < score:
                best_successor_val = score
                neighbor = successor

        if neighbor is None or best_successor_val < current_val:
            break

        if best_successor_val == current_val:
            total_sideways += 1
            if total_sideways > max_sideways_moves:
                break
        
        current_val = best_successor_val
        current_state = neighbor
        tracker.add(current_state.signature)

        yield {
            "iteration": iteration,
            "objective_value": current_val,
            "state": {k: v.to_dict() for k, v in current_state.placements.items()},
            "duration": time.perf_counter() - start_time,
            "sideways_count": total_sideways,
            "message": f"Step {iteration}: Sideways move to best neighbor ({current_val:.1f})",
        }

