from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from src.core.models import Package, Placement, State, Truck
from src.core.objective import calculate_objective
from src.core.validator import is_valid_state


@dataclass
class Individual:
    """Merepresentasikan satu kromosom / individu dalam populasi Genetic Algorithm"""
    state: State
    fitness: float = 0.0
    is_valid: bool = False
    violations: List[str] = field(default_factory=list)

    def evaluate(self, objective_func: Callable[[State], float] = calculate_objective) -> float:
        """Menghitung nilai fitness individu berdasarkan fungsi objektif"""
        self.is_valid, self.violations = is_valid_state(self.state)
        self.fitness = objective_func(self.state)
        return self.fitness

    def clone(self) -> Individual:
        """Duplikasi objek individu."""
        return Individual(
            state=self.state.clone(),
            fitness=self.fitness,
            is_valid=self.is_valid,
            violations=list(self.violations),
        )

    @classmethod
    def create_random(
        cls,
        truck: Truck,
        packages: Dict[str, Package],
        strategy: str = "valid_floor",
        rng: Optional[random.Random] = None,
    ) -> Individual:
        """Membuat individu acak menggunakan generator state domain"""
        from src.core.moves import generate_initial_state
        state = generate_initial_state(truck, packages, random_strategy=strategy)
        ind = cls(state=state)
        ind.evaluate()
        return ind
