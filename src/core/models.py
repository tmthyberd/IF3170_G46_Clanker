from __future__ import annotations
from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, List, Optional, Tuple, Union

# Orientasi ortogonal 3D (0..5)
ORIENTATION_MAP = [
    {"w": "x", "l": "y", "h": "z"},  # 0: (w, l, h)
    {"w": "x", "l": "z", "h": "y"},  # 1: (w, h, l)
    {"w": "y", "l": "x", "h": "z"},  # 2: (l, w, h)
    {"w": "y", "l": "z", "h": "x"},  # 3: (l, h, w)
    {"w": "z", "l": "x", "h": "y"},  # 4: (h, w, l)
    {"w": "z", "l": "y", "h": "x"},  # 5: (h, l, w)
]

ORIENTATION_NAMES = [
    "0: (X, Y, Z) - Default",
    "1: (X, Z, Y) - Rotated Z-X",
    "2: (Y, X, Z) - Rotated Z 90°",
    "3: (Y, Z, X) - Rotated Y 90°",
    "4: (Z, X, Y) - Rotated X 90°",
    "5: (Z, Y, Z) - Rotated X-Z",
]


@dataclass
class Package:
    """Merepresentasikan satu entitas paket barang"""
    id: str
    w: float
    l: float
    h: float
    value: float
    weight: float
    is_fragile: bool = False
    eta: float = 1.0
    orientation: int = 0

    def get_rotated_dimensions(self, orientation: Optional[int] = None) -> Tuple[float, float, float]:
        ori = int(self.orientation if orientation is None else orientation) % 6
        if ori == 0:
            return (self.w, self.l, self.h)
        elif ori == 1:
            return (self.w, self.h, self.l)
        elif ori == 2:
            return (self.l, self.w, self.h)
        elif ori == 3:
            return (self.l, self.h, self.w)
        elif ori == 4:
            return (self.h, self.w, self.l)
        elif ori == 5:
            return (self.h, self.l, self.w)

    def get_effective_dimensions(self, orientation: Optional[int] = None) -> Tuple[float, float, float]:
        return self.get_rotated_dimensions(orientation)

    @property
    def volume(self) -> float:
        return self.w * self.l * self.h

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "w": self.w,
            "l": self.l,
            "h": self.h,
            "weight": self.weight,
            "value": self.value,
            "is_fragile": self.is_fragile,
            "eta": self.eta,
            "orientation": self.orientation,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Package:
        pkg_id = str(d.get("id") or d.get("name") or "Pkg")
        dims = d.get("dimensions", d)
        w = float(dims.get("w", d.get("w", d.get("width", 1.0))))
        l = float(dims.get("l", d.get("l", d.get("length", 1.0))))
        h = float(dims.get("h", d.get("h", d.get("height", 1.0))))
        weight = float(d.get("weight", d.get("wt", 1.0)))
        value = float(d.get("value", d.get("val", 0.0)))
        is_fragile = bool(d.get("is_fragile", d.get("isFragile", d.get("fragile", False))))
        eta = float(d.get("eta", d.get("ETA", 1.0)))
        orientation = int(d.get("orientation", 0)) % 6
        return cls(
            id=pkg_id,
            w=w,
            l=l,
            h=h,
            value=value,
            weight=weight,
            is_fragile=is_fragile,
            eta=eta,
            orientation=orientation,
        )


@dataclass
class Truck:
    """
    Merepresentasikan kontainer truk beserta batas kapasitas berat
    """
    id: str = "Truck_1"
    w: float = 10.0
    l: float = 20.0
    h: float = 5.0
    max_capacity: float = 500.0

    @property
    def volume(self) -> float:
        return self.w * self.l * self.h

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "w": self.w,
            "l": self.l,
            "h": self.h,
            "max_capacity": self.max_capacity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], default_idx: int = 0) -> Truck:
        truck_id = str(data.get("id") or f"Truck_{default_idx + 1}")
        dims = data.get("dimensions", data)
        w = float(dims.get("w", data.get("w", data.get("width", 10.0))))
        l = float(dims.get("l", data.get("l", data.get("length", 20.0))))
        h = float(dims.get("h", data.get("h", data.get("height", 5.0))))
        max_cap = float(data.get("max_capacity", 500.0))
        return cls(id=truck_id, w=w, l=l, h=h, max_capacity=max_cap)


