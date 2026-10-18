from __future__ import annotations
import random
import time
from typing import Callable
from src.core.models import State
from src.core.objective import calculate_objective
from src.core.moves import generate_neighbors
from src.algorithms.hill_climbing.base import HillClimbingResult


def stochastic_hill_climbing(
    initial_state: State,
    max_iterations: int = 500,
    sample_neighbors: int = 40,
    objective_fn: Callable[[State], float] = calculate_objective,
) -> HillClimbingResult:
    """Stochastic Hill-Climbing: memilih secara acak dari daftar neighbor yang lebih baik"""
    start_time = time.perf_counter()
    current_state = initial_state.clone()
    current_val = objective_fn(current_state)

    history = [current_val]
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        neighbors = generate_neighbors(current_state, sample_size=sample_neighbors, valid_only=True)
        improving = [(n, val, val - current_val) for n in neighbors if (val := objective_fn(n)) > current_val]
        if not improving:
            break

        # Pilih salah satu langkah menanjak secara acak terbobot berdasarkan nilai delta
        weights = [delta for _, _, delta in improving]
        current_state, current_val, _ = random.choices(improving, weights=weights, k=1)[0]
        history.append(current_val)

    return HillClimbingResult(
        algorithm_name="Stochastic Hill-Climbing",
        initial_state=initial_state,
        final_state=current_state,
        initial_objective=history[0],
        final_objective=current_val,
        duration_seconds=time.perf_counter() - start_time,
        total_iterations=iteration,
        objective_history=history,
        extra_metrics={"iterations_to_stop": iteration},
    )
