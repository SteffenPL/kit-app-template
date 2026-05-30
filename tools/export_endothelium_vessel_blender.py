from __future__ import annotations

import argparse
import os
import sys


EXTENSION_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "source", "extensions", "ku.cell_sim")
)
if EXTENSION_ROOT not in sys.path:
    sys.path.insert(0, EXTENSION_ROOT)

import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

from ku.cell_sim.authoring import MaterialSpec, VesselSceneSpec, build_endothelium_vessel_scene  # noqa: E402
from ku.cell_sim.simulation import Vec3  # noqa: E402


def _parse_args() -> argparse.Namespace:
    argv = sys.argv
    script_args = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description="Export a Blender-authored endothelial vessel OpenUSD scene.")
    parser.add_argument("--output", default="outputs/endothelium_vessel_blender/endothelium_vessel_420.usda")
    parser.add_argument("--blend-output", default="outputs/endothelium_vessel_blender/endothelium_vessel_420.blend")
    parser.add_argument("--cells", type=int, default=420)
    parser.add_argument("--cells-per-ring", type=int, default=14)
    return parser.parse_args(script_args)


def _material(spec: MaterialSpec) -> bpy.types.Material:
    material = bpy.data.materials.new(spec.name)
    material.diffuse_color = (*spec.color, spec.opacity)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*spec.color, spec.opacity)
        bsdf.inputs["Alpha"].default_value = spec.opacity
        bsdf.inputs["Roughness"].default_value = 0.62
    material.blend_method = "BLEND"
    return material


def _basis_matrix(center: Vec3, x_axis: Vec3, y_axis: Vec3, z_axis: Vec3, scale: Vec3) -> Matrix:
    return Matrix(
        (
            (x_axis.x * scale.x, y_axis.x * scale.y, z_axis.x * scale.z, center.x),
            (x_axis.y * scale.x, y_axis.y * scale.y, z_axis.y * scale.z, center.y),
            (x_axis.z * scale.x, y_axis.z * scale.y, z_axis.z * scale.z, center.z),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def _add_oriented_sphere(
    name: str,
    center: Vec3,
    x_axis: Vec3,
    y_axis: Vec3,
    z_axis: Vec3,
    scale: Vec3,
    material: bpy.types.Material,
    segments: int,
    rings: int,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=0.5)
    obj = bpy.context.object
    obj.name = name
    obj.matrix_world = _basis_matrix(center, x_axis, y_axis, z_axis, scale)
    obj.data.materials.append(material)
    return obj


def _build_scene(spec: VesselSceneSpec) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    materials = {material.name: _material(material) for material in spec.materials}

    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=spec.radius * 0.96, depth=spec.length, location=(0, 0, 0))
    lumen = bpy.context.object
    lumen.name = "vessel_lumen_open_space"
    lumen.rotation_euler[1] = 1.57079632679
    lumen.data.materials.append(materials["lumen_marker"])
    lumen.display_type = "WIRE"

    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=spec.radius + 0.09, depth=spec.length, location=(0, 0, 0))
    basement = bpy.context.object
    basement.name = "basement_membrane_outer_reference"
    basement.rotation_euler[1] = 1.57079632679
    basement.data.materials.append(materials["basement_membrane"])
    basement.display_type = "WIRE"

    for cell in spec.cells:
        cortex = _add_oriented_sphere(
            f"{cell.name}_cortex",
            cell.center,
            cell.vessel_axis,
            cell.circumferential_axis,
            cell.radial_axis,
            cell.cell_scale,
            materials[cell.cortex_material],
            segments=24,
            rings=12,
        )
        cortex["biology_role"] = "endothelial cortex tile on vessel wall"
        cortex["cell_index"] = int(cell.name.rsplit("_", 1)[1])

        nucleus = _add_oriented_sphere(
            f"{cell.name}_nucleus",
            cell.nucleus_center,
            cell.vessel_axis,
            cell.circumferential_axis,
            cell.radial_axis,
            cell.nucleus_scale,
            materials[cell.nucleus_material],
            segments=16,
            rings=8,
        )
        nucleus["biology_role"] = "flattened endothelial nucleus"

    bpy.ops.object.light_add(type="AREA", location=(2.0, -5.0, 5.0))
    light = bpy.context.object
    light.name = "large_softbox_area_light"
    light.data.energy = 600.0
    light.data.size = 5.0

    bpy.ops.object.camera_add(location=(5.8, -8.0, 5.4), rotation=(1.012, 0.0, 0.66))
    bpy.context.scene.camera = bpy.context.object
    bpy.context.scene.render.engine = "BLENDER_EEVEE"


def main() -> None:
    args = _parse_args()
    spec = build_endothelium_vessel_scene(cell_count=args.cells, cells_per_ring=args.cells_per_ring)
    _build_scene(spec)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.blend_output)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend_output))
    bpy.ops.wm.usd_export(
        filepath=os.path.abspath(args.output),
        export_materials=True,
        export_cameras=True,
        export_lights=True,
    )
    print(f"Exported {spec.cell_count} endothelial cells to {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