class TruckList(list):
    """Daftar truk yang juga mengekspos atribut truk pertama demi kompatibilitas kode single-truck."""
    @property
    def w(self) -> float:
        return self[0].w if self else 0.0

    @property
    def l(self) -> float:
        return self[0].l if self else 0.0

    @property
    def h(self) -> float:
        return self[0].h if self else 0.0

    @property
    def max_capacity(self) -> float:
        return self[0].max_capacity if self else 0.0

    @property
    def id(self) -> str:
        return self[0].id if self else ""

    @property
    def volume(self) -> float:
        return sum(t.volume for t in self)


class Placement:
    """Menyimpan posisi, orientasi, dan status penempatan paket (bisa multi-truk)."""
    def __init__(
        self,
        package_id_or_truck_id: Any = None,
        position: Optional[Tuple[float, float, float]] = None,
        orientation: int = 0,
        in_truck: Optional[bool] = None,
        truck_id: Optional[int] = None,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        package_id: str = "",
    ):
        # Deteksi gaya pemanggilan
        if isinstance(package_id_or_truck_id, str):
            self.package_id = package_id_or_truck_id
            self.orientation = int(orientation) % 6
            if position is not None:
                self.x = float(position[0])
                self.y = float(position[1])
                self.z = float(position[2])
            else:
                self.x, self.y, self.z = float(x), float(y), float(z)
            
            if truck_id is not None:
                self.truck_id = int(truck_id) if int(truck_id) >= 0 else None
            elif in_truck is not None:
                self.truck_id = 0 if in_truck else None
            else:
                self.truck_id = None
        else:
            # Gaya top-level: Placement(truck_id, x, y, z, orientation)
            t_id = truck_id if truck_id is not None else package_id_or_truck_id
            if t_id is not None and int(t_id) >= 0:
                self.truck_id = int(t_id)
            else:
                self.truck_id = None
            
            self.package_id = package_id
            if position is not None:
                self.x = float(position[0])
                self.y = float(position[1])
                self.z = float(position[2])
            else:
                self.x = float(x)
                self.y = float(y)
                self.z = float(z)
            self.orientation = int(orientation) % 6

            if in_truck is not None:
                if in_truck and self.truck_id is None:
                    self.truck_id = 0
                elif not in_truck:
                    self.truck_id = None

    @property
    def in_truck(self) -> bool:
        return self.truck_id is not None and self.truck_id >= 0

    @in_truck.setter
    def in_truck(self, val: bool):
        if val:
            if self.truck_id is None or self.truck_id < 0:
                self.truck_id = 0
        else:
            self.truck_id = None

    @property
    def is_packed(self) -> bool:
        return self.in_truck

    @property
    def position(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @position.setter
    def position(self, pos: Tuple[float, float, float]):
        self.x = float(pos[0])
        self.y = float(pos[1])
        self.z = float(pos[2])

    def copy(self) -> Placement:
        return Placement(
            package_id=self.package_id,
            truck_id=self.truck_id,
            x=self.x,
            y=self.y,
            z=self.z,
            orientation=self.orientation,
        )

    def clone(self) -> Placement:
        return self.copy()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "truck_id": self.truck_id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "orientation": self.orientation,
            "in_truck": self.in_truck,
            "position": [self.x, self.y, self.z],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Placement:
        pkg_id = str(data.get("package_id") or data.get("id") or "")
        truck_id = data.get("truck_id")
        in_truck = data.get("in_truck")
        pos = data.get("position")
        if pos is not None and len(pos) >= 3:
            x, y, z = float(pos[0]), float(pos[1]), float(pos[2])
        else:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
            z = float(data.get("z", 0.0))
        ori = int(data.get("orientation", 0)) % 6

        return cls(
            package_id=pkg_id,
            truck_id=truck_id,
            x=x,
            y=y,
            z=z,
            orientation=ori,
            in_truck=in_truck,
        )


class SolverState:
    """State lengkap penempatan seluruh paket di dalam dan di luar truk (mendukung multi-truk)."""
    def __init__(
        self,
        trucks: Optional[Union[List[Truck], Truck]] = None,
        packages: Optional[Dict[str, Package]] = None,
        placements: Optional[Dict[str, Placement]] = None
    ):
        if trucks is not None:
            if isinstance(trucks, list):
                self.trucks = list(trucks)
            else:
                self.trucks = [trucks]
        else:
            self.trucks = [Truck()]

        self.packages = dict(packages) if packages is not None else {}
        self.placements: Dict[str, Placement] = dict(placements) if placements is not None else {}

<<<<<<< HEAD

@dataclass
class State:
    """State lengkap penempatan seluruh paket di dalam dan di luar truk"""
    truck: Truck
    packages: Dict[str, Package]
    placements: Dict[str, Placement] = field(default_factory=dict)

    def __post_init__(self):
=======
        # Pastikan setiap paket memiliki data penempatan awal
>>>>>>> feat/sim-annealing
        for pkg_id in self.packages:
            if pkg_id not in self.placements:
                self.placements[pkg_id] = Placement(package_id=pkg_id, in_truck=False)
            elif not self.placements[pkg_id].package_id:
                self.placements[pkg_id].package_id = pkg_id

    @property
    def truck(self) -> Truck:
        return self.trucks[0]

    @truck.setter
    def truck(self, val: Truck):
        if self.trucks:
            self.trucks[0] = val
        else:
            self.trucks = [val]

    def get_package_dims(self, pkg_id: str) -> Tuple[float, float, float]:
        ori = self.placements[pkg_id].orientation
        return self.packages[pkg_id].get_rotated_dimensions(ori)

    def get_bounding_box(self, pkg_id: str) -> Tuple[float, float, float, float, float, float]:
        x, y, z = self.placements[pkg_id].position
        dx, dy, dz = self.get_package_dims(pkg_id)
        return x, y, z, dx, dy, dz

    @property
    def packages_in_truck(self) -> Generator[Placement, None, None]:
        for p in self.placements.values():
            if p.in_truck:
                yield p

    def packages_in_truck_id(self, truck_id: int) -> Generator[Placement, None, None]:
        for p in self.placements.values():
            if p.truck_id == truck_id:
                yield p

    @property
    def packages_outside_truck(self) -> Generator[Placement, None, None]:
        for p in self.placements.values():
            if not p.in_truck:
                yield p

    @property
    def signature(self) -> Tuple[str, int, float, float, float, int]:
        return tuple(sorted((k, v.truck_id, round(v.x, 4), round(v.y, 4), round(v.z, 4), v.orientation) for k, v in self.placements.items()))

    @property
    def total_weight_in_truck(self) -> float:
        return sum(self.packages[p.package_id].weight for p in self.packages_in_truck)

    def total_weight_in_truck_id(self, truck_id: int) -> float:
        return sum(self.packages[p.package_id].weight for p in self.packages_in_truck_id(truck_id))

    @property
    def total_value_in_truck(self) -> float:
        return sum(self.packages[p.package_id].value for p in self.packages_in_truck)

    def clone(self) -> SolverState:
        return SolverState(
            trucks=[Truck(**t.to_dict()) for t in self.trucks],
            packages=self.packages,
            placements={k: v.copy() for k, v in self.placements.items()},
        )

    def to_placements_dict(self) -> Dict[str, Placement]:
        return {k: v.copy() for k, v in self.placements.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "truck": asdict(self.trucks[0]) if len(self.trucks) == 1 else None,
            "trucks": [asdict(t) for t in self.trucks],
            "packages_in_truck": [
                {
                    **p.to_dict(),
                    "position": list(p.position),
                    "dimensions_effective": list(self.get_package_dims(p.package_id)),
                }
                for p in self.packages_in_truck
            ],
            "packages_outside_truck": [p.package_id for p in self.packages_outside_truck],
            "total_value": self.total_value_in_truck,
            "total_weight": self.total_weight_in_truck,
        }


@dataclass
class ProblemInstance:
    packages: List[Package] = field(default_factory=list)
    trucks: List[Truck] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trucks": [t.to_dict() for t in self.trucks],
            "packages": [p.to_dict() for p in self.packages],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProblemInstance:
        trucks = []
        raw_trucks = data.get("trucks")
        if raw_trucks is None and "truck" in data:
            raw_trucks = [data["truck"]]
        elif raw_trucks is None:
            raw_trucks = []

        for idx, t_data in enumerate(raw_trucks):
            trucks.append(Truck.from_dict(t_data, idx))

        if not trucks:
            trucks.append(Truck(id="Truck_1", w=10.0, l=20.0, h=5.0, max_capacity=500.0))

        packages = []
        raw_packages = data.get("packages") or data.get("cases") or []
        for p_data in raw_packages:
            packages.append(Package.from_dict(p_data))

        return cls(packages=packages, trucks=trucks)

    @classmethod
    def from_json(cls, json_str: str) -> ProblemInstance:
        return cls.from_dict(json.loads(json_str))
