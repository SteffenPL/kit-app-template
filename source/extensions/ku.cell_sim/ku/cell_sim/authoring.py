from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

from .simulation import Vec3


@dataclass(frozen=True)
class MaterialSpec:
    name: str
    color: tuple[float, float, float]
    opacity: float = 1.0


@dataclass(frozen=True)
class EndothelialCellSpec:
    name: str
    center: Vec3
    vessel_axis: Vec3
    circumferential_axis: Vec3
    radial_axis: Vec3
    cell_scale: Vec3
    nucleus_center: Vec3
    nucleus_scale: Vec3
    cortex_material: str
    nucleus_material: str


@dataclass(frozen=True)
class VesselSceneSpec:
    name: str
    radius: float
    length: float
    cell_count: int
    cells_per_ring: int
    rings: int
    cells: tuple[EndothelialCellSpec, ...]
    materials: tuple[MaterialSpec, ...]


DEFAULT_VESSEL_MATERIALS = (
    MaterialSpec("endothelial_cortex", (0.12, 0.62, 0.55), 0.72),
    MaterialSpec("endothelial_cortex_alt", (0.18, 0.48, 0.78), 0.70),
    MaterialSpec("endothelial_nucleus", (0.08, 0.13, 0.46), 1.0),
    MaterialSpec("lumen_marker", (0.68, 0.88, 0.95), 0.18),
    MaterialSpec("basement_membrane", (0.82, 0.76, 0.56), 0.28),
)


def build_endothelium_vessel_scene(
    cell_count: int = 420,
    cells_per_ring: int = 14,
    radius: float = 2.0,
    length: float = 12.0,
) -> VesselSceneSpec:
    """Build a deterministic endothelial tube layout around a vessel lumen."""

    if cell_count <= 0:
        raise ValueError("cell_count must be positive")
    if cells_per_ring <= 2:
        raise ValueError("cells_per_ring must be greater than 2")
    if radius <= 0.0:
        raise ValueError("radius must be positive")
    if length <= 0.0:
        raise ValueError("length must be positive")

    rings = (cell_count + cells_per_ring - 1) // cells_per_ring
    axis = Vec3(1.0, 0.0, 0.0)
    cells: list[EndothelialCellSpec] = []
    axial_spacing = length / max(rings, 1)
    cell_scale_factor = 2.5
    cell_length = min(axial_spacing * 0.78, 0.42) * cell_scale_factor
    cell_width = min((2.0 * pi * radius / cells_per_ring) * 0.46, 0.46) * cell_scale_factor
    cell_thickness = 0.22 * cell_scale_factor

    for index in range(cell_count):
        ring = index // cells_per_ring
        slot = index % cells_per_ring
        stagger = 0.5 if ring % 2 else 0.0
        angle = 2.0 * pi * (slot + stagger) / cells_per_ring
        x = -length * 0.5 + axial_spacing * (ring + 0.5)
        radial = Vec3(0.0, cos(angle), sin(angle))
        circumferential = Vec3(0.0, -sin(angle), cos(angle))
        center = Vec3(x, radius * radial.y, radius * radial.z)
        nucleus_center = center - radial * 0.035
        cortex_material = "endothelial_cortex_alt" if (ring + slot) % 3 == 0 else "endothelial_cortex"

        cells.append(
            EndothelialCellSpec(
                name=f"EndothelialCell_{index + 1:03d}",
                center=center,
                vessel_axis=axis,
                circumferential_axis=circumferential,
                radial_axis=radial,
                cell_scale=Vec3(cell_length, cell_width, cell_thickness),
                nucleus_center=nucleus_center,
                nucleus_scale=Vec3(cell_length * 0.42, cell_width * 0.36, cell_thickness * 0.76),
                cortex_material=cortex_material,
                nucleus_material="endothelial_nucleus",
            )
        )

    return VesselSceneSpec(
        name="BloodVesselEndothelium",
        radius=radius,
        length=length,
        cell_count=cell_count,
        cells_per_ring=cells_per_ring,
        rings=rings,
        cells=tuple(cells),
        materials=DEFAULT_VESSEL_MATERIALS,
    )
