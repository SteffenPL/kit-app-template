# Reading Notes

## Modeling Decision

Use overdamped dynamics as the scientific core:

```text
drag_i * velocity_i = sum(forces_i)
```

This matches the cellular scale better than inertia-dominated rigid-body physics. A high-friction PhysX version can be useful for early Omniverse learning, but the first serious model should use explicit force updates, likely in Python first and then NVIDIA Warp.

## Literature Themes

### 1. Migration Cycle

Adherent cell migration is commonly decomposed into:

- leading-edge protrusion
- new adhesion formation
- traction generation through actin/adhesion coupling
- rear adhesion release and cell-body contraction

For the prototype, this maps naturally to a front-biased protrusion force, dynamic adhesion springs, contractile cytoskeletal springs, and rear detachment.

### 2. Molecular Clutch

The molecular clutch picture treats adhesions as force-transmitting couplings between retrograde actin flow and the substrate. If engaged, actin-generated or contractile forces become substrate traction and forward cell movement. If disengaged, actin flow slips and motion is inefficient.

Prototype implication:

- adhesion sites should attach/detach dynamically
- adhesion force should depend on extension
- detachment can initially be stochastic or force-threshold based
- substrate stiffness and adhesion density should be tunable

### 3. Cortex and Cytoskeleton as Active Matter

The actomyosin cortex is not a passive elastic shell. It consumes energy and generates active contractile stresses. A first model can represent this with contractile springs or preferred edge-length reduction in the cortex/fiber network.

Prototype implication:

- contractility should be a parameter
- front/rear polarity should bias contractility and protrusion
- no need for a full active-gel PDE in the first version

### 4. Cytoplasm as Viscous Drag First

Full cytoplasmic flow, poroelasticity, and hydrodynamic coupling are major upgrades. For a first scaffold, treating cytoplasm as drag and volume preservation is acceptable.

Prototype implication:

- each particle/node has drag
- nucleus can have higher drag
- preserve cell volume/shape with soft constraints

### 5. Nucleus as a Mechanical Obstacle

The nucleus should be mechanically distinct: larger, stiffer, and slower-moving than surrounding cortex/cytoplasm. It can lag behind the leading edge and be pulled forward by cytoskeletal links.

Prototype implication:

- internal nucleus sphere/ellipsoid
- nucleus-cortex tethers
- collision or exclusion between nucleus and cortex
- optional nucleus deformation later

## Realistic First Milestone

Create an Omniverse scene with:

- flat substrate
- deformable cell shell
- visible nucleus
- visible cytoskeletal fibers
- visible adhesion points
- update loop that applies overdamped forces
- sliders or config values for adhesion stiffness, detach probability, cortical stiffness, contractility, drag, and protrusion bias

Success means the cell visibly migrates in a stable way and changing parameters produces interpretable behavior, even if not quantitatively calibrated.

