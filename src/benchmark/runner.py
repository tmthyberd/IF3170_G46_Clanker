from __future__ import annotations
import argparse
import random
import sys
from typing import Any, Dict, List, Optional
from src.core.interfaces import AlgorithmResult
from src.core.io_utils import load_input_json
from src.core.models import Package, State, Truck
from src.core.moves import generate_initial_state
from src.benchmark.logger import save_benchmark_log


def run_single_algorithm(
    algo_key: str,
    truck: Truck,
    packages: Dict[str, Package],
    params: Dict[str, Any],
    seed: Optional[int] = None,
) -> AlgorithmResult:
    """
    Menjalankan satu kali eksekusi algoritma tertentu dan mengembalikan AlgorithmResult terstandar.
    """
    if algo_key.startswith("hc_"):
        variant = algo_key.replace("hc_", "")
        init_state = generate_initial_state(truck, packages, random_strategy="valid_floor")

        if variant == "steepest":
            from src.algorithms.hill_climbing import steepest_ascent_hill_climbing
            hc_res = steepest_ascent_hill_climbing(
                init_state, max_iterations=params.get("hc_iterations", 200)
            )
        elif variant == "stochastic":
            from src.algorithms.hill_climbing import stochastic_hill_climbing
            hc_res = stochastic_hill_climbing(
                init_state, max_iterations=params.get("hc_iterations", 200)
            )
        elif variant == "sideways":
            from src.algorithms.hill_climbing import sideways_hill_climbing
            hc_res = sideways_hill_climbing(
                init_state,
                max_sideways_moves=params.get("hc_max_sideways", 50),
                max_iterations=params.get("hc_iterations", 200),
            )
        elif variant == "restart":
            from src.algorithms.hill_climbing import random_restart_hill_climbing
            hc_res = random_restart_hill_climbing(
                truck,
                packages,
                max_restarts=params.get("hc_max_restarts", 5),
                max_iterations_per_restart=params.get("hc_iterations", 200),
            )
        else:
            raise ValueError(f"Unknown Hill-Climbing variant: {variant}")

        return AlgorithmResult(
            algorithm_name=hc_res.algorithm_name,
            initial_state=hc_res.initial_state,
            final_state=hc_res.final_state,
            initial_objective=hc_res.initial_objective,
            final_objective=hc_res.final_objective,
            duration_seconds=hc_res.duration_seconds,
            total_iterations=hc_res.total_iterations,
            objective_history=hc_res.objective_history,
            extra_metrics=hc_res.extra_metrics,
        )

    elif algo_key == "ga":
        from src.algorithms.genetic_algorithm import genetic_algorithm
        return genetic_algorithm(
            truck=truck,
            packages=packages,
            population_size=params.get("ga_population", 50),
            max_generations=params.get("ga_generations", 100),
            crossover_rate=params.get("ga_crossover_rate", 0.8),
            mutation_rate=params.get("ga_mutation_rate", 0.2),
            tournament_size=params.get("ga_tournament_size", 3),
            elitism_count=params.get("ga_elitism", 2),
            selection_method=params.get("ga_selection", "tournament"),
            crossover_method=params.get("ga_crossover", "uniform"),
            seed=seed,
            verbose=params.get("verbose", False),
        )

    elif algo_key == "sa":
        try:
            from src.algorithms.simulated_annealing import simulated_annealing  # type: ignore
            init_state = generate_initial_state(truck, packages, random_strategy="valid_floor")
            return simulated_annealing(init_state, **params)
        except ImportError:
            raise NotImplementedError(
                "Modul Simulated Annealing belum tersedia (tugas Orang 2). "
                "Harness siap mengintegrasikannya begitu modul dibuat."
            )

    else:
        raise ValueError(f"Algoritma '{algo_key}' tidak dikenali.")


