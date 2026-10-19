from __future__ import annotations
import random
from typing import List, Optional, Tuple
from src.core.models import Placement, State, Truck
from src.core.moves import (
    swap_packages,
    move_package_coordinate,
    rotate_package,
    toggle_in_truck,
)
from src.algorithms.genetic_algorithm.individual import Individual


def tournament_selection(
    population: List[Individual],
    tournament_size: int = 3,
    rng: Optional[random.Random] = None,
) -> Individual:
    """Tournament selection."""
    r = rng if rng is not None else random
    k = min(tournament_size, len(population))
    candidates = r.sample(population, k)
    return max(candidates, key=lambda ind: ind.fitness).clone()


def roulette_wheel_selection(
    population: List[Individual],
    rng: Optional[random.Random] = None,
) -> Individual:
    """Roulette wheel selection."""
    r = rng if rng is not None else random
    min_fit = min(ind.fitness for ind in population)
    shifted_fitnesses = [ind.fitness - min_fit + 1.0 for ind in population]
    total_fit = sum(shifted_fitnesses)
    pick = r.uniform(0, total_fit)

    current = 0.0
    for ind, fit in zip(population, shifted_fitnesses):
        current += fit
        if current >= pick:
            return ind.clone()
    return population[-1].clone()


def uniform_crossover(
    parent1: Individual,
    parent2: Individual,
    rng: Optional[random.Random] = None,
) -> Tuple[Individual, Individual]:
    """Crossover seragam: tiap gen penempatan paket diwariskan dari salah satu induk secara independen"""
    r = rng if rng is not None else random
    c1_state = parent1.state.clone()
    c2_state = parent2.state.clone()

    for pkg_id in parent1.state.packages.keys():
        if r.random() < 0.5:
            c1_state.placements[pkg_id] = parent1.state.placements[pkg_id].copy()
            c2_state.placements[pkg_id] = parent2.state.placements[pkg_id].copy()
        else:
            c1_state.placements[pkg_id] = parent2.state.placements[pkg_id].copy()
            c2_state.placements[pkg_id] = parent1.state.placements[pkg_id].copy()

    child1 = Individual(state=c1_state)
    child2 = Individual(state=c2_state)
    return child1, child2


def two_point_crossover(
    parent1: Individual,
    parent2: Individual,
    rng: Optional[random.Random] = None,
) -> Tuple[Individual, Individual]:
    """Crossover dua titik pada susunan kromosom penempatan paket"""
    r = rng if rng is not None else random
    pkg_ids = list(parent1.state.packages.keys())
    n = len(pkg_ids)

    if n < 2:
        return parent1.clone(), parent2.clone()

    pt1, pt2 = sorted(r.sample(range(n + 1), 2))

    c1_state = parent1.state.clone()
    c2_state = parent2.state.clone()

    for i, pkg_id in enumerate(pkg_ids):
        if pt1 <= i < pt2:
            c1_state.placements[pkg_id] = parent2.state.placements[pkg_id].copy()
            c2_state.placements[pkg_id] = parent1.state.placements[pkg_id].copy()
        else:
            c1_state.placements[pkg_id] = parent1.state.placements[pkg_id].copy()
            c2_state.placements[pkg_id] = parent2.state.placements[pkg_id].copy()

    child1 = Individual(state=c1_state)
    child2 = Individual(state=c2_state)
    return child1, child2


def mutate_individual(
    individual: Individual,
    truck: Truck,
    rng: Optional[random.Random] = None,
) -> Individual:
    """Mutasi stokastik: swap penempatan, translasi posisi/status muat, atau rotasi orientasi."""
    r = rng if rng is not None else random
    state = individual.state.clone()
    pkg_ids = list(state.packages.keys())

    if not pkg_ids:
        return individual.clone()

    move_type = r.choice(["swap", "relocate", "rotate"])

    if move_type == "swap" and len(pkg_ids) >= 2:
        p1, p2 = r.sample(pkg_ids, 2)
        state = swap_packages(state, p1, p2)

    elif move_type == "relocate":
        pid = r.choice(pkg_ids)
        current_p = state.placements[pid]
        if r.random() < 0.4:
            new_in_truck = not current_p.in_truck
            dx, dy, dz = state.get_package_dims(pid)
            new_x = r.randint(0, max(0, truck.w - dx))
            new_y = r.randint(0, max(0, truck.l - dy))
            new_z = 0 if r.random() < 0.7 else r.randint(0, max(0, truck.h - dz))
            state = toggle_in_truck(state, pid, in_truck=new_in_truck, coord=(new_x, new_y, new_z))
        else:
            dx, dy, dz = state.get_package_dims(pid)
            new_x = r.randint(0, max(0, truck.w - dx))
            new_y = r.randint(0, max(0, truck.l - dy))
            new_z = 0 if r.random() < 0.7 else r.randint(0, max(0, truck.h - dz))
            state = move_package_coordinate(state, pid, (new_x, new_y, new_z))

    elif move_type == "rotate":
        pid = r.choice(pkg_ids)
        new_ori = r.randint(0, 5)
        state = rotate_package(state, pid, new_orientation=new_ori)

    mutated = Individual(state=state)
    mutated.evaluate()
    return mutated
