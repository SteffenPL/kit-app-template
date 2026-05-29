from __future__ import annotations

from pathlib import Path

from .authoring import VesselSceneSpec
from .simulation import Vec3


def export_vessel_scene_openusd(spec: VesselSceneSpec, path: str | Path) -> Path:
    """Write a compact OpenUSD stage with analytic prims using the official pxr API."""

    try:
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade, Vt
    except ImportError as exc:
        raise RuntimeError(
            "The pxr OpenUSD bindings are required. Install usd-core, for example: "
            "uv pip install --python _openusd_env/bin/python usd-core==26.5"
        ) from exc

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stage = Usd.Stage.CreateNew(str(output_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    stage.SetMetadata("metersPerUnit", 1.0)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.Xform.Define(stage, "/World/AuthoredScenes")
    root_path = f"/World/AuthoredScenes/{spec.name}"
    root = UsdGeom.Xform.Define(stage, root_path)
    root.GetPrim().CreateAttribute("authoredCellCount", Sdf.ValueTypeNames.Int).Set(spec.cell_count)
    root.GetPrim().CreateAttribute("cellsPerRing", Sdf.ValueTypeNames.Int).Set(spec.cells_per_ring)
    root.GetPrim().CreateAttribute("rings", Sdf.ValueTypeNames.Int).Set(spec.rings)

    materials = {}
    materials_path = f"{root_path}/Materials"
    UsdGeom.Scope.Define(stage, materials_path)
    for material in spec.materials:
        materials[material.name] = _create_preview_material(
            stage,
            f"{materials_path}/{material.name}",
            material.color,
            material.opacity,
            Sdf,
            Gf,
            UsdShade,
        )

    _create_cylinder(
        stage,
        f"{root_path}/Lumen",
        spec.radius * 0.96,
        spec.length,
        (0.68, 0.88, 0.95),
        0.18,
        materials["lumen_marker"],
        Gf,
        UsdGeom,
        UsdShade,
        Vt,
    )
    _create_cylinder(
        stage,
        f"{root_path}/BasementMembrane",
        spec.radius + 0.09,
        spec.length,
        (0.82, 0.76, 0.56),
        0.28,
        materials["basement_membrane"],
        Gf,
        UsdGeom,
        UsdShade,
        Vt,
    )

    cells_path = f"{root_path}/Cells"
    UsdGeom.Xform.Define(stage, cells_path)
    material_specs = {material.name: material for material in spec.materials}
    for cell in spec.cells:
        cell_path = f"{cells_path}/{cell.name}"
        UsdGeom.Xform.Define(stage, cell_path)
        cortex_material = material_specs[cell.cortex_material]
        nucleus_material = material_specs[cell.nucleus_material]
        _create_oriented_sphere(
            stage,
            f"{cell_path}/Cortex",
            cell.center,
            cell.vessel_axis,
            cell.circumferential_axis,
            cell.radial_axis,
            cell.cell_scale,
            cortex_material.color,
            cortex_material.opacity,
            materials[cell.cortex_material],
            Gf,
            UsdGeom,
            UsdShade,
            Vt,
        )
        _create_oriented_sphere(
            stage,
            f"{cell_path}/Nucleus",
            cell.nucleus_center,
            cell.vessel_axis,
            cell.circumferential_axis,
            cell.radial_axis,
            cell.nucleus_scale,
            nucleus_material.color,
            nucleus_material.opacity,
            materials[cell.nucleus_material],
            Gf,
            UsdGeom,
            UsdShade,
            Vt,
        )

    light = UsdLux.DistantLight.Define(stage, f"{root_path}/FillLight")
    light.CreateIntensityAttr(1200.0)
    UsdGeom.Xformable(light).AddRotateXYZOp().Set(Gf.Vec3f(-42.0, 0.0, 28.0))

    camera = UsdGeom.Camera.Define(stage, f"{root_path}/Camera")
    camera.CreateFocalLengthAttr(55.0)
    camera_xform = UsdGeom.Xformable(camera)
    camera_xform.AddTranslateOp().Set(Gf.Vec3d(5.8, -8.0, 5.4))
    camera_xform.AddRotateXYZOp().Set(Gf.Vec3f(58.0, 0.0, 38.0))

    stage.GetRootLayer().Save()
    return output_path


def _create_oriented_sphere(
    stage,
    path: str,
    center: Vec3,
    x_axis: Vec3,
    y_axis: Vec3,
    z_axis: Vec3,
    scale: Vec3,
    color: tuple[float, float, float],
    opacity: float,
    material,
    Gf,
    UsdGeom,
    UsdShade,
    Vt,
) -> None:
    sphere = UsdGeom.Sphere.Define(stage, path)
    sphere.CreateRadiusAttr(0.5)
    sphere.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(*color)]))
    sphere.CreateDisplayOpacityAttr(Vt.FloatArray([opacity]))
    xform = UsdGeom.Xformable(sphere)
    xform.AddTransformOp().Set(_basis_matrix(center, x_axis, y_axis, z_axis, scale, Gf))
    UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(material)


def _create_cylinder(
    stage,
    path: str,
    radius: float,
    length: float,
    color: tuple[float, float, float],
    opacity: float,
    material,
    Gf,
    UsdGeom,
    UsdShade,
    Vt,
) -> None:
    cylinder = UsdGeom.Cylinder.Define(stage, path)
    cylinder.CreateAxisAttr("X")
    cylinder.CreateRadiusAttr(radius)
    cylinder.CreateHeightAttr(length)
    cylinder.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(*color)]))
    cylinder.CreateDisplayOpacityAttr(Vt.FloatArray([opacity]))
    UsdShade.MaterialBindingAPI.Apply(cylinder.GetPrim()).Bind(material)


def _create_preview_material(stage, path: str, color: tuple[float, float, float], opacity: float, Sdf, Gf, UsdShade):
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, f"{path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.58)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _basis_matrix(center: Vec3, x_axis: Vec3, y_axis: Vec3, z_axis: Vec3, scale: Vec3, Gf):
    return Gf.Matrix4d(
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
