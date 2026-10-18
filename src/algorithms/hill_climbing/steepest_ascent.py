from __future__ import annotations
from typing import Callable
from src.core.models import State
from src.core.objective import calculate_objective
from src.algorithms.hill_climbing.base import HillClimbingResult
from src.algorithms.hill_climbing.sideways_move import sideways_hill_climbing


def steepest_ascent_hill_climbing(
    initial_state: State,
    max_iterations: int = 500,
    sample_neighbors: int = 40,
    objective_fn: Callable[[State], float] = calculate_objective,
) -> HillClimbingResult:
    """Steepest Ascent Hill-Climbing (sama dengan Sideways Move saat max_sideways_moves=0)"""
    res = sideways_hill_climbing(
        initial_state=initial_state,
        max_sideways_moves=0,
        max_iterations=max_iterations,
        sample_neighbors=sample_neighbors,
        objective_fn=objective_fn,
    )
    res.algorithm_name = "Steepest Ascent Hill-Climbing"
    res.extra_metrics = {"iterations_to_stop": res.total_iterations}
    return res
