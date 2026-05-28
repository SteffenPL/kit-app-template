from __future__ import annotations

import warp as wp

from .simulation import SoftCellParameters, Spring, Vec3


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
def _integrate_overdamped(
    positions: wp.array(dtype=wp.vec3),
    rest_offsets: wp.array(dtype=wp.vec3),
    forces: wp.array(dtype=wp.vec3),
    center_sum: wp.array(dtype=wp.vec3),
    migration_direction: wp.vec3,
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

    target = center + rest_offsets[tid]
    force = force + (target - position) * shape_stiffness

    if position[2] < 0.0:
        force = force + wp.vec3(0.0, 0.0, -position[2] * plane_stiffness)

    polarity = wp.dot(rest_offsets[tid], migration_direction)
    if polarity > radius * 0.35:
        force = force + migration_direction * migration_force

    positions[tid] = position + (force / drag) * dt


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

    def step_once(self, dt: float) -> list[Vec3]:
        params = self._parameters
        drag = max(params.drag, 1.0e-6)
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
