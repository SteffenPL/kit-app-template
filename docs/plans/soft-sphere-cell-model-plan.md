# Soft Sphere Cell Model Plan

Created: 2026-05-01
Status: draft

## Problem Frame

Build the first runnable model for a cell-migration prototype in Omniverse Kit. The first milestone should be a soft spherical cell on a flat substrate, with overdamped or high-friction behavior. This is primarily a learning and scaffolding milestone: it should establish scene creation, simulation update flow, and a clean place to add nucleus, cortex, adhesion, cytoskeleton, and Warp kernels later.

## Scope

In scope:

- Create a simple Omniverse scene with a substrate plane and soft cell body.
- Represent the cell body as a deformable sphere-like mesh or particle shell.
- Use an overdamped update rule for the model logic, even if the first visual version is high-friction and simplified.
- Add a visible nucleus if it is cheap enough for the first pass; otherwise reserve it for the second pass.
- Keep parameters explicit: drag, stiffness, gravity or plane contact, and timestep.

Out of scope for the first milestone:

- Full cytoplasm fluid simulation.
- Biochemical polarity.
- Quantitative parameter calibration.
- Detailed molecular clutch kinetics.
- Full active-gel or finite-element mechanics.

## Recommended Technical Direction

Start with a Python Omniverse extension that owns a small simulation loop and draws/updates USD prims. Keep PhysX useful for scene contact and visual sanity checks, but do not make rigid-body inertia the scientific model.

The first implementation can use a CPU Python overdamped integrator for clarity:

```text
position += dt * force / drag
```

Once the force model is understandable and stable, move the same state arrays and force update to NVIDIA Warp. The app already enables `omni.warp.core` in `source/apps/ku.demo.kit`, so Warp is a natural second implementation backend.

## Implementation Units

### 1. Simulation Extension Skeleton

Likely files:

- `source/extensions/ku.cell_sim/extension.toml`
- `source/extensions/ku.cell_sim/ku/cell_sim/extension.py`
- `source/extensions/ku.cell_sim/ku/cell_sim/__init__.py`

Behavior:

- Register a Kit extension.
- On startup, create or reset a stage with the substrate and cell.
- Add a simple update callback for simulation steps.
- Expose minimal controls or constants for timestep and reset.

Tests/checks:

- App starts with the extension enabled.
- Stage contains substrate and cell prims.
- Reset does not duplicate stale prims.

### 2. Overdamped Soft Sphere Core

Likely files:

- `source/extensions/ku.cell_sim/ku/cell_sim/simulation.py`
- `source/extensions/ku.cell_sim/tests/test_simulation.py`

Behavior:

- Store particle positions and velocities or position deltas.
- Build an approximate sphere shell from particles or mesh vertices.
- Apply spring forces between neighboring particles.
- Apply soft plane-contact forces.
- Apply drag-based integration.

Tests/checks:

- With no external forces, a relaxed sphere remains numerically stable.
- A node below the substrate receives an upward contact force.
- Higher drag produces smaller displacement for the same force and timestep.
- Spring forces pull stretched neighbor pairs back toward rest length.

### 3. USD Visualization Bridge

Likely files:

- `source/extensions/ku.cell_sim/ku/cell_sim/scene.py`

Behavior:

- Create substrate, cell surface, and optional nucleus prims.
- Update cell mesh points or particle markers from simulation state.
- Use distinct materials for substrate, cortex/cell body, and nucleus.

Tests/checks:

- Visual scene is readable at app startup.
- Cell is above or touching the plane, not hidden below it.
- Materials make the cell and substrate visually distinct.

### 4. Nucleus as Second Milestone

Likely files:

- `source/extensions/ku.cell_sim/ku/cell_sim/simulation.py`
- `source/extensions/ku.cell_sim/ku/cell_sim/scene.py`

Behavior:

- Add a central nucleus sphere or ellipsoid.
- Couple it to cortex particles with soft tethers.
- Give it higher drag or stiffness than cortex nodes.

Tests/checks:

- Nucleus remains inside the cell body under ordinary motion.
- Tether forces pull displaced nucleus state back toward the cell center.
- Nucleus material remains visually distinct from cytoplasm/cortex.

### 5. Warp Backend Later

Likely files:

- `source/extensions/ku.cell_sim/ku/cell_sim/warp_simulation.py`

Behavior:

- Port force and integration arrays to Warp kernels.
- Keep the CPU implementation as a readable reference path until Warp behavior matches.

Tests/checks:

- CPU and Warp backends produce comparable one-step results for a tiny fixture.
- Warp backend can run repeatedly without reallocating all state each frame.

## Sequencing

1. Create the extension skeleton and make the app load it.
2. Create a static scene: plane, sphere/cell, camera, materials.
3. Add a CPU overdamped particle/spring sphere.
4. Update USD geometry every frame from simulation state.
5. Add a nucleus.
6. Add adhesion points and front-biased protrusion.
7. Move compute-heavy force updates to Warp.

## Key Risks

- Soft-body behavior through PhysX may be harder to control scientifically than an explicit integrator.
- Updating USD mesh geometry every frame may be enough for a prototype but could become slow.
- Warp integration inside Kit may require some extension packaging details beyond a plain Python module.
- The model can look biological before it behaves biologically, so keep parameters and assumptions visible in code and docs.

## Success Criteria

- The app opens a scene with a soft sphere on a plane.
- The simulation step is easy to read and uses overdamped force balance.
- The cell object remains stable for at least several seconds of simulation.
- The next components, nucleus and adhesions, have obvious extension points.

