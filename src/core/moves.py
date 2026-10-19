from __future__ import annotations
import random
from typing import Dict, List, Optional, Set, Tuple, Union
from src.core.models import Package, Placement, SolverState, Truck
from src.core.validator import validate_state


# Tukar atribut penempatan antara dua paket, dalam truk yang sama atau ke truk yang lain 
def swap_packages(state: SolverState, pkg_id1: str, pkg_id2: str) -> SolverState:
    new_state = state.clone()
    p1, p2 = new_state.placements[pkg_id1], new_state.placements[pkg_id2]
    p1.truck_id, p1.x, p1.y, p1.z, p1.orientation, p2.truck_id, p2.x, p2.y, p2.z, p2.orientation = (
        p2.truck_id, p2.x, p2.y, p2.z, p2.orientation, p1.truck_id, p1.x, p1.y, p1.z, p1.orientation
    )

    return new_state


# Memindahkan paket ke setiap koordinat (x, y, z) baru yang valid di dalam truk atau ke truk yang lain
def move_package_coordinate(state: SolverState,
    pkg_id: str,
    new_coord: Tuple[float, float, float],
    truck_id: Optional[int] = None
) -> SolverState:
    new_state = state.clone()
    p = new_state.placements[pkg_id]
    p.position = (float(new_coord[0]), float(new_coord[1]), float(new_coord[2]))

    if truck_id is not None:
        p.truck_id = int(truck_id)
    elif p.truck_id is None:
        p.truck_id = 0
        
    return new_state


# Putar orientasi paket 90 derajat
def rotate_package(state: SolverState, pkg_id: str, new_orientation: Optional[int] = None) -> SolverState:
    new_state = state.clone()
    p = new_state.placements[pkg_id]
    p.orientation = new_orientation % 6 if new_orientation is not None else (p.orientation + 1) % 6
    return new_state


# Helper memasukkan atau mengeluarkan paket ke truk tertentu
def toggle_in_truck(
    state: SolverState,
    pkg_id: str,
    in_truck: bool,
    coord: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    truck_id: int = 0,
) -> SolverState:
    new_state = state.clone()
    p = new_state.placements[pkg_id]
    if in_truck:
        p.truck_id = max(0, min(len(state.trucks) - 1, truck_id)) # Bound checks
        p.position = coord
    else:
        p.truck_id = None
    return new_state


# Ambil semua koordinat valid yang bisa jadi tempat peletakkan package lain
def get_all_valid_move(state: SolverState, pkg_id: str, truck_idx: int) -> Generator[Tuple[float, float, float], None, None]:
    truck = state.trucks[truck_idx]
    dx, dy, dz = state.get_package_dims(pkg_id)
    found = False

   # Titik-titik berdampingan dan bertumpuk di atas paket lain dalam truk yang sama
    for p in state.packages_in_truck_id(truck_idx):
        if p.package_id == pkg_id:
            continue

        found = True
        ox, oy, oz, odx, ody, odz = state.get_bounding_box(p.package_id)
        is_fragile = state.packages[p.package_id].is_fragile

        # Menempel pada sumbu-X milik paket ini
        if ox + odx + dx <= truck.l + 1e-4:
            yield (float(ox + odx), float(oy), 0.0)
            yield (float(ox + odx), 0.0, 0.0)

        # Menempel pada sumbu-Y milik paket ini
        if oy + ody + dy <= truck.w + 1e-4:
            yield (float(ox), float(oy + ody), 0.0)
            yield (0.0, float(oy + ody), 0.0)

        # Jika non-fragile, menempel pada sumbu-Z milik paket ini
        if not is_fragile and oz + odz + dz <= truck.h + 1e-4:
            top_z = float(oz + odz)
            yield (float(ox), float(oy), top_z)

            if ox + dx <= truck.l + 1e-4 and oy + dy <= truck.w + 1e-4:
                yield (float(ox), float(oy), top_z)

    if not found:
        yield (0.0, 0.0, 0.0)


