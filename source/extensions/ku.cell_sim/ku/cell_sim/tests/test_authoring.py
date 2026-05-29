import math
import tempfile
import unittest
from pathlib import Path

from ku.cell_sim.authoring import build_endothelium_vessel_scene
from ku.cell_sim.openusd_export import export_vessel_scene_openusd
from ku.cell_sim.usda_export import export_vessel_scene_usda


class EndotheliumAuthoringTests(unittest.TestCase):
    def test_vessel_scene_builds_requested_cell_count(self):
        spec = build_endothelium_vessel_scene(cell_count=200, cells_per_ring=10)

        self.assertEqual(spec.cell_count, 200)
        self.assertEqual(spec.rings, 20)
        self.assertEqual(len(spec.cells), 200)
        self.assertEqual(len({cell.name for cell in spec.cells}), 200)

    def test_cells_lie_on_vessel_wall(self):
        spec = build_endothelium_vessel_scene(cell_count=200, cells_per_ring=10, radius=2.0)

        for cell in spec.cells:
            radial_distance = math.sqrt(cell.center.y * cell.center.y + cell.center.z * cell.center.z)
            self.assertAlmostEqual(radial_distance, spec.radius)

    def test_cell_basis_vectors_are_orthogonal(self):
        spec = build_endothelium_vessel_scene(cell_count=12, cells_per_ring=6)

        for cell in spec.cells:
            axis_dot_radial = cell.vessel_axis.x * cell.radial_axis.x
            circum_dot_radial = (
                cell.circumferential_axis.y * cell.radial_axis.y
                + cell.circumferential_axis.z * cell.radial_axis.z
            )
            self.assertAlmostEqual(axis_dot_radial, 0.0)
            self.assertAlmostEqual(circum_dot_radial, 0.0)

    def test_direct_usda_export_uses_analytic_prims(self):
        spec = build_endothelium_vessel_scene(cell_count=20, cells_per_ring=5)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_vessel_scene_usda(spec, Path(temp_dir) / "vessel.usda")
            text = path.read_text()

        self.assertIn('def Cylinder "Lumen"', text)
        self.assertEqual(text.count('def Sphere "Cortex"'), 20)
        self.assertEqual(text.count('def Sphere "Nucleus"'), 20)
        self.assertNotIn("faceVertexIndices", text)

    def test_openusd_export_uses_pxr_when_available(self):
        try:
            from pxr import Usd
        except ImportError as exc:
            self.skipTest(f"OpenUSD pxr bindings are not available: {exc}")

        spec = build_endothelium_vessel_scene(cell_count=20, cells_per_ring=5)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_vessel_scene_openusd(spec, Path(temp_dir) / "vessel.usdc")
            stage = Usd.Stage.Open(str(path))

        self.assertTrue(stage.GetPrimAtPath("/World/AuthoredScenes/BloodVesselEndothelium/Lumen").IsValid())
        self.assertTrue(
            stage.GetPrimAtPath("/World/AuthoredScenes/BloodVesselEndothelium/Cells/EndothelialCell_001/Cortex")
            .IsValid()
        )


if __name__ == "__main__":
    unittest.main()
