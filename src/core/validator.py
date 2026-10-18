from __future__ import annotations
from typing import List, Tuple
from src.core.models import State


def _xy_overlap(b1: Tuple[int, ...], b2: Tuple[int, ...]) -> bool:
    """Memeriksa apakah dua paket beririsan pada bidang XY"""
    x1, y1, _, dx1, dy1, _ = b1
    x2, y2, _, dx2, dy2, _ = b2
    return max(x1, x2) < min(x1 + dx1, x2 + dx2) and max(y1, y2) < min(y1 + dy1, y2 + dy2)


def _placed_boxes(state: State) -> List[Tuple[str, Tuple[int, int, int, int, int, int]]]:
    """Mengambil daftar (package_id, bounding_box) untuk semua paket di dalam truk"""
    return [(p.package_id, state.get_bounding_box(p.package_id)) for p in state.packages_in_truck]


def check_boundary_violations(state: State) -> List[str]:
    """Memeriksa apakah ada paket yang keluar dari batas dimensi kontainer truk"""
    truck = state.truck
    violations: List[str] = []
    for pid, (x, y, z, dx, dy, dz) in _placed_boxes(state):
        if x < 0 or y < 0 or z < 0:
            violations.append(f"Negative coordinate: {pid} at ({x}, {y}, {z})")
        if x + dx > truck.w or y + dy > truck.l or z + dz > truck.h:
            violations.append(f"Boundary exceeded: {pid} ends at ({x+dx}, {y+dy}, {z+dz})")
    return violations


def check_overlap_violations(state: State) -> List[str]:
    """Memeriksa apakah ada dua paket di dalam truk yang saling bertabrakan di ruang 3D"""
    boxes = _placed_boxes(state)
    violations: List[str] = []
    for i, (id1, b1) in enumerate(boxes):
        z1, dz1 = b1[2], b1[5]
        for id2, b2 in boxes[i + 1 :]:
            z2, dz2 = b2[2], b2[5]
            if _xy_overlap(b1, b2) and max(z1, z2) < min(z1 + dz1, z2 + dz2):
                violations.append(f"Packages '{id1}' and '{id2}' overlap in 3D")
    return violations


def check_floating_violations(state: State) -> List[str]:
    """Memeriksa apakah ada paket yang melayang tanpa penopang di bawahnya"""
    boxes = _placed_boxes(state)
    violations: List[str] = []
    for pid, box in boxes:
        z = box[2]
        if z == 0:
            continue
        supported = any(
            oid != pid and obox[2] + obox[5] == z and _xy_overlap(box, obox)
            for oid, obox in boxes
        )
        if not supported:
            violations.append(f"Package '{pid}' is floating at z={z}")
    return violations


def check_fragile_violations(state: State) -> List[str]:
    """Memeriksa apakah ada paket fragile yang ditumpuk oleh paket lain di atasnya"""
    boxes = _placed_boxes(state)
    violations: List[str] = []
    for oid, obox in boxes:
        if not state.packages[oid].is_fragile:
            continue
        top_z = obox[2] + obox[5]
        for pid, box in boxes:
            if pid != oid and box[2] == top_z and _xy_overlap(box, obox):
                violations.append(f"Fragile package '{oid}' has '{pid}' on top")
    return violations


def check_capacity_violations(state: State) -> List[str]:
    """Memeriksa apakah total berat paket melebihi kapasitas maksimum truk"""
    if state.total_weight_in_truck > state.truck.max_capacity:
        return [f"Total weight ({state.total_weight_in_truck:.1f}) exceeds truck capacity ({state.truck.max_capacity:.1f})"]
    return []


def is_valid_state(state: State) -> Tuple[bool, List[str]]:
    """Menjalankan seluruh validasi aturan 3D dan mengembalikan status valid beserta daftar pelanggaran"""
    violations = (
        check_boundary_violations(state)
        + check_overlap_violations(state)
        + check_floating_violations(state)
        + check_fragile_violations(state)
        + check_capacity_violations(state)
    )
    return len(violations) == 0, violations
