# UI Physics Authoring Guide

Last checked: 2026-05-23

Omniverse UI details vary between USD Composer, Isaac Sim, and a custom Kit app, but the physics concepts are consistent: a visual mesh does not automatically participate in simulation. To make objects interact, the stage needs physics metadata and a runtime that consumes it.

Sources:

- [Physics Authoring Toolbar](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/ux/source/omni.physx.supportui/docs/dev_guide/authoring_tools.html)
- [Physics visual authoring and debugging](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/authoring_debugging.html)
- [Isaac Sim adding props tutorial](https://docs.isaacsim.omniverse.nvidia.com/latest/core_api_tutorials/tutorial_core_adding_props.html)
- [SimReady physics best practices](https://docs.omniverse.nvidia.com/simready/latest/simready-asset-creation/physics-best-practices.html)

## The Five Pieces

| Piece | What it does | Static or dynamic? |
| --- | --- | --- |
| Visual geometry | What you see in the viewport | Neither by itself |
| Collider | Shape used for contact | Static if no rigid body |
| Rigid body | Makes a prim move under simulation | Dynamic unless configured kinematic/static |
| Mass/inertia | Controls how dynamic bodies respond | Dynamic body property |
| Physics material | Friction, restitution, density | Used by colliders/bodies |

If an object only has a mesh, it is visual. If it has a collider but no rigid body, it can block other bodies but usually will not move. If it has a rigid body but no collider, it can be simulated but may pass through things.

## Minimal UI Workflow

### 1. Create or Open a Stage

In a Kit-based UI such as USD Composer or Isaac Sim:

1. Use `File > New` or `File > New Stage`.
2. Add a ground plane, flat grid, or substrate.
3. Add a simple prop such as a cube or sphere.
4. Place the prop above the ground so movement is visible.

### 2. Make the Ground a Static Collider

Select the ground or substrate mesh, then add collider physics. Depending on the app and enabled extensions, this is typically available through one of these UI paths:

- Right click the prim, then choose `Add > Physics > Collider` or `Collider Presets`.
- Use a physics authoring toolbar command for static colliders.
- Use the Properties panel's physics section if the schema is already applied.

Expected behavior: the ground will not fall, but it can stop dynamic objects.

### 3. Make the Prop Dynamic

Select the prop's root prim and add a rigid body:

- Right click the prim, then choose `Add > Physics > Rigid Body`.
- If the asset has child meshes, apply the rigid body to the asset root and colliders to the relevant geometry prims.

Then add a collider to the prop's mesh:

- Right click the mesh, then choose `Add > Physics > Collider` or `Collider Presets`.
- Pick a simple approximation first: box, sphere, convex hull, or a small set of primitive colliders.

Expected behavior: when you press `Play`, the prop should fall, hit the ground collider, and stop or bounce depending on material settings.

### 4. Add Mass

Select the dynamic object and add mass properties:

- Right click the prim, then choose `Add > Physics > Mass`.
- In the Properties panel, set `Mass` or `Density`.
- If mass is left to automatic computation, verify the result is plausible for the scene scale.

Mass matters most for interaction between dynamic bodies and forces. A collider-only static object does not need to be treated like a movable body.

### 5. Add a Physics Material

Create or assign a physics material for surface behavior:

- Create a physics material from the object or scene context menu.
- Set `Static Friction`, `Dynamic Friction`, and `Restitution`.
- Assign the material to the collider or selected physics material slot in the Properties panel.

Typical effects:

- Higher friction reduces sliding.
- Higher restitution increases bounce.
- Density can contribute to automatic mass calculation.

### 6. Press Play and Inspect

Use the simulation `Play` control. Then inspect:

- Does the object move?
- Does it collide with the ground?
- Does it tunnel through?
- Does it spin, bounce, or slide as expected?
- Do material changes visibly affect behavior?

Use viewport visibility controls to show physics colliders. In Isaac Sim documentation this is shown through the viewport eye menu under `Show By Type > Physics > Colliders > All`; similar visibility controls may be exposed differently in other Kit apps.

## Simulation Mode Manipulation

The Physics Authoring Toolbar includes a rigid-body manipulator. In simulation mode, the transform gizmo can move rigid bodies by applying physics forces, so objects collide and constraints remain meaningful while you drag them. This differs from editing a transform while stopped, which simply authors a new pose.

Use simulation-mode manipulation when:

- You want to push one dynamic object into another.
- You want joints and links to respond while dragging.
- You want collision to remain active during interaction.

Use stopped transform editing when:

- You are placing an object before running the simulation.
- You are setting up initial conditions.
- You need precise coordinates.

## Troubleshooting

### Object Does Not Move

Likely causes:

- The object has a collider but no rigid body.
- Simulation is not playing.
- Gravity is disabled or the object is kinematic.
- The object starts already supported by a static collider.
- The rigid body API is applied to the wrong prim in the hierarchy.

Fix:

- Add `Rigid Body` to the movable object's root.
- Confirm the app's physics extensions are enabled.
- Press `Play`.
- Move the object above the ground and try again.

### Object Falls Through Ground

Likely causes:

- The ground is only visual geometry.
- The dynamic object has a rigid body but no collider.
- The collider is on the wrong child prim.
- Collision approximation is too small or misaligned.
- Scene scale or timestep is causing tunneling.

Fix:

- Add a collider to the ground.
- Add a collider to the object's visible mesh or an aligned primitive proxy.
- Show colliders in the viewport and verify their size and position.
- Use simpler collider approximations first.
- Reduce timestep or enable stronger collision settings if available.

### Object Collides Incorrectly

Likely causes:

- Mesh collider is too complex or concave.
- Collider approximation does not match the visual mesh.
- Mass distribution is unreasonable.
- Object scale is wrong.

Fix:

- Replace a complex mesh collider with primitive or convex approximations.
- Use the Properties panel to inspect collider approximation.
- Add or edit mass and inertia.
- Check stage units and object dimensions.

### Object Moves When Edited but Not Physically

Likely cause:

- You are editing transforms while stopped instead of manipulating the body in simulation mode.

Fix:

- Start simulation.
- Use the rigid-body manipulator or apply forces through the physics UI/API.

### A Cell Body Looks Dynamic but Behaves Like a Prop

Likely cause:

- The cell is being modeled as a rigid body instead of as a deformable or custom force-balance system.

Fix for this repo:

- Use PhysX only for surrounding rigid interaction and smoke tests.
- Keep cortex, nucleus, adhesions, and protrusion in explicit simulation state.
- Write the cell update as overdamped force balance, then visualize it through USD prim updates.

## Checklist for "Not Static"

- The simulation timeline is playing.
- The moving object has a rigid body.
- The moving object has a collider.
- The ground or obstacle has a collider.
- The moving object has plausible mass or density.
- Physics material values are plausible.
- Colliders are visible and aligned with meshes.
- The app has physics extensions loaded.
- You are using simulation-mode manipulation if you expect physical response while dragging.
