# Agent Instructions

This project is an NVIDIA Omniverse Kit application prototype for learning Omniverse while building a biologically motivated cell-migration simulation.

## Project Intent

The near-term goal is a simple 3D model of a migrating cell on a substrate. Start with the smallest useful mechanical scaffold:

- a soft spherical or ellipsoidal cell body on a flat plane
- a visible nucleus inside the cell
- a deformable cortex/membrane representation
- optional cytoskeleton fibers and cell-matrix adhesion markers once the basic body is stable
- overdamped or high-friction motion, not inertia-dominated rigid-body dynamics

The first useful coding milestone can be just a soft sphere on a plane. Prefer a stable, inspectable prototype over premature biological detail.

## Modeling Guidance

- Treat cell-scale motion as overdamped force balance whenever possible.
- A high-friction PhysX prototype is acceptable as an early visual/mechanical smoke test.
- NVIDIA Warp is a good direction for the scientific core because explicit force kernels can map cleanly to spring, adhesion, volume, drag, and protrusion forces.
- Keep cytoplasm simple at first: approximate it with drag and volume/shape constraints rather than full fluid simulation.
- Keep the nucleus mechanically distinct: stiffer, slower, and visibly coupled to the cell body.
- Use the reference bundle in `references/cell-migration-biophysics/` when making modeling decisions.

## Coding Guidance

- Follow existing Omniverse Kit template conventions before introducing new structure.
- Keep prototype code small and easy to inspect. Avoid large abstractions until the model has at least one stable running loop.
- Prefer explicit names that reflect the biology and mechanics, such as `cortex`, `nucleus`, `adhesion`, `substrate`, `drag`, and `contractility`.
- Separate simulation state/update logic from visualization glue when the code grows beyond a minimal demo.
- Add tests or small reproducible scripts for simulation math where practical, especially force calculations and integration behavior.

## Git Workflow

- Regular commits and pushes are encouraged.
- Keep commits focused around coherent milestones, such as "add soft sphere scene", "add overdamped integrator", or "add adhesion springs".
- Do not rewrite or revert user changes unless explicitly asked.
- Before committing, review `git status` and make sure unrelated local edits are not accidentally included.

## References

- Start with `references/cell-migration-biophysics/README.md`.
- Use `references/cell-migration-biophysics/reading-notes.md` for the current modeling summary.
- Use `references/cell-migration-biophysics/to-download.md` and `bibliography.bib` for deeper reading.

