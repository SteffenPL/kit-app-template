import unittest

from ku.cell_sim.simulation import (
    CellCultureParameters,
    CellCultureSimulation,
    SoftCellParameters,
    SoftCellSimulation,
    Vec3,
)


try:
    import omni.kit.test as kit_test

    TestCaseBase = kit_test.AsyncTestCase
except Exception:
    TestCaseBase = unittest.TestCase


def _skip_unless_warp_available(test_case: unittest.TestCase) -> None:
    try:
        import warp  # noqa: F401
    except Exception as exc:
        test_case.skipTest(f"Warp is not available in this Python environment: {exc}")


def _move_cell_center(sim: SoftCellSimulation, target: Vec3) -> None:
    offset = target - sim.center
    sim.positions = [position + offset for position in sim.positions]


class SoftCellSimulationTests(TestCaseBase):
    def test_contact_force_lifts_particle_above_plane(self):
        sim = SoftCellSimulation(
            SoftCellParameters(lat_segments=4, lon_segments=8, gravity=0.0, migration_force=0.0),
            backend="python",
        )
        sim.positions[0] = Vec3(sim.positions[0].x, sim.positions[0].y, -0.1)

        before = sim.positions[0].z
        sim.step(1.0 / 60.0)

        self.assertGreater(sim.positions[0].z, before)

    def test_higher_drag_reduces_displacement(self):
        low_drag = SoftCellSimulation(
            SoftCellParameters(lat_segments=4, lon_segments=8, drag=5.0, gravity=0.0),
            backend="python",
        )
        high_drag = SoftCellSimulation(
            SoftCellParameters(lat_segments=4, lon_segments=8, drag=50.0, gravity=0.0),
            backend="python",
        )
        front_index = max(range(len(low_drag.positions)), key=lambda index: low_drag.rest_offsets[index].x)

        low_before = low_drag.positions[front_index].x
        high_before = high_drag.positions[front_index].x

        low_drag.step(1.0 / 30.0)
        high_drag.step(1.0 / 30.0)

        self.assertGreater(
            abs(low_drag.positions[front_index].x - low_before),
            abs(high_drag.positions[front_index].x - high_before),
        )

    def test_spring_network_is_stable_for_short_run(self):
        sim = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8), backend="python")

        for _ in range(30):
            sim.step(1.0 / 60.0)

        self.assertEqual(len(sim.positions), 40)
        self.assertTrue(all(position.z > -0.05 for position in sim.positions))

    def test_cell_culture_defaults_to_inspectable_cell_count(self):
        culture = CellCultureSimulation(backend="python")

        self.assertGreaterEqual(len(culture.cells), 10)
        self.assertLessEqual(len(culture.cells), 20)
        self.assertEqual(len({cell.name for cell in culture.cells}), len(culture.cells))

    def test_cell_culture_places_cells_on_large_substrate(self):
        culture = CellCultureSimulation(backend="python")

        for cell in culture.cells:
            center = cell.simulation.center
            self.assertGreaterEqual(center.x, -3.1)
            self.assertLessEqual(center.x, 3.1)
            self.assertGreaterEqual(center.y, -2.0)
            self.assertLessEqual(center.y, 2.0)
            self.assertGreater(center.z, 0.0)

    def test_cell_culture_random_seed_is_reproducible(self):
        first = CellCultureSimulation(seed=23, backend="python")
        second = CellCultureSimulation(seed=23, backend="python")
        different = CellCultureSimulation(seed=24, backend="python")

        first_centers = [cell.simulation.center.as_tuple() for cell in first.cells]
        second_centers = [cell.simulation.center.as_tuple() for cell in second.cells]
        different_centers = [cell.simulation.center.as_tuple() for cell in different.cells]

        self.assertEqual(first_centers, second_centers)
        self.assertNotEqual(first_centers, different_centers)

    def test_cell_culture_contact_forces_separate_overlapping_cells(self):
        culture = CellCultureSimulation(
            count=10,
            backend="python",
            parameters=CellCultureParameters(contact_stiffness=120.0, contact_margin=0.0),
        )
        first = culture.cells[0].simulation
        second = culture.cells[1].simulation
        _move_cell_center(first, Vec3(0.0, 0.0, first.parameters.radius))
        _move_cell_center(second, Vec3(0.45, 0.0, second.parameters.radius))
        for index, cell in enumerate(culture.cells[2:], start=2):
            _move_cell_center(cell.simulation, Vec3(10.0 + index * 2.0, 0.0, cell.simulation.parameters.radius))

        before = (first.center - second.center).length()
        contact_forces = culture._cell_contact_forces()
        culture.step(1.0 / 30.0)
        after = (first.center - second.center).length()

        self.assertLess(contact_forces[0].x, 0.0)
        self.assertGreater(contact_forces[1].x, 0.0)
        self.assertGreater(after, before)

    def test_python_backend_can_be_selected_for_headless_tests(self):
        sim = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8), backend="python")

        self.assertEqual(sim.backend_name, "python")
        self.assertIsNone(sim.backend_error)

    def test_warp_backend_runs_one_step_when_available(self):
        _skip_unless_warp_available(self)
        sim = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8), backend="warp")

        before = sim.center
        sim.step(1.0 / 60.0)
        after = sim.center

        self.assertTrue(sim.backend_name.startswith("warp:"))
        self.assertNotEqual(before.as_tuple(), after.as_tuple())

    def test_cell_culture_defaults_to_warp_when_available(self):
        _skip_unless_warp_available(self)
        culture = CellCultureSimulation(count=10)

        self.assertTrue(culture.backend_name.startswith("warp-culture:"))
        self.assertTrue(all(cell.simulation.backend_name == "python" for cell in culture.cells))
        culture.step(1.0 / 60.0)

    def test_warp_culture_backend_separates_overlapping_cells(self):
        _skip_unless_warp_available(self)
        culture = CellCultureSimulation(
            count=10,
            parameters=CellCultureParameters(contact_stiffness=120.0, contact_margin=0.0),
        )
        first = culture.cells[0].simulation
        second = culture.cells[1].simulation
        _move_cell_center(first, Vec3(0.0, 0.0, first.parameters.radius))
        _move_cell_center(second, Vec3(0.45, 0.0, second.parameters.radius))
        for index, cell in enumerate(culture.cells[2:], start=2):
            _move_cell_center(cell.simulation, Vec3(10.0 + index * 2.0, 0.0, cell.simulation.parameters.radius))
        culture._configure_backend()

        before = (first.center - second.center).length()
        culture.step(1.0 / 30.0)
        after = (first.center - second.center).length()

        self.assertTrue(culture.backend_name.startswith("warp-culture:"))
        self.assertGreater(after, before)


if __name__ == "__main__":
    unittest.main()
