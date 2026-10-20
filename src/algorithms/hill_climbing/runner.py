from __future__ import annotations
import argparse
from src.core.io_utils import load_input_json, save_run_output
from src.core.moves import generate_initial_state
from src.core.models import Placement, SolverState
from src.core.validator import is_valid_state
from src.algorithms.hill_climbing import (
    steepest_ascent_hill_climbing,
    stochastic_hill_climbing,
    sideways_hill_climbing,
    random_restart_hill_climbing,
)


def main():
    parser = argparse.ArgumentParser(description="Jalankan eksperimen Hill-Climbing untuk 3D Bin Packing")
    parser.add_argument("--input", default="data/sample_input.json", help="Path ke file JSON input")
    parser.add_argument(
        "--variant",
        choices=["steepest", "stochastic", "sideways", "restart", "all"],
        default="all",
        help="Varian Hill-Climbing yang akan dijalankan",
    )
    parser.add_argument("--runs", type=int, default=3, help="Jumlah run per varian")
    parser.add_argument("--iterations", type=int, default=200, help="Batas iterasi maksimum")
    parser.add_argument("--max_sideways", type=int, default=50, help="Batas maksimum sideways move")
    parser.add_argument("--max_restarts", type=int, default=5, help="Batas maksimum restart")
    parser.add_argument("--output_dir", default="output", help="Direktori penyimpanan log hasil run")

    args = parser.parse_args()

    truck, packages = load_input_json(args.input)
    print(f"Loaded truck: ({truck.w}x{truck.l}x{truck.h}, MaxCapacity={truck.max_capacity})")
    print(f"Loaded {len(packages)} packages.")

    variants_to_run = (
        ["steepest", "stochastic", "sideways", "restart"]
        if args.variant == "all"
        else [args.variant]
    )

    for var in variants_to_run:
        print(f"\n{'='*20} Running Variant: {var.upper()} ({args.runs} runs) {'='*20}")
        for r in range(1, args.runs + 1):
            init_state = generate_initial_state(truck, packages)

            if var == "steepest":
                gen = steepest_ascent_hill_climbing(init_state)
                algo_name = "Steepest Ascent Hill-Climbing"
            elif var == "stochastic":
                gen = stochastic_hill_climbing(init_state, max_iterations=args.iterations)
                algo_name = "Stochastic Hill-Climbing"
            elif var == "sideways":
                gen = sideways_hill_climbing(
                    init_state,
                    max_sideways_moves=args.max_sideways
                )
                algo_name = "Hill-Climbing (Sideways Move)"
            else:
                gen = random_restart_hill_climbing(
                    truck,
                    packages,
                    max_restarts=args.max_restarts
                )
                algo_name = "Random Restart Hill-Climbing"

            history = list(gen)
            initial_step = history[0]
            final_step = history[-1]

            initial_objective = initial_step.get("objective_value", 0.0)
            final_objective = final_step.get("global_best_value", final_step.get("objective_value", 0.0))
            duration_seconds = final_step.get("duration", 0.0)
            total_iterations = final_step.get("iteration", len(history) - 1)
            objective_history = [
                h.get("objective_value", h.get("global_best_value", 0.0))
                for h in history
                if "objective_value" in h or "global_best_value" in h
            ]

            raw_final_state = final_step.get("global_best_state") or final_step.get("state", {})
            final_placements = {
                pid: Placement.from_dict(pdata)
                for pid, pdata in raw_final_state.items()
            }
            final_state = SolverState(
                trucks=truck if isinstance(truck, list) else [truck],
                packages=packages,
                placements=final_placements,
            )

            is_valid, violations = is_valid_state(final_state)
            saved_file = save_run_output(
                output_dir=args.output_dir,
                algorithm_name=algo_name,
                initial_state=init_state,
                final_state=final_state,
                objective_history=objective_history,
                duration=duration_seconds,
                extra_metrics={"is_valid": is_valid, "violations": violations, "run_index": r},
            )

            print(
                f"Run #{r}: Initial={initial_objective:.1f} -> Final={final_objective:.1f} | "
                f"Iterations={total_iterations} | Time={duration_seconds:.3f}s | "
                f"Valid={is_valid} | Log={saved_file}"
            )


if __name__ == "__main__":
    main()
