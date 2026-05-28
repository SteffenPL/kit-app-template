from __future__ import annotations

import omni.ext
import omni.kit.app
import omni.kit.commands
import omni.timeline
import omni.ui as ui
import omni.usd
import carb.eventdispatcher

from .scene import CAMERA_PATH, ROOT_PATH, CellScene
from .simulation import CellCultureSimulation


class CellSimulationExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        self._simulation = CellCultureSimulation()
        self._scene = None
        self._stage = None
        self._window = None
        self._animation_status = None
        self._timeline = omni.timeline.get_timeline_interface()
        self._update_subscription = None
        self._frames_before_create = 2
        self._needs_viewport_focus = True
        self._step_accumulator = 0.0
        self._step_interval = 1.0 / 12.0
        self._build_window()

        self._update_subscription = carb.eventdispatcher.get_eventdispatcher().observe_event(
            order=omni.kit.app.UPDATE_ORDER_PYTHON_EXEC_END_UPDATE,
            event_name=omni.kit.app.GLOBAL_EVENT_UPDATE,
            on_event=self._on_update,
            observer_name="ku.cell_sim.update",
        )

        print("[ku.cell_sim] Soft cell simulation started")

    def on_shutdown(self):
        self._update_subscription = None
        self._window = None
        self._animation_status = None
        self._timeline = None
        self._scene = None
        self._stage = None
        self._simulation = None
        print("[ku.cell_sim] Soft cell simulation stopped")

    def _build_window(self) -> None:
        self._window = ui.Window("Cell Demo", width=220, height=156, visible=True)
        with self._window.frame:
            with ui.VStack(spacing=6):
                ui.Label("Cell culture")
                self._animation_status = ui.Label("Timeline: paused")
                ui.Button("Create Scene", height=28, clicked_fn=self._recreate_scene)
                ui.Button("Reset Motion", height=28, clicked_fn=self._reset_motion)
                with ui.HStack(spacing=6, height=28):
                    ui.Button("Start", clicked_fn=self._start_animation)
                    ui.Button("Stop", clicked_fn=self._stop_animation)

    def _is_timeline_playing(self) -> bool:
        return bool(self._timeline is not None and self._timeline.is_playing())

    def _sync_animation_status(self) -> None:
        if self._animation_status is not None:
            self._animation_status.text = "Timeline: playing" if self._is_timeline_playing() else "Timeline: paused"

    def _start_animation(self) -> None:
        if self._timeline is not None:
            self._timeline.play()
        self._step_accumulator = 0.0
        self._sync_animation_status()
        print("[ku.cell_sim] Kit timeline started")

    def _stop_animation(self) -> None:
        if self._timeline is not None:
            self._timeline.pause()
        self._step_accumulator = 0.0
        self._sync_animation_status()
        print("[ku.cell_sim] Kit timeline paused")

    def _get_or_create_stage(self):
        context = omni.usd.get_context()
        stage = context.get_stage()
        if stage is None:
            context.new_stage()
            stage = context.get_stage()
        return stage

    def _ensure_scene(self) -> None:
        stage = self._get_or_create_stage()
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

    def _recreate_scene(self) -> None:
        stage = self._get_or_create_stage()
        if stage is None:
            return

        self._simulation = CellCultureSimulation()
        self._scene = CellScene(stage, self._simulation)
        self._scene.create()
        self._stage = stage
        self._needs_viewport_focus = True
        self._stop_animation()
        print("[ku.cell_sim] Recreated cell culture scene")

    def _reset_motion(self) -> None:
        if self._simulation is None:
            return

        self._simulation.reset()
        if self._scene is not None:
            self._scene.create()
            self._needs_viewport_focus = True
        self._stop_animation()
        print("[ku.cell_sim] Reset cell culture motion")

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

        self._sync_animation_status()
        if not self._is_timeline_playing():
            return

        dt = event["dt"] if "dt" in event else 1.0 / 60.0
        self._step_accumulator += min(float(dt), 0.1)
        if self._step_accumulator < self._step_interval:
            return

        step_dt = self._step_accumulator
        self._step_accumulator = 0.0
        self._simulation.step(step_dt)
        self._scene.update()
