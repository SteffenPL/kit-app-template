from __future__ import annotations

from pathlib import Path

from .authoring import VesselSceneSpec
from .simulation import Vec3


def export_vessel_scene_usda(spec: VesselSceneSpec, path: str | Path) -> Path:
    """Write a compact ASCII USD file from the portable vessel scene spec."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_vessel_scene_to_usda(spec), encoding="utf-8")
    return output_path


def _vessel_scene_to_usda(spec: VesselSceneSpec) -> str:
    lines = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "World"',
        "    metersPerUnit = 1",
        '    upAxis = "Z"',
        ")",
        "",
        'def Xform "World"',
        "{",
        '    def Xform "AuthoredScenes"',
        "    {",
        f'        def Xform "{spec.name}"',
        "        {",
        f"            custom int authoredCellCount = {spec.cell_count}",
        f"            custom int cellsPerRing = {spec.cells_per_ring}",
        f"            custom int rings = {spec.rings}",
        "",
        _cylinder_block("Lumen", spec.radius * 0.96, spec.length, (0.68, 0.88, 0.95), 0.18, 3),
        _cylinder_block("BasementMembrane", spec.radius + 0.09, spec.length, (0.82, 0.76, 0.56), 0.28, 3),
        '            def Xform "Cells"',
        "            {",
    ]

    material_colors = {material.name: material.color for material in spec.materials}
    material_opacity = {material.name: material.opacity for material in spec.materials}
    for cell in spec.cells:
        color = material_colors[cell.cortex_material]
        opacity = material_opacity[cell.cortex_material]
        nucleus_color = material_colors[cell.nucleus_material]
        nucleus_opacity = material_opacity[cell.nucleus_material]
        lines.extend(
            [
                f'                def Xform "{cell.name}"',
                "                {",
                _sphere_block(
                    "Cortex",
                    cell.center,
                    cell.vessel_axis,
                    cell.circumferential_axis,
                    cell.radial_axis,
                    cell.cell_scale,
                    color,
                    opacity,
                    5,
                ),
                _sphere_block(
                    "Nucleus",
                    cell.nucleus_center,
                    cell.vessel_axis,
                    cell.circumferential_axis,
                    cell.radial_axis,
                    cell.nucleus_scale,
                    nucleus_color,
                    nucleus_opacity,
                    5,
                ),
                "                }",
            ]
        )

    lines.extend(
        [
            "            }",
            "",
            '            def DistantLight "FillLight"',
            "            {",
            "                float intensity = 1200",
            "                float3 xformOp:rotateXYZ = (-42, 0, 28)",
            '                uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]',
            "            }",
            "",
            '            def Camera "Camera"',
            "            {",
            "                float focalLength = 55",
            "                double3 xformOp:translate = (5.8, -8, 5.4)",
            "                float3 xformOp:rotateXYZ = (58, 0, 38)",
            '                uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]',
            "            }",
            "        }",
            "    }",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _sphere_block(
    name: str,
    center: Vec3,
    x_axis: Vec3,
    y_axis: Vec3,
    z_axis: Vec3,
    scale: Vec3,
    color: tuple[float, float, float],
    opacity: float,
    indent: int,
) -> str:
    pad = "    " * indent
    matrix = _matrix_rows(center, x_axis, y_axis, z_axis, scale)
    return "\n".join(
        [
            f'{pad}def Sphere "{name}"',
            f"{pad}{{",
            f"{pad}    double radius = 0.5",
            f"{pad}    color3f[] primvars:displayColor = [{_vec3(color)}]",
            f"{pad}    float[] primvars:displayOpacity = [{_number(opacity)}]",
            f"{pad}    matrix4d xformOp:transform = {matrix}",
            f'{pad}    uniform token[] xformOpOrder = ["xformOp:transform"]',
            f"{pad}}}",
        ]
    )


def _cylinder_block(
    name: str,
    radius: float,
    length: float,
    color: tuple[float, float, float],
    opacity: float,
    indent: int,
) -> str:
    pad = "    " * indent
    return "\n".join(
        [
            f'{pad}def Cylinder "{name}"',
            f"{pad}{{",
            f"{pad}    uniform token axis = \"X\"",
            f"{pad}    double radius = {_number(radius)}",
            f"{pad}    double height = {_number(length)}",
            f"{pad}    color3f[] primvars:displayColor = [{_vec3(color)}]",
            f"{pad}    float[] primvars:displayOpacity = [{_number(opacity)}]",
            f"{pad}}}",
            "",
        ]
    )


def _matrix_rows(center: Vec3, x_axis: Vec3, y_axis: Vec3, z_axis: Vec3, scale: Vec3) -> str:
    rows = (
        (x_axis.x * scale.x, x_axis.y * scale.x, x_axis.z * scale.x, 0.0),
        (y_axis.x * scale.y, y_axis.y * scale.y, y_axis.z * scale.y, 0.0),
        (z_axis.x * scale.z, z_axis.y * scale.z, z_axis.z * scale.z, 0.0),
        (center.x, center.y, center.z, 1.0),
    )
    return "( " + ", ".join("(" + ", ".join(_number(value) for value in row) + ")" for row in rows) + " )"


def _vec3(values: tuple[float, float, float]) -> str:
    return "(" + ", ".join(_number(value) for value in values) + ")"


def _number(value: float) -> str:
    return f"{value:.6g}"
