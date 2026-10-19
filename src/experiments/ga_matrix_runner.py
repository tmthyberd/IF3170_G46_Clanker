from __future__ import annotations
import argparse
import json
import os
import statistics
import time
from typing import Any, Dict, List, Optional
from src.core.io_utils import load_input_json
from src.core.models import Package, Truck
from src.algorithms.genetic_algorithm import genetic_algorithm
from src.benchmark.logger import save_benchmark_log
from src.experiments.plotting import plot_ga_convergence, plot_parameter_analysis


def run_ga_matrix_experiments(
    input_file: str = "data/sample_input.json",
    output_dir: str = "output",
    fixed_population: int = 50,
    iteration_variations: Optional[List[int]] = None,
    fixed_iterations: int = 100,
    population_variations: Optional[List[int]] = None,
    repetitions: int = 3,
    base_seed: Optional[int] = 42,
    generate_plots: bool = True,
) -> Dict[str, Any]:
    """
    Menjalankan matriks pengujian lengkap 18x run Genetic Algorithm sesuai spesifikasi:
    - Kontrol Populasi: 3 variasi iterasi x 3 repetisi = 9 run
    - Kontrol Iterasi: 3 variasi populasi x 3 repetisi = 9 run
    Setiap run mencatat state awal/akhir, nilai objective akhir, durasi, dan grafik konvergensi.
    """
    iter_vars = iteration_variations or [50, 100, 200]
    pop_vars = population_variations or [20, 50, 100]

    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    truck, packages = load_input_json(input_file)

    summary: Dict[str, Any] = {
        "metadata": {
            "total_runs": 2 * len(iter_vars) * repetitions,
            "repetitions_per_config": repetitions,
            "input_file": input_file,
            "truck": f"{truck.w}x{truck.l}x{truck.h} (Cap: {truck.max_capacity})",
            "total_packages": len(packages),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "control_population": {
            "fixed_population": fixed_population,
            "variations": {},
        },
        "control_generations": {
            "fixed_generations": fixed_iterations,
            "variations": {},
        },
        "all_runs": [],
    }

    run_counter = 0
    total_runs_expected = (len(iter_vars) + len(pop_vars)) * repetitions

    print(f"\n{'='*75}")
    print(f"AUTOMATED GA EXPERIMENT MATRIX (TOTAL: {total_runs_expected} RUNS)")
    print(f"Bagian 1: Kontrol Populasi (N={fixed_population}) x Iterasi {iter_vars}")
    print(f"Bagian 2: Kontrol Iterasi (G={fixed_iterations}) x Populasi {pop_vars}")
    print(f"{'='*75}\n")

    # ==========================================
    # BAGIAN 1: KONTROL POPULASI (VARIASI ITERASI)
    # ==========================================
    print(f">>> [BAGIAN 1] Kontrol Populasi Tetap (N = {fixed_population}) <<<")
    for iters in iter_vars:
        runs_for_iter: List[Dict[str, Any]] = []
        objectives: List[float] = []
        durations: List[float] = []

        for r in range(1, repetitions + 1):
            run_counter += 1
            run_seed = (base_seed + run_counter) if base_seed is not None else None

            res = genetic_algorithm(
                truck=truck,
                packages=packages,
                population_size=fixed_population,
                max_generations=iters,
                seed=run_seed,
            )

            # Simpan log detail per run
            saved_log = save_benchmark_log(
                output_dir=output_dir,
                result=res,
                run_index=run_counter,
                extra_info={
                    "experiment_group": "control_population",
                    "fixed_population": fixed_population,
                    "target_iterations": iters,
                    "repeat_index": r,
                },
            )

            # Plot konvergensi per run
            plot_file = None
            if generate_plots:
                plot_filename = f"ga_ctrl_pop_{fixed_population}_iter_{iters}_run_{r}.png"
                plot_path = os.path.join(plots_dir, plot_filename)
                avg_hist = res.extra_metrics.get("avg_fitness_history", [])
                plot_ga_convergence(
                    history_max=res.objective_history,
                    history_avg=avg_hist,
                    title=f"Konvergensi GA (N={fixed_population}, Gen={iters}, Run #{r})",
                    output_path=plot_path,
                )
                plot_file = os.path.relpath(plot_path, output_dir)

            record = {
                "run_id": run_counter,
                "group": "control_population",
                "population": fixed_population,
                "iterations": iters,
                "repetition": r,
                "initial_objective": res.initial_objective,
                "final_objective": res.final_objective,
                "duration_seconds": round(res.duration_seconds, 4),
                "is_valid": res.extra_metrics.get("final_is_valid", True),
                "log_file": os.path.relpath(saved_log, output_dir),
                "plot_file": plot_file,
            }
            runs_for_iter.append(record)
            summary["all_runs"].append(record)
            objectives.append(res.final_objective)
            durations.append(res.duration_seconds)

            print(
                f"  [{run_counter:2d}/{total_runs_expected:2d}] "
                f"Pop={fixed_population:3d} | Iter={iters:3d} | Rep={r} | "
                f"Obj: {res.final_objective:7.1f} | Waktu: {res.duration_seconds:6.3f}s | "
                f"Valid: {record['is_valid']}"
            )

        summary["control_population"]["variations"][str(iters)] = {
            "mean_objective": round(statistics.mean(objectives), 2),
            "std_objective": round(statistics.stdev(objectives), 2) if len(objectives) > 1 else 0.0,
            "mean_duration": round(statistics.mean(durations), 4),
            "runs": runs_for_iter,
        }

    # ==========================================
    # BAGIAN 2: KONTROL ITERASI (VARIASI POPULASI)
    # ==========================================
    print(f"\n>>> [BAGIAN 2] Kontrol Iterasi Tetap (G = {fixed_iterations}) <<<")
    for pop in pop_vars:
        runs_for_pop: List[Dict[str, Any]] = []
        objectives: List[float] = []
        durations: List[float] = []

        for r in range(1, repetitions + 1):
            run_counter += 1
            run_seed = (base_seed + run_counter) if base_seed is not None else None

            res = genetic_algorithm(
                truck=truck,
                packages=packages,
                population_size=pop,
                max_generations=fixed_iterations,
                seed=run_seed,
            )

            saved_log = save_benchmark_log(
                output_dir=output_dir,
                result=res,
                run_index=run_counter,
                extra_info={
                    "experiment_group": "control_generations",
                    "fixed_generations": fixed_iterations,
                    "target_population": pop,
                    "repeat_index": r,
                },
            )

            plot_file = None
            if generate_plots:
                plot_filename = f"ga_ctrl_iter_{fixed_iterations}_pop_{pop}_run_{r}.png"
                plot_path = os.path.join(plots_dir, plot_filename)
                avg_hist = res.extra_metrics.get("avg_fitness_history", [])
                plot_ga_convergence(
                    history_max=res.objective_history,
                    history_avg=avg_hist,
                    title=f"Konvergensi GA (N={pop}, Gen={fixed_iterations}, Run #{r})",
                    output_path=plot_path,
                )
                plot_file = os.path.relpath(plot_path, output_dir)

            record = {
                "run_id": run_counter,
                "group": "control_generations",
                "population": pop,
                "iterations": fixed_iterations,
                "repetition": r,
                "initial_objective": res.initial_objective,
                "final_objective": res.final_objective,
                "duration_seconds": round(res.duration_seconds, 4),
                "is_valid": res.extra_metrics.get("final_is_valid", True),
                "log_file": os.path.relpath(saved_log, output_dir),
                "plot_file": plot_file,
            }
            runs_for_pop.append(record)
            summary["all_runs"].append(record)
            objectives.append(res.final_objective)
            durations.append(res.duration_seconds)

            print(
                f"  [{run_counter:2d}/{total_runs_expected:2d}] "
                f"Pop={pop:3d} | Iter={fixed_iterations:3d} | Rep={r} | "
                f"Obj: {res.final_objective:7.1f} | Waktu: {res.duration_seconds:6.3f}s | "
                f"Valid: {record['is_valid']}"
            )

        summary["control_generations"]["variations"][str(pop)] = {
            "mean_objective": round(statistics.mean(objectives), 2),
            "std_objective": round(statistics.stdev(objectives), 2) if len(objectives) > 1 else 0.0,
            "mean_duration": round(statistics.mean(durations), 4),
            "runs": runs_for_pop,
        }

    # Simpan ringkasan eksperimen ke JSON
    summary_path = os.path.join(output_dir, "ga_experiments_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Buat grafik perbandingan parameter
    if generate_plots:
        analysis_plot = os.path.join(plots_dir, "ga_parameter_analysis.png")
        plot_parameter_analysis(summary, analysis_plot)
        print(f"\nGrafik analisis komparatif disimpan ke: {analysis_plot}")

    print(f"Ringkasan eksperimen 18x run disimpan ke: {summary_path}\n")
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Otomasi Eksperimen 18x Run Genetic Algorithm IF3170"
    )
    parser.add_argument("--input", default="data/sample_input.json", help="Path ke file data JSON input")
    parser.add_argument("--output_dir", default="output", help="Folder penyimpanan hasil eksperimen")
    parser.add_argument("--fixed_pop", type=int, default=50, help="Nilai kontrol populasi (default: 50)")
    parser.add_argument(
        "--iter_vars",
        nargs="+",
        type=int,
        default=[50, 100, 200],
        help="3 variasi banyak iterasi (default: 50 100 200)",
    )
    parser.add_argument("--fixed_iter", type=int, default=100, help="Nilai kontrol iterasi (default: 100)")
    parser.add_argument(
        "--pop_vars",
        nargs="+",
        type=int,
        default=[20, 50, 100],
        help="3 variasi jumlah populasi (default: 20 50 100)",
    )
    parser.add_argument("--runs", type=int, default=3, help="Jumlah repetisi per konfigurasi (default: 3)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed (default: 42)")
    parser.add_argument("--no_plots", action="store_true", help="Nonaktifkan pembuatan file grafik png")

    args = parser.parse_args()
    run_ga_matrix_experiments(
        input_file=args.input,
        output_dir=args.output_dir,
        fixed_population=args.fixed_pop,
        iteration_variations=args.iter_vars,
        fixed_iterations=args.fixed_iter,
        population_variations=args.pop_vars,
        repetitions=args.runs,
        base_seed=args.seed,
        generate_plots=not args.no_plots,
    )


if __name__ == "__main__":
    main()
