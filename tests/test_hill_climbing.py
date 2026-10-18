import unittest
from src.core.models import Truck, Package
from src.core.moves import generate_initial_state
from src.core.validator import is_valid_state
from src.algorithms.hill_climbing import (
    steepest_ascent_hill_climbing,
    stochastic_hill_climbing,
    sideways_hill_climbing,
    random_restart_hill_climbing,
)
from src.core.io_utils import load_input_json


class TestHillClimbing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truck, cls.packages = load_input_json("data/sample_input.json")
        cls.initial_state = generate_initial_state(
            cls.truck, cls.packages, random_strategy="valid_floor"
        )

    def test_steepest_ascent(self):
        res = steepest_ascent_hill_climbing(
            self.initial_state, max_iterations=20, sample_neighbors=15
        )
        self.assertGreaterEqual(res.final_objective, res.initial_objective)
        self.assertIn("iterations_to_stop", res.extra_metrics)
        valid, violations = is_valid_state(res.final_state)
        self.assertTrue(valid, f"Final state has violations: {violations}")

    def test_stochastic(self):
        res = stochastic_hill_climbing(
            self.initial_state, max_iterations=20, sample_neighbors=15
        )
        self.assertGreaterEqual(res.final_objective, res.initial_objective)
        self.assertIn("iterations_to_stop", res.extra_metrics)
        valid, violations = is_valid_state(res.final_state)
        self.assertTrue(valid, f"Final state has violations: {violations}")

    def test_sideways_move(self):
        res = sideways_hill_climbing(
            self.initial_state,
            max_sideways_moves=5,
            max_iterations=20,
            sample_neighbors=15,
        )
        self.assertGreaterEqual(res.final_objective, res.initial_objective)
        self.assertIn("total_sideways_moves_taken", res.extra_metrics)
        valid, violations = is_valid_state(res.final_state)
        self.assertTrue(valid, f"Final state has violations: {violations}")

    def test_random_restart(self):
        res = random_restart_hill_climbing(
            self.truck,
            self.packages,
            max_restarts=2,
            max_iterations_per_restart=10,
            sample_neighbors=10,
        )
        self.assertGreater(res.final_objective, 0)
        self.assertIn("restarts_completed", res.extra_metrics)
        valid, violations = is_valid_state(res.final_state)
        self.assertTrue(valid, f"Final state has violations: {violations}")


if __name__ == "__main__":
    unittest.main()
