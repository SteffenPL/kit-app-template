# Source Index

Last checked: 2026-05-23

This page lists the original sources used for the Omniverse ecosystem notes. Prefer these primary sources when refreshing the docs because NVIDIA product names, extension versions, and distribution paths change quickly.

## NVIDIA Omniverse and Kit

- [NVIDIA Omniverse docs index](https://docs.nvidia.com/omniverse/index.html) - top-level entry point for current Omniverse SDKs, APIs, Kit SDK, OpenUSD Exchange SDK, streaming, and extension references.
- [Omniverse Kit overview](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html) - explains Kit as the SDK for building Omniverse applications and lists its main components.
- [Kit App Template repository](https://github.com/NVIDIA-Omniverse/kit-app-template) - upstream template used by this repo.
- [USD Composer overview](https://docs.omniverse.nvidia.com/composer/latest/index.html) - describes USD Composer as a Kit-based world-building app.

## OpenUSD

- [OpenUSD home](https://openusd.org/release/index.html) - official OpenUSD documentation entry point.
- [OpenUSD core API overview](https://openusd.org/dev/api/usd_page_front.html) - core USD API concepts.
- [NVIDIA OpenUSD docs](https://docs.omniverse.nvidia.com/usd/latest/index.html) - NVIDIA's OpenUSD documentation hub.
- [OpenUSD physics schema](https://openusd.org/release/api/usd_physics_page_front.html) - USD Physics schema reference.
- [Learn OpenUSD composition basics](https://docs.nvidia.com/learn-openusd/latest/composition-basics/index.html) - practical learning material for layers, references, and composition.

## Physics and UI Authoring

- [Omniverse Physics developer guide](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/index.html) - explains USD Physics, PhysX schemas, Fabric, and the `omni.physx` runtime role.
- [Rigid bodies in Omni Physics](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html) - developer guide for rigid bodies, colliders, materials, and mass distribution.
- [Physics Authoring Toolbar](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/ux/source/omni.physx.supportui/docs/dev_guide/authoring_tools.html) - UI tools for physics authoring, rigid body manipulation, mass distribution, and inspection.
- [Physics visual authoring and debugging](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/authoring_debugging.html) - overview of physics UI and debugging extensions.
- [Isaac Sim adding props tutorial](https://docs.isaacsim.omniverse.nvidia.com/latest/core_api_tutorials/tutorial_core_adding_props.html) - practical UI sequence for adding rigid bodies, colliders, mass, collider visualization, and physics materials.
- [PhysX SDK documentation](https://nvidia-omniverse.github.io/PhysX/physx/) - standalone PhysX SDK documentation entry point.

## Warp and Newton

- [NVIDIA Warp documentation](https://nvidia.github.io/warp/) - primary Warp SDK docs.
- [Warp Omniverse extension docs](https://docs.omniverse.nvidia.com/extensions/latest/ext_warp.html) - how Warp appears inside Omniverse, including OmniGraph/Warp kernel nodes and sample scenes.
- [NVIDIA Newton Physics page](https://developer.nvidia.com/newton-physics) - NVIDIA overview of Newton as a Warp/OpenUSD-based physics engine.
- [Newton documentation](https://newton-physics.github.io/newton/stable/guide/overview.html) - Newton feature overview and solver orientation.
- [Newton GitHub repository](https://github.com/newton-physics/newton) - source repository for Newton.

## Isaac and SimReady

- [Isaac Sim Omniverse and USD docs](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/omniverse_usd/index.html) - Isaac Sim's OpenUSD and Omniverse reference section.
- [SimReady specification](https://docs.omniverse.nvidia.com/simready/latest/overview/simready-spec.html) - specification goals and current scope.
- [SimReady FAQ](https://docs.omniverse.nvidia.com/simready/latest/simready-faq.html) - explains the relationship between OpenUSD, AOUSD, and SimReady.
- [SimReady physics best practices](https://docs.omniverse.nvidia.com/simready/latest/simready-asset-creation/physics-best-practices.html) - practical physics metadata guidance for simulation-ready assets.

## Local Project Sources

- `AGENTS.md` - project intent and modeling guidance.
- `docs/plans/soft-sphere-cell-model-plan.md` - current implementation plan for the first soft-sphere cell scaffold.
- `references/cell-migration-biophysics/README.md` - biological and mechanical modeling anchors.
- `references/cell-migration-biophysics/reading-notes.md` - current local modeling summary.
- `source/apps/ku.demo.kit` - local Kit app configuration, including PhysX and Warp extension dependencies.
- `source/exts/ku.cell_sim/` - local cell-simulation extension.
