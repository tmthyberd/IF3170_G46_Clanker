from __future__ import annotations
from typing import Dict, List, Tuple
from src.core.models import SolverState


def _xy_overlap(b1: Tuple[float, ...], b2: Tuple[float, ...], eps: float = 1e-5) -> bool:
    """
    Memeriksa apakah dua paket beririsan pada bidang XY
    """
    x1, y1, _, dx1, dy1, _ = b1
    x2, y2, _, dx2, dy2, _ = b2
    overlap_x = min(x1 + dx1, x2 + dx2) - max(x1, x2)
    overlap_y = min(y1 + dy1, y2 + dy2) - max(y1, y2)
    return overlap_x > eps and overlap_y > eps



def _placed_boxes_by_truck(state: State) -> Dict[int, List[Tuple[str, Tuple[float, float, float, float, float, float]]]]:
    """
    Mengelompokkan paket di dalam truk berdasarkan indeks truknya
    """
    res: Dict[int, List[Tuple[str, Tuple[float, float, float, float, float, float]]]] = {
        i: [] for i in range(len(state.trucks))
    }
    for p in state.packages_in_truck:
        t_id = p.truck_id if p.truck_id is not None else 0
        if t_id not in res:
            res[t_id] = []
        res[t_id].append((p.package_id, state.get_bounding_box(p.package_id)))
    return res



def check_boundary_violations(state: State) -> List[str]:
    """
    Memeriksa apakah ada paket yang keluar dari batas dimensi kontainer truk
    """
    violations: List[str] = []
    boxes_by_truck = _placed_boxes_by_truck(state)

    for t_id, boxes in boxes_by_truck.items():
        if t_id < 0 or t_id >= len(state.trucks):
            for pid, _ in boxes:
                violations.append(f"Package '{pid}' assigned to invalid truck index {t_id}")
            continue

        truck = state.trucks[t_id]
        for pid, (x, y, z, dx, dy, dz) in boxes:
            if x < -1e-5 or y < -1e-5 or z < -1e-5:
                violations.append(f"Truck {t_id}: Negative coordinate for '{pid}' at ({x}, {y}, {z})")
            
            # Batas kontainer: Panjang X (l), Lebar Y (w), Tinggi Z (h)
            # Jika truk simetris w=l, keduanya sama.
            if x + dx > truck.l + 1e-5:
                violations.append(f"Truck {t_id}: Boundary exceeded along length for '{pid}' (x={x}, dx={dx}, L={truck.l})")
            if y + dy > truck.w + 1e-5:
                violations.append(f"Truck {t_id}: Boundary exceeded along width for '{pid}' (y={y}, dy={dy}, W={truck.w})")
            if z + dz > truck.h + 1e-5:
                violations.append(f"Truck {t_id}: Boundary exceeded along height for '{pid}' (z={z}, dz={dz}, H={truck.h})")

    return violations



def check_overlap_violations(state: State) -> List[str]:
    """
    Memeriksa apakah ada dua paket di dalam truk yang sama yang saling bertabrakan di ruang 3D
    """
    violations: List[str] = []
    boxes_by_truck = _placed_boxes_by_truck(state)

    for t_id, boxes in boxes_by_truck.items():
        for i, (id1, b1) in enumerate(boxes):
            z1, dz1 = b1[2], b1[5]
            for id2, b2 in boxes[i + 1 :]:
                z2, dz2 = b2[2], b2[5]
                overlap_z = min(z1 + dz1, z2 + dz2) - max(z1, z2)
                if _xy_overlap(b1, b2) and overlap_z > 1e-5:
                    violations.append(f"Truck {t_id}: Packages '{id1}' and '{id2}' overlap in 3D")

    return violations


def check_floating_violations(state: State) -> List[str]:
    """
    Memeriksa apakah ada paket yang melayang tanpa penopang di bawahnya di dalam truk yang sama
    """
    violations: List[str] = []
    boxes_by_truck = _placed_boxes_by_truck(state)

    for t_id, boxes in boxes_by_truck.items():
        for pid, box in boxes:
            z = box[2]
            if abs(z) < 1e-5:
                continue
            supported = any(
                oid != pid and abs(obox[2] + obox[5] - z) < 1e-4 and _xy_overlap(box, obox)
                for oid, obox in boxes
            )
            if not supported:
                violations.append(f"Truck {t_id}: Package '{pid}' is floating at z={z:.2f}")

    return violations


def check_fragile_violations(state: State) -> List[str]:
    """
    Memeriksa apakah ada paket fragile yang ditumpuk oleh paket lain di atasnya di dalam truk yang sama
    """
    violations: List[str] = []
    boxes_by_truck = _placed_boxes_by_truck(state)

    for t_id, boxes in boxes_by_truck.items():
        for oid, obox in boxes:
            if not state.packages[oid].is_fragile:
                continue
            top_z = obox[2] + obox[5]
            for pid, box in boxes:
                if pid != oid and abs(box[2] - top_z) < 1e-4 and _xy_overlap(box, obox):
                    violations.append(f"Truck {t_id}: Fragile package '{oid}' has '{pid}' on top")

    return violations


def check_capacity_violations(state: State) -> List[str]:
    """
    Memeriksa apakah total berat paket melebihi kapasitas maksimum masing-masing truk
    """
    violations: List[str] = []
    for t_id, truck in enumerate(state.trucks):
        w_in_truck = state.total_weight_in_truck_id(t_id)
        if w_in_truck > truck.max_capacity + 1e-5:
            violations.append(
                f"Truck {t_id} capacity exceeded: weight ({w_in_truck:.1f}) exceeds max capacity ({truck.max_capacity:.1f})"
            )
    return violations


def validate_state(state: State) -> Tuple[bool, List[str]]:
    """
    Menjalankan seluruh validasi aturan 3D dan mengembalikan status valid beserta daftar pelanggaran
    """
    violations = (
        check_boundary_violations(state)
        + check_overlap_violations(state)
        + check_floating_violations(state)
        + check_fragile_violations(state)
        + check_capacity_violations(state)
    )
    return len(violations) == 0, violations


def evaluate_state_metrics(state: State) -> Dict[str, Any]:
    """Merangkum status validitas, daftar pelanggaran, dan metrik penataan state"""
    is_valid, violations = is_valid_state(state)
    return {
        "is_valid": is_valid,
        "violations_count": len(violations),
        "violations": violations,
        "total_value": state.total_value_in_truck,
        "total_weight": state.total_weight_in_truck,
        "packages_in_truck_count": len(state.packages_in_truck),
        "packages_outside_count": len(state.packages_outside_truck),
    }
