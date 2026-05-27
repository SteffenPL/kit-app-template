from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt


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


class SoftCellSimulation:
    """Small overdamped cell-shell model used before moving kernels to Warp."""

    def __init__(self, parameters: SoftCellParameters | None = None):
        self.parameters = parameters or SoftCellParameters()
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
        self.positions = [offset + Vec3(0.0, 0.0, self.parameters.radius) for offset in self.rest_offsets]
        self.springs = self._build_springs()
        self.faces = self._build_faces()

    def step(self, dt: float) -> None:
        remaining = max(0.0, dt)
        while remaining > 0.0:
            sub_dt = min(remaining, self.parameters.max_step)
            self._step_once(sub_dt)
            remaining -= sub_dt

    def _step_once(self, dt: float) -> None:
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
            target = center + self.rest_offsets[index]
            forces[index] += (target - position) * self.parameters.shape_stiffness

            if position.z < 0.0:
                forces[index] += Vec3(0.0, 0.0, -position.z * self.parameters.plane_stiffness)

            # A tiny polarity cue makes the prototype visibly cell-like without
            # introducing an adhesion model yet.
            if self.rest_offsets[index].x > self.parameters.radius * 0.35:
                forces[index] += Vec3(self.parameters.migration_force, 0.0, 0.0)

        drag = max(self.parameters.drag, 1e-6)
        self.positions = [position + (force / drag) * dt for position, force in zip(self.positions, forces)]

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

