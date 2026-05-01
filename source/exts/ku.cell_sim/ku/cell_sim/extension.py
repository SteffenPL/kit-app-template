from __future__ import annotations

import omni.ext
import omni.kit.app
import omni.usd

from .scene import CellScene
from .simulation import SoftCellSimulation


class CellSimulationExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._simulation = SoftCellSimulation()
        self._scene = None
        self._update_subscription = None

        self._ensure_stage()
        self._update_subscription = (
            omni.kit.app.get_app()
            .get_update_event_stream()
            .create_subscription_to_pop(self._on_update, name="ku.cell_sim.update")
        )

        print("[ku.cell_sim] Soft cell simulation started")

    def on_shutdown(self):
        self._update_subscription = None
        self._scene = None
        self._simulation = None
        print("[ku.cell_sim] Soft cell simulation stopped")

    def _ensure_stage(self) -> None:
        context = omni.usd.get_context()
        stage = context.get_stage()
        if stage is None:
            context.new_stage()
            stage = context.get_stage()

        if stage is None:
            return

        self._scene = CellScene(stage, self._simulation)
        self._scene.create()

    def _on_update(self, event) -> None:
        if self._scene is None:
            self._ensure_stage()
            return

        dt = getattr(event, "payload", {}).get("dt", 1.0 / 60.0)
        self._simulation.step(float(dt))
        self._scene.update()