def run_experiment(
    algorithms: List[str],
    input_file: str,
    runs: int = 3,
    output_dir: str = "output",
    params: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
) -> List[AlgorithmResult]:
    """
    Eksekutor eksperimen terpusat: memuat data, mengeksekusi algoritma, dan mencatat output.
    """
    truck, packages = load_input_json(input_file)
    exec_params = params or {}
    results: List[AlgorithmResult] = []

    print(f"\n{'='*70}")
    print(f"BENCHMARK RUNNER: 3D CONTAINER LOADING")
    print(f"Truk: {truck.w}x{truck.l}x{truck.h} | Kapasitas Beban: {truck.max_capacity}")
    print(f"Total Paket: {len(packages)} | Repetisi per Algoritma: {runs}")
    print(f"{'='*70}\n")

    for algo in algorithms:
        print(f"\n>>> Menjalankan: {algo.upper()} ({runs} runs) <<<")
        for r in range(1, runs + 1):
            run_seed = seed + r if seed is not None else None
            try:
                res = run_single_algorithm(algo, truck, packages, exec_params, seed=run_seed)
                saved_path = save_benchmark_log(output_dir, res, run_index=r, extra_info={"seed": run_seed})
                results.append(res)

                is_valid = res.extra_metrics.get("final_is_valid", True)
                print(
                    f"  [Run {r:2d}/{runs:2d}] "
                    f"Initial: {res.initial_objective:7.1f} -> Final: {res.final_objective:7.1f} | "
                    f"Iterasi: {res.total_iterations:4d} | "
                    f"Waktu: {res.duration_seconds:6.3f}s | "
                    f"Valid: {is_valid} | "
                    f"File: {saved_path}"
                )
            except NotImplementedError as e:
                print(f"  [Lewati] {e}")
                break

    return results


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Centralized Benchmark Harness untuk IF3170 Tugas Besar 1 (Local Search 3D Container Loading)"
    )
    parser.add_argument(
        "--algorithm",
        "-a",
        choices=["hc", "ga", "sa", "all"],
        default="ga",
        help="Algoritma utama yang ingin dijalankan (default: ga)",
    )
    parser.add_argument(
        "--hc_variant",
        choices=["steepest", "stochastic", "sideways", "restart", "all"],
        default="all",
        help="Varian Hill-Climbing jika memilih algoritma hc (default: all)",
    )
    parser.add_argument(
        "--input",
        "-i",
        default="data/sample_input.json",
        help="Path ke file konfigurasi JSON input (default: data/sample_input.json)",
    )
    parser.add_argument(
        "--runs",
        "-r",
        type=int,
        default=3,
        help="Jumlah eksekusi repetisi (default: 3)",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        default="output",
        help="Folder penyimpanan log JSON hasil eksekusi (default: output)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed untuk reprodusibilitas (opsional)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Cetak rincian proses per iterasi",
    )

    parser.add_argument("--hc_iterations", type=int, default=200, help="Maksimum iterasi Hill-Climbing")
    parser.add_argument("--hc_max_sideways", type=int, default=50, help="Batas maksimum sideways moves")
    parser.add_argument("--hc_max_restarts", type=int, default=5, help="Batas maksimum restart")

    parser.add_argument("--ga_population", type=int, default=50, help="Jumlah populasi GA (default: 50)")
    parser.add_argument("--ga_generations", type=int, default=100, help="Jumlah generasi/iterasi GA (default: 100)")
    parser.add_argument("--ga_crossover_rate", type=float, default=0.8, help="Probabilitas crossover (default: 0.8)")
    parser.add_argument("--ga_mutation_rate", type=float, default=0.2, help="Probabilitas mutasi (default: 0.2)")
    parser.add_argument("--ga_tournament_size", type=int, default=3, help="Ukuran tournament selection (default: 3)")
    parser.add_argument("--ga_elitism", type=int, default=2, help="Jumlah individu elit dipertahankan (default: 2)")
    parser.add_argument(
        "--ga_selection",
        choices=["tournament", "roulette"],
        default="tournament",
        help="Metode seleksi GA (default: tournament)",
    )
    parser.add_argument(
        "--ga_crossover",
        choices=["uniform", "two_point"],
        default="uniform",
        help="Metode crossover GA (default: uniform)",
    )
    parser.add_argument(
        "--run_ga_matrix",
        action="store_true",
        help="Jalankan otomatis seluruh 18 kombinasi eksperimen matriks GA (kontrol populasi & iterasi)",
    )

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.run_ga_matrix:
        from src.experiments.ga_matrix_runner import run_ga_matrix_experiments
        run_ga_matrix_experiments(
            input_file=args.input,
            output_dir=args.output_dir,
            fixed_population=args.ga_population,
            fixed_iterations=args.ga_generations,
            repetitions=args.runs,
            base_seed=args.seed or 42,
        )
        return

    algo_list: List[str] = []
    if args.algorithm == "all":
        algo_list = ["hc_steepest", "hc_stochastic", "hc_sideways", "hc_restart", "sa", "ga"]
    elif args.algorithm == "hc":
        if args.hc_variant == "all":
            algo_list = ["hc_steepest", "hc_stochastic", "hc_sideways", "hc_restart"]
        else:
            algo_list = [f"hc_{args.hc_variant}"]
    elif args.algorithm == "ga":
        algo_list = ["ga"]
    elif args.algorithm == "sa":
        algo_list = ["sa"]

    params = vars(args)
    run_experiment(
        algorithms=algo_list,
        input_file=args.input,
        runs=args.runs,
        output_dir=args.output_dir,
        params=params,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
