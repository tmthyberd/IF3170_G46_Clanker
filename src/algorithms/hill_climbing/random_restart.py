from __future__ import annotations
import time
from typing import Callable, Dict, List
from src.core.models import Package, State, Truck
from src.core.objective import calculate_objective
from src.core.moves import generate_initial_state
from src.algorithms.hill_climbing.base import HillClimbingResult
from src.algorithms.hill_climbing.steepest_ascent import steepest_ascent_hill_climbing


def random_restart_hill_climbing(
    truck: Truck,
    packages: Dict[str, Package],
    max_restarts: int = 5,
    max_iterations_per_restart: int = 200,
    sample_neighbors: int = 30,
    objective_fn: Callable[[State], float] = calculate_objective,
) -> HillClimbingResult:
    """Random Restart Hill-Climbing: menjalankan Steepest Ascent berulang kali dari state acak baru"""
    start_time = time.perf_counter()
    first_state = generate_initial_state(truck, packages, random_strategy="valid_floor")
    best_state = first_state
    best_val = objective_fn(best_state)

    combined_history: List[float] = [best_val]
    iters_per_restart: List[int] = []

    for r in range(max_restarts):
        init_state = first_state if r == 0 else generate_initial_state(truck, packages, random_strategy="valid_floor")
        run = steepest_ascent_hill_climbing(
            initial_state=init_state,
            max_iterations=max_iterations_per_restart,
            sample_neighbors=sample_neighbors,
            objective_fn=objective_fn,
        )
        iters_per_restart.append(run.total_iterations)
        combined_history.extend(run.objective_history[1:])

        if run.final_objective > best_val:
            best_val = run.final_objective
            best_state = run.final_state

    total_iters = sum(iters_per_restart)
    return HillClimbingResult(
        algorithm_name="Random Restart Hill-Climbing",
        initial_state=first_state,
        final_state=best_state,
        initial_objective=combined_history[0],
        final_objective=best_val,
        duration_seconds=time.perf_counter() - start_time,
        total_iterations=total_iters,
        objective_history=combined_history,
        extra_metrics={
            "max_restarts": max_restarts,
            "restarts_completed": max_restarts,
            "iterations_per_restart": iters_per_restart,
            "avg_iterations_per_restart": total_iters / max(1, max_restarts),
        },
    )
