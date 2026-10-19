import unittest
import os
import shutil
from src.core.models import Truck, Package, State, Placement
from src.core.interfaces import AlgorithmResult
from src.benchmark.logger import save_benchmark_log
from src.benchmark.runner import build_arg_parser, run_single_algorithm, run_experiment


class TestBenchmarkHarness(unittest.TestCase):
    def setUp(self):
        self.test_output_dir = "test_output_temp"
        self.truck = Truck(w=10, l=10, h=5, max_capacity=200.0)
        self.packages = {
            "P1": Package("P1", w=2, l=2, h=2, value=50.0, weight=10.0, is_fragile=False),
            "P2": Package("P2", w=3, l=3, h=1, value=75.0, weight=15.0, is_fragile=False),
        }
        self.state = State(truck=self.truck, packages=self.packages)
        self.state.placements["P1"] = Placement("P1", position=(0, 0, 0), in_truck=True)
        self.state.placements["P2"] = Placement("P2", position=(3, 0, 0), in_truck=True)

    def tearDown(self):
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_save_benchmark_log(self):
        result = AlgorithmResult(
            algorithm_name="TestGA",
            initial_state=self.state,
            final_state=self.state,
            initial_objective=125.0,
            final_objective=125.0,
            duration_seconds=0.05,
            total_iterations=10,
            objective_history=[125.0] * 10,
            extra_metrics={"test_key": "test_val"},
        )
        saved_file = save_benchmark_log(self.test_output_dir, result, run_index=1)
        self.assertTrue(os.path.exists(saved_file))

    def test_run_single_algorithm_ga(self):
        params = {
            "ga_population": 10,
            "ga_generations": 3,
            "ga_crossover_rate": 0.8,
            "ga_mutation_rate": 0.2,
        }
        res = run_single_algorithm("ga", self.truck, self.packages, params, seed=42)
        self.assertEqual(res.algorithm_name, "Genetic Algorithm")
        self.assertEqual(res.total_iterations, 3)

    def test_arg_parser(self):
        parser = build_arg_parser()
        args = parser.parse_args(["--algorithm", "ga", "--runs", "2", "--ga_population", "25"])
        self.assertEqual(args.algorithm, "ga")
        self.assertEqual(args.runs, 2)
        self.assertEqual(args.ga_population, 25)

    def test_run_experiment_smoke(self):
        results = run_experiment(
            algorithms=["ga"],
            input_file="data/sample_input.json",
            runs=1,
            output_dir=self.test_output_dir,
            params={"ga_population": 10, "ga_generations": 2},
            seed=1,
        )
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
