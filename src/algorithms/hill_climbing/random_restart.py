from __future__ import annotations
import time
from typing import Dict, List, Generator, Any

from src.core.models import Package, SolverState, Truck

from src.core.objective import calculate_objective
from src.core.moves import generate_initial_state, get_all_successors

from src.algorithms.hill_climbing.steepest_ascent import steepest_ascent_hill_climbing


DEFAULT_MAX_RESTART = 25


def random_restart_hill_climbing(
    trucks: List[Truck],
    packages: List[Package],
    max_restarts: int = DEFAULT_MAX_RESTART,
    strict: bool = False,
    objective_type: str = "default"
) -> Generator[Dict[str, Any], None, None]:

    start_time = time.perf_counter()

    global_idx = 0
    global_best_val = float('-inf')
    global_best_state = None

    iter_count = []

    for restart_id in range(max_restarts):
        current_state = generate_initial_state(trucks, packages, randomize=True)
        current_val = calculate_objective(current_state, objective_type=objective_type, strict=strict)

        if current_val > global_best_val:
            global_best_val = current_val
            global_best_state = current_state.clone()

        yield {
            "restart_id": restart_id,
            "iteration": global_idx,
            "objective_value": current_val,
            "state": {k: v.to_dict() for k, v in current_state.placements.items()},
            "duration": 0.0,
            "message": f"Restart {restart_id}: Initial state (Score: {current_val:.1f})"
        }
        global_idx += 1


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

            if current_val > global_best_val:
                global_best_val = current_val
                global_best_state = current_state.clone()

            yield {
                "restart_id": restart_id,
                "iteration": global_idx,
                "objective_value": current_val,
                "state": {k: v.to_dict() for k, v in current_state.placements.items()},
                "duration": time.perf_counter() - start_time,
                "message": f"Restart {restart_id}: Step {iteration}: Steepest ascent to best neighbor ({current_val:.1f})",
            }
            global_idx += 1
        
        iter_count.append(iteration)

    print(iter_count)
    yield {
        "restart_iter_count": iter_count,
        "global_best_value": global_best_val,
        "global_best_state": {k: v.to_dict() for k, v in global_best_state.placements.items()},
        "finished": f"Finished {max_restarts} random restart process"
    }
