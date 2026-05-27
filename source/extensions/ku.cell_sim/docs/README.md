# KU Cell Simulation

Prototype extension for a soft cell on a substrate.

The first model uses an explicit overdamped particle/spring shell rather than inertia-dominated rigid-body dynamics. This keeps the code close to the intended cell-scale force-balance model and leaves a clear path toward NVIDIA Warp kernels.

