import threading
from typing import Dict, Any, Optional

import moderngl_window as mglw
import os
import cv2
import numpy as np
import time

from . import config
from .state_machine import StateMachine, AppState
from .undo_redo import UndoRedoManager, AddVoxelAction, DeleteVoxelAction, MoveVoxelAction
from ..vision.camera import CameraCapture
from ..render.renderer import Renderer
from ..voxel.voxel_grid import VoxelGrid
from ..voxel.interpolation import interpolate_positions
from ..ui.radial_menu import RadialMenu
from ..scene.scene_io import save_scene, load_scene


class HoloForgeWindow(mglw.WindowConfig):  # type: ignore[name-defined,misc]
    gl_version = (4, 3)
    title = "HoloForge"
    window_size = (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    fullscreen = True
    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app: Optional['HoloForgeApp'] = HoloForgeApp._instance
        assert self.app is not None, "HoloForgeApp instance not initialized"
        self.renderer = Renderer(self.ctx, config, self.app.shared_state, self.app.voxel_grid)

    def on_render(self, time: float, frame_time: float):
        actions = []
        app = self.app
        assert app is not None
        
        # 1. Clear events from shared state
        if lock := app.shared_state.get("frame_lock"):
            with lock:
                events = app.shared_state.get("gesture_events") or []
                app.shared_state["gesture_events"] = []
                # Keep original cursor mapping or handle it here?
                # The renderer currently does mapping in _update_cursor_from_hands called by render_frame.
        else:
            events = app.shared_state.get("gesture_events") or []
            app.shared_state["gesture_events"] = []

        # 2. Pre-update (Hover Detection)
        app._update_hover()

        # 3. Process Gesture Events
        for e in events:
            actions.extend(app.state_machine.process_event(e.get("name"), e))
        
        # 4. Handle Menu Interaction
        if app.state_machine.state == AppState.MENU_OPEN:
            if rxry := app.shared_state.get("cursor_normalized"):
                rx, ry, _ = rxry
                app.menu.update_selection((rx * 2.0 - 1.0, ry * 2.0 - 1.0))
            
            # Check for hold confirmation if "Clear Scene" is active
            if app.menu.active_index is not None and app.menu.mode == app.menu.MAIN:
                if app.menu.main_options[app.menu.active_index][0] == "Clear Scene":
                    if app.menu.hold_start_time is None:
                        app.menu.hold_start_time = time
                    elif time - app.menu.hold_start_time >= app.menu.hold_duration:
                        actions.extend(app.handle_actions([{"type": "menu_select", "option": "Clear Scene"}]))
                        app.menu.hold_start_time = None
                else:
                    app.menu.hold_start_time = None
            else:
                app.menu.hold_start_time = None

            for e in events:
                if e.get("name") == "RIGHT_PALM_OPEN":
                    if res := app.menu.confirm():
                        if res["type"] == "ui_nav":
                            pass # Mode change already handled in confirm()
                        elif res["type"] == "set_color":
                            actions.extend(app.handle_actions([{"type": "set_color", "color": res["color"], "name": res["name"]}]))
                        elif res["type"] == "action":
                            # Action trigger (excluding Clear Scene which is hold-based now)
                            if res["option"] != "Clear Scene":
                                actions.extend(app.handle_actions([{"type": "menu_select", "option": res["option"]}]))
                if e.get("name") == "LEFT_PALM_CLOSE":
                    actions.extend(app.state_machine.process_event("MENU_RELEASE"))
        
        # 5. FSM Update (e.g. timers)
        actions.extend(app.state_machine.update(app.shared_state))
        
        # 6. Dispatch Actions
        if actions:
            app.handle_actions(actions)

        # 7. Post-update (Sync State for Renderer)
        app.shared_state["fsm_state"] = app.state_machine.state.value
        app.shared_state["selected_voxel"] = app.state_machine.selected_voxel
        app.shared_state["pre_move_pos"] = app.state_machine.pre_move_pos
        app.shared_state["preview_buffer_positions"] = list(app.voxel_grid.build_buffer)
        
        self.renderer.render_frame(time, frame_time, menu=app.menu)

    def key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        if action != keys.ACTION_PRESS:
            return
        app = self.app
        assert app is not None
        
        # Undo / Redo (U / R)
        if key == keys.U:
            app.handle_actions([{"type": "undo"}])
        elif key == keys.R:
            app.handle_actions([{"type": "redo"}])
        
        elif key == keys.S:
            app.handle_actions([{"type": "menu_select", "option": "Save Scene"}])
        elif key == keys.L:
            app.handle_actions([{"type": "menu_select", "option": "Load Scene"}])
        elif key == keys.B:
            app.handle_actions([{"type": "menu_select", "option": "Toggle Bloom"}])
        elif key == keys.G:
            app.handle_actions([{"type": "menu_select", "option": "Toggle Grid Visibility"}])
        elif key == keys.C:
            app.handle_actions([{"type": "menu_select", "option": "Change Voxel Colour"}])
        elif key == keys.M:
            app.handle_actions([{"type": "menu_select", "option": "Cycle Material"}])
        elif key == keys.E:
            app.handle_actions([{"type": "menu_select", "option": "Toggle Emissive"}])
        elif key == keys.N:
            app.handle_actions([{"type": "menu_select", "option": "Toggle Continuous Build"}])
        elif key == keys.K:
            app.handle_actions([{"type": "menu_select", "option": "Clear Scene"}])


class HoloForgeApp:
    _instance: Optional['HoloForgeApp'] = None

    def __init__(self):
        HoloForgeApp._instance = self
        self.config = config
        self.shared_state: Dict[str, Any] = {}
        self.state_machine = StateMachine(self.config)
        self.camera = CameraCapture(self.config, self.shared_state)
        self.voxel_grid = VoxelGrid(
            default_color=self.config.VOXEL_DEFAULT_COLOR,
            default_emissive=self.config.DEFAULT_EMISSIVE,
            default_metallic=getattr(self.config, "DEFAULT_MATERIAL_METALLIC", 0.0),
            default_roughness=getattr(self.config, "DEFAULT_MATERIAL_ROUGHNESS", 0.5),
        )
        self.undo_redo = UndoRedoManager(self.voxel_grid)
        self.menu = RadialMenu()
        self.shared_state["grid_visible"] = True
        self.shared_state["bloom_enabled"] = getattr(self.config, "BLOOM_ENABLED", False)
        self.shared_state["menu_open"] = False
        self._started = False

    def _update_hover(self):
        # Simply check if cursor is near an existing voxel
        cur = self.shared_state.get("cursor_grid")
        if cur and self.voxel_grid.exists(cur):
            self.shared_state["hovered_voxel"] = cur
            self.state_machine.hovered_voxel = cur
        else:
            self.shared_state["hovered_voxel"] = None
            self.state_machine.hovered_voxel = None

    def run(self):
        if not self._started:
            self.camera.start()
            self._started = True

        def _safe_loop():
            try:
                while True:
                    lock = self.shared_state.get("frame_lock")
                    frame = None
                    cur = None
                    if lock:
                        with lock:
                            frame = self.shared_state.get("frame")
                            cur = self.shared_state.get("cursor_normalized")
                    else:
                        frame = self.shared_state.get("frame")
                        cur = self.shared_state.get("cursor_normalized")
                    
                    if frame is not None:
                        if cur:
                            h, w, _ = frame.shape
                            x = int(cur[0] * w)
                            y = int(cur[1] * h)
                            s = 10
                            x0 = max(0, x - s)
                            x1 = min(w, x + s)
                            y0 = max(0, y - s)
                            y1 = min(h, y + s)
                            c = np.array([int(255 * self.config.VOXEL_DEFAULT_COLOR[0]),
                                          int(255 * self.config.VOXEL_DEFAULT_COLOR[1]),
                                          int(255 * self.config.VOXEL_DEFAULT_COLOR[2])], dtype=np.uint8)
                            alpha = self.config.VOXEL_PREVIEW_ALPHA
                            region = frame[y0:y1, x0:x1]
                            blend = (region.astype(np.float32) * (1.0 - alpha) + c.astype(np.float32) * alpha).astype(np.uint8)
                            frame[y0:y1, x0:x1] = blend
                        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        cv2.imshow("HoloForge Safe Mode", bgr)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
            finally:
                cv2.destroyAllWindows()
                self.camera.stop()

        if os.environ.get("HOLOFORGE_SAFE_MODE") == "1":
            _safe_loop()
        else:
            try:
                mglw.run_window_config(HoloForgeWindow)
            except Exception as e:
                print("Failed to open OpenGL window, entering safe mode:", e)
                _safe_loop()
            finally:
                if self._started:
                    self.camera.stop()

    def handle_actions(self, actions):
        for a in actions:
            t = a.get("type")
            
            # Undo / Redo
            if t == "undo":
                self.undo_redo.undo()
            elif t == "redo":
                self.undo_redo.redo()

            elif t == "confirm_pending_start":
                if (pos := self.shared_state.get("cursor_grid")):
                    self.voxel_grid.build_buffer = [pos]
                    self.shared_state["build_last_pos"] = pos
            elif t == "commit_build_buffer":
                # For continuous build, we might have many points. 
                # Ideally each commit is one Undo action.
                # However, voxel_grid.commit_build_buffer doesn't return the points.
                pts = list(self.voxel_grid.build_buffer)
                if pts:
                    # We can't easily undo a batch of random adds with one AddVoxelAction
                    # unless we create a BatchAction. Let's keep it simple for now.
                    for p in pts:
                        action = AddVoxelAction(p, self.voxel_grid.default_color, self.voxel_grid.default_emissive, 
                                               self.voxel_grid.default_metallic, self.voxel_grid.default_roughness)
                        self.undo_redo.perform_action(action)
                    self.voxel_grid.build_buffer.clear()
                    self.voxel_grid.build_version += 1
            elif t == "discard_build_buffer":
                self.voxel_grid.discard_build_buffer()
                
            elif t == "delete_voxel_under_cursor":
                if (pos := self.shared_state.get("cursor_grid")) and self.voxel_grid.exists(pos):
                    vox = self.voxel_grid.voxels[pos]
                    action = DeleteVoxelAction(pos, vox.color, vox.emissive, vox.metallic, vox.roughness)
                    self.undo_redo.perform_action(action)
                    self.shared_state["delete_candidate"] = pos

            elif t == "move_start":
                # Visual only or snapshot? Handled in StateMachine
                pass
            elif t == "move_update":
                if (pos := self.shared_state.get("cursor_grid")):
                    self.state_machine.selected_voxel = pos
            elif t == "move_commit":
                old_p, new_p = a.get("old_pos"), a.get("new_pos")
                if old_p and new_p and old_p != new_p:
                    action = MoveVoxelAction(old_p, new_p)
                    self.undo_redo.perform_action(action)

            elif t == "building_start":
                if self.config.CONTINUOUS_BUILD:
                    self.voxel_grid.build_buffer = []
                    self.shared_state["build_last_pos"] = None
            elif t == "building_add_pos":
                if self.config.CONTINUOUS_BUILD:
                    if pos := self.shared_state.get("cursor_grid"):
                        last = self.shared_state.get("build_last_pos")
                        if last is None:
                            last = pos
                        pts = interpolate_positions(last, pos)
                        buf_set = set(self.voxel_grid.build_buffer)
                        for p in pts:
                            if p not in buf_set:
                                self.voxel_grid.build_buffer.append(p)
                                buf_set.add(p)
                        self.shared_state["build_last_pos"] = pos
            elif t == "orbit_start":
                self.shared_state["orbit_active"] = True
                cx, cy, cz = self.voxel_grid.centroid()
                self.shared_state["orbit_center"] = (cx * self.config.VOXEL_SIZE, cy * self.config.VOXEL_SIZE, cz * self.config.VOXEL_SIZE)
                self.shared_state["orbit_delta"] = (0.0, 0.0)
            elif t == "orbit_move":
                d = a.get("delta", (0.0, 0.0))
                prev = self.shared_state.get("orbit_delta", (0.0, 0.0))
                self.shared_state["orbit_delta"] = (prev[0] + d[0], prev[1] + d[1])
            elif t == "orbit_stop":
                self.shared_state["orbit_active"] = False
                self.shared_state["orbit_delta"] = (0.0, 0.0)
            elif t == "orbit_reset_view":
                self.shared_state["orbit_reset"] = True
            elif t == "shift_start":
                self.shared_state["shift_accum"] = (0.0, 0.0)
            elif t == "shift_delta":
                acc = self.shared_state.get("shift_accum", (0.0, 0.0))
                d = a.get("delta", (0.0, 0.0))
                acc = (acc[0] + d[0], acc[1] + d[1])
                step_x = int(round(acc[0] / self.config.VOXEL_SIZE))
                step_z = int(round(acc[1] / self.config.VOXEL_SIZE))
                if step_x != 0 or step_z != 0:
                    self.voxel_grid.shift((step_x, 0, step_z))
                    acc = (acc[0] - step_x * self.config.VOXEL_SIZE, acc[1] - step_z * self.config.VOXEL_SIZE)
                self.shared_state["shift_accum"] = acc
            elif t == "shift_stop":
                self.shared_state["shift_accum"] = (0.0, 0.0)
            elif t == "menu_open":
                self.menu.open_menu()
                self.shared_state["menu_open"] = True
            elif t == "menu_close":
                self.menu.close_menu()
                self.shared_state["menu_open"] = False
            elif t == "set_color":
                self.config.VOXEL_DEFAULT_COLOR = a.get("color")
                self.shared_state["hud_message"] = f"Colour set to {a.get('name')}"
                self.shared_state["hud_until"] = time.time() + 2.0
            elif t == "menu_select":
                option = a.get("option")
                if option == "Toggle Continuous Build":
                    self.config.CONTINUOUS_BUILD = not self.config.CONTINUOUS_BUILD
                    self.shared_state["hud_message"] = f"Continuous Build: {'On' if self.config.CONTINUOUS_BUILD else 'Off'}"
                    self.shared_state["hud_until"] = time.time() + 2.0
                elif option == "Toggle Grid Visibility":
                    gv = self.shared_state.get("grid_visible", True)
                    self.shared_state["grid_visible"] = not gv
                    self.shared_state["hud_message"] = f"Grid: {'On' if self.shared_state['grid_visible'] else 'Off'}"
                    self.shared_state["hud_until"] = time.time() + 2.0
                elif option == "Toggle Bloom":
                    be = self.shared_state.get("bloom_enabled", getattr(self.config, "BLOOM_ENABLED", False))
                    self.shared_state["bloom_enabled"] = not be
                    self.shared_state["hud_message"] = f"Bloom: {'On' if self.shared_state['bloom_enabled'] else 'Off'}"
                    self.shared_state["hud_until"] = time.time() + 2.0
                elif option == "Clear Scene":
                    self.voxel_grid.voxels.clear()
                    self.voxel_grid.build_buffer.clear()
                    self.undo_redo.undo_stack.clear()
                    self.undo_redo.redo_stack.clear()
                    self.shared_state["hud_message"] = "Scene cleared"
                    self.shared_state["hud_until"] = time.time() + 2.0
                elif option == "Change Voxel Colour":
                    pass
                elif option == "Toggle Emissive":
                    self.voxel_grid.default_emissive = not self.voxel_grid.default_emissive
                    self.shared_state["hud_message"] = f"Emissive: {'On' if self.voxel_grid.default_emissive else 'Off'}"
                    self.shared_state["hud_until"] = time.time() + 2.0
                elif option == "Cycle Material":
                    mats = [("Matte", (0.0, 0.8)), ("Metal", (0.9, 0.2)), ("Glass", (0.1, 0.05))]
                    midx = self.shared_state.get("material_index", 0)
                    midx = (midx + 1) % len(mats)
                    self.shared_state["material_index"] = midx
                    name, (m, r) = mats[midx]
                    self.voxel_grid.default_metallic = m
                    self.voxel_grid.default_roughness = r
                    self.shared_state["hud_message"] = f"Material: {name}"
                    self.shared_state["hud_until"] = time.time() + 2.0
                    self.shared_state["material_name"] = name
                elif option == "Save Scene":
                    p = save_scene(self.voxel_grid, self.shared_state, self.config)
                    self.shared_state["hud_message"] = f"Saved: {os.path.basename(p)}"
                    self.shared_state["hud_until"] = time.time() + 2.0
                elif option == "Load Scene":
                    p = load_scene(self.voxel_grid, self.shared_state, self.config)
                    self.shared_state["hud_message"] = f"Loaded: {os.path.basename(p)}"
                    self.shared_state["hud_until"] = time.time() + 2.0
        return []

