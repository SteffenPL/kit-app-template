---
status: completed
created: 2026-05-23
---

# NVIDIA Omniverse Ecosystem Docs Plan

## Problem Frame

Create a repo-local markdown reference set that explains the current NVIDIA ecosystem around Omniverse, OpenUSD, simulation engines, NVIDIA Warp, and adjacent tools. The reference should help this project use Omniverse intentionally while building the biologically motivated cell-migration prototype described in `AGENTS.md` and `references/cell-migration-biophysics/README.md`.

The user specifically asked for markdown files, links to original sources, and practical user-interface guidance for adding physical elements and making objects interact rather than remain static.

## Scope

In scope:

- Add a compact index page for navigating the ecosystem summary.
- Summarize the roles of Omniverse Kit, USD Composer, OpenUSD, PhysX/Omni Physics, Warp, Newton, Isaac Sim/Lab, and SimReady.
- Keep links to original sources near the claims they support.
- Add practical UI guidance for physics authoring: rigid bodies, colliders, mass, physics materials, simulation mode, collision visualization, and common reasons objects remain static or pass through the ground.
- Connect ecosystem choices back to this repo's cell-migration direction: OpenUSD for scene state, Kit extension code for the app, PhysX as a visual/mechanical smoke test, CPU overdamped logic first, Warp/Newton as future scientific-simulation directions.

Out of scope:

- Installing Omniverse or NVIDIA drivers.
- Implementing new simulation code.
- Replacing the existing soft-sphere implementation plan.
- Writing a complete general Omniverse manual.

## Requirements Traceability

- "markdown files based summary and index" maps to `docs/nvidia-omniverse-ecosystem/README.md` plus focused child pages.
- "current nvidia ecosystem around omniverse, openusd, simulation engines, nvidia warp and more" maps to an ecosystem overview and simulation-stack page sourced from current official docs.
- "keep links to original sources" maps to explicit source links in each page and a source index.
- "outline also how to use the user interface eg how to add physical elements and make things interact not be static" maps to a UI physics authoring guide with checklists and troubleshooting.

## Implementation Units

### 1. Ecosystem Index

Files:

- `docs/nvidia-omniverse-ecosystem/README.md`

Content:

- A short navigation index.
- A "how to use this for the cell prototype" section.
- Links to each child page and source index.

Checks:

- The page links to every new markdown file.
- Repo-relative links resolve locally.

### 2. Ecosystem Overview

Files:

- `docs/nvidia-omniverse-ecosystem/ecosystem-overview.md`

Content:

- Explain the stack from OpenUSD data model through Kit applications, USD Composer, RTX rendering, PhysX/Omni Physics, Warp, Newton, Isaac Sim/Lab, and SimReady.
- Include a decision map for this project.
- Keep source links close to each section.

Checks:

- Each major ecosystem component has an original-source link.
- Claims about current products are dated "last checked 2026-05-23".

### 3. Simulation Stack Guide

Files:

- `docs/nvidia-omniverse-ecosystem/simulation-stack.md`

Content:

- Compare PhysX/Omni Physics, USD Physics schemas, Warp, Newton, Isaac Sim/Lab, and simple custom Python integrators.
- Explain which layer is appropriate for static scene composition, rigid-body interaction, overdamped cell mechanics, deformable/numerical experiments, and robot-learning style workloads.
- Tie the guidance to the repo's existing soft-sphere and cell-migration plans.

Checks:

- The guide does not imply PhysX rigid-body dynamics are the final scientific model for cell migration.
- It preserves the repo guidance that overdamped mechanics are preferred and Warp is a natural later backend.

### 4. UI Physics Authoring Guide

Files:

- `docs/nvidia-omniverse-ecosystem/ui-physics-authoring.md`

Content:

- Practical steps for making a scene object interact: create/open stage, add geometry, add rigid body, add collider, add mass, add physics material, play simulation, visualize colliders.
- Explain static collider versus dynamic rigid body behavior.
- Include troubleshooting for "nothing moves", "falls through ground", "collides incorrectly", and "gizmo moves without physical interaction."

Checks:

- UI actions are written as user-facing menu/property-panel steps.
- The guide distinguishes visual mesh, collider, rigid body, mass, and physics material.

### 5. Source Index

Files:

- `docs/nvidia-omniverse-ecosystem/source-index.md`

Content:

- Categorized links to official NVIDIA, OpenUSD, and project sources used in the docs.
- Brief notes on why each source matters.

Checks:

- No bare unsupported claims are left in the source index.
- Links are grouped so future updates are easy.

## Key Decisions

- Use official NVIDIA/OpenUSD/Newton sources as the primary authority because the ecosystem changes quickly.
- Store docs under `docs/nvidia-omniverse-ecosystem/` so they are separate from the biology reference bundle but easy to find.
- Keep the docs project-specific: the output should teach the current ecosystem only insofar as it helps this Omniverse cell-migration prototype choose tools and author interactive scenes.

## Verification

- Run link-oriented text checks with `rg` to catch placeholder URLs, TODOs, and broken repo-relative links.
- Run `git diff --check` to catch trailing whitespace.
- If a markdown linter is configured locally, run it; otherwise, rely on focused manual review and `git diff --check`.

## Risks

- NVIDIA product boundaries and names change quickly, so each page should include a "last checked" date.
- UI menu paths differ slightly between USD Composer, Isaac Sim, and custom Kit apps; the guide should call this out rather than pretending one exact UI applies everywhere.
- Simulation engines can be confused with scene schemas. The docs should separate "USD schema describes physical metadata" from "engine/extension executes simulation."
