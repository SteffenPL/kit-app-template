from __future__ import annotations

from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade, Vt

from .simulation import CellCultureSimulation, CellInstance


ROOT_PATH = Sdf.Path("/World/CellMigrationPrototype")
SUBSTRATE_PATH = ROOT_PATH.AppendPath("Substrate")
CELLS_PATH = ROOT_PATH.AppendPath("Cells")
MATERIALS_PATH = ROOT_PATH.AppendPath("Materials")
CLIP_PLANE_PATH = ROOT_PATH.AppendPath("ClipPlane")
LIGHT_PATH = ROOT_PATH.AppendPath("KeyLight")
DISTANT_LIGHT_PATH = ROOT_PATH.AppendPath("FillLight")
CAMERA_PATH = ROOT_PATH.AppendPath("Camera")


class CellScene:
    def __init__(self, stage, simulation: CellCultureSimulation):
        self._stage = stage
        self._simulation = simulation
        self._cell_meshes = {}
        self._nuclei = {}
        self._materials = {}

    def create(self) -> None:
        if self._stage.GetPrimAtPath(ROOT_PATH).IsValid():
            self._stage.RemovePrim(ROOT_PATH)

        UsdGeom.Xform.Define(self._stage, Sdf.Path("/World"))
        UsdGeom.Xform.Define(self._stage, ROOT_PATH)
        UsdGeom.Xform.Define(self._stage, CELLS_PATH)
        UsdGeom.Xform.Define(self._stage, MATERIALS_PATH)
        self._create_materials()
        self._create_substrate()
        for cell in self._simulation.cells:
            self._create_cell(cell)
        self._create_clip_plane()
        self._create_light()
        self._create_camera()
        self.update()

    def update(self) -> None:
        for cell in self._simulation.cells:
            mesh = self._cell_meshes.get(cell.name)
            if mesh is None:
                continue

            points = [Gf.Vec3f(*position.as_tuple()) for position in cell.simulation.positions]
            mesh.GetPointsAttr().Set(Vt.Vec3fArray(points))

            nucleus = self._nuclei.get(cell.name)
            if nucleus is None:
                continue

            center = cell.simulation.center
            radius = cell.simulation.parameters.radius
            xform = UsdGeom.Xformable(nucleus)
            xform.ClearXformOpOrder()
            xform.AddTranslateOp().Set(Gf.Vec3d(center.x, center.y, center.z))
            xform.AddScaleOp().Set(Gf.Vec3f(radius * 0.42, radius * 0.42, radius * 0.42))

    def _create_substrate(self) -> None:
        substrate = UsdGeom.Cube.Define(self._stage, SUBSTRATE_PATH)
        substrate.CreateSizeAttr(1.0)
        xform = UsdGeom.Xformable(substrate)
        xform.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.06))
        xform.AddScaleOp().Set(Gf.Vec3f(7.2, 4.7, 0.04))
        substrate.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.05, 0.06, 0.07)]))
        self._bind_material(substrate.GetPrim(), self._materials["substrate"])

    def _create_cell(self, cell: CellInstance) -> None:
        cell_path = CELLS_PATH.AppendPath(cell.name)
        UsdGeom.Xform.Define(self._stage, cell_path)
        self._create_cell_mesh(cell, cell_path.AppendPath("Cortex"))
        self._create_nucleus(cell, cell_path.AppendPath("Nucleus"))

    def _create_cell_mesh(self, cell: CellInstance, path: Sdf.Path) -> None:
        mesh = UsdGeom.Mesh.Define(self._stage, path)
        face_vertex_counts = [3 for _ in cell.simulation.faces]
        face_vertex_indices = [index for face in cell.simulation.faces for index in face]
        mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
        mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)
        mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(*cell.style.cortex_color)]))
        mesh.CreateDisplayOpacityAttr(Vt.FloatArray([0.38]))
        mesh.CreateDoubleSidedAttr(True)
        self._bind_material(mesh.GetPrim(), self._materials[f"{cell.name}_cortex"])
        self._cell_meshes[cell.name] = mesh

    def _create_nucleus(self, cell: CellInstance, path: Sdf.Path) -> None:
        nucleus = UsdGeom.Sphere.Define(self._stage, path)
        nucleus.CreateRadiusAttr(1.0)
        nucleus.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(*cell.style.nucleus_color)]))
        self._bind_material(nucleus.GetPrim(), self._materials[f"{cell.name}_nucleus"])
        self._nuclei[cell.name] = nucleus

    def _create_clip_plane(self) -> None:
        plane = UsdGeom.Cube.Define(self._stage, CLIP_PLANE_PATH)
        plane.CreateSizeAttr(1.0)
        plane.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.70, 0.86, 1.0)]))
        plane.CreateDisplayOpacityAttr(Vt.FloatArray([0.22]))
        xform = UsdGeom.Xformable(plane)
        xform.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.82))
        xform.AddScaleOp().Set(Gf.Vec3f(0.012, 4.6, 1.35))
        self._bind_material(plane.GetPrim(), self._materials["clip_plane"])

    def _create_light(self) -> None:
        light = UsdLux.SphereLight.Define(self._stage, LIGHT_PATH)
        light.CreateRadiusAttr(1.2)
        light.CreateIntensityAttr(45000.0)
        xform = UsdGeom.Xformable(light)
        xform.AddTranslateOp().Set(Gf.Vec3d(-3.0, -5.0, 7.0))

        fill = UsdLux.DistantLight.Define(self._stage, DISTANT_LIGHT_PATH)
        fill.CreateIntensityAttr(900.0)
        fill.CreateAngleAttr(0.7)
        fill_xform = UsdGeom.Xformable(fill)
        fill_xform.AddRotateXYZOp().Set(Gf.Vec3f(-45.0, 0.0, 35.0))

    def _create_camera(self) -> None:
        camera = UsdGeom.Camera.Define(self._stage, CAMERA_PATH)
        camera.CreateFocalLengthAttr(42.0)
        camera.CreateFocusDistanceAttr(10.0)
        camera.GetPrim().CreateAttribute("clippingPlanes", Sdf.ValueTypeNames.Float4Array).Set(
            Vt.Vec4fArray([Gf.Vec4f(1.0, 0.0, 0.0, 0.0)])
        )
        xform = UsdGeom.Xformable(camera)
        xform.AddTranslateOp().Set(Gf.Vec3d(6.8, -9.2, 5.4))
        xform.AddRotateXYZOp().Set(Gf.Vec3f(61.0, 0.0, 38.0))
        self._stage.SetDefaultPrim(self._stage.GetPrimAtPath(ROOT_PATH))

    def _create_materials(self) -> None:
        self._materials = {
            "substrate": self._create_preview_material(
                MATERIALS_PATH.AppendPath("Substrate"), (0.018, 0.024, 0.030), 1.0, emissive=(0.01, 0.02, 0.03)
            ),
            "clip_plane": self._create_preview_material(
                MATERIALS_PATH.AppendPath("ClipPlane"), (0.70, 0.86, 1.0), 0.22, emissive=(0.07, 0.10, 0.16)
            ),
        }

        for cell in self._simulation.cells:
            self._materials[f"{cell.name}_cortex"] = self._create_preview_material(
                MATERIALS_PATH.AppendPath(f"{cell.name}_Cortex"),
                cell.style.cortex_color,
                0.38,
                emissive=tuple(channel * 0.18 for channel in cell.style.cortex_color),
            )
            self._materials[f"{cell.name}_nucleus"] = self._create_preview_material(
                MATERIALS_PATH.AppendPath(f"{cell.name}_Nucleus"),
                cell.style.nucleus_color,
                1.0,
                emissive=tuple(channel * 0.10 for channel in cell.style.nucleus_color),
            )

    def _create_preview_material(
        self,
        path: Sdf.Path,
        color: tuple[float, float, float],
        opacity: float,
        emissive: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        material = UsdShade.Material.Define(self._stage, path)
        shader = UsdShade.Shader.Define(self._stage, path.AppendPath("Shader"))
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*emissive))
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.48)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        return material

    def _bind_material(self, prim, material) -> None:
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
