# Agent Instructions

This project is an NVIDIA Omniverse Kit application prototype for learning Omniverse while building a biologically motivated cell-migration simulation.

## Project Intent

The near-term goal is a simple 3D model of migrating cells on a substrate. The current prototype has moved beyond the first single-cell smoke test and now shows a small culture of soft spherical/ellipsoidal cells on a larger substrate.

Keep the scaffold biologically interpretable:

- a soft spherical or ellipsoidal cell body on a flat plane
- a visible nucleus inside the cell
- a deformable cortex/membrane representation
- multiple cells with simple cell-cell exclusion
- optional cytoskeleton fibers and cell-matrix adhesion markers once the basic body is stable
- overdamped or high-friction motion, not inertia-dominated rigid-body dynamics

Prefer a stable, inspectable prototype over premature biological detail.

## Current Architecture

- `source/extensions/ku.cell_sim/ku/cell_sim/simulation.py` contains the readable Python model and the cell-culture data structures.
- `source/extensions/ku.cell_sim/ku/cell_sim/warp_backend.py` contains the Warp kernels. The current default is a culture-level Warp backend, not one Warp backend per cell.
- `source/extensions/ku.cell_sim/ku/cell_sim/scene.py` owns the USD visualization bridge: substrate, cortex meshes, nuclei, materials, camera, lights, and the visual clip plane.
- `source/extensions/ku.cell_sim/ku/cell_sim/extension.py` owns Kit integration. The Omniverse timeline is the playback source of truth; extension Start/Stop buttons proxy the Kit timeline.
- The Python backend remains as a reference and headless test path. Do not remove it unless an equivalent CPU-verifiable path exists.

## Modeling Guidance

- Treat cell-scale motion as overdamped force balance whenever possible.
- Use NVIDIA Warp for the scientific core when model flexibility matters. Explicit kernels map cleanly to spring, adhesion, volume, drag, protrusion, and contact forces.
- Use PhysX for Omniverse learning, surrounding rigid interactions, or visual/mechanical smoke tests. Do not move the biological cell mechanics into PhysX if that would force inertia-dominated rigid-body behavior.
- Keep cytoplasm simple at first: approximate it with drag and volume/shape constraints rather than full fluid simulation.
- Keep the nucleus mechanically distinct: stiffer, slower, and visibly coupled to the cell body.
- Current cell-cell collision is center-radius soft repulsion at the culture level. The next collision upgrade should use Warp spatial tools such as `wp.HashGrid` for cortex-particle neighbor queries instead of hand-rolled broadphase code.
- Use the reference bundle in `references/cell-migration-biophysics/` when making modeling decisions.

## Coding Guidance

- Follow existing Omniverse Kit template conventions before introducing new structure.
- Keep prototype code small and easy to inspect. Avoid large abstractions until the model has at least one stable running loop.
- Prefer explicit names that reflect the biology and mechanics, such as `cortex`, `nucleus`, `adhesion`, `substrate`, `drag`, and `contractility`.
- Separate simulation state/update logic from visualization glue when the code grows beyond a minimal demo.
- Add tests or small reproducible scripts for simulation math where practical, especially force calculations and integration behavior.
- Keep playback coupled to the Kit timeline. Do not reintroduce an extension-local animation boolean that can disagree with the Omniverse play/stop controls.
- For new collision or adhesion work, update both the Python reference path and the Warp path, then add tests that exercise the Kit/Warp runtime when possible.
- Prefer culture-level data layouts for interactions between cells. Per-cell backends cannot see neighboring cells and are the wrong boundary for contact, adhesion, and collective migration.

## Git Workflow

- Regular commits and pushes are encouraged.
- Keep commits focused around coherent milestones, such as "add cortex particle contacts", "add adhesion springs", or "wire timeline playback".
- Do not rewrite or revert user changes unless explicitly asked.
- Before committing, review `git status` and make sure unrelated local edits are not accidentally included.

## References

- Start with `references/cell-migration-biophysics/README.md`.
- Use `references/cell-migration-biophysics/reading-notes.md` for the current modeling summary.
- Use `references/cell-migration-biophysics/to-download.md` and `bibliography.bib` for deeper reading.
