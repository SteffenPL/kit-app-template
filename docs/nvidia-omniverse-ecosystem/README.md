# NVIDIA Omniverse Ecosystem Notes

Last checked: 2026-05-23

This folder is a project-local orientation guide for the NVIDIA Omniverse, OpenUSD, physics, and GPU simulation ecosystem relevant to this cell-migration prototype.

## Start Here

- [Ecosystem overview](ecosystem-overview.md) - map of OpenUSD, Kit, USD Composer, PhysX, Warp, Newton, Isaac Sim/Lab, and SimReady.
- [Simulation stack](simulation-stack.md) - which simulation layer to use for static props, rigid interaction, overdamped cell mechanics, deformable experiments, and robot-learning style workloads.
- [UI physics authoring](ui-physics-authoring.md) - practical UI steps for making objects collide, fall, bounce, and interact instead of staying static.
- [Source index](source-index.md) - original sources used for these notes.

## How This Applies to This Repo

The current prototype should stay small and inspectable:

- Use OpenUSD as the scene and asset data model.
- Use the Kit app and extension structure already present in `source/apps/ku.demo.kit` and `source/extensions/ku.cell_sim/`.
- Use PhysX/Omni Physics for visual and mechanical smoke tests where rigid contact is useful.
- Keep the scientific cell-motion model overdamped rather than inertia-dominated.
- Use Python arrays first when that keeps force logic readable.
- Move force kernels to NVIDIA Warp once the model has stable state, force, and integration contracts.
- Treat Newton as a promising future path for GPU-accelerated, differentiable simulation, especially if the project grows toward robotics-style benchmark workloads.

Related local context:

- `AGENTS.md`
- `docs/plans/soft-sphere-cell-model-plan.md`
- `references/cell-migration-biophysics/README.md`
- `references/cell-migration-biophysics/reading-notes.md`
