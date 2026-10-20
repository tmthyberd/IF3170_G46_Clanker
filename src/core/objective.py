from __future__ import annotations
from typing import Any, Dict, Tuple
from src.core.models import SolverState
from src.core.validator import validate_state

PENALTY_PER_VIOLATION = 100.0


# Fungsi objektif dengan lima variasi (total value, eta, density, total value + eta, total value + density)
# Asumsi total volume yan dapat ditampung truck lebih dari nol     
def calculate_objective(state: SolverState, objective_type: str = "default", strict: bool = True) -> float:
    is_valid, violations = validate_state(state)
    if not is_valid and strict:
        return 0.0

    if objective_type == "eta":
        eta_score = sum(
            state.packages[p.package_id].value * (1.0 + 1.0 / max(0.5, state.packages[p.package_id].eta))
            for p in state.packages_in_truck
        )
        value = eta_score

    elif objective_type == "volume":
        used_vol = 0.0
        for p in state.packages_in_truck:
            dx, dy, dz = state.get_package_dims(p.package_id)
            used_vol += (dx * dy * dz)

        total_trucks_vol = sum(t.volume for t in state.trucks)
        vol_ratio = used_vol / total_trucks_vol

        value = vol_ratio * 100

    elif objective_type == "bonus_volume":
        used_vol = 0.0
        for p in state.packages_in_truck:
            dx, dy, dz = state.get_package_dims(p.package_id)
            used_vol += (dx * dy * dz)

        total_trucks_vol = sum(t.volume for t in state.trucks)
        vol_ratio = used_vol / total_trucks_vol

        value = state.total_value_in_truck * (1.0 + 0.5 * vol_ratio)

    elif objective_type == "bonus_eta":
        eta_bonus = sum(
            state.packages[p.package_id].value * 0.15 / max(1.0, state.packages[p.package_id].eta)
            for p in state.packages_in_truck
        )
        value = state.total_value_in_truck + eta_bonus

    elif objective_type == "bonus_volume_eta":
        used_vol = 0.0
        for p in state.packages_in_truck:
            dx, dy, dz = state.get_package_dims(p.package_id)
            used_vol += (dx * dy * dz)

        total_trucks_vol = sum(t.volume for t in state.trucks)
        vol_ratio = used_vol / total_trucks_vol

        eta_bonus = sum(
            state.packages[p.package_id].value * 0.15 / max(1.0, state.packages[p.package_id].eta)
            for p in state.packages_in_truck
        )

        value = state.total_value_in_truck * (1.0 + 0.5 * vol_ratio) + eta_bonus

    elif objective_type == "default":
        value = state.total_value_in_truck

    else:
        raise NotImplementedError(f"Invalid objective function type: \"{objective_type}\"")        


    return value - PENALTY_PER_VIOLATION * len(violations)


# Overview evaluasi sebua state
def evaluate_state(state: SolverState, objective_type: str = "default", strict: bool = False) -> Tuple[float, Dict[str, Any]]:
    is_valid, violations = validate_state(state)
    score = calculate_objective(state, objective_type=objective_type, strict=strict)

    metrics = {
        "score": score,
        "raw_value": state.total_value_in_truck,
        "is_valid": is_valid,
        "violations": violations,
        "packed_count": len(list(state.packages_in_truck)),
        "unpacked_count": len(list(state.packages_outside_truck)),
        "truck_weights": {i: state.total_weight_in_truck_id(i) for i in range(len(state.trucks))}
    }
    return score, metrics
