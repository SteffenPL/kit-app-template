from __future__ import annotations

import warp as wp

from .simulation import CellCultureParameters, CellInstance, SoftCellParameters, Spring, Vec3


@wp.kernel
def _clear_forces_and_sum_center(
    positions: wp.array(dtype=wp.vec3),
    forces: wp.array(dtype=wp.vec3),
    center_sum: wp.array(dtype=wp.vec3),
    gravity: float,
):
    tid = wp.tid()
    position = positions[tid]
    forces[tid] = wp.vec3(0.0, 0.0, -gravity)
    wp.atomic_add(center_sum, 0, position)


@wp.kernel
def _clear_forces_and_sum_cell_centers(
    positions: wp.array(dtype=wp.vec3),
    forces: wp.array(dtype=wp.vec3),
    cell_center_sums: wp.array(dtype=wp.vec3),
    particle_cell: wp.array(dtype=int),
    gravity_by_cell: wp.array(dtype=float),
):
    tid = wp.tid()
    cell_index = particle_cell[tid]
    position = positions[tid]
    forces[tid] = wp.vec3(0.0, 0.0, -gravity_by_cell[cell_index])
    wp.atomic_add(cell_center_sums, cell_index, position)


@wp.kernel
def _apply_springs(
    positions: wp.array(dtype=wp.vec3),
    spring_a: wp.array(dtype=int),
    spring_b: wp.array(dtype=int),
    spring_rest_lengths: wp.array(dtype=float),
    spring_stiffness: wp.array(dtype=float),
    forces: wp.array(dtype=wp.vec3),
):
    tid = wp.tid()
    a = spring_a[tid]
    b = spring_b[tid]

    delta = positions[b] - positions[a]
    length = wp.length(delta)
    if length <= 1.0e-12:
        return

    force = (delta / length) * (spring_stiffness[tid] * (length - spring_rest_lengths[tid]))
    wp.atomic_add(forces, a, force)
    wp.atomic_sub(forces, b, force)


@wp.kernel
def _apply_cell_center_contacts(
    cell_center_sums: wp.array(dtype=wp.vec3),
    cell_counts: wp.array(dtype=int),
    cell_radii: wp.array(dtype=float),
    cell_contact_forces: wp.array(dtype=wp.vec3),
    cell_count: int,
    contact_stiffness: float,
    contact_margin: float,
):
    tid = wp.tid()
    center = cell_center_sums[tid] / float(cell_counts[tid])
    force = wp.vec3(0.0, 0.0, 0.0)

    for other_index in range(cell_count):
        if other_index == tid:
            continue

        other_center = cell_center_sums[other_index] / float(cell_counts[other_index])
        delta = center - other_center
        distance = wp.length(delta)
        contact_distance = cell_radii[tid] + cell_radii[other_index] + contact_margin
        penetration = contact_distance - distance
        if penetration <= 0.0:
            continue

        direction = wp.vec3(1.0, 0.0, 0.0)
        if distance > 1.0e-9:
            direction = delta / distance
        force = force + direction * (penetration * contact_stiffness)

    cell_contact_forces[tid] = force


@wp.kernel
def _integrate_overdamped(
    positions: wp.array(dtype=wp.vec3),
    rest_offsets: wp.array(dtype=wp.vec3),
    forces: wp.array(dtype=wp.vec3),
    center_sum: wp.array(dtype=wp.vec3),
    migration_direction: wp.vec3,
    external_force: wp.vec3,
    node_count: int,
    radius: float,
    shape_stiffness: float,
    plane_stiffness: float,
    drag: float,
    migration_force: float,
    dt: float,
):
    tid = wp.tid()
    position = positions[tid]
    center = center_sum[0] / float(node_count)
    force = forces[tid]
    force = force + external_force

    target = center + rest_offsets[tid]
    force = force + (target - position) * shape_stiffness

    if position[2] < 0.0:
        force = force + wp.vec3(0.0, 0.0, -position[2] * plane_stiffness)

    polarity = wp.dot(rest_offsets[tid], migration_direction)
    if polarity > radius * 0.35:
        force = force + migration_direction * migration_force

    positions[tid] = position + (force / drag) * dt


