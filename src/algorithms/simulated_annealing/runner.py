from __future__ import annotations
import argparse
import os
import time
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.io_utils import load_input_json, save_run_output
from src.core.moves import generate_initial_state
from src.core.models import Placement, SolverState
from src.core.validator import validate_state
from src.algorithms.simulated_annealing import simulated_annealing


def _unique_plot_path(plots_dir: str, stem: str) -> str:
    """Return a collision-free path for a plot file, using timestamp + counter."""
    time_str = time.strftime("%Y%m%d_%H%M%S")
    subsecond = f"{int(time.time() * 1000) % 1000:03d}"
    base = f"{stem}_{time_str}_{subsecond}"
    path = os.path.join(plots_dir, f"{base}.png")
    counter = 1
    while os.path.exists(path):
        path = os.path.join(plots_dir, f"{base}_{counter}.png")
        counter += 1
    return path


def plot_sa_run(
    iterations: List[int],
    objective_history: List[float],
    acceptance_history: List[float],
    temperature_history: List[float],
    run_index: int,
    output_dir: str,
) -> Dict[str, str]:
    """Menyimpan grafik objektif dan grafik e^(delta_E/T) serta suhu terhadap iterasi sesuai spesifikasi."""
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    obj_plot_path = _unique_plot_path(plots_dir, f"sa_objective_run_{run_index}")
    fig, ax1 = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax1.plot(iterations, objective_history, color="#2563eb", linewidth=2.0, label="Objective Value")
    ax1.set_title(f"Simulated Annealing: Objective Value vs Iteration (Run #{run_index})", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Iterasi", fontsize=10)
    ax1.set_ylabel("Nilai Objective", fontsize=10, color="#2563eb")
    ax1.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(obj_plot_path)
    plt.close(fig)

    metric_plot_path = _unique_plot_path(plots_dir, f"sa_acceptance_temp_run_{run_index}")
    fig, ax2 = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax2.scatter(iterations, acceptance_history, color="#f59e0b", s=10, alpha=0.7, label="e^(ΔE/T) Acceptance Probability")
    ax2.set_title(f"Simulated Annealing: e^(ΔE/T) & Suhu vs Iterasi (Run #{run_index})", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Iterasi", fontsize=10)
    ax2.set_ylabel("Probabilitas Penerimaan e^(ΔE/T)", fontsize=10, color="#d97706")
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, linestyle=":", alpha=0.6)

    ax2_twin = ax2.twinx()
    ax2_twin.plot(iterations, temperature_history, color="#06b6d4", linestyle="--", linewidth=1.5, label="Temperature (T)")
    ax2_twin.set_ylabel("Suhu (T)", fontsize=10, color="#0891b2")

    plt.tight_layout()
    plt.savefig(metric_plot_path)
    plt.close(fig)

    return {
        "objective_plot": os.path.relpath(obj_plot_path, output_dir),
        "acceptance_plot": os.path.relpath(metric_plot_path, output_dir),
    }


def main():
    parser = argparse.ArgumentParser(description="Jalankan eksperimen Simulated Annealing untuk 3D Bin Packing")
    parser.add_argument("--input", default="data/sample_input.json", help="Path ke file JSON input")
    parser.add_argument("--runs", type=int, default=3, help="Jumlah repetisi eksekusi (default: 3)")
    parser.add_argument("--initial_temp", type=float, default=1000.0, help="Suhu awal T0 (default: 1000.0)")
    parser.add_argument("--cooling_rate", type=float, default=0.95, help="Laju pendinginan alpha (default: 0.95)")
    parser.add_argument("--max_iterations", type=int, default=300, help="Batas iterasi maksimum (-1 untuk run sampai T_min, default: 300)")
    parser.add_argument("--strict", action="store_true", help="Aktifkan validasi ketat (strict=True)")
    parser.add_argument("--objective", default="default", help="Tipe fungsi objektif (default: default)")
    parser.add_argument("--output_dir", default="output", help="Direktori penyimpanan log hasil run")
    parser.add_argument("--no_plots", action="store_true", help="Nonaktifkan pembuatan grafik png")

    args = parser.parse_args()

    truck, packages = load_input_json(args.input)
    print(f"Loaded truck: ({truck.w}x{truck.l}x{truck.h}, MaxCapacity={truck.max_capacity})")
    print(f"Loaded {len(packages)} packages.")
    print(f"\n{'='*20} Running Simulated Annealing ({args.runs} runs) {'='*20}")
    print(f"Parameters: T0={args.initial_temp}, CoolingRate={args.cooling_rate}, MaxIter={args.max_iterations}, Strict={args.strict}, Obj={args.objective}\n")

    for r in range(1, args.runs + 1):
        init_state = generate_initial_state(truck, packages)

        gen = simulated_annealing(
            initial_state=init_state,
            initial_temp=args.initial_temp,
            cooling_rate=args.cooling_rate,
            max_iterations=args.max_iterations,
            strict=args.strict,
            objective_type=args.objective,
        )

        history = list(gen)
        initial_step = history[0]
        final_step = history[-1]

        initial_objective = initial_step.get("objective_value", 0.0)
        final_objective = final_step.get("objective_value", 0.0)
        duration_seconds = final_step.get("duration", 0.0)
        total_iterations = final_step.get("iteration", len(history) - 1)

        iterations = [h.get("iteration", i) for i, h in enumerate(history)]
        objective_history = [h.get("objective_value", 0.0) for h in history]
        acceptance_history = [h.get("acceptance_chance", 0.0) for h in history]
        temperature_history = [h.get("temperature", 0.0) for h in history]

        stuck_count = sum(1 for h in history if h.get("is_stuck", 0) == 1)
        stuck_frequency = stuck_count / max(1, total_iterations)

        raw_final_state = final_step.get("state", {})
        final_placements = {
            pid: Placement.from_dict(pdata)
            for pid, pdata in raw_final_state.items()
        }
        final_state = SolverState(
            trucks=truck if isinstance(truck, list) else [truck],
            packages=packages,
            placements=final_placements,
        )

        is_valid, violations = validate_state(final_state)

        plots = {}
        if not args.no_plots:
            plots = plot_sa_run(
                iterations=iterations,
                objective_history=objective_history,
                acceptance_history=acceptance_history,
                temperature_history=temperature_history,
                run_index=r,
                output_dir=args.output_dir,
            )

        saved_file = save_run_output(
            output_dir=args.output_dir,
            algorithm_name="Simulated Annealing",
            initial_state=init_state,
            final_state=final_state,
            objective_history=objective_history,
            duration=duration_seconds,
            extra_metrics={
                "is_valid": is_valid,
                "violations": violations,
                "stuck_count": stuck_count,
                "stuck_frequency": round(stuck_frequency, 4),
                "total_iterations": total_iterations,
                "initial_temp": args.initial_temp,
                "cooling_rate": args.cooling_rate,
                "acceptance_history": acceptance_history,
                "temperature_history": temperature_history,
                "plots": plots,
                "run_index": r,
            },
        )

        print(
            f"Run #{r}: Initial={initial_objective:7.1f} -> Final={final_objective:7.1f} | "
            f"Iterations={total_iterations:4d} | Time={duration_seconds:6.3f}s | "
            f"Stuck={stuck_count:3d}/{total_iterations} ({stuck_frequency:5.1%}) | "
            f"Valid={is_valid} | Log={saved_file}"
        )


if __name__ == "__main__":
    main()
