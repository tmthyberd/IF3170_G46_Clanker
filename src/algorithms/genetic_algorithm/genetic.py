from __future__ import annotations
import random
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Union
from src.core.models import Package, Placement, SolverState, Truck
from src.core.objective import calculate_objective
from src.core.validator import validate_state
from src.core.moves import generate_initial_state
from src.algorithms.genetic_algorithm.individual import Individual
from src.algorithms.genetic_algorithm.operators import (
    mutate_individual,
    roulette_wheel_selection,
    tournament_selection,
    two_point_crossover,
    uniform_crossover,
)

DEFAULT_GA_POPULATION_SIZE = 50
DEFAULT_GA_MAX_GENERATIONS = 100


def genetic_algorithm(
    initial_state: Optional[SolverState] = None,
    population_size: int = 50,
    max_generations: int = 100,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.2,
    tournament_size: int = 3,
    elitism_count: int = 2,
    selection_method: str = "tournament",
    crossover_method: str = "uniform",
    strict: bool = False,
    objective_type: str = "default",
    seed: Optional[int] = None,
    truck: Optional[Any] = None,
    trucks: Optional[Any] = None,
    packages: Optional[Any] = None,
    verbose: bool = False,
    **kwargs: Any,
) -> Generator[Dict[str, Any], None, None]:
    """
    Eksekusi Genetic Algorithm untuk optimasi penataan 3D Container Loading.
    Menghasilkan generator dictionary per generasi yang mencakup nilai objektif terbaik,
    fitness rata-rata populasi, durasi keseluruhan, dan state penempatan paket.
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)

    if initial_state is not None:
        target_trucks = initial_state.trucks
        target_packages = initial_state.packages
    else:
        target_trucks = trucks if trucks is not None else (truck if truck is not None else [Truck()])
        target_packages = packages if packages is not None else {}
        initial_state = generate_initial_state(target_trucks, target_packages)

    population: List[Individual] = []
    if initial_state is not None:
        init_ind = Individual(state=initial_state.clone())
        init_ind.evaluate(objective_type=objective_type, strict=strict)
        population.append(init_ind)

    while len(population) < population_size:
        ind = Individual.create_random(
            trucks=target_trucks,
            packages=target_packages,
            objective_type=objective_type,
            strict=strict,
            rng=rng,
        )
        population.append(ind)

    population.sort(key=lambda x: x.fitness, reverse=True)
    best_ind = population[0]
    current_best = best_ind.fitness
    current_avg = sum(x.fitness for x in population) / len(population)

    # Initial state yield (Generasi 0)
    yield {
        "iteration": 0,
        "objective_value": current_best,
        "pop_max": current_best,
        "pop_avg": current_avg,
        "state": {k: v.to_dict() for k, v in best_ind.state.placements.items()},
        "duration": 0.0,
        "message": f"Gen 0: Initial Population Best={current_best:.1f}, Avg={current_avg:.1f}",
    }

    select_fn = (
        (lambda pop: tournament_selection(pop, tournament_size=tournament_size, rng=rng))
        if selection_method == "tournament"
        else (lambda pop: roulette_wheel_selection(pop, rng=rng))
    )

    cross_fn = (
        (lambda p1, p2: uniform_crossover(p1, p2, objective_type=objective_type, strict=strict, rng=rng))
        if crossover_method == "uniform"
        else (lambda p1, p2: two_point_crossover(p1, p2, objective_type=objective_type, strict=strict, rng=rng))
    )

    for gen in range(1, max_generations + 1):
        population.sort(key=lambda x: x.fitness, reverse=True)

        next_gen: List[Individual] = [
            population[i].clone() for i in range(min(elitism_count, len(population)))
        ]

        while len(next_gen) < population_size:
            p1 = select_fn(population)
            p2 = select_fn(population)

            if rng.random() < crossover_rate:
                c1, c2 = cross_fn(p1, p2)
            else:
                c1, c2 = p1.clone(), p2.clone()

            if rng.random() < mutation_rate:
                c1 = mutate_individual(c1, truck=c1.state.trucks[0] if c1.state.trucks else None, objective_type=objective_type, strict=strict, rng=rng)
            else:
                c1.evaluate(objective_type=objective_type, strict=strict)

            if rng.random() < mutation_rate:
                c2 = mutate_individual(c2, truck=c2.state.trucks[0] if c2.state.trucks else None, objective_type=objective_type, strict=strict, rng=rng)
            else:
                c2.evaluate(objective_type=objective_type, strict=strict)

            next_gen.append(c1)
            if len(next_gen) < population_size:
                next_gen.append(c2)

        population = next_gen
        population.sort(key=lambda x: x.fitness, reverse=True)

        best_ind = population[0]
        current_best = best_ind.fitness
        current_avg = sum(x.fitness for x in population) / len(population)
        elapsed = time.perf_counter() - start_time

        if verbose and (gen % 10 == 0 or gen == max_generations):
            print(f"Gen {gen:4d} | Best Fitness: {current_best:8.2f} | Avg Fitness: {current_avg:8.2f}")

        yield {
            "iteration": gen,
            "objective_value": current_best,
            "pop_max": current_best,
            "pop_avg": current_avg,
            "state": {k: v.to_dict() for k, v in best_ind.state.placements.items()},
            "duration": elapsed,
            "message": f"Gen {gen}: Best={current_best:.1f}, Avg={current_avg:.1f}",
        }