@wp.kernel
def _integrate_culture_overdamped(
    positions: wp.array(dtype=wp.vec3),
    rest_offsets: wp.array(dtype=wp.vec3),
    particle_cell: wp.array(dtype=int),
    forces: wp.array(dtype=wp.vec3),
    cell_center_sums: wp.array(dtype=wp.vec3),
    cell_counts: wp.array(dtype=int),
    cell_contact_forces: wp.array(dtype=wp.vec3),
    migration_directions: wp.array(dtype=wp.vec3),
    cell_radii: wp.array(dtype=float),
    shape_stiffness_by_cell: wp.array(dtype=float),
    plane_stiffness_by_cell: wp.array(dtype=float),
    drag_by_cell: wp.array(dtype=float),
    migration_force_by_cell: wp.array(dtype=float),
    dt: float,
):
    tid = wp.tid()
    cell_index = particle_cell[tid]
    position = positions[tid]
    center = cell_center_sums[cell_index] / float(cell_counts[cell_index])
    force = forces[tid] + cell_contact_forces[cell_index]

    target = center + rest_offsets[tid]
    force = force + (target - position) * shape_stiffness_by_cell[cell_index]

    if position[2] < 0.0:
        force = force + wp.vec3(0.0, 0.0, -position[2] * plane_stiffness_by_cell[cell_index])

    migration_direction = migration_directions[cell_index]
    polarity = wp.dot(rest_offsets[tid], migration_direction)
    if polarity > cell_radii[cell_index] * 0.35:
        force = force + migration_direction * migration_force_by_cell[cell_index]

    positions[tid] = position + (force / drag_by_cell[cell_index]) * dt


class WarpSoftCellBackend:
    """Warp implementation of one overdamped soft-cell shell."""

    def __init__(
        self,
        positions: list[Vec3],
        rest_offsets: list[Vec3],
        springs: list[Spring],
        parameters: SoftCellParameters,
        migration_direction: Vec3,
        device: str | None = None,
    ):
        self._wp = wp
        self._parameters = parameters
        self._node_count = len(positions)
        self._spring_count = len(springs)
        self._device = self._select_device(device)
        self.name = f"warp:{self._device.alias if hasattr(self._device, 'alias') else self._device}"

        self._positions = wp.array([position.as_tuple() for position in positions], dtype=wp.vec3, device=self._device)
        self._rest_offsets = wp.array([offset.as_tuple() for offset in rest_offsets], dtype=wp.vec3, device=self._device)
        self._forces = wp.zeros(self._node_count, dtype=wp.vec3, device=self._device)
        self._center_sum = wp.zeros(1, dtype=wp.vec3, device=self._device)

        self._spring_a = wp.array([spring.a for spring in springs], dtype=int, device=self._device)
        self._spring_b = wp.array([spring.b for spring in springs], dtype=int, device=self._device)
        self._spring_rest_lengths = wp.array(
            [spring.rest_length for spring in springs],
            dtype=float,
            device=self._device,
        )
        self._spring_stiffness = wp.array([spring.stiffness for spring in springs], dtype=float, device=self._device)
        self._migration_direction = wp.vec3(*migration_direction.as_tuple())
        self._positions_host = None
        if self._device.is_cuda:
            self._positions_host = wp.zeros(self._node_count, dtype=wp.vec3, device="cpu")

    def step_once(self, dt: float, external_force: Vec3 | None = None) -> list[Vec3]:
        params = self._parameters
        drag = max(params.drag, 1.0e-6)
        external_force = external_force or Vec3(0.0, 0.0, 0.0)
        self._center_sum.zero_()

        wp.launch(
            kernel=_clear_forces_and_sum_center,
            dim=self._node_count,
            inputs=[self._positions, self._forces, self._center_sum, params.gravity],
            device=self._device,
        )
        wp.launch(
            kernel=_apply_springs,
            dim=self._spring_count,
            inputs=[
                self._positions,
                self._spring_a,
                self._spring_b,
                self._spring_rest_lengths,
                self._spring_stiffness,
                self._forces,
            ],
            device=self._device,
        )
        wp.launch(
            kernel=_integrate_overdamped,
            dim=self._node_count,
            inputs=[
                self._positions,
                self._rest_offsets,
                self._forces,
                self._center_sum,
                self._migration_direction,
                wp.vec3(*external_force.as_tuple()),
                self._node_count,
                params.radius,
                params.shape_stiffness,
                params.plane_stiffness,
                drag,
                params.migration_force,
                dt,
            ],
            device=self._device,
        )

        return self._read_positions()

    def _read_positions(self) -> list[Vec3]:
        if self._positions_host is not None:
            wp.copy(self._positions_host, self._positions)
            wp.synchronize_device(self._device)
            values = self._positions_host.numpy()
        else:
            values = self._positions.numpy()

        return [Vec3(float(value[0]), float(value[1]), float(value[2])) for value in values]

    def _select_device(self, device: str | None):
        if device is not None:
            return wp.get_device(device)
        if wp.is_cuda_available():
            return wp.get_device("cuda:0")
        return wp.get_device("cpu")


