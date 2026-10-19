from __future__ import annotations
import random
from typing import Dict, List, Optional, Tuple
from src.core.models import Package, Placement, State, Truck
from src.core.validator import is_valid_state


def swap_packages(state: State, pkg_id1: str, pkg_id2: str) -> State:
    """Tukar atribut penempatan antara dua paket."""
    new_state = state.clone()
    p1, p2 = new_state.placements[pkg_id1], new_state.placements[pkg_id2]
    p1.position, p1.orientation, p1.in_truck, p2.position, p2.orientation, p2.in_truck = (
        p2.position, p2.orientation, p2.in_truck, p1.position, p1.orientation, p1.in_truck,
    )
    return new_state


def move_package_coordinate(state: State, pkg_id: str, new_coord: Tuple[int, int, int]) -> State:
    """Pindahkan paket ke koordinat baru di dalam truk."""
    new_state = state.clone()
    p = new_state.placements[pkg_id]
    p.position = new_coord
    p.in_truck = True
    return new_state


def rotate_package(state: State, pkg_id: str, new_orientation: Optional[int] = None) -> State:
    """Putar orientasi paket 90 derajat."""
    new_state = state.clone()
    p = new_state.placements[pkg_id]
    p.orientation = new_orientation % 6 if new_orientation is not None else (p.orientation + 1) % 6
    return new_state


def toggle_in_truck(state: State, pkg_id: str, in_truck: bool, coord: Tuple[int, int, int] = (0, 0, 0)) -> State:
    """Masukkan paket ke dalam truk atau keluarkan paket dari truk"""
    new_state = state.clone()
    p = new_state.placements[pkg_id]
    p.in_truck = in_truck
    if in_truck:
        p.position = coord
    return new_state


def _sample_supported_coord(state: State, pkg_id: str) -> Tuple[int, int, int]:
    """Pilih koordinat di lantai truk (z=0) atau di atas permukaan paket non-fragile"""
    truck = state.truck
    dx, dy, dz = state.get_package_dims(pkg_id)
    max_x, max_y = max(0, truck.w - dx), max(0, truck.l - dy)

    supports = [
        state.get_bounding_box(p.package_id)
        for p in state.packages_in_truck
        if p.package_id != pkg_id and not state.packages[p.package_id].is_fragile
    ]
    valid_supports = [b for b in supports if b[2] + b[5] + dz <= truck.h]

    if valid_supports and random.random() < 0.4:
        ox, oy, oz, odx, ody, odz = random.choice(valid_supports)
        x = min(max_x, max(0, ox + random.randint(0, max(0, odx - 1))))
        y = min(max_y, max(0, oy + random.randint(0, max(0, ody - 1))))
        return (x, y, oz + odz)

    return (random.randint(0, max_x), random.randint(0, max_y), 0)


def get_random_neighbor(state: State, valid_only: bool = False, max_attempts: int = 50) -> State:
    """Terapkan satu langkah acak (swap, move, rotate, atau toggle) untuk menghasilkan neighbor"""
    pkg_ids = list(state.packages.keys())
    if not pkg_ids:
        return state.clone()

    in_ids = [p.package_id for p in state.packages_in_truck]

    for _ in range(max_attempts if valid_only else 1):
        move_type = random.choice(["swap", "move", "rotate", "toggle"]) if in_ids else "toggle"

        if move_type == "swap" and len(pkg_ids) >= 2:
            id1 = random.choice(in_ids)
            id2 = random.choice([k for k in pkg_ids if k != id1])
            candidate = swap_packages(state, id1, id2)
        elif move_type == "move":
            pid = random.choice(in_ids)
            candidate = move_package_coordinate(state, pid, _sample_supported_coord(state, pid))
        elif move_type == "rotate":
            pid = random.choice(in_ids)
            candidate = rotate_package(state, pid, random.randint(0, 5))
        else:
            pid = random.choice(pkg_ids)
            if state.placements[pid].in_truck:
                candidate = toggle_in_truck(state, pid, False)
            else:
                candidate = toggle_in_truck(state, pid, True, _sample_supported_coord(state, pid))

        if not valid_only or is_valid_state(candidate)[0]:
            return candidate

    return state.clone()


def generate_neighbors(state: State, sample_size: int = 30, valid_only: bool = False) -> List[State]:
    """Bangkitkan daftar state tetangga yang berbeda dari state saat ini"""
    neighbors = [get_random_neighbor(state, valid_only=valid_only) for _ in range(sample_size)]
    return [n for n in neighbors if n.placements != state.placements]


def generate_initial_state(
    truck: Truck,
    packages: Dict[str, Package],
    random_strategy: str = "valid_floor",
) -> State:
    """Bangkitkan initial state secara acak ('valid_floor' atau 'pure_random')"""
    state = State(truck=truck, packages=packages)
    pkg_list = list(packages.values())
    random.shuffle(pkg_list)

    if random_strategy == "pure_random":
        for pkg in pkg_list:
            rot = random.randint(0, 5)
            dx, dy, dz = pkg.get_rotated_dimensions(rot)
            pos = (
                random.randint(0, max(0, truck.w - dx)),
                random.randint(0, max(0, truck.l - dy)),
                random.randint(0, max(0, truck.h - dz)),
            )
            state.placements[pkg.id] = Placement(pkg.id, pos, rot, random.choice([True, False]))
        return state

    for pkg in pkg_list:
        if state.total_weight_in_truck + pkg.weight > truck.max_capacity:
            continue
        rot = random.randint(0, 5)
        dx, dy, dz = pkg.get_rotated_dimensions(rot)
        if dx > truck.w or dy > truck.l or dz > truck.h:
            continue
        candidates = [
            (x, y, 0)
            for x in range(0, truck.w - dx + 1, max(1, dx))
            for y in range(0, truck.l - dy + 1, max(1, dy))
        ]
        random.shuffle(candidates)
        for pos in candidates:
            state.placements[pkg.id] = Placement(pkg.id, pos, rot, True)
            if is_valid_state(state)[0]:
                break
            state.placements[pkg.id] = Placement(pkg.id, in_truck=False)

    return state
