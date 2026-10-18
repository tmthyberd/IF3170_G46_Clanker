from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.models import SolverState

@dataclass
class SimulatedAnnealingResult:
    """
    Menyimpan hasil akhir dan metrik eksperimen Simulated Annealing
    """
    algorithm_name: str
    initial_state: SolverState
    final_state: SolverState
    initial_objective: float
    final_objective: float
    duration_seconds: float
    total_iterations: int
    objective_history: List[float] = field(default_factory=list)
    temperature_history: List[float] = field(default_factory=list)
    acceptance_chance_history: List[float] = field(default_factory=list)
    delta_e_history: List[float] = field(default_factory=list)
    extra_metrics: Dict[str, Any] = field(default_factory=dict)
