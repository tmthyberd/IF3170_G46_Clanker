from __future__ import annotations
import argparse
from src.core.io_utils import load_input_json, save_run_output
from src.core.moves import generate_initial_state
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
            init_state = generate_initial_state(truck, packages, random_strategy="valid_floor")

            if var == "steepest":
                res = steepest_ascent_hill_climbing(init_state, max_iterations=args.iterations)
            elif var == "stochastic":
                res = stochastic_hill_climbing(init_state, max_iterations=args.iterations)
            elif var == "sideways":
                res = sideways_hill_climbing(
                    init_state,
                    max_sideways_moves=args.max_sideways,
                    max_iterations=args.iterations,
                )
            else:
                res = random_restart_hill_climbing(
                    truck,
                    packages,
                    max_restarts=args.max_restarts,
                    max_iterations_per_restart=args.iterations,
                )

            is_valid, violations = is_valid_state(res.final_state)
            saved_file = save_run_output(
                output_dir=args.output_dir,
                algorithm_name=res.algorithm_name,
                initial_state=res.initial_state,
                final_state=res.final_state,
                objective_history=res.objective_history,
                duration=res.duration_seconds,
                extra_metrics={**res.extra_metrics, "is_valid": is_valid, "violations": violations, "run_index": r},
            )

            print(
                f"Run #{r}: Initial={res.initial_objective:.1f} -> Final={res.final_objective:.1f} | "
                f"Iterations={res.total_iterations} | Time={res.duration_seconds:.3f}s | "
                f"Valid={is_valid} | Log={saved_file}"
            )


if __name__ == "__main__":
    main()
