import unittest

from ku.cell_sim.simulation import SoftCellParameters, SoftCellSimulation, Vec3


class SoftCellSimulationTests(unittest.TestCase):
    def test_contact_force_lifts_particle_above_plane(self):
        sim = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8, gravity=0.0, migration_force=0.0))
        sim.positions[0] = Vec3(sim.positions[0].x, sim.positions[0].y, -0.1)

        before = sim.positions[0].z
        sim.step(1.0 / 60.0)

        self.assertGreater(sim.positions[0].z, before)

    def test_higher_drag_reduces_displacement(self):
        low_drag = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8, drag=5.0, gravity=0.0))
        high_drag = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8, drag=50.0, gravity=0.0))
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
        sim = SoftCellSimulation(SoftCellParameters(lat_segments=4, lon_segments=8))

        for _ in range(30):
            sim.step(1.0 / 60.0)

        self.assertEqual(len(sim.positions), 40)
        self.assertTrue(all(position.z > -0.05 for position in sim.positions))


if __name__ == "__main__":
    unittest.main()
