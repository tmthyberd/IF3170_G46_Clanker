from __future__ import annotations
from dataclasses import dataclass, field
import math
import random
import time
from typing import Dict, Generator, Any

from src.core.models import SolverState
from src.core.objective import calculate_objective
from src.core.moves import get_random_successor


MINIMAL_TEMPERATURE = 1e-4
DEFAULT_INITIAL_TEMP = 1000
DEFAULT_COOLING_RATE = 0.95



def simulated_annealing(
    initial_state: SolverState,
    initial_temp: float = DEFAULT_INITIAL_TEMP,
    cooling_rate: float = DEFAULT_COOLING_RATE,
    max_iterations: int = -1,
    strict: bool = False,
    objective_type: str = "default"
) -> Generator[Dict[str, Any], None, None]:

    start_time = time.perf_counter()
    current_state = initial_state.clone()
    current_val = calculate_objective(current_state, strict=strict, objective_type=objective_type)

    yield {
        "iteration": 0,
        "objective_value": current_val,
        "state": {k: v.to_dict() for k, v in current_state.placements.items()},
        "duration": time.perf_counter() - start_time,
        "temperature": float(initial_temp),
        "delta_e": 0.0,
        "acceptance_chance": 1.0,
        "is_stuck": 0,
        "message": f"Initial state (Score: {current_val:.1f})"
    }

    best_state = current_state.clone()
    best_val = current_val

    temp = float(initial_temp)
    stuck_count = 0
    iteration = 0

    while (max_iterations == -1 or iteration < max_iterations) and temp > MINIMAL_TEMPERATURE:
        iteration += 1
        neighbor = get_random_successor(current_state, valid_only=True)
        neighbor_val = calculate_objective(neighbor, strict=strict, objective_type=objective_type)
        delta_e = neighbor_val - current_val

        if delta_e > 0:
            prob = 1.0
            accepted = True
        else:
            prob = math.exp(delta_e / max(MINIMAL_TEMPERATURE, temp))
            accepted = random.random() < prob

        if accepted:
            current_state = neighbor
            current_val = neighbor_val
            if current_val > best_val:
                best_val = current_val
                best_state = current_state.clone()
        else:
            stuck_count += 1

        temp *= cooling_rate

        yield {
            "iteration": iteration,
            "objective_value": current_val,
            "duration": time.perf_counter() - start_time,
            "state": {k: v.to_dict() for k, v in current_state.placements.items()},
            "temperature": temp,
            "delta_e": delta_e,
            "acceptance_chance": prob,
            "is_stuck": int(not accepted),
            "message": f"Simulated Annealing Step {iteration}: Temperature={temp:.1f}, Probability={prob:.3f}, Score={current_val:.1f}"
        }

