from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from src.core.models import State


@dataclass
class HillClimbingResult:
    """Menyimpan hasil akhir dan metrik eksperimen algoritma Hill-Climbing"""
    algorithm_name: str
    initial_state: State
    final_state: State
    initial_objective: float
    final_objective: float
    duration_seconds: float
    total_iterations: int
    objective_history: List[float] = field(default_factory=list)
    extra_metrics: Dict[str, Any] = field(default_factory=dict)
