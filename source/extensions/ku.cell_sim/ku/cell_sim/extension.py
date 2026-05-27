from __future__ import annotations

import omni.ext
import omni.kit.app
import omni.usd
import carb.eventdispatcher

from .scene import CellScene
from .simulation import SoftCellSimulation


class CellSimulationExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._simulation = SoftCellSimulation()
        self._scene = None
        self._update_subscription = None

        self._ensure_stage()
        self._update_subscription = carb.eventdispatcher.get_eventdispatcher().observe_event(
            order=omni.kit.app.UPDATE_ORDER_PYTHON_EXEC_END_UPDATE,
            event_name=omni.kit.app.GLOBAL_EVENT_UPDATE,
            on_event=self._on_update,
            observer_name="ku.cell_sim.update",
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

        dt = event["dt"] if "dt" in event else 1.0 / 60.0
        self._simulation.step(float(dt))
        self._scene.update()
