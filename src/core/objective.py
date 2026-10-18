from __future__ import annotations
from src.core.models import State
from src.core.validator import is_valid_state

PENALTY_PER_VIOLATION = 1000.0


def calculate_raw_value(state: State) -> float:
    """Mengembalikan total nilai paket yang berada di dalam truk"""
    return state.total_value_in_truck


def calculate_objective(state: State, enforce_hard_constraints: bool = True) -> float:
    """Fungsi objektif utama: memaksimalkan total nilai paket dengan penalti negatif jika melanggar aturan"""
    is_valid, violations = is_valid_state(state)
    if not is_valid:
        return -PENALTY_PER_VIOLATION * len(violations) if enforce_hard_constraints else 0.0
    return state.total_value_in_truck


def calculate_alternative_objective(state: State) -> float:
    """Bonus 1 (+3 poin): gabungan nilai paket, utilisasi volume, urgensi ETA, dan stabilitas titik berat"""
    is_valid, violations = is_valid_state(state)
    if not is_valid:
        return -PENALTY_PER_VIOLATION * len(violations)

    truck_vol = max(1, state.truck.w * state.truck.l * state.truck.h)
    max_cap = max(1.0, state.truck.max_capacity)

    used_vol = 0
    eta_bonus = 0.0
    stability = 0.0

    for p in state.packages_in_truck:
        pkg = state.packages[p.package_id]
        dx, dy, dz = state.get_package_dims(p.package_id)
        used_vol += dx * dy * dz
        eta_bonus += pkg.value * 0.15 / max(1, pkg.eta)
        stability += (state.truck.h - p.position[2]) * (pkg.weight / max_cap) * 10.0

    return state.total_value_in_truck + (used_vol / truck_vol) * 50.0 + eta_bonus + stability
