from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Optional
from src.core.interfaces import AlgorithmResult
from src.core.validator import evaluate_state_metrics


def save_benchmark_log(
    output_dir: str,
    result: AlgorithmResult,
    run_index: int = 1,
    extra_info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Menyimpan hasil eksekusi algoritma ke folder output dalam format JSON terstandar.
    Mengembalikan path file yang berhasil disimpan.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    safe_name = result.algorithm_name.lower().replace(" ", "_").replace("-", "_")
    filename = f"{safe_name}_run_{run_index}_{timestamp}.json"
    file_path = os.path.join(output_dir, filename)

    final_metrics = evaluate_state_metrics(result.final_state)
    initial_metrics = evaluate_state_metrics(result.initial_state)

    payload = {
        "algorithm": result.algorithm_name,
        "run_index": run_index,
        "timestamp": timestamp,
        "duration_seconds": round(result.duration_seconds, 4),
        "total_iterations": result.total_iterations,
        "initial_objective": result.initial_objective,
        "final_objective": result.final_objective,
        "is_valid": final_metrics["is_valid"],
        "total_value": final_metrics["total_value"],
        "total_weight": final_metrics["total_weight"],
        "truck_capacity": result.final_state.truck.max_capacity,
        "packages_in_truck_count": final_metrics["packages_in_truck_count"],
        "packages_outside_count": final_metrics["packages_outside_count"],
        "violations": final_metrics["violations"],
        "initial_metrics": initial_metrics,
        "initial_state": result.initial_state.to_dict(),
        "final_state": result.final_state.to_dict(),
        "objective_history": result.objective_history,
        "extra_metrics": {**(result.extra_metrics or {}), **(extra_info or {})},
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return file_path
