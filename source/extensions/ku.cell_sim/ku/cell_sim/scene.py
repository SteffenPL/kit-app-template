from __future__ import annotations

from pxr import Gf, Sdf, UsdGeom, UsdLux, Vt

from .simulation import SoftCellSimulation


ROOT_PATH = Sdf.Path("/World/CellMigrationPrototype")
SUBSTRATE_PATH = ROOT_PATH.AppendPath("Substrate")
CELL_PATH = ROOT_PATH.AppendPath("CellCortex")
NUCLEUS_PATH = ROOT_PATH.AppendPath("Nucleus")
LIGHT_PATH = ROOT_PATH.AppendPath("KeyLight")
DISTANT_LIGHT_PATH = ROOT_PATH.AppendPath("FillLight")
CAMERA_PATH = ROOT_PATH.AppendPath("Camera")


class CellScene:
    def __init__(self, stage, simulation: SoftCellSimulation):
        self._stage = stage
        self._simulation = simulation
        self._cell_mesh = None
        self._nucleus = None

    def create(self) -> None:
        UsdGeom.Xform.Define(self._stage, Sdf.Path("/World"))
        UsdGeom.Xform.Define(self._stage, ROOT_PATH)
        self._create_substrate()
        self._create_cell_mesh()
        self._create_nucleus()
        self._create_light()
        self._create_camera()
        self.update()

    def update(self) -> None:
        if self._cell_mesh is None:
            return

        points = [Gf.Vec3f(*position.as_tuple()) for position in self._simulation.positions]
        self._cell_mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))

        if self._nucleus is not None:
            center = self._simulation.center
            xform = UsdGeom.Xformable(self._nucleus)
            xform.ClearXformOpOrder()
            xform.AddTranslateOp().Set(Gf.Vec3d(center.x, center.y, center.z))
            xform.AddScaleOp().Set(Gf.Vec3f(0.38, 0.38, 0.38))

    def _create_substrate(self) -> None:
        substrate = UsdGeom.Cube.Define(self._stage, SUBSTRATE_PATH)
        substrate.CreateSizeAttr(1.0)
        xform = UsdGeom.Xformable(substrate)
        xform.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.06))
        xform.AddScaleOp().Set(Gf.Vec3f(5.0, 3.0, 0.04))
        substrate.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.18, 0.20, 0.21)]))

    def _create_cell_mesh(self) -> None:
        mesh = UsdGeom.Mesh.Define(self._stage, CELL_PATH)
        face_vertex_counts = [3 for _ in self._simulation.faces]
        face_vertex_indices = [index for face in self._simulation.faces for index in face]
        mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
        mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)
        mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.12, 0.62, 0.78)]))
        mesh.CreateDoubleSidedAttr(True)
        self._cell_mesh = mesh

    def _create_nucleus(self) -> None:
        nucleus = UsdGeom.Sphere.Define(self._stage, NUCLEUS_PATH)
        nucleus.CreateRadiusAttr(1.0)
        nucleus.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.88, 0.34, 0.58)]))
        self._nucleus = nucleus

    def _create_light(self) -> None:
        light = UsdLux.SphereLight.Define(self._stage, LIGHT_PATH)
        light.CreateRadiusAttr(0.4)
        light.CreateIntensityAttr(25000.0)
        xform = UsdGeom.Xformable(light)
        xform.AddTranslateOp().Set(Gf.Vec3d(-2.0, -3.0, 5.0))

        fill = UsdLux.DistantLight.Define(self._stage, DISTANT_LIGHT_PATH)
        fill.CreateIntensityAttr(650.0)
        fill.CreateAngleAttr(0.7)
        fill_xform = UsdGeom.Xformable(fill)
        fill_xform.AddRotateXYZOp().Set(Gf.Vec3f(-45.0, 0.0, 35.0))

    def _create_camera(self) -> None:
        camera = UsdGeom.Camera.Define(self._stage, CAMERA_PATH)
        camera.CreateFocalLengthAttr(35.0)
        camera.CreateFocusDistanceAttr(5.0)
        xform = UsdGeom.Xformable(camera)
        xform.AddTranslateOp().Set(Gf.Vec3d(3.2, -5.0, 2.7))
        xform.AddRotateXYZOp().Set(Gf.Vec3f(62.0, 0.0, 35.0))
        self._stage.SetDefaultPrim(self._stage.GetPrimAtPath(ROOT_PATH))
