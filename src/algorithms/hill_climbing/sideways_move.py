from __future__ import annotations
import random
import time
from typing import Callable
from src.core.models import State
from src.core.objective import calculate_objective
from src.core.moves import generate_neighbors
from src.algorithms.hill_climbing.base import HillClimbingResult


def sideways_hill_climbing(
    initial_state: State,
    max_sideways_moves: int = 50,
    max_iterations: int = 500,
    sample_neighbors: int = 40,
    objective_fn: Callable[[State], float] = calculate_objective,
) -> HillClimbingResult:
    """Hill-Climbing dengan Sideways Move (jika max_sideways_moves=0 menjadi Steepest Ascent)"""
    start_time = time.perf_counter()
    current_state = initial_state.clone()
    current_val = objective_fn(current_state)

    history = [current_val]
    iteration = 0
    consecutive_sideways = 0
    total_sideways = 0

    while iteration < max_iterations:
        iteration += 1
        neighbors = generate_neighbors(current_state, sample_size=sample_neighbors, valid_only=True)
        if not neighbors:
            break

        scored = [(objective_fn(n), n) for n in neighbors]
        best_val = max(val for val, _ in scored)
        best_neighbors = [n for val, n in scored if val == best_val]

        if best_val > current_val:
            current_state = random.choice(best_neighbors)
            current_val = best_val
            consecutive_sideways = 0
            history.append(current_val)
        elif best_val == current_val and consecutive_sideways < max_sideways_moves:
            consecutive_sideways += 1
            total_sideways += 1
            current_state = random.choice(best_neighbors)
            history.append(current_val)
        else:
            break

    return HillClimbingResult(
        algorithm_name="Hill-Climbing with Sideways Move",
        initial_state=initial_state,
        final_state=current_state,
        initial_objective=history[0],
        final_objective=current_val,
        duration_seconds=time.perf_counter() - start_time,
        total_iterations=iteration,
        objective_history=history,
        extra_metrics={
            "iterations_to_stop": iteration,
            "max_sideways_moves_limit": max_sideways_moves,
            "total_sideways_moves_taken": total_sideways,
        },
    )
