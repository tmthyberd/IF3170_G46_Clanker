from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from src.core.models import Package, Placement, SolverState, Truck
from src.core.objective import calculate_objective
from src.core.validator import validate_state


@dataclass
class Individual:
    """Merepresentasikan satu kromosom / individu dalam populasi Genetic Algorithm"""
    state: SolverState
    fitness: float = 0.0
    is_valid: bool = False
    violations: List[str] = field(default_factory=list)

    def evaluate(
        self,
        objective_type: str = "default",
        strict: bool = False,
        objective_func: Optional[Callable[[SolverState], float]] = None,
    ) -> float:
        """Menghitung nilai fitness individu berdasarkan fungsi objektif"""
        self.is_valid, self.violations = validate_state(self.state)
        if objective_func is not None:
            self.fitness = objective_func(self.state)
        else:
            self.fitness = calculate_objective(self.state, objective_type=objective_type, strict=strict)
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
        trucks: Union[List[Truck], Truck],
        packages: Union[Dict[str, Package], List[Package]],
        objective_type: str = "default",
        strict: bool = False,
        rng: Optional[random.Random] = None,
        truck: Optional[Union[List[Truck], Truck]] = None,
        **kwargs: Any,
    ) -> Individual:
        """Membuat individu acak menggunakan generator state domain"""
        from src.core.moves import generate_initial_state
        target_trucks = trucks if trucks is not None else truck
        state = generate_initial_state(target_trucks, packages, randomize=True)
        ind = cls(state=state)
        ind.evaluate(objective_type=objective_type, strict=strict)
        return ind
