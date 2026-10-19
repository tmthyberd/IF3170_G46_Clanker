from __future__ import annotations
import random
import time
from typing import Any, Callable, Dict, List, Optional
from src.core.interfaces import AlgorithmResult, BaseAlgorithm
from src.core.models import Package, State, Truck
from src.core.objective import calculate_objective
from src.core.validator import is_valid_state
from src.algorithms.genetic_algorithm.individual import Individual
from src.algorithms.genetic_algorithm.operators import (
    mutate_individual,
    roulette_wheel_selection,
    tournament_selection,
    two_point_crossover,
    uniform_crossover,
)


def genetic_algorithm(
    truck: Truck,
    packages: Dict[str, Package],
    population_size: int = 50,
    max_generations: int = 100,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.2,
    tournament_size: int = 3,
    elitism_count: int = 2,
    selection_method: str = "tournament",
    crossover_method: str = "uniform",
    objective_func: Callable[[State], float] = calculate_objective,
    initial_state: Optional[State] = None,
    seed: Optional[int] = None,
    verbose: bool = False,
) -> AlgorithmResult:
    """
    Eksekusi Genetic Algorithm untuk optimasi penataan 3D Container Loading.
    Mendukung tracking nilai objektif maksimum dan rata-rata per generasi.
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)

    population: List[Individual] = []
    if initial_state is not None:
        init_ind = Individual(state=initial_state.clone())
        init_ind.evaluate(objective_func)
        population.append(init_ind)

    while len(population) < population_size:
        ind = Individual.create_random(truck, packages, strategy="valid_floor", rng=rng)
        ind.evaluate(objective_func)
        population.append(ind)

    population.sort(key=lambda x: x.fitness, reverse=True)
    init_best_ind = population[0].clone()
    init_best_fitness = init_best_ind.fitness

    best_history: List[float] = []
    avg_history: List[float] = []

    select_fn = (
        (lambda pop: tournament_selection(pop, tournament_size=tournament_size, rng=rng))
        if selection_method == "tournament"
        else (lambda pop: roulette_wheel_selection(pop, rng=rng))
    )

    cross_fn = (
        (lambda p1, p2: uniform_crossover(p1, p2, rng=rng))
        if crossover_method == "uniform"
        else (lambda p1, p2: two_point_crossover(p1, p2, rng=rng))
    )

    for gen in range(max_generations):
        population.sort(key=lambda x: x.fitness, reverse=True)

        current_best = population[0].fitness
        current_avg = sum(x.fitness for x in population) / len(population)

        best_history.append(current_best)
        avg_history.append(current_avg)

        if verbose and (gen % 10 == 0 or gen == max_generations - 1):
            print(f"Gen {gen:4d} | Best Fitness: {current_best:8.2f} | Avg Fitness: {current_avg:8.2f}")

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
                c1 = mutate_individual(c1, truck, rng=rng)
            else:
                c1.evaluate(objective_func)

            if rng.random() < mutation_rate:
                c2 = mutate_individual(c2, truck, rng=rng)
            else:
                c2.evaluate(objective_func)

            next_gen.append(c1)
            if len(next_gen) < population_size:
                next_gen.append(c2)

        population = next_gen

    population.sort(key=lambda x: x.fitness, reverse=True)
    best_final = population[0].clone()
    elapsed = time.perf_counter() - start_time

    is_valid, violations = is_valid_state(best_final.state)

    extra_metrics: Dict[str, Any] = {
        "avg_fitness_history": avg_history,
        "population_size": population_size,
        "max_generations": max_generations,
        "crossover_rate": crossover_rate,
        "mutation_rate": mutation_rate,
        "tournament_size": tournament_size,
        "elitism_count": elitism_count,
        "selection_method": selection_method,
        "crossover_method": crossover_method,
        "final_is_valid": is_valid,
        "final_violations": violations,
        "final_placed_count": len(best_final.state.packages_in_truck),
        "final_total_weight": best_final.state.total_weight_in_truck,
        "final_total_value": best_final.state.total_value_in_truck,
    }

    return AlgorithmResult(
        algorithm_name="Genetic Algorithm",
        initial_state=init_best_ind.state,
        final_state=best_final.state,
        initial_objective=init_best_fitness,
        final_objective=best_final.fitness,
        duration_seconds=elapsed,
        total_iterations=max_generations,
        objective_history=best_history,
        extra_metrics=extra_metrics,
    )


class GeneticAlgorithm(BaseAlgorithm):
    """Implementasi BaseAlgorithm untuk Genetic Algorithm"""

    def __init__(
        self,
        population_size: int = 50,
        max_generations: int = 100,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.2,
        tournament_size: int = 3,
        elitism_count: int = 2,
        selection_method: str = "tournament",
        crossover_method: str = "uniform",
        seed: Optional[int] = None,
    ):
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elitism_count = elitism_count
        self.selection_method = selection_method
        self.crossover_method = crossover_method
        self.seed = seed

    @property
    def name(self) -> str:
        return "Genetic Algorithm"

    def run(self, initial_state: State, **kwargs: Any) -> AlgorithmResult:
        pop_size = kwargs.get("population_size", self.population_size)
        max_gen = kwargs.get("max_generations", kwargs.get("max_iterations", self.max_generations))
        cx_rate = kwargs.get("crossover_rate", self.crossover_rate)
        mut_rate = kwargs.get("mutation_rate", self.mutation_rate)
        t_size = kwargs.get("tournament_size", self.tournament_size)
        elites = kwargs.get("elitism_count", self.elitism_count)
        sel_method = kwargs.get("selection_method", self.selection_method)
        cx_method = kwargs.get("crossover_method", self.crossover_method)
        seed = kwargs.get("seed", self.seed)

        return genetic_algorithm(
            truck=initial_state.truck,
            packages=initial_state.packages,
            population_size=pop_size,
            max_generations=max_gen,
            crossover_rate=cx_rate,
            mutation_rate=mut_rate,
            tournament_size=t_size,
            elitism_count=elites,
            selection_method=sel_method,
            crossover_method=cx_method,
            initial_state=initial_state,
            seed=seed,
        )
