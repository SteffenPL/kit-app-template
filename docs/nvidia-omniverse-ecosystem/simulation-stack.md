# Simulation Stack Guide

Last checked: 2026-05-23

## Short Version

For this repo:

- Use USD for data.
- Use Kit for the app and extension runtime.
- Use PhysX/Omni Physics for built-in rigid interactions and UI learning.
- Use a small custom overdamped integrator for cell-scale mechanics.
- Move the custom force update to Warp when the model is stable.
- Revisit Newton if the project needs differentiable GPU physics or broader solver infrastructure.

## Layer Comparison

| Layer | What it is | Best for | Not ideal for |
| --- | --- | --- | --- |
| OpenUSD | Scene description, composition, schemas, APIs | Persistent stage data, geometry, materials, physics metadata | Executing simulation by itself |
| USD Physics schema | Standard USD metadata for physics concepts | Marking prims as rigid bodies, colliders, joints, masses, materials | Custom biological force laws by itself |
| PhysX / Omni Physics | Runtime physics integration inside Omniverse | Rigid bodies, colliders, contacts, joints, articulations, smoke tests | Final overdamped cell mechanics if it forces inertial behavior |
| Python custom integrator | Plain readable state and force code | First cell model, tests, force design, numerical clarity | Large particle counts or heavy 3D kernels |
| NVIDIA Warp | Python-authored GPU kernels | Parallel force updates, particles, springs, mesh deformation, spatial queries | Premature use before state and forces are clear |
| Newton | Warp/OpenUSD-based GPU physics engine | Research physics, differentiable simulation, robot-learning style workloads | Small first prototype if it adds too much surface area |
| Isaac Sim / Isaac Lab | Robotics simulation app and learning framework | Robotics, sensors, robot schemas, RL examples, physics setup references | A cell-migration app unless the project shifts toward robotics |
| SimReady | Asset-readiness specification direction | Making assets carry usable simulation metadata | Executing dynamics |

Sources:

- [Omniverse Physics developer guide](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/index.html)
- [OpenUSD physics schema](https://openusd.org/release/api/usd_physics_page_front.html)
- [Warp documentation](https://nvidia.github.io/warp/)
- [Newton documentation](https://newton-physics.github.io/newton/stable/guide/overview.html)
- [SimReady specification](https://docs.omniverse.nvidia.com/simready/latest/overview/simready-spec.html)

## Recommended Path for the Cell Prototype

### 1. Keep Scene State in USD

The stage should contain the visual and inspectable world:

- `/World/Substrate`
- `/World/Cell`
- `/World/Cell/Cortex`
- `/World/Cell/Nucleus`
- `/World/Cell/Adhesions`
- cameras, lights, and materials

Use USD prims and attributes for things that should be inspectable, saved, or layered. Do not hide core state only inside Python objects if a user needs to inspect it in the stage.

### 2. Use PhysX for Interaction Smoke Tests

PhysX is good for answering questions such as:

- Does the substrate behave like a collider?
- Do props fall under gravity?
- Are object scales reasonable?
- Are collision shapes aligned with visuals?
- Do friction and restitution values visibly change interaction?

PhysX is not the main scientific model for cell migration here. The local modeling guidance prefers overdamped force balance, and the existing soft-sphere plan says PhysX should not force the model into rigid-body inertia.

### 3. Use a Custom Overdamped Integrator for the First Cell Mechanics

The current cell model should stay close to:

```text
drag_i * velocity_i = sum(forces_i)
position_i += dt * velocity_i
```

This makes the biology-facing force pathways explicit:

- cortex springs
- volume or shape preservation
- plane repulsion
- adhesion springs
- contractility
- front-biased protrusion
- nucleus-cortex tethers
- higher nucleus drag or stiffness

This is easier to test than a black-box engine path. Keep the CPU implementation as the readable reference even after adding Warp.

### 4. Move Compute to Warp After Contracts Stabilize

Warp becomes useful once the model has stable arrays and one-step tests:

- positions
- velocities or position deltas
- spring endpoints
- rest lengths
- adhesion state
- force accumulators
- drag coefficients

Use Warp for parallel kernels that compute forces and integrate positions. Keep the initial kernel surface close to the Python reference so CPU/Warp comparisons are possible.

### 5. Track Newton, But Do Not Start There

Newton's Warp/OpenUSD foundation makes it relevant. It may become useful for differentiable simulation, solver comparisons, and robot-learning style experiments. For the current prototype, it is a later evaluation item because the immediate value is understanding the cell force model, not adopting the largest engine.

## Choosing a Physics Representation

| Thing in scene | First representation | When to upgrade |
| --- | --- | --- |
| Substrate | Static collider plane or USD mesh with collider | Add elasticity or ECM fibers when adhesion mechanics need it |
| Cell cortex | Custom spring shell, visualized as mesh/points | Warp kernels for particle count and spatial operations |
| Cytoplasm | Drag plus volume/shape constraint | Porous/fluid model only after scaffold is stable |
| Nucleus | Stiffer visible body with high drag and tethers | Deformable nucleus if squeezing through ECM becomes a target |
| Adhesions | Dynamic spring bonds to substrate | Molecular clutch kinetics and force-dependent detachment |
| Cytoskeleton | Contractile springs/fibers | Active gel or polarity fields |

## Engine vs Schema

Do not conflate these:

- USD Physics schema describes that an object has physical properties.
- PhysX/Omni Physics executes simulation inside Omniverse.
- Warp executes custom kernels you write.
- Newton is an engine built on Warp/OpenUSD.
- SimReady describes asset capability expectations.

This distinction matters because a USD file can contain collider and mass metadata without magically executing dynamics outside a compatible runtime.

## Practical Stability Rules

- Use real-world scale consistently.
- Prefer simple collision shapes for early interaction tests.
- Start with high damping and small timesteps.
- Keep mass, drag, and stiffness visible as parameters.
- Test one-step force behavior before tuning visuals.
- Visualize colliders and adhesion points when debugging.
- Keep "looks right" separate from "mechanically justified."
