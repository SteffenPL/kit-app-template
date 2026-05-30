from __future__ import annotations

import argparse
import os
import sys


EXTENSION_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "source", "extensions", "ku.cell_sim")
)
if EXTENSION_ROOT not in sys.path:
    sys.path.insert(0, EXTENSION_ROOT)

from ku.cell_sim.authoring import build_endothelium_vessel_scene  # noqa: E402
from ku.cell_sim.usda_export import export_vessel_scene_usda  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a compact direct OpenUSD endothelial vessel scene.")
    parser.add_argument("--output", default="outputs/endothelium_vessel_usda/endothelium_vessel_420.usda")
    parser.add_argument("--cells", type=int, default=420)
    parser.add_argument("--cells-per-ring", type=int, default=14)
    args = parser.parse_args()

    spec = build_endothelium_vessel_scene(cell_count=args.cells, cells_per_ring=args.cells_per_ring)
    output_path = export_vessel_scene_usda(spec, args.output)
    print(f"Exported {spec.cell_count} endothelial cells to {output_path.resolve()}")


if __name__ == "__main__":
    main()
