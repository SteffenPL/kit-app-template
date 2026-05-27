from __future__ import annotations

import omni.ext
import omni.kit.app
import omni.kit.commands
import omni.usd
import carb.eventdispatcher

from .scene import CAMERA_PATH, ROOT_PATH, CellScene
from .simulation import SoftCellSimulation


class CellSimulationExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._simulation = SoftCellSimulation()
        self._scene = None
        self._stage = None
        self._update_subscription = None
        self._frames_before_create = 12
        self._needs_viewport_focus = True

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
        self._stage = None
        self._simulation = None
        print("[ku.cell_sim] Soft cell simulation stopped")

    def _ensure_scene(self) -> None:
        context = omni.usd.get_context()
        stage = context.get_stage()
        if stage is None:
            context.new_stage()
            stage = context.get_stage()

        if stage is None:
            return

        root_exists = stage.GetPrimAtPath(ROOT_PATH).IsValid()
        if self._scene is not None and self._stage == stage and root_exists:
            return

        self._scene = CellScene(stage, self._simulation)
        self._scene.create()
        self._stage = stage
        self._needs_viewport_focus = True
        print("[ku.cell_sim] Created soft cell scene at /World/CellMigrationPrototype")

    def _focus_viewport(self) -> None:
        try:
            from omni.kit.viewport.utility import get_active_viewport
        except ImportError:
            return

        viewport = get_active_viewport()
        if not viewport:
            return

        viewport.camera_path = CAMERA_PATH
        resolution = viewport.resolution
        aspect_ratio = resolution[0] / resolution[1] if resolution[1] else 1.0
        omni.kit.commands.execute(
            "FramePrimsCommand",
            prim_to_move=CAMERA_PATH,
            prims_to_frame=[ROOT_PATH.pathString],
            time_code=viewport.time,
            aspect_ratio=aspect_ratio,
            zoom=0.72,
        )
        self._needs_viewport_focus = False

    def _on_update(self, event) -> None:
        if self._frames_before_create > 0:
            self._frames_before_create -= 1
            return

        if self._scene is None:
            self._ensure_scene()
            return

        self._ensure_scene()
        if self._needs_viewport_focus:
            self._focus_viewport()

        dt = event["dt"] if "dt" in event else 1.0 / 60.0
        self._simulation.step(float(dt))
        self._scene.update()