class WarpCellCultureBackend:
    """Warp implementation of a whole cell culture with center-radius contact."""

    def __init__(
        self,
        cells: list[CellInstance],
        parameters: CellCultureParameters,
        device: str | None = None,
    ):
        self._parameters = parameters
        self._cells = cells
        self._cell_count = len(cells)
        self._device = self._select_device(device)
        self.name = f"warp-culture:{self._device.alias if hasattr(self._device, 'alias') else self._device}"

        (
            positions,
            rest_offsets,
            particle_cell,
            cell_counts,
            spring_a,
            spring_b,
            spring_rest_lengths,
            spring_stiffness,
            cell_radii,
            shape_stiffness,
            plane_stiffness,
            drag,
            gravity,
            migration_force,
            migration_directions,
            self._cell_slices,
        ) = self._flatten_cells(cells)

        self._node_count = len(positions)
        self._spring_count = len(spring_a)
        self._max_step = min(cell.simulation.parameters.max_step for cell in cells)

        self._positions = wp.array(positions, dtype=wp.vec3, device=self._device)
        self._rest_offsets = wp.array(rest_offsets, dtype=wp.vec3, device=self._device)
        self._particle_cell = wp.array(particle_cell, dtype=int, device=self._device)
        self._forces = wp.zeros(self._node_count, dtype=wp.vec3, device=self._device)

        self._spring_a = wp.array(spring_a, dtype=int, device=self._device)
        self._spring_b = wp.array(spring_b, dtype=int, device=self._device)
        self._spring_rest_lengths = wp.array(spring_rest_lengths, dtype=float, device=self._device)
        self._spring_stiffness = wp.array(spring_stiffness, dtype=float, device=self._device)

        self._cell_center_sums = wp.zeros(self._cell_count, dtype=wp.vec3, device=self._device)
        self._cell_contact_forces = wp.zeros(self._cell_count, dtype=wp.vec3, device=self._device)
        self._cell_counts = wp.array(cell_counts, dtype=int, device=self._device)
        self._cell_radii = wp.array(cell_radii, dtype=float, device=self._device)
        self._shape_stiffness = wp.array(shape_stiffness, dtype=float, device=self._device)
        self._plane_stiffness = wp.array(plane_stiffness, dtype=float, device=self._device)
        self._drag = wp.array(drag, dtype=float, device=self._device)
        self._gravity = wp.array(gravity, dtype=float, device=self._device)
        self._migration_force = wp.array(migration_force, dtype=float, device=self._device)
        self._migration_directions = wp.array(migration_directions, dtype=wp.vec3, device=self._device)

        self._positions_host = None
        if self._device.is_cuda:
            self._positions_host = wp.zeros(self._node_count, dtype=wp.vec3, device="cpu")

    def step(self, dt: float) -> list[list[Vec3]]:
        remaining = max(0.0, dt)
        while remaining > 0.0:
            sub_dt = min(remaining, self._max_step)
            self._step_once(sub_dt)
            remaining -= sub_dt
        return self._read_positions_by_cell()

    def _step_once(self, dt: float) -> None:
        params = self._parameters
        self._cell_center_sums.zero_()

        wp.launch(
            kernel=_clear_forces_and_sum_cell_centers,
            dim=self._node_count,
            inputs=[
                self._positions,
                self._forces,
                self._cell_center_sums,
                self._particle_cell,
                self._gravity,
            ],
            device=self._device,
        )
        wp.launch(
            kernel=_apply_springs,
            dim=self._spring_count,
            inputs=[
                self._positions,
                self._spring_a,
                self._spring_b,
                self._spring_rest_lengths,
                self._spring_stiffness,
                self._forces,
            ],
            device=self._device,
        )
        wp.launch(
            kernel=_apply_cell_center_contacts,
            dim=self._cell_count,
            inputs=[
                self._cell_center_sums,
                self._cell_counts,
                self._cell_radii,
                self._cell_contact_forces,
                self._cell_count,
                params.contact_stiffness,
                params.contact_margin,
            ],
            device=self._device,
        )
        wp.launch(
            kernel=_integrate_culture_overdamped,
            dim=self._node_count,
            inputs=[
                self._positions,
                self._rest_offsets,
                self._particle_cell,
                self._forces,
                self._cell_center_sums,
                self._cell_counts,
                self._cell_contact_forces,
                self._migration_directions,
                self._cell_radii,
                self._shape_stiffness,
                self._plane_stiffness,
                self._drag,
                self._migration_force,
                dt,
            ],
            device=self._device,
        )

    def _read_positions_by_cell(self) -> list[list[Vec3]]:
        if self._positions_host is not None:
            wp.copy(self._positions_host, self._positions)
            wp.synchronize_device(self._device)
            values = self._positions_host.numpy()
        else:
            values = self._positions.numpy()

        positions = [Vec3(float(value[0]), float(value[1]), float(value[2])) for value in values]
        return [positions[start:end] for start, end in self._cell_slices]

    def _flatten_cells(self, cells: list[CellInstance]):
        positions: list[tuple[float, float, float]] = []
        rest_offsets: list[tuple[float, float, float]] = []
        particle_cell: list[int] = []
        cell_counts: list[int] = []
        spring_a: list[int] = []
        spring_b: list[int] = []
        spring_rest_lengths: list[float] = []
        spring_stiffness: list[float] = []
        cell_radii: list[float] = []
        shape_stiffness: list[float] = []
        plane_stiffness: list[float] = []
        drag: list[float] = []
        gravity: list[float] = []
        migration_force: list[float] = []
        migration_directions: list[tuple[float, float, float]] = []
        cell_slices: list[tuple[int, int]] = []

        node_offset = 0
        for cell_index, cell in enumerate(cells):
            sim = cell.simulation
            params = sim.parameters
            cell_slices.append((node_offset, node_offset + len(sim.positions)))
            cell_counts.append(len(sim.positions))
            cell_radii.append(params.radius)
            shape_stiffness.append(params.shape_stiffness)
            plane_stiffness.append(params.plane_stiffness)
            drag.append(max(params.drag, 1.0e-6))
            gravity.append(params.gravity)
            migration_force.append(params.migration_force)
            migration_directions.append(sim.migration_direction.as_tuple())

            positions.extend(position.as_tuple() for position in sim.positions)
            rest_offsets.extend(offset.as_tuple() for offset in sim.rest_offsets)
            particle_cell.extend([cell_index] * len(sim.positions))

            for spring in sim.springs:
                spring_a.append(node_offset + spring.a)
                spring_b.append(node_offset + spring.b)
                spring_rest_lengths.append(spring.rest_length)
                spring_stiffness.append(spring.stiffness)

            node_offset += len(sim.positions)

        return (
            positions,
            rest_offsets,
            particle_cell,
            cell_counts,
            spring_a,
            spring_b,
            spring_rest_lengths,
            spring_stiffness,
            cell_radii,
            shape_stiffness,
            plane_stiffness,
            drag,
            gravity,
            migration_force,
            migration_directions,
            cell_slices,
        )

    def _select_device(self, device: str | None):
        if device is not None:
            return wp.get_device(device)
        if wp.is_cuda_available():
            return wp.get_device("cuda:0")
        return wp.get_device("cpu")
