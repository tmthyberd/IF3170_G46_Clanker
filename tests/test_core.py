import unittest
from src.core.models import Truck, Package, Placement, State
from src.core.validator import (
    is_valid_state,
    check_boundary_violations,
    check_overlap_violations,
    check_floating_violations,
    check_fragile_violations,
    check_capacity_violations,
)
from src.core.objective import calculate_objective
from src.core.moves import (
    swap_packages,
    move_package_coordinate,
    rotate_package,
    generate_initial_state,
)
from src.core.io_utils import load_input_json


class TestCoreDomain(unittest.TestCase):
    def setUp(self):
        self.truck = Truck(w=10, l=10, h=10, max_capacity=100.0)
        self.pkg_normal = Package(
            id="P1", w=2, l=2, h=2, value=100.0, weight=10.0, is_fragile=False
        )
        self.pkg_fragile = Package(
            id="P2", w=2, l=2, h=2, value=200.0, weight=5.0, is_fragile=True
        )
        self.pkg_top = Package(
            id="P3", w=2, l=2, h=2, value=50.0, weight=5.0, is_fragile=False
        )
        self.packages = {
            "P1": self.pkg_normal,
            "P2": self.pkg_fragile,
            "P3": self.pkg_top,
        }

    def test_valid_floor_placement(self):
        state = State(truck=self.truck, packages=self.packages)
        state.placements["P1"] = Placement("P1", position=(0, 0, 0), in_truck=True)
        state.placements["P2"] = Placement("P2", position=(3, 0, 0), in_truck=True)
        valid, violations = is_valid_state(state)
        self.assertTrue(valid, f"Violations found: {violations}")

    def test_overlap_detection(self):
        state = State(truck=self.truck, packages=self.packages)
        state.placements["P1"] = Placement("P1", position=(0, 0, 0), in_truck=True)
        state.placements["P2"] = Placement("P2", position=(1, 1, 0), in_truck=True)
        valid, violations = is_valid_state(state)
        self.assertFalse(valid)
        self.assertTrue(any("overlap" in v for v in violations))

    def test_floating_detection(self):
        state = State(truck=self.truck, packages=self.packages)
        # P3 diletakkan pada z=3 tanpa penopang di bawahnya
        state.placements["P3"] = Placement("P3", position=(0, 0, 3), in_truck=True)
        valid, violations = is_valid_state(state)
        self.assertFalse(valid)
        self.assertTrue(any("floating" in v for v in violations))

    def test_valid_stack_on_non_fragile(self):
        state = State(truck=self.truck, packages=self.packages)
        # P1 di lantai (z=0, h=2)
        state.placements["P1"] = Placement("P1", position=(0, 0, 0), in_truck=True)
        # P3 ditumpuk di atas P1 (z=2)
        state.placements["P3"] = Placement("P3", position=(0, 0, 2), in_truck=True)
        valid, violations = is_valid_state(state)
        self.assertTrue(valid, f"Expected valid stack but got violations: {violations}")

    def test_fragile_underneath_violation(self):
        state = State(truck=self.truck, packages=self.packages)
        # P2 bersifat fragile di lantai (z=0, h=2)
        state.placements["P2"] = Placement("P2", position=(0, 0, 0), in_truck=True)
        # P3 ditumpuk di atas paket fragile P2
        state.placements["P3"] = Placement("P3", position=(0, 0, 2), in_truck=True)
        valid, violations = is_valid_state(state)
        self.assertFalse(valid)
        self.assertTrue(any("Fragile" in v for v in violations))

    def test_capacity_violation(self):
        heavy_pkg = Package("P_heavy", w=1, l=1, h=1, value=10, weight=150.0)
        pkgs = {"P_heavy": heavy_pkg}
        state = State(truck=self.truck, packages=pkgs)
        state.placements["P_heavy"] = Placement("P_heavy", position=(0, 0, 0), in_truck=True)
        valid, violations = is_valid_state(state)
        self.assertFalse(valid)
        self.assertTrue(any("capacity" in v for v in violations))

    def test_json_loading(self):
        truck, pkgs = load_input_json("data/sample_input.json")
        self.assertGreater(len(pkgs), 0)
        self.assertEqual(truck.w, 10)


if __name__ == "__main__":
    unittest.main()