# Iterasikan seluru suksesor berdasarkan operasi swap, rotate, dan move (bisa antar truk)
def get_all_successors(state: SolverState, valid_only: bool = True) -> Generator[SolverState, None, None]:
    tracker: Set[Tuple[Any, ...]] = set()
    tracker.add(state.signature)

    pkg_ids = list(state.packages.keys())
    num_trucks = len(state.trucks)

    # 1. Operator Swap
    for i in range(len(pkg_ids)):
        for j in range(i+1, len(pkg_ids)):
            cand = swap_packages(state, pkg_ids[i], pkg_ids[j])
            signature = cand.signature
            if signature not in tracker:
                tracker.add(signature)
                if not valid_only or validate_state(cand)[0]:
                    yield cand

    # 2. Operator Rotate
    for p in state.packages_in_truck:
        for ori in range(6):
            if ori == p.orientation:
                continue

            cand = rotate_package(state, p.package_id, ori)
            signature = cand.signature
            if signature not in tracker:
                tracker.add(signature)
                if not valid_only or validate_state(cand)[0]:
                    yield cand

    # 3. Operator Move
    for pid in pkg_ids:
        placement = state.placements[pid]

        # 3.1. Mengeluarkan paket dari truk
        if placement.in_truck:
            cand = toggle_in_truck(state, pid, False)
            signature = cand.signature
            if signature not in tracker:
                tracker.add(signature)
                if not valid_only or validate_state(cand)[0]:
                    yield cand

        # 3.2. Mencoba kombinasi truk yang berbeda
        for t_idx in range(num_trucks):
            for coord in get_all_valid_move(state, pid, t_idx):
                if placement.in_truck and placement.truck_id == t_idx and (placement.x, placement.y, placement.z) == coord:
                    continue

                cand = move_package_coordinate(state, pid, coord, t_idx)
                signature = cand.signature
                if signature not in tracker:
                    tracker.add(signature)
                    if not valid_only or validate_state(cand)[0]:
                        yield cand



# Ambil suksesor acak dengan memilih satu operasi Swap, Move, atau Rotate. Jika tidak bisa menemukan suksesor maka akan return state itu tersendiri
def get_random_successor(state: SolverState, valid_only: bool = True, max_attempts: int = 50) -> SolverState:
    pkg_ids = list(state.packages.keys())
    if len(pkg_ids) == 0:
        return state.clone()

    in_ids = [p.package_id for p in state.packages_in_truck]
    num_trucks = len(state.trucks)

    for _ in range(max_attempts if valid_only else 1):
        move_type = random.choice(["swap", "move_in_truck", "move_between_truck", "rotate"]) if len(in_ids) > 0 else "move_between_truck"

        if move_type == "swap" and len(pkg_ids) >= 2:
            id1 = random.choice(in_ids)
            id2 = random.choice([k for k in pkg_ids if k != id1])
            candidate = swap_packages(state, id1, id2)

        elif move_type == "move_in_truck":
            pid = random.choice(in_ids)

            target_truck = random.randint(0, num_trucks - 1)
            coords = list(get_all_valid_move(state, pid, target_truck)) 
            while len(coords) == 0:
                target_truck = random.randint(0, num_trucks - 1)
                coords = list(get_all_valid_move(state, pid, target_truck)) 

            coord = random.choice(coords)
            candidate = move_package_coordinate(state, pid, new_coord=coord, truck_id=target_truck)

        elif move_type == "move_between_truck":
            pid = random.choice(pkg_ids)
            if state.placements[pid].in_truck:
                candidate = toggle_in_truck(state, pid, False)
            else:
                target_truck = random.randint(0, num_trucks - 1)
                coords = list(get_all_valid_move(state, pid, target_truck)) 
                while len(coords) == 0:
                    target_truck = random.randint(0, num_trucks - 1)
                    coords = list(get_all_valid_move(state, pid, target_truck)) 

                coord = random.choice(coords)
                candidate = toggle_in_truck(state, pid, True, coord=coord, truck_id=target_truck)
        
        else: # move_type == "rotate"
            pid = random.choice(in_ids)
            candidate = rotate_package(state, pid, random.randint(0, 5))

        if not valid_only or validate_state(candidate)[0]:
            return candidate

    return state.clone()


