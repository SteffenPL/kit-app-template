from __future__ import annotations

from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade, Vt

from .authoring import VesselSceneSpec
from .simulation import Vec3


VESSEL_ROOT_PATH = Sdf.Path("/World/AuthoredScenes/BloodVesselEndothelium")


class AuthoredUsdScene:
    """USD stage adapter for portable authored scene specs."""

    def __init__(self, stage, spec: VesselSceneSpec):
        self._stage = stage
        self._spec = spec
        self._materials = {}

    def create(self) -> None:
        if self._stage.GetPrimAtPath(VESSEL_ROOT_PATH).IsValid():
            self._stage.RemovePrim(VESSEL_ROOT_PATH)

        UsdGeom.Xform.Define(self._stage, Sdf.Path("/World"))
        UsdGeom.Xform.Define(self._stage, Sdf.Path("/World/AuthoredScenes"))
        UsdGeom.Xform.Define(self._stage, VESSEL_ROOT_PATH)
        self._create_materials()
        self._create_lumen()
        self._create_cells()
        self._create_light_and_camera()
        self._stage.SetDefaultPrim(self._stage.GetPrimAtPath(VESSEL_ROOT_PATH))

    def _create_materials(self) -> None:
        materials_path = VESSEL_ROOT_PATH.AppendPath("Materials")
        UsdGeom.Scope.Define(self._stage, materials_path)
        self._materials = {}
        for material in self._spec.materials:
            self._materials[material.name] = self._create_preview_material(
                materials_path.AppendPath(material.name),
                material.color,
                material.opacity,
            )

    def _create_lumen(self) -> None:
        lumen = UsdGeom.Cylinder.Define(self._stage, VESSEL_ROOT_PATH.AppendPath("Lumen"))
        lumen.CreateRadiusAttr(self._spec.radius * 0.96)
        lumen.CreateHeightAttr(self._spec.length)
        lumen.CreateAxisAttr("X")
        lumen.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.68, 0.88, 0.95)]))
        lumen.CreateDisplayOpacityAttr(Vt.FloatArray([0.18]))
        self._bind_material(lumen.GetPrim(), self._materials["lumen_marker"])

        basement = UsdGeom.Cylinder.Define(self._stage, VESSEL_ROOT_PATH.AppendPath("BasementMembrane"))
        basement.CreateRadiusAttr(self._spec.radius + 0.09)
        basement.CreateHeightAttr(self._spec.length)
        basement.CreateAxisAttr("X")
        basement.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.82, 0.76, 0.56)]))
        basement.CreateDisplayOpacityAttr(Vt.FloatArray([0.28]))
        self._bind_material(basement.GetPrim(), self._materials["basement_membrane"])

    def _create_cells(self) -> None:
        cells_path = VESSEL_ROOT_PATH.AppendPath("Cells")
        UsdGeom.Xform.Define(self._stage, cells_path)
        for cell in self._spec.cells:
            cell_path = cells_path.AppendPath(cell.name)
            UsdGeom.Xform.Define(self._stage, cell_path)
            self._create_oriented_sphere(
                cell_path.AppendPath("Cortex"),
                cell.center,
                cell.vessel_axis,
                cell.circumferential_axis,
                cell.radial_axis,
                cell.cell_scale,
                cell.cortex_material,
            )
            self._create_oriented_sphere(
                cell_path.AppendPath("Nucleus"),
                cell.nucleus_center,
                cell.vessel_axis,
                cell.circumferential_axis,
                cell.radial_axis,
                cell.nucleus_scale,
                cell.nucleus_material,
            )

    def _create_oriented_sphere(
        self,
        path: Sdf.Path,
        center: Vec3,
        x_axis: Vec3,
        y_axis: Vec3,
        z_axis: Vec3,
        scale: Vec3,
        material_name: str,
    ) -> None:
        sphere = UsdGeom.Sphere.Define(self._stage, path)
        sphere.CreateRadiusAttr(0.5)
        matrix = Gf.Matrix4d(
            x_axis.x * scale.x,
            x_axis.y * scale.x,
            x_axis.z * scale.x,
            0.0,
            y_axis.x * scale.y,
            y_axis.y * scale.y,
            y_axis.z * scale.y,
            0.0,
            z_axis.x * scale.z,
            z_axis.y * scale.z,
            z_axis.z * scale.z,
            0.0,
            center.x,
            center.y,
            center.z,
            1.0,
        )
        xform = UsdGeom.Xformable(sphere)
        xform.AddTransformOp().Set(matrix)
        self._bind_material(sphere.GetPrim(), self._materials[material_name])

    def _create_light_and_camera(self) -> None:
        light = UsdLux.DistantLight.Define(self._stage, VESSEL_ROOT_PATH.AppendPath("FillLight"))
        light.CreateIntensityAttr(1200.0)
        UsdGeom.Xformable(light).AddRotateXYZOp().Set(Gf.Vec3f(-42.0, 0.0, 28.0))

        camera = UsdGeom.Camera.Define(self._stage, VESSEL_ROOT_PATH.AppendPath("Camera"))
        camera.CreateFocalLengthAttr(55.0)
        xform = UsdGeom.Xformable(camera)
        xform.AddTranslateOp().Set(Gf.Vec3d(5.8, -8.0, 5.4))
        xform.AddRotateXYZOp().Set(Gf.Vec3f(58.0, 0.0, 38.0))

    def _create_preview_material(self, path: Sdf.Path, color: tuple[float, float, float], opacity: float):
        material = UsdShade.Material.Define(self._stage, path)
        shader = UsdShade.Shader.Define(self._stage, path.AppendPath("Shader"))
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.58)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        return material

    def _bind_material(self, prim, material) -> None:
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
