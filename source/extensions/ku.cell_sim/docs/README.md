# KU Cell Simulation

Prototype extension for a small soft-cell culture on a substrate.

The model uses an explicit overdamped particle/spring shell rather than inertia-dominated rigid-body dynamics. This keeps the code close to the intended cell-scale force-balance model.

## Current State

- The demo creates a larger substrate with 10-20 seeded cells.
- Each cell has a visible cortex mesh and nucleus.
- Playback follows the Omniverse Kit timeline. The extension Start/Stop buttons proxy the Kit timeline rather than maintaining a separate animation state.
- The default simulation backend is a culture-level NVIDIA Warp backend.
- The Python backend remains available for readable reference behavior and plain headless tests.
- Current cell-cell collision is a simple center-radius soft repulsion in both Python and Warp.

## Important Files

- `ku/cell_sim/extension.py` - Kit extension lifecycle, timeline playback, and UI.
- `ku/cell_sim/scene.py` - USD scene creation and per-frame visual updates.
- `ku/cell_sim/simulation.py` - Python reference model and culture data structures.
- `ku/cell_sim/warp_backend.py` - Warp kernels for soft-cell updates and culture-level contact.
- `ku/cell_sim/tests/test_simulation.py` - Python and Kit/Warp behavior checks.

## Next Mechanics Targets

- Replace center-radius contact with cortex-particle contact using Warp spatial primitives such as `wp.HashGrid`.
- Add adhesion markers and substrate traction.
- Make the nucleus mechanically distinct, not only visually distinct.
- Add parameterized tests comparing Python and Warp behavior on small fixtures.