# Initial state, semua package berada di luar truk atau randomized initial state jika dibutuhkan
def generate_initial_state(
    trucks: Union[List[Truck], Truck],
    packages: Union[Dict[str, Package], List[Package]],
    randomize: bool = False
) -> SolverState:

    truck_list = trucks if isinstance(trucks, list) else [trucks]
    
    if isinstance(packages, dict):
        pkg_list = list(packages.values())
        pkg_dict = packages
    else:
        pkg_list = list(packages)
        pkg_dict = {p.id: p for p in packages}

    state = SolverState(trucks=truck_list, packages=pkg_dict)

    if not randomize:
        for pkg in pkg_list:
            state.placements[pkg.id] = Placement(package_id=pkg.id, in_truck=False)
        return state

    shuffled_packages = pkg_list.copy()
    random.shuffle(shuffled_packages)

    truck_weights = {i: 0.0 for i in range(len(truck_list))}

    for pkg in shuffled_packages:
        placed = False
        truck_indices = list(range(len(truck_list)))
        random.shuffle(truck_indices)

        for t_idx in truck_indices:
            truck = truck_list[t_idx]
            
            if truck_weights[t_idx] + pkg.weight > truck.max_capacity:
                continue

            candidate_positions = [(0.0, 0.0, 0.0)]
            existing_boxes = [
                (p.package_id, state.get_bounding_box(p.package_id)) 
                for p in state.packages_in_truck_id(t_idx)
            ]
            
            for _, box in existing_boxes:
                ex, ey, ez, edx, edy, edz = box
                candidate_positions.append((ex + edx, ey, ez))
                candidate_positions.append((ex, ey + edy, ez))
                candidate_positions.append((ex, ey, ez + edz))

            orientations = list(range(6))
            random.shuffle(orientations)
            random.shuffle(candidate_positions)

            found_pos = None
            chosen_ori = 0

            for ori in orientations:
                dx, dy, dz = pkg.get_rotated_dimensions(ori)
                for (x, y, z) in candidate_positions:
                    if x + dx > truck.l + 1e-5 or y + dy > truck.w + 1e-5 or z + dz > truck.h + 1e-5:
                        continue

                    b1 = (x, y, z, dx, dy, dz)
                    valid = True

                    for other_id, b2 in existing_boxes:
                        overlap_x = min(x + dx, b2[0] + b2[3]) - max(x, b2[0])
                        overlap_y = min(y + dy, b2[1] + b2[4]) - max(y, b2[1])

                        if overlap_x > 1e-5 and overlap_y > 1e-5:
                            z1, dz1 = z, dz
                            z2, dz2 = b2[2], b2[5]
                            overlap_z = min(z1 + dz1, z2 + dz2) - max(z1, z2)
                            if overlap_z > 1e-5:
                                valid = False
                                break

                    if not valid:
                        continue

                    if z > 1e-5:
                        supported = False
                        for _, b2 in existing_boxes:
                            overlap_x = min(x + dx, b2[0] + b2[3]) - max(x, b2[0])
                            overlap_y = min(y + dy, b2[1] + b2[4]) - max(y, b2[1])
                            if overlap_x > 1e-5 and overlap_y > 1e-5:
                                if abs((b2[2] + b2[5]) - z) < 1e-4:
                                    supported = True
                                    break

                        if not supported:
                            valid = False

                    if valid:
                        for other_id, b2 in existing_boxes:
                            if state.packages[other_id].is_fragile:
                                top_z = b2[2] + b2[5]
                                overlap_x = min(x + dx, b2[0] + b2[3]) - max(x, b2[0])
                                overlap_y = min(y + dy, b2[1] + b2[4]) - max(y, b2[1])
                                if overlap_x > 1e-5 and overlap_y > 1e-5 and abs(z - top_z) < 1e-4:
                                    valid = False
                                    break

                    if valid:
                        found_pos = (x, y, z)
                        chosen_ori = ori
                        break

                if found_pos:
                    break

            if found_pos:
                x, y, z = found_pos
                state.placements[pkg.id] = Placement(
                    package_id=pkg.id,
                    truck_id=t_idx,
                    x=x, y=y, z=z,
                    orientation=chosen_ori
                )

                truck_weights[t_idx] += pkg.weight
                placed = True
                break

        if not placed:
            state.placements[pkg.id] = Placement(package_id=pkg.id, in_truck=False)

    return state
