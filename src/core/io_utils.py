from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Tuple
from src.core.models import Package, SolverState, Truck


def load_input_json(file_path: str) -> Tuple[Truck, Dict[str, Package]]:
    """Memuat konfigurasi truk dan daftar paket dari file JSON"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    truck = Truck.from_dict(data["truck"])
    packages = {p["id"]: Package.from_dict(p) for p in data["packages"]}
    return truck, packages


def save_run_output(
    output_dir: str,
    algorithm_name: str,
    initial_state: SolverState,
    final_state: SolverState,
    objective_history: list[float],
    duration: float,
    extra_metrics: Dict[str, Any] | None = None,
    filename: str | None = None,
) -> str:
    """Menyimpan hasil eksperimen ke direktori output dalam format JSON"""
    os.makedirs(output_dir, exist_ok=True)
    if filename is None:
        algo_slug = algorithm_name.lower().replace(" ", "_")
        run_idx = extra_metrics.get("run_index") if extra_metrics else None
        idx_str = f"_run{run_idx}" if run_idx is not None else ""
        time_str = time.strftime("%Y%m%d_%H%M%S")
        subsecond = f"{int(time.time() * 1000) % 1000:03d}"
        base_name = f"{algo_slug}{idx_str}_{time_str}_{subsecond}"
        filename = f"{base_name}.json"
        counter = 1
        while os.path.exists(os.path.join(output_dir, filename)):
            filename = f"{base_name}_{counter}.json"
            counter += 1
    file_path = os.path.join(output_dir, filename)

    payload = {
        "algorithm": algorithm_name,
        "duration_seconds": duration,
        "initial_state": initial_state.to_dict(),
        "final_state": final_state.to_dict(),
        "final_objective": objective_history[-1] if objective_history else final_state.total_value_in_truck,
        "objective_history": objective_history,
        "extra_metrics": extra_metrics or {},
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return file_path