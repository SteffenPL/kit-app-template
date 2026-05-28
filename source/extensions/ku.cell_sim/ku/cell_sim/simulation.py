from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from random import Random


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vec3":
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def length(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Vec3":
        length = self.length()
        if length <= 1e-12:
            return Vec3(0.0, 0.0, 0.0)
        return self / length

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class Spring:
    a: int
    b: int
    rest_length: float
    stiffness: float


@dataclass(frozen=True)
class SoftCellParameters:
    radius: float = 1.0
    lat_segments: int = 8
    lon_segments: int = 16
    spring_stiffness: float = 24.0
    shape_stiffness: float = 10.0
    plane_stiffness: float = 80.0
    drag: float = 18.0
    gravity: float = 1.4
    migration_force: float = 0.8
    max_step: float = 1.0 / 30.0


@dataclass(frozen=True)
class CellCultureParameters:
    contact_stiffness: float = 38.0
    contact_margin: float = 0.05


class SoftCellSimulation:
    """Small overdamped cell-shell model used before moving kernels to Warp."""

    def __init__(
        self,
        parameters: SoftCellParameters | None = None,
        origin: Vec3 | None = None,
        migration_direction: Vec3 | None = None,
        backend: str = "warp",
    ):
        self.parameters = parameters or SoftCellParameters()
        self.origin = origin or Vec3(0.0, 0.0, 0.0)
        self.migration_direction = (migration_direction or Vec3(1.0, 0.0, 0.0)).normalized()
        self.backend_mode = backend
        self.backend_name = "python"
        self.backend_error: str | None = None
        self._backend = None
        self.positions: list[Vec3] = []
        self.rest_offsets: list[Vec3] = []
        self.springs: list[Spring] = []
        self.faces: list[tuple[int, int, int]] = []
        self.reset()

    @property
    def center(self) -> Vec3:
        total = Vec3(0.0, 0.0, 0.0)
        for position in self.positions:
            total += position
        return total / len(self.positions)

    def reset(self) -> None:
        self.rest_offsets = self._build_sphere_offsets()
        center = self.origin + Vec3(0.0, 0.0, self.parameters.radius)
        self.positions = [offset + center for offset in self.rest_offsets]
        self.springs = self._build_springs()
        self.faces = self._build_faces()
        self._configure_backend()

    def step(self, dt: float, external_force: Vec3 | None = None) -> None:
        remaining = max(0.0, dt)
        external_force = external_force or Vec3(0.0, 0.0, 0.0)
        while remaining > 0.0:
            sub_dt = min(remaining, self.parameters.max_step)
            self._step_once(sub_dt, external_force)
            remaining -= sub_dt

    def _step_once(self, dt: float, external_force: Vec3) -> None:
        if self._backend is not None:
            try:
                self.positions = self._backend.step_once(dt, external_force)
                return
            except Exception as exc:
                self._backend = None
                self.backend_name = "python"
                self.backend_error = str(exc)

        self._step_once_python(dt, external_force)

    def _step_once_python(self, dt: float, external_force: Vec3) -> None:
        forces = [Vec3(0.0, 0.0, -self.parameters.gravity) for _ in self.positions]
        center = self.center

        for spring in self.springs:
            delta = self.positions[spring.b] - self.positions[spring.a]
            length = delta.length()
            if length <= 1e-12:
                continue
            force = delta.normalized() * (spring.stiffness * (length - spring.rest_length))
            forces[spring.a] += force
            forces[spring.b] -= force

        for index, position in enumerate(self.positions):
            forces[index] += external_force
            target = center + self.rest_offsets[index]
            forces[index] += (target - position) * self.parameters.shape_stiffness

            if position.z < 0.0:
                forces[index] += Vec3(0.0, 0.0, -position.z * self.parameters.plane_stiffness)

            # A tiny polarity cue makes the prototype visibly cell-like without
            # introducing an adhesion model yet.
            polarity = (
                self.rest_offsets[index].x * self.migration_direction.x
                + self.rest_offsets[index].y * self.migration_direction.y
                + self.rest_offsets[index].z * self.migration_direction.z
            )
            if polarity > self.parameters.radius * 0.35:
                forces[index] += self.migration_direction * self.parameters.migration_force

        drag = max(self.parameters.drag, 1e-6)
        self.positions = [position + (force / drag) * dt for position, force in zip(self.positions, forces)]

    def _configure_backend(self) -> None:
        self._backend = None
        self.backend_name = "python"
        self.backend_error = None

        if self.backend_mode == "python":
            return

        if self.backend_mode not in {"auto", "warp"}:
            raise ValueError(f"Unknown simulation backend: {self.backend_mode}")

        try:
            from .warp_backend import WarpSoftCellBackend

            self._backend = WarpSoftCellBackend(
                positions=self.positions,
                rest_offsets=self.rest_offsets,
                springs=self.springs,
                parameters=self.parameters,
                migration_direction=self.migration_direction,
            )
            self.backend_name = self._backend.name
        except Exception as exc:
            self._backend = None
            self.backend_name = "python"
            self.backend_error = str(exc)
            if self.backend_mode == "warp":
                raise RuntimeError(f"Failed to initialize Warp simulation backend: {exc}") from exc

    def _build_sphere_offsets(self) -> list[Vec3]:
        params = self.parameters
        offsets: list[Vec3] = []

        for lat in range(params.lat_segments + 1):
            theta = pi * lat / params.lat_segments
            z = params.radius * cos(theta)
            ring_radius = params.radius * sin(theta)
            for lon in range(params.lon_segments):
                phi = 2.0 * pi * lon / params.lon_segments
                offsets.append(Vec3(ring_radius * cos(phi), ring_radius * sin(phi), z))

        return offsets

    def _index(self, lat: int, lon: int) -> int:
        lon_wrapped = lon % self.parameters.lon_segments
        return lat * self.parameters.lon_segments + lon_wrapped

    def _build_springs(self) -> list[Spring]:
        params = self.parameters
        springs: list[Spring] = []
        seen: set[tuple[int, int]] = set()

        def add(a: int, b: int, stiffness: float) -> None:
            key = (min(a, b), max(a, b))
            if key in seen:
                return
            seen.add(key)
            rest_length = (self.rest_offsets[b] - self.rest_offsets[a]).length()
            springs.append(Spring(a, b, rest_length, stiffness))

        for lat in range(params.lat_segments + 1):
            for lon in range(params.lon_segments):
                current = self._index(lat, lon)
                add(current, self._index(lat, lon + 1), params.spring_stiffness)
                if lat < params.lat_segments:
                    add(current, self._index(lat + 1, lon), params.spring_stiffness)
                    add(current, self._index(lat + 1, lon + 1), params.spring_stiffness * 0.55)

        return springs

    def _build_faces(self) -> list[tuple[int, int, int]]:
        params = self.parameters
        faces: list[tuple[int, int, int]] = []

        for lat in range(params.lat_segments):
            for lon in range(params.lon_segments):
                a = self._index(lat, lon)
                b = self._index(lat, lon + 1)
                c = self._index(lat + 1, lon)
                d = self._index(lat + 1, lon + 1)
                faces.append((a, c, b))
                faces.append((b, c, d))

        return faces


@dataclass(frozen=True)
class CellStyle:
    cortex_color: tuple[float, float, float]
    nucleus_color: tuple[float, float, float]


@dataclass(frozen=True)
class CellInstance:
    name: str
    simulation: SoftCellSimulation
    style: CellStyle


class CellCultureSimulation:
    """Seeded multi-cell culture built from the single-cell scaffold."""

    def __init__(
        self,
        count: int = 16,
        seed: int = 11,
        backend: str = "warp",
        parameters: CellCultureParameters | None = None,
    ):
        self.count = min(max(count, 10), 20)
        self.seed = seed
        self.backend = backend
        self.parameters = parameters or CellCultureParameters()
        self.cells: list[CellInstance] = []
        self.backend_name = "python"
        self.backend_error: str | None = None
        self._backend = None
        self.reset()

    def reset(self) -> None:
        self.cells = []
        rng = Random(self.seed)
        palette = [
            CellStyle((0.08, 0.85, 0.76), (1.0, 0.18, 0.70)),
            CellStyle((0.28, 0.95, 0.34), (0.76, 0.30, 1.0)),
            CellStyle((0.12, 0.68, 1.0), (1.0, 0.35, 0.46)),
            CellStyle((0.96, 0.82, 0.20), (0.42, 0.65, 1.0)),
        ]

        origins = self._random_origins(rng)

        for index in range(self.count):
            radius = rng.uniform(0.46, 0.55)
            direction = Vec3(rng.uniform(0.65, 1.0), rng.uniform(-0.35, 0.35), 0.0).normalized()
            params = SoftCellParameters(
                radius=radius,
                lat_segments=8,
                lon_segments=16,
                spring_stiffness=26.0,
                shape_stiffness=12.0,
                plane_stiffness=90.0,
                drag=24.0,
                gravity=1.1,
                migration_force=0.22,
            )
            self.cells.append(
                CellInstance(
                    name=f"Cell_{index + 1:02d}",
                    simulation=SoftCellSimulation(
                        params,
                        origin=origins[index],
                        migration_direction=direction,
                        backend="python" if self.backend == "warp" else self.backend,
                    ),
                    style=palette[index % len(palette)],
                )
            )

        self._configure_backend()

    def step(self, dt: float) -> None:
        if self._backend is not None:
            try:
                cell_positions = self._backend.step(dt)
                self._apply_backend_positions(cell_positions)
                return
            except Exception as exc:
                self._backend = None
                self.backend_name = "python"
                self.backend_error = str(exc)

        self._step_python(dt)

    def _step_python(self, dt: float) -> None:
        external_forces = self._cell_contact_forces()
        for cell, force in zip(self.cells, external_forces):
            cell.simulation.step(dt, external_force=force)

    def _cell_contact_forces(self) -> list[Vec3]:
        forces = [Vec3(0.0, 0.0, 0.0) for _ in self.cells]
        for first_index in range(len(self.cells)):
            first = self.cells[first_index].simulation
            first_center = first.center
            for second_index in range(first_index + 1, len(self.cells)):
                second = self.cells[second_index].simulation
                second_center = second.center
                delta = first_center - second_center
                distance = delta.length()
                contact_distance = (
                    first.parameters.radius + second.parameters.radius + self.parameters.contact_margin
                )
                penetration = contact_distance - distance
                if penetration <= 0.0:
                    continue

                direction = delta.normalized() if distance > 1e-9 else Vec3(1.0, 0.0, 0.0)
                force = direction * (penetration * self.parameters.contact_stiffness)
                forces[first_index] += force
                forces[second_index] -= force

        return forces

    def _configure_backend(self) -> None:
        self._backend = None
        self.backend_name = "python"
        self.backend_error = None

        if self.backend == "python":
            return

        if self.backend not in {"auto", "warp"}:
            raise ValueError(f"Unknown culture simulation backend: {self.backend}")

        try:
            from .warp_backend import WarpCellCultureBackend

            self._backend = WarpCellCultureBackend(self.cells, self.parameters)
            self.backend_name = self._backend.name
        except Exception as exc:
            self._backend = None
            self.backend_name = "python"
            self.backend_error = str(exc)
            if self.backend == "warp":
                raise RuntimeError(f"Failed to initialize Warp culture backend: {exc}") from exc

    def _apply_backend_positions(self, cell_positions: list[list[Vec3]]) -> None:
        for cell, positions in zip(self.cells, cell_positions):
            cell.simulation.positions = positions

    def _random_origins(self, rng: Random) -> list[Vec3]:
        origins: list[Vec3] = []
        x_radius = 3.0
        y_radius = 1.9
        min_distance = 0.95
        max_attempts = 2000

        while len(origins) < self.count and max_attempts > 0:
            max_attempts -= 1
            x = rng.uniform(-x_radius, x_radius)
            y = rng.uniform(-y_radius, y_radius)
            if (x / x_radius) ** 2 + (y / y_radius) ** 2 > 1.0:
                continue

            candidate = Vec3(x, y, 0.0)
            if all((candidate - origin).length() >= min_distance for origin in origins):
                origins.append(candidate)

        if len(origins) < self.count:
            origins.extend(self._fallback_origins(rng, self.count - len(origins)))

        return origins

    def _fallback_origins(self, rng: Random, remaining: int) -> list[Vec3]:
        columns = 5
        spacing = 1.05
        rows = (remaining + columns - 1) // columns
        x_origin = -((columns - 1) * spacing) / 2.0
        y_origin = -((rows - 1) * spacing) / 2.0

        origins: list[Vec3] = []
        for index in range(remaining):
            row = index // columns
            column = index % columns
            origins.append(
                Vec3(
                    x_origin + column * spacing + rng.uniform(-0.12, 0.12),
                    y_origin + row * spacing + rng.uniform(-0.12, 0.12),
                    0.0,
                )
            )
        return origins
