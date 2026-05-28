# Soft Sphere Cell Model Plan

Created: 2026-05-01
Status: implemented baseline; use as historical scaffold

## Problem Frame

Build the first runnable model for a cell-migration prototype in Omniverse Kit. The first milestone should be a soft spherical cell on a flat substrate, with overdamped or high-friction behavior. This is primarily a learning and scaffolding milestone: it should establish scene creation, simulation update flow, and a clean place to add nucleus, cortex, adhesion, cytoskeleton, and Warp kernels later.

## Current Implementation Snapshot

As of 2026-05-29, the repo has passed the first milestone and now contains:

- a Kit extension under `source/extensions/ku.cell_sim/`
- a larger substrate with a seeded 10-20 cell culture
- semi-transparent cortex meshes and visible nuclei
- a visual clip plane
- extension UI for scene creation, reset, and timeline playback
- playback driven by the Omniverse Kit timeline
- a Python reference path for headless tests
- a culture-level Warp backend as the default simulation path
- center-radius soft cell-cell repulsion in both Python and Warp

Treat the remaining sections as design history and as a checklist for future mechanics, not as an unstarted plan.

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

The current default backend is NVIDIA Warp. The Python implementation remains as a reference path for tests and for checking small force-law changes before moving them into kernels.

## Implementation Units

### 1. Simulation Extension Skeleton

Likely files:

- `source/extensions/ku.cell_sim/config/extension.toml`
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
- `source/extensions/ku.cell_sim/ku/cell_sim/tests/test_simulation.py`

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

### 5. Warp Backend

Likely files:

- `source/extensions/ku.cell_sim/ku/cell_sim/warp_backend.py`

Behavior:

- Port force and integration arrays to Warp kernels.
- Keep the CPU implementation as a readable reference path until Warp behavior matches.
- Keep culture-level data in shared arrays so cell-cell contact and later adhesion can see neighboring cells.
- Use Warp spatial primitives for the next contact upgrade rather than custom broadphase code.

Tests/checks:

- CPU and Warp backends produce comparable one-step results for a tiny fixture.
- Warp backend can run repeatedly without reallocating all state each frame.
- Warp culture backend separates overlapping cells in the Kit test runtime.

## Sequencing

1. Create the extension skeleton and make the app load it.
2. Create a static scene: plane, sphere/cell, camera, materials.
3. Add a CPU overdamped particle/spring sphere.
4. Update USD geometry every frame from simulation state.
5. Add a nucleus.
6. Move compute-heavy force updates to Warp.
7. Add cell-cell exclusion and then cortex-particle contact.
8. Add adhesion points and front-biased protrusion.

## Key Risks

- Soft-body behavior through PhysX may be harder to control scientifically than an explicit integrator.
- Updating USD mesh geometry every frame may be enough for a prototype but could become slow.
- Warp integration inside Kit requires extension dependencies and Kit-runtime tests, not only plain Python tests.
- The model can look biological before it behaves biologically, so keep parameters and assumptions visible in code and docs.

## Success Criteria

- The app opens a scene with soft cells on a substrate.
- The simulation step is easy to read and uses overdamped force balance.
- The cell object remains stable for at least several seconds of simulation.
- The next components, nucleus and adhesions, have obvious extension points.
