# NVIDIA Omniverse Ecosystem Overview

Last checked: 2026-05-23

## Mental Model

Think of the ecosystem in layers:

1. OpenUSD describes scene data: geometry, transforms, materials, variants, payloads, references, and physics metadata.
2. Kit is the application SDK that hosts OpenUSD, rendering, extensions, UI, scripting, and simulation integrations.
3. USD Composer and Isaac Sim are Kit-based applications aimed at world building and robotics simulation.
4. Omni Physics/PhysX executes many built-in physics behaviors from USD Physics and NVIDIA PhysX schemas.
5. Warp is a Python-first GPU kernel framework for custom simulation and spatial computing.
6. Newton is a newer GPU-accelerated, extensible physics engine built on Warp and OpenUSD for robotics and research workflows.
7. SimReady is an OpenUSD-based specification direction for assets that carry enough metadata to work in simulation.

## Core Components

### OpenUSD

OpenUSD is the shared scene-description substrate. It is more than a file extension: it provides a composition model, schemas, layers, references, payloads, variants, Python/C++ APIs, and a stage abstraction. For this project, it is the right place to store the visible cell scene, substrate, materials, and any physics metadata that should survive outside the running app.

Use it for:

- Stage hierarchy and prim paths.
- Meshes, transforms, materials, cameras, and lights.
- Non-destructive overrides and variants.
- Physics schemas when an object needs rigid-body, collider, mass, or material metadata.

Sources:

- [OpenUSD home](https://openusd.org/release/index.html)
- [OpenUSD core API overview](https://openusd.org/dev/api/usd_page_front.html)
- [NVIDIA OpenUSD overview](https://docs.omniverse.nvidia.com/usd/latest/index.html)
- [OpenUSD physics schema](https://openusd.org/release/api/usd_physics_page_front.html)

### Omniverse Kit

Kit is the SDK for building Omniverse applications. It combines USD/Hydra, RTX rendering, Python/C++ extension loading, UI tooling, scripting, and application services. This repo is already a Kit App Template project, so local work should follow Kit extension conventions before introducing a separate framework.

Use it for:

- Custom app assembly in `.kit` files.
- Extension lifecycle and update loops.
- UI panels and controls.
- Direct access to the active USD stage.
- Wiring rendering and physics extensions into a runnable app.

Sources:

- [NVIDIA Omniverse docs index](https://docs.nvidia.com/omniverse/index.html)
- [Omniverse Kit overview](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html)
- [Kit App Template repository](https://github.com/NVIDIA-Omniverse/kit-app-template)

### USD Composer

USD Composer is a Kit-based world-building app. It is useful as an interactive stage editor for assembling, lighting, simulating, and rendering USD scenes. It is not the scientific core of this repo, but it is a useful way to inspect and author scene data.

Use it for:

- Visual stage authoring.
- Inspecting assets and layers.
- Trying physics authoring workflows.
- Checking whether USD assets are readable and visually sane.

Source:

- [USD Composer overview](https://docs.omniverse.nvidia.com/composer/latest/index.html)

### Omni Physics and PhysX

Omni Physics is the Omniverse integration layer that reads physics-related data from USD/Fabric, passes it to PhysX, runs simulation, and writes results back. USD Physics schemas cover common concepts such as rigid bodies, colliders, joints, mass, and physical materials; NVIDIA PhysX schemas extend this for Omniverse-specific capabilities.

Use it for:

- Rigid-body motion and collision.
- Static and dynamic colliders.
- Physics materials such as friction and restitution.
- Joints, articulations, and simulation debugging.
- Early smoke tests for contact and scene scale.

For the cell prototype, PhysX is useful for the substrate, contact intuition, and UI learning. It should not become the final biological model if that would force cell migration into inertia-dominated rigid-body dynamics.

Sources:

- [Omniverse Physics developer guide](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/index.html)
- [Rigid bodies in Omni Physics](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html)
- [Physics visual authoring and debugging](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/authoring_debugging.html)
- [PhysX SDK documentation](https://nvidia-omniverse.github.io/PhysX/physx/)

### NVIDIA Warp

Warp is a Python framework for GPU-accelerated simulation, robotics, geometry processing, and spatial computing. In Omniverse, Warp can be used through extensions and OmniGraph nodes. For this repo, Warp is the most natural later backend for explicit force updates because cell migration maps well to particle, spring, adhesion, volume, drag, and protrusion kernels.

Use it for:

- Custom simulation kernels.
- GPU-parallel force computation.
- Spatial queries and mesh/particle operations.
- A later high-performance backend once the CPU model is stable.

Sources:

- [NVIDIA Warp documentation](https://nvidia.github.io/warp/)
- [Warp Omniverse extension docs](https://docs.omniverse.nvidia.com/extensions/latest/ext_warp.html)

### Newton

Newton is an open-source, GPU-accelerated, extensible physics engine built on Warp and OpenUSD, with robotics and research workflows in mind. It also integrates MuJoCo Warp and includes multiple solver implementations. For this project, Newton is worth tracking, but it should not displace the simple current path unless we need a broader differentiable or robotics-oriented simulation engine.

Use it later if:

- The project needs differentiable simulation.
- We need solver infrastructure beyond a small custom overdamped model.
- We want to compare against robotics simulation workloads.
- Newton's OpenUSD/Warp integration becomes directly useful for the cell scaffold.

Sources:

- [NVIDIA Newton Physics page](https://developer.nvidia.com/newton-physics)
- [Newton documentation](https://newton-physics.github.io/newton/stable/guide/overview.html)
- [Newton GitHub repository](https://github.com/newton-physics/newton)

### Isaac Sim and Isaac Lab

Isaac Sim is NVIDIA's robotics simulation application/framework built on Omniverse and OpenUSD. Isaac Lab is a robot learning framework around simulation workflows. They matter here because their docs are often the clearest examples of USD physics authoring, scene setup, and simulation-ready assets, even if this project is not a robot project.

Use them as references for:

- Stage conventions and asset setup.
- Physics authoring examples.
- Sensors, robot schemas, and reinforcement-learning workflows if the project later branches that way.

Sources:

- [Isaac Sim Omniverse and USD docs](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/omniverse_usd/index.html)
- [Isaac Sim adding props tutorial](https://docs.isaacsim.omniverse.nvidia.com/latest/core_api_tutorials/tutorial_core_adding_props.html)

### SimReady

SimReady is an OpenUSD-based specification direction for simulation-ready assets. It emphasizes metadata such as semantic labels, physical properties, real-world scale, rigid-body physics, materials, and other information needed by simulation runtimes.

Use it for:

- Thinking about asset quality beyond visuals.
- Remembering that simulation assets need scale, mass, materials, collision shapes, and semantics.
- Future dataset or benchmark assets.

Sources:

- [SimReady specification](https://docs.omniverse.nvidia.com/simready/latest/overview/simready-spec.html)
- [SimReady physics best practices](https://docs.omniverse.nvidia.com/simready/latest/simready-asset-creation/physics-best-practices.html)

## Project Decision Map

| Project need | Best current layer |
| --- | --- |
| Store scene, cell mesh, substrate, camera, materials | OpenUSD |
| Build and run the prototype app | Omniverse Kit |
| Author or inspect a scene interactively | USD Composer or the local Kit app |
| Make boxes, spheres, props, and substrate collide | Omni Physics / PhysX |
| Make a cell migrate with overdamped force balance | Custom simulation state first |
| Accelerate explicit cell force updates | NVIDIA Warp |
| Explore differentiable GPU physics later | Newton |
| Keep imported assets simulation-ready | SimReady guidance |
