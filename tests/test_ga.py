import unittest
import random
from src.core.models import Truck, Package, Placement, State
from src.core.objective import calculate_objective
from src.core.validator import is_valid_state
from src.algorithms.genetic_algorithm import (
    Individual,
    tournament_selection,
    roulette_wheel_selection,
    uniform_crossover,
    two_point_crossover,
    mutate_individual,
    genetic_algorithm,
    GeneticAlgorithm,
)


class TestGeneticAlgorithm(unittest.TestCase):
    def setUp(self):
        self.truck = Truck(w=10, l=10, h=5, max_capacity=200.0)
        self.packages = {
            "P1": Package("P1", w=2, l=2, h=2, value=50.0, weight=10.0, is_fragile=False),
            "P2": Package("P2", w=3, l=3, h=1, value=75.0, weight=15.0, is_fragile=False),
            "P3": Package("P3", w=2, l=1, h=1, value=30.0, weight=5.0, is_fragile=True),
            "P4": Package("P4", w=4, l=2, h=2, value=120.0, weight=30.0, is_fragile=False),
        }
        self.state = State(truck=self.truck, packages=self.packages)
        self.state.placements["P1"] = Placement("P1", position=(0, 0, 0), in_truck=True)
        self.state.placements["P2"] = Placement("P2", position=(3, 0, 0), in_truck=True)
        self.state.placements["P3"] = Placement("P3", position=(7, 0, 0), in_truck=True)
        self.state.placements["P4"] = Placement("P4", position=(0, 0, 0), in_truck=False)

    def test_individual_evaluation_and_clone(self):
        ind = Individual(state=self.state)
        fit = ind.evaluate()
        self.assertTrue(ind.is_valid)
        self.assertEqual(fit, 155.0)  # P1(50) + P2(75) + P3(30)

        cloned = ind.clone()
        self.assertEqual(cloned.fitness, ind.fitness)
        cloned.state.placements["P1"].position = (9, 9, 9)
        self.assertNotEqual(ind.state.placements["P1"].position, (9, 9, 9))

    def test_tournament_selection(self):
        rng = random.Random(42)
        pop = []
        for i in range(5):
            ind = Individual(state=self.state.clone(), fitness=float(i * 10))
            pop.append(ind)
        selected = tournament_selection(pop, tournament_size=3, rng=rng)
        self.assertIsInstance(selected, Individual)
        self.assertGreaterEqual(selected.fitness, 0.0)

    def test_roulette_wheel_selection(self):
        rng = random.Random(42)
        pop = [
            Individual(state=self.state.clone(), fitness=-50.0),
            Individual(state=self.state.clone(), fitness=100.0),
            Individual(state=self.state.clone(), fitness=200.0),
        ]
        selected = roulette_wheel_selection(pop, rng=rng)
        self.assertIsInstance(selected, Individual)

    def test_crossover_operators(self):
        rng = random.Random(42)
        p1 = Individual(state=self.state.clone())
        p2 = Individual(state=self.state.clone())
        p2.state.placements["P1"].in_truck = False
        p2.state.placements["P4"].in_truck = True

        c1, c2 = uniform_crossover(p1, p2, rng=rng)
        self.assertEqual(len(c1.state.placements), 4)
        self.assertEqual(len(c2.state.placements), 4)

        c3, c4 = two_point_crossover(p1, p2, rng=rng)
        self.assertEqual(len(c3.state.placements), 4)
        self.assertEqual(len(c4.state.placements), 4)

    def test_mutation_operator(self):
        rng = random.Random(42)
        ind = Individual(state=self.state.clone())
        ind.evaluate()
        mutated = mutate_individual(ind, self.truck, rng=rng)
        self.assertIsInstance(mutated, Individual)
        self.assertEqual(len(mutated.state.placements), len(ind.state.placements))

    def test_genetic_algorithm_execution(self):
        result = genetic_algorithm(
            truck=self.truck,
            packages=self.packages,
            population_size=10,
            max_generations=5,
            crossover_rate=0.8,
            mutation_rate=0.2,
            seed=42,
        )
        self.assertEqual(result.algorithm_name, "Genetic Algorithm")
        self.assertEqual(result.total_iterations, 5)
        self.assertEqual(len(result.objective_history), 5)
        self.assertIn("avg_fitness_history", result.extra_metrics)
        self.assertEqual(len(result.extra_metrics["avg_fitness_history"]), 5)
        self.assertGreaterEqual(result.duration_seconds, 0.0)

    def test_base_algorithm_wrapper(self):
        ga = GeneticAlgorithm(population_size=10, max_generations=3, seed=123)
        self.assertEqual(ga.name, "Genetic Algorithm")
        res = ga.run(self.state)
        self.assertEqual(res.total_iterations, 3)
        self.assertEqual(len(res.objective_history), 3)


if __name__ == "__main__":
    unittest.main()
