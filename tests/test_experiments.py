import os
import shutil
import unittest
from src.experiments.plotting import plot_ga_convergence, plot_parameter_analysis
from src.experiments.ga_matrix_runner import run_ga_matrix_experiments


class TestExperiments(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_experiments_temp"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_plot_ga_convergence(self):
        hist_max = [100.0, 150.0, 180.0, 200.0]
        hist_avg = [40.0, 70.0, 110.0, 140.0]
        plot_path = os.path.join(self.test_dir, "test_convergence.png")
        result_path = plot_ga_convergence(
            history_max=hist_max,
            history_avg=hist_avg,
            title="Test Convergence",
            output_path=plot_path,
        )
        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 1000)

    def test_plot_parameter_analysis(self):
        dummy_summary = {
            "control_population": {
                "fixed_population": 50,
                "variations": {
                    "50": {"mean_objective": 180.0, "mean_duration": 0.5},
                    "100": {"mean_objective": 220.0, "mean_duration": 1.1},
                },
            },
            "control_generations": {
                "fixed_generations": 100,
                "variations": {
                    "20": {"mean_objective": 150.0, "mean_duration": 0.4},
                    "50": {"mean_objective": 220.0, "mean_duration": 1.0},
                },
            },
        }
        plot_path = os.path.join(self.test_dir, "test_param_analysis.png")
        result_path = plot_parameter_analysis(dummy_summary, plot_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 1000)

    def test_run_ga_matrix_mini(self):
        summary = run_ga_matrix_experiments(
            input_file="data/sample_input.json",
            output_dir=self.test_dir,
            fixed_population=5,
            iteration_variations=[2],
            fixed_iterations=2,
            population_variations=[5],
            repetitions=1,
            base_seed=123,
            generate_plots=True,
        )
        self.assertIn("control_population", summary)
        self.assertIn("control_generations", summary)
        self.assertEqual(len(summary["all_runs"]), 2)
        summary_json = os.path.join(self.test_dir, "ga_experiments_summary.json")
        self.assertTrue(os.path.exists(summary_json))


if __name__ == "__main__":
    unittest.main()
