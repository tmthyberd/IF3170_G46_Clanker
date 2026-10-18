from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
from src.core.models import State


@dataclass
class AlgorithmResult:
    """Kontainer standar penyimpan hasil eksekusi algoritma local search"""
    algorithm_name: str
    initial_state: State
    final_state: State
    initial_objective: float
    final_objective: float
    duration_seconds: float
    total_iterations: int
    objective_history: List[float] = field(default_factory=list)
    extra_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm_name,
            "duration_seconds": self.duration_seconds,
            "total_iterations": self.total_iterations,
            "initial_objective": self.initial_objective,
            "final_objective": self.final_objective,
            "initial_state": self.initial_state.to_dict(),
            "final_state": self.final_state.to_dict(),
            "objective_history": self.objective_history,
            "extra_metrics": self.extra_metrics,
        }


class BaseValidator(ABC):
    """Antarmuka validator untuk memeriksa pemenuhan aturan ruang 3D"""
    @abstractmethod
    def is_valid(self, state: State) -> Tuple[bool, List[str]]:
        pass

    @abstractmethod
    def evaluate(self, state: State) -> Dict[str, Any]:
        pass


class BaseAlgorithm(ABC):
    """Antarmuka standar untuk seluruh varian algoritma optimasi"""
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, initial_state: State, **kwargs: Any) -> AlgorithmResult:
        pass
