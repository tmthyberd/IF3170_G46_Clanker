from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

# 6 orientasi rotasi 3D ortogonal untuk paket (w, l, h) ke (dx, dy, dz)
ORIENTATION_MAP = [
    {"w": "x", "l": "y", "h": "z"},  # 0: (w, l, h)
    {"w": "x", "l": "z", "h": "y"},  # 1: (w, h, l)
    {"w": "y", "l": "x", "h": "z"},  # 2: (l, w, h)
    {"w": "y", "l": "z", "h": "x"},  # 3: (l, h, w)
    {"w": "z", "l": "x", "h": "y"},  # 4: (h, w, l)
    {"w": "z", "l": "y", "h": "x"},  # 5: (h, l, w)
]


@dataclass(frozen=True)
class Package:
    """Merepresentasikan satu entitas paket barang"""
    id: str
    w: int
    l: int
    h: int
    value: float
    weight: float
    is_fragile: bool = False
    eta: int = 1

    def get_rotated_dimensions(self, orientation: int) -> Tuple[int, int, int]:
        """Mengembalikan dimensi (dx, dy, dz) sesuai indeks orientasi (0..5)"""
        w, l, h = self.w, self.l, self.h
        return ((w, l, h), (w, h, l), (l, w, h), (l, h, w), (h, w, l), (h, l, w))[orientation % 6]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Package:
        dims = d.get("dimensions", d)
        return cls(
            id=str(d["id"]),
            w=int(dims.get("w", 1)),
            l=int(dims.get("l", 1)),
            h=int(dims.get("h", 1)),
            value=float(d.get("value", 0.0)),
            weight=float(d.get("weight", 0.0)),
            is_fragile=bool(d.get("is_fragile", False)),
            eta=int(d.get("eta", 1)),
        )


@dataclass(frozen=True)
class Truck:
    """Merepresentasikan kontainer truk beserta batas kapasitas berat"""
    w: int
    l: int
    h: int
    max_capacity: float

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Truck:
        dims = d.get("dimensions", d)
        return cls(
            w=int(dims.get("w", 10)),
            l=int(dims.get("l", 20)),
            h=int(dims.get("h", 5)),
            max_capacity=float(d.get("max_capacity", 500.0)),
        )


@dataclass
class Placement:
    """Menyimpan posisi, orientasi, dan status penempatan paket di dalam truk"""
    package_id: str
    position: Tuple[int, int, int] = (0, 0, 0)
    orientation: int = 0
    in_truck: bool = False

    def copy(self) -> Placement:
        return Placement(self.package_id, self.position, self.orientation, self.in_truck)


@dataclass
class State:
    """State lengkap penempatan seluruh paket di dalam dan di luar truk"""
    truck: Truck
    packages: Dict[str, Package]
    placements: Dict[str, Placement] = field(default_factory=dict)

    def __post_init__(self):
        # Pastikan setiap paket memiliki data penempatan awal
        for pkg_id in self.packages:
            if pkg_id not in self.placements:
                self.placements[pkg_id] = Placement(package_id=pkg_id, in_truck=False)

    def get_package_dims(self, pkg_id: str) -> Tuple[int, int, int]:
        return self.packages[pkg_id].get_rotated_dimensions(self.placements[pkg_id].orientation)

    def get_bounding_box(self, pkg_id: str) -> Tuple[int, int, int, int, int, int]:
        x, y, z = self.placements[pkg_id].position
        dx, dy, dz = self.get_package_dims(pkg_id)
        return x, y, z, dx, dy, dz

    @property
    def packages_in_truck(self) -> List[Placement]:
        return [p for p in self.placements.values() if p.in_truck]

    @property
    def packages_outside_truck(self) -> List[Placement]:
        return [p for p in self.placements.values() if not p.in_truck]

    @property
    def total_weight_in_truck(self) -> float:
        return sum(self.packages[p.package_id].weight for p in self.packages_in_truck)

    @property
    def total_value_in_truck(self) -> float:
        return sum(self.packages[p.package_id].value for p in self.packages_in_truck)

    def clone(self) -> State:
        return State(
            truck=self.truck,
            packages=self.packages,
            placements={k: v.copy() for k, v in self.placements.items()},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "truck": asdict(self.truck),
            "packages_in_truck": [
                {
                    **asdict(p),
                    "position": list(p.position),
                    "dimensions_effective": list(self.get_package_dims(p.package_id)),
                }
                for p in self.packages_in_truck
            ],
            "packages_outside_truck": [p.package_id for p in self.packages_outside_truck],
            "total_value": self.total_value_in_truck,
            "total_weight": self.total_weight_in_truck,
        }
