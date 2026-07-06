import os
import time
from typing import Dict, Any, Optional

import numpy as np
import cv2
import moderngl
from pyrr import Matrix44, Vector3

from .grid import HolographicGrid
from ..ui.cursor_preview import CursorPreview
from .camera_controller import CameraController

class Renderer:
    def __init__(self, ctx: moderngl.Context, config, shared_state: Dict[str, Any], voxel_grid):
        self.ctx = ctx
        print(f"--- GPU Info ---")
        print(f"Vendor:   {self.ctx.info['GL_VENDOR']}")
        print(f"Renderer: {self.ctx.info['GL_RENDERER']}")
        print(f"Version:  {self.ctx.info['GL_VERSION']}")
        print(f"----------------")
        self.config = config
        self.state = shared_state
        self.voxel_grid = voxel_grid
        self.bg_prog = self._load_program("camera_bg.vert", "camera_bg.frag")
        self.bg_vao = self._create_fullscreen_quad(self.bg_prog)
        self.camera_tex: Optional[moderngl.Texture] = None
        self.ui_text_tex: Optional[moderngl.Texture] = None
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.grid = HolographicGrid(self.ctx, self.config.GRID_COLOR)
        self.cursor = CursorPreview(self.config.VOXEL_SIZE)
        self._last_rz = 0.5
        self.voxel_prog = self._load_program("voxel.vert", "voxel.frag")
        self.bright_prog = self._load_program("camera_bg.vert", "bloom_bright.frag")
        self.blur_h_prog = self._load_program("camera_bg.vert", "bloom_blur_h.frag")
        self.blur_v_prog = self._load_program("camera_bg.vert", "bloom_blur_v.frag")
        self.composite_prog = self._load_program("camera_bg.vert", "bloom_composite.frag")
        self.ui_prog = self._load_program("ui_glass.vert", "ui_glass.frag")
        self.ui_vao = self._create_fullscreen_quad(self.ui_prog)
        self.ui_overlay_prog = self._load_program("camera_bg.vert", "ui_overlay.frag")
        self.ui_overlay_vao = self._create_fullscreen_quad(self.ui_overlay_prog)
        self._voxel_vao = None
        self._voxel_inst_offsets = None
        self._voxel_inst_colors = None
        self._voxel_inst_emissive = None
        self._last_voxel_version = -1
        self._preview_vao = None
        self._preview_inst_offsets = None
        self._preview_inst_colors = None
        self._preview_inst_emissive = None
        self._last_preview_hash = None
        self._delete_vao = None
        self._delete_inst_offset = None
        self._delete_inst_color = None
        self._delete_inst_emissive = None
        self.cam = CameraController(
            radius=self.config.ORBIT_DEFAULT_RADIUS,
            smooth=self.config.ORBIT_SMOOTH_FACTOR,
            sensitivity=self.config.ORBIT_SENSITIVITY,
        )
        s = self.config.VOXEL_SIZE * 0.5
        faces = [
            ((-s, -s, -s), ( s, -s, -s), ( s,  s, -s), (0.0, 0.0, -1.0)),
            ((-s, -s, -s), ( s,  s, -s), (-s,  s, -s), (0.0, 0.0, -1.0)),
            ((-s, -s,  s), ( s, -s,  s), ( s,  s,  s), (0.0, 0.0, 1.0)),
            ((-s, -s,  s), ( s,  s,  s), (-s,  s,  s), (0.0, 0.0, 1.0)),
            ((-s, -s, -s), (-s,  s, -s), (-s,  s,  s), (-1.0, 0.0, 0.0)),
            ((-s, -s, -s), (-s,  s,  s), (-s, -s,  s), (-1.0, 0.0, 0.0)),
            (( s, -s, -s), ( s,  s, -s), ( s,  s,  s), (1.0, 0.0, 0.0)),
            (( s, -s, -s), ( s,  s,  s), ( s, -s,  s), (1.0, 0.0, 0.0)),
            ((-s, -s, -s), ( s, -s, -s), ( s, -s,  s), (0.0, -1.0, 0.0)),
            ((-s, -s, -s), ( s, -s,  s), (-s, -s,  s), (0.0, -1.0, 0.0)),
            ((-s,  s, -s), ( s,  s, -s), ( s,  s,  s), (0.0, 1.0, 0.0)),
            ((-s,  s, -s), ( s,  s,  s), (-s,  s,  s), (0.0, 1.0, 0.0)),
        ]
        pos_data = []
        nrm_data = []
        for a, b, c, n in faces:
            pos_data.extend([a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]])
            nrm_data.extend([n[0], n[1], n[2], n[0], n[1], n[2], n[0], n[1], n[2]])
        self._cube_vbo_pos = self.ctx.buffer(np.array(pos_data, dtype="f4").tobytes())
        self._cube_vbo_normals = self.ctx.buffer(np.array(nrm_data, dtype="f4").tobytes())
        self._light_dir = np.array([0.5, 1.0, 0.3], dtype="f4")
        s = self.config.VOXEL_SIZE * 0.5
        local = np.array([
            -s, -s, -s,  s, -s, -s,  s,  s, -s,
            -s, -s, -s,  s,  s, -s, -s,  s, -s,
            -s, -s,  s,  s, -s,  s,  s,  s,  s,
            -s, -s,  s,  s,  s,  s, -s,  s,  s,
            -s, -s, -s, -s,  s, -s, -s,  s,  s,
            -s, -s, -s, -s,  s,  s, -s, -s,  s,
             s, -s, -s,  s,  s, -s,  s,  s,  s,
             s, -s, -s,  s,  s,  s,  s, -s,  s,
            -s, -s, -s,  s, -s, -s,  s, -s,  s,
            -s, -s, -s,  s, -s,  s, -s, -s,  s,
            -s,  s, -s,  s,  s, -s,  s,  s,  s,
            -s,  s, -s,  s,  s,  s, -s,  s,  s,
        ], dtype="f4")
        self._cube_vbo_pos = self.ctx.buffer(local.tobytes())
        self._ghost_vao = None
        self._ghost_vbo_pos = None
        self._ghost_vbo_col = None
        self._ghost_vbo_em = None
        self._last_ghost_pos = None
        self._scene_tex = None
        self._scene_fbo = None
        self._ping_tex = None
        self._ping_fbo = None
        self._pong_tex = None
        self._pong_fbo = None
        self._bright_vao = self._create_fullscreen_quad(self.bright_prog)
        self._blur_h_vao = self._create_fullscreen_quad(self.blur_h_prog)
        self._blur_v_vao = self._create_fullscreen_quad(self.blur_v_prog)
        self._composite_vao = self._create_fullscreen_quad(self.composite_prog)
        self._bloom_threshold = getattr(self.config, "BLOOM_THRESHOLD", 0.8)
        self._bloom_strength = getattr(self.config, "BLOOM_STRENGTH", 0.6)
        self._bloom_passes = getattr(self.config, "BLOOM_BLUR_PASSES", 2)

    def _shader_path(self, name: str) -> str:
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "render", "shaders")
        return os.path.join(base, name)

    def _load_program(self, vert_name: str, frag_name: str) -> moderngl.Program:
        with open(self._shader_path(vert_name), "r", encoding="utf-8") as vf:
            vs = vf.read()
        with open(self._shader_path(frag_name), "r", encoding="utf-8") as ff:
            fs = ff.read()
        return self.ctx.program(vertex_shader=vs, fragment_shader=fs)

    def _create_fullscreen_quad(self, prog: moderngl.Program) -> moderngl.VertexArray:
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4")
        vbo = self.ctx.buffer(vertices.tobytes())
        vao = self.ctx.vertex_array(
            prog,
            [
                (vbo, "2f 2f", "in_position", "in_uv"),
            ],
        )
        return vao

    def _render_ui_panel(self, pos: tuple, size: tuple, color: tuple, time_sec: float):
        self.ui_prog["u_position"].value = pos
        self.ui_prog["u_size"].value = size
        self.ui_prog["u_color"].value = color
        self.ui_prog["u_time"].value = time_sec
        self.ui_vao.render(moderngl.TRIANGLE_STRIP)

    def _draw_ui_glass_panels(self, time_sec: float, menu):
        # 1. Status Bar Panel (Bottom)
        self._render_ui_panel((-0.0, -0.85), (0.9, 0.1), (0.1, 0.2, 0.3, 0.4), time_sec)
        
        # 2. Mode Display (Top Left)
        self._render_ui_panel((-0.75, 0.85), (0.2, 0.08), (0.1, 0.2, 0.3, 0.4), time_sec)
        
        # 3. HUD Message (Under Mode)
        if self.state.get("hud_message"):
            self._render_ui_panel((-0.75, 0.72), (0.2, 0.05), (0.1, 0.2, 0.3, 0.4), time_sec)
        
        # 4. Radial Menu Background
        if menu and menu.open:
            self._render_ui_panel((0.0, 0.0), (0.4, 0.4), (0.05, 0.05, 0.1, 0.6), time_sec)

    def _ensure_camera_texture(self, frame: np.ndarray):
        h, w, _ = frame.shape
        if self.camera_tex is None or self.camera_tex.size != (w, h):
            if self.camera_tex:
                self.camera_tex.release()
            self.camera_tex = self.ctx.texture((w, h), 3, data=frame.tobytes())
            self.camera_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)

    def _ensure_ui_texture(self, w, h):
        if self.ui_text_tex is None or self.ui_text_tex.size != (w, h):
            if self.ui_text_tex:
                self.ui_text_tex.release()
            self.ui_text_tex = self.ctx.texture((w, h), 4) # RGBA
            self.ui_text_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    def _ensure_offscreen(self):
        w = self.config.WINDOW_WIDTH
        h = self.config.WINDOW_HEIGHT
        if (self._scene_tex is None) or (self._scene_tex.size != (w, h)):
            if self._scene_tex:
                self._scene_tex.release()
                self._scene_fbo.release()
            self._scene_tex = self.ctx.texture((w, h), 3)
            self._scene_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._scene_fbo = self.ctx.framebuffer(color_attachments=[self._scene_tex])
        if (self._ping_tex is None) or (self._ping_tex.size != (w, h)):
            if self._ping_tex:
                self._ping_tex.release()
                self._ping_fbo.release()
            self._ping_tex = self.ctx.texture((w, h), 3)
            self._ping_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._ping_fbo = self.ctx.framebuffer(color_attachments=[self._ping_tex])
        if (self._pong_tex is None) or (self._pong_tex.size != (w, h)):
            if self._pong_tex:
                self._pong_tex.release()
                self._pong_fbo.release()
            self._pong_tex = self.ctx.texture((w, h), 3)
            self._pong_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._pong_fbo = self.ctx.framebuffer(color_attachments=[self._pong_tex])

    def _overlay_landmarks(self, frame: np.ndarray, hands: Optional[Dict[str, Any]]):
        if not hands:
            return
        h, w, _ = frame.shape
        # MediaPipe Hand Connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]
        for hnd in hands.get("hands", []):
            pts = []
            for (nx, ny, nz) in hnd["landmarks"]:
                x = int(nx * w)
                y = int(ny * h)
                pts.append((x, y))
            
            # Draw connections (lines)
            for a, b in connections:
                if a < len(pts) and b < len(pts):
                    cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2, cv2.LINE_AA)
            
            # Draw points
            for pt in pts:
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    def _update_cursor_from_hands(self, hands: Optional[Dict[str, Any]], frame_shape):
        if not hands or not hands.get("hands"):
            return
        right = None
        left = None
        for hnd in hands.get("hands", []):
            if hnd.get("label") == "Right":
                right = hnd
            elif hnd.get("label") == "Left":
                left = hnd
        if right:
            idx = right["landmarks"][8]
            rx, ry = 1.0 - idx[0], idx[1] # Mirror mapping
            rz = self._last_rz
            
            # Intuitive Z: mapping left hand X to depth
            if left:
                lx = left["landmarks"][0][0]
                rz_clamped = max(0.2, min(0.8, lx))
                rz = (rz_clamped - 0.2) / 0.6
                self._last_rz = rz
            
            self.cursor.update_from_normalized(rx, ry, rz)
            self.state["cursor_normalized"] = (rx, ry, rz)
            self.state["cursor_grid"] = self.cursor.get_position()

    def _overlay_cursor_preview(self, frame: np.ndarray):
        cur = self.state.get("cursor_normalized")
        if not cur:
            return
        h, w, _ = frame.shape
        rx, ry, _ = cur
        x = int(rx * w)
        y = int(ry * h)
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

    def _overlay_state_text(self, frame: np.ndarray):
        st = self.state.get("fsm_state")
        if not st:
            return
        h, w, _ = frame.shape
        text = f"STATE: {st}"
        color = (0, 255, 255)
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    def _overlay_hud_message(self, frame: np.ndarray):
        msg = self.state.get("hud_message")
        until = self.state.get("hud_until")
        if not msg or not until:
            return
        if time.time() > until:
            self.state["hud_message"] = None
            self.state["hud_until"] = None
            return
        h, w, _ = frame.shape
        color = (255, 255, 0)
        cv2.putText(frame, msg, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    def _overlay_status_bar(self, frame: np.ndarray):
        h, w, _ = frame.shape
        cb = "On" if self.config.CONTINUOUS_BUILD else "Off"
        gv = "On" if self.state.get("grid_visible", True) else "Off"
        bl = "On" if self.state.get("bloom_enabled", False) else "Off"
        c = self.config.VOXEL_DEFAULT_COLOR
        ce = f"{int(c[0]*255):02X}{int(c[1]*255):02X}{int(c[2]*255):02X}"
        em = "On" if getattr(self.voxel_grid, "default_emissive", True) else "Off"
        mn = self.state.get("material_name")
        m = getattr(self.voxel_grid, "default_metallic", 0.0)
        r = getattr(self.voxel_grid, "default_roughness", 0.5)
        mat = mn if mn else f"m={m:.2f} r={r:.2f}"
        text = f"CB:{cb} Grid:{gv} Bloom:{bl} Color:#{ce} Emissive:{em} Material:{mat}"
        color = (255, 255, 255)
        cv2.putText(frame, text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    def _overlay_radial_menu(self, frame: np.ndarray, menu):
        if not menu or not menu.open:
            return
        
        h, w, _ = frame.shape
        center = (w // 2, h // 2)
        radius = 150
        
        # Draw background ring
        cv2.circle(frame, center, radius + 20, (50, 50, 50), -1)
        cv2.circle(frame, center, radius + 20, (200, 200, 200), 2)
        
        options = menu.main_options if menu.mode == menu.MAIN else menu.color_options
        for i, opt in enumerate(options):
            name, pos = opt[0], opt[1]
            # Convert normalized pos to pixel pos
            px = int(center[0] + pos[0] * radius)
            py = int(center[1] - pos[1] * radius) # Flip Y for screen space
            
            is_active = (menu.active_index == i)
            color = (0, 255, 255) if is_active else (255, 255, 255)
            thickness = 3 if is_active else 1
            
            # Special handling for color options (show color circles)
            if menu.mode == menu.COLOR:
                c = opt[2] # (r,g,b)
                cv2.circle(frame, (px, py), 30, (int(c[2]*255), int(c[1]*255), int(c[0]*255)), -1)
                if is_active:
                    cv2.circle(frame, (px, py), 35, (255, 255, 255), 2)
            else:
                # Text for main menu
                text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                tx = px - text_size[0] // 2
                ty = py + text_size[1] // 2
                cv2.putText(frame, name, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness, cv2.LINE_AA)


    def _build_voxel_buffers(self):
        offsets = []
        colors = []
        emissive = []
        metallic = []
        roughness = []
        for pos, vox in self.voxel_grid.voxels.items():
            offsets.extend([pos[0] * self.config.VOXEL_SIZE, pos[1] * self.config.VOXEL_SIZE, pos[2] * self.config.VOXEL_SIZE])
            colors.extend([vox.color[0], vox.color[1], vox.color[2]])
            emissive.append(1.0 if vox.emissive else 0.0)
            metallic.append(vox.metallic)
            roughness.append(vox.roughness)
        if offsets:
            if self._voxel_inst_offsets:
                self._voxel_inst_offsets.release()
            if self._voxel_inst_colors:
                self._voxel_inst_colors.release()
            if self._voxel_inst_emissive:
                self._voxel_inst_emissive.release()
            if getattr(self, "_voxel_inst_metallic", None):
                self._voxel_inst_metallic.release()
            if getattr(self, "_voxel_inst_roughness", None):
                self._voxel_inst_roughness.release()
            self._voxel_inst_offsets = self.ctx.buffer(np.array(offsets, dtype="f4").tobytes())
            self._voxel_inst_colors = self.ctx.buffer(np.array(colors, dtype="f4").tobytes())
            self._voxel_inst_emissive = self.ctx.buffer(np.array(emissive, dtype="f4").tobytes())
            self._voxel_inst_metallic = self.ctx.buffer(np.array(metallic, dtype="f4").tobytes())
            self._voxel_inst_roughness = self.ctx.buffer(np.array(roughness, dtype="f4").tobytes())
            self._voxel_vao = self.ctx.vertex_array(
                self.voxel_prog,
                [
                    (self._cube_vbo_pos, "3f", "in_pos"),
                    (self._cube_vbo_normals, "3f", "in_normal"),
                    (self._voxel_inst_offsets, "3f/i", "in_offset"),
                    (self._voxel_inst_colors, "3f/i", "in_color"),
                    (self._voxel_inst_emissive, "1f/i", "in_emissive"),
                    (self._voxel_inst_metallic, "1f/i", "in_metallic"),
                    (self._voxel_inst_roughness, "1f/i", "in_roughness"),
                ],
            )
        else:
            self._voxel_vao = None
        self._last_voxel_version = self.voxel_grid.version

    def _draw_voxels(self):
        if self.voxel_grid.version != self._last_voxel_version:
            self._build_voxel_buffers()
        if not self._voxel_vao:
            return
        mvp = self._compute_mvp()
        self.voxel_prog["u_mvp"].write(mvp.astype("f4").tobytes())
        self.voxel_prog["u_alpha"].value = 1.0
        self.voxel_prog["u_tint"].value = (1.0, 1.0, 1.0)
        
        # Skip original voxel if in MOVE_MODE
        skip = self.state.get("pre_move_pos")
        if skip:
            sv = self.config.VOXEL_SIZE
            self.voxel_prog["u_skip_pos"].value = (float(skip[0]*sv), float(skip[1]*sv), float(skip[2]*sv))
        else:
            self.voxel_prog["u_skip_pos"].value = (-1000.0, -1000.0, -1000.0)

        ld = self._light_dir
        ldn = ld / np.linalg.norm(ld)
        self.voxel_prog["u_light_dir"].value = (float(ldn[0]), float(ldn[1]), float(ldn[2]))
        self._voxel_vao.render(moderngl.TRIANGLES, instances=len(self.voxel_grid.voxels))

    def _build_preview_buffers(self):
        offsets = []
        colors = []
        emissive = []
        metallic = []
        roughness = []
        c = self.config.VOXEL_DEFAULT_COLOR
        arr = self.state.get("preview_buffer_positions", []) or []
        for pos in arr:
            offsets.extend([pos[0] * self.config.VOXEL_SIZE, pos[1] * self.config.VOXEL_SIZE, pos[2] * self.config.VOXEL_SIZE])
            colors.extend([c[0], c[1], c[2]])
            emissive.append(1.0)
            metallic.append(self.voxel_grid.default_metallic)
            roughness.append(self.voxel_grid.default_roughness)
        if offsets:
            if self._preview_inst_offsets:
                self._preview_inst_offsets.release()
            if self._preview_inst_colors:
                self._preview_inst_colors.release()
            if self._preview_inst_emissive:
                self._preview_inst_emissive.release()
            if getattr(self, "_preview_inst_metallic", None):
                self._preview_inst_metallic.release()
            if getattr(self, "_preview_inst_roughness", None):
                self._preview_inst_roughness.release()
            self._preview_inst_offsets = self.ctx.buffer(np.array(offsets, dtype="f4").tobytes())
            self._preview_inst_colors = self.ctx.buffer(np.array(colors, dtype="f4").tobytes())
            self._preview_inst_emissive = self.ctx.buffer(np.array(emissive, dtype="f4").tobytes())
            self._preview_inst_metallic = self.ctx.buffer(np.array(metallic, dtype="f4").tobytes())
            self._preview_inst_roughness = self.ctx.buffer(np.array(roughness, dtype="f4").tobytes())
            self._preview_vao = self.ctx.vertex_array(
                self.voxel_prog,
                [
                    (self._cube_vbo_pos, "3f", "in_pos"),
                    (self._cube_vbo_normals, "3f", "in_normal"),
                    (self._preview_inst_offsets, "3f/i", "in_offset"),
                    (self._preview_inst_colors, "3f/i", "in_color"),
                    (self._preview_inst_emissive, "1f/i", "in_emissive"),
                    (self._preview_inst_metallic, "1f/i", "in_metallic"),
                    (self._preview_inst_roughness, "1f/i", "in_roughness"),
                ],
            )
        else:
            self._preview_vao = None
        arr = self.state.get("preview_buffer_positions", []) or []
        self._last_preview_hash = (len(arr), sum([p[0] + p[1] * 3 + p[2] * 7 for p in arr]))

    def _draw_preview(self):
        arr = self.state.get("preview_buffer_positions", []) or []
        h = (len(arr), sum([p[0] + p[1] * 3 + p[2] * 7 for p in arr]))
        if h != self._last_preview_hash:
            self._build_preview_buffers()
        if not self._preview_vao:
            return
        mvp = self._compute_mvp()
        self.voxel_prog["u_mvp"].write(mvp.astype("f4").tobytes())
        self.voxel_prog["u_alpha"].value = self.config.VOXEL_PREVIEW_ALPHA
        self.voxel_prog["u_tint"].value = (1.2, 1.2, 1.2)
        ld = self._light_dir
        ldn = ld / np.linalg.norm(ld)
        self.voxel_prog["u_light_dir"].value = (float(ldn[0]), float(ldn[1]), float(ldn[2]))
        self._preview_vao.render(moderngl.TRIANGLES, instances=len(arr))

    def _draw_highlights(self):
        # 1. Hover Highlight
        hov = self.state.get("hovered_voxel")
        if hov:
            self._draw_single_voxel(hov, (1.5, 1.5, 1.5), 1.0)
        
        # 2. Selection Highlight (MOVE_MODE)
        sel = self.state.get("selected_voxel")
        if sel:
            pulse = 0.5 + 0.5 * np.sin(time.time() * 10.0)
            tint = (0.5, 1.0 + pulse * 0.5, 0.5)
            self._draw_single_voxel(sel, tint, 1.0)

    def _draw_single_voxel(self, pos, tint, alpha):
        offset = np.array([pos[0] * self.config.VOXEL_SIZE, pos[1] * self.config.VOXEL_SIZE, pos[2] * self.config.VOXEL_SIZE], dtype="f4")
        self.voxel_prog["u_mvp"].write(self._compute_mvp().astype("f4").tobytes())
        self.voxel_prog["u_alpha"].value = alpha
        self.voxel_prog["u_tint"].value = tint
        
        # Build a temporary VAO for one instance
        vbo_off = self.ctx.buffer(offset.tobytes())
        vox = self.voxel_grid.voxels.get(pos)
        c = vox.color if vox else self.config.VOXEL_DEFAULT_COLOR
        em = 1.0 if (vox and vox.emissive) else 0.0
        m = vox.metallic if vox else 0.0
        r = vox.roughness if vox else 0.5
        vbo_col = self.ctx.buffer(np.array(c, dtype="f4").tobytes())
        vbo_em = self.ctx.buffer(np.array([em], dtype="f4").tobytes())
        vbo_m = self.ctx.buffer(np.array([m], dtype="f4").tobytes())
        vbo_r = self.ctx.buffer(np.array([r], dtype="f4").tobytes())
        vao = self.ctx.vertex_array(
            self.voxel_prog,
            [
                (self._cube_vbo_pos, "3f", "in_pos"),
                (self._cube_vbo_normals, "3f", "in_normal"),
                (vbo_off, "3f/i", "in_offset"),
                (vbo_col, "3f/i", "in_color"),
                (vbo_em, "1f/i", "in_emissive"),
                (vbo_m, "1f/i", "in_metallic"),
                (vbo_r, "1f/i", "in_roughness"),
            ],
        )
        vao.render(moderngl.TRIANGLES, instances=1)
        vao.release()
        vbo_off.release()
        vbo_col.release()
        vbo_em.release()
        vbo_m.release()
        vbo_r.release()

    def render_frame(self, time_sec: float, frame_time: float, menu=None):
        frame = None
        lock = self.state.get("frame_lock")
        if lock:
            with lock:
                frame = self.state.get("frame")
                hands = self.state.get("hands")
                if frame is not None:
                    self._update_cursor_from_hands(hands, frame.shape)
        if frame is not None:
            pass # landmarks moved to ui_frame
            self._overlay_state_text(frame)
            self._overlay_hud_message(frame)
            self._overlay_status_bar(frame)
            self._overlay_radial_menu(frame, menu)
        if frame is not None:
            self._ensure_camera_texture(frame)

            self.camera_tex.write(frame.tobytes())
            self.camera_tex.use(location=0)
            self.bg_prog["u_camera"].value = 0
        
        ui_frame = None
        if frame is not None:
            h, w, _ = frame.shape
            ui_frame = np.zeros((h, w, 4), dtype=np.uint8)
            self._overlay_landmarks(ui_frame, hands)
            self._overlay_state_text(ui_frame)
            self._overlay_hud_message(ui_frame)
            self._overlay_status_bar(ui_frame)
            self._overlay_radial_menu(ui_frame, menu)
            
            self._ensure_ui_texture(w, h)
            self.ui_text_tex.write(ui_frame.tobytes())

        self._ensure_offscreen()
        if self._scene_fbo:
            self._scene_fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            if self.camera_tex is not None:
                self.bg_vao.render(moderngl.TRIANGLE_STRIP)
            
            if self.grid and self.state.get("grid_visible", True):
                self.grid.draw(time_sec)
            
            self._draw_voxels()
            self._draw_preview()
            self._draw_ghost()
            self._draw_highlights()
            self._draw_delete_candidate()
            self.state["delete_candidate"] = None
            
            # Draw UI Glass Panels
            self.ctx.enable(moderngl.BLEND)
            self._draw_ui_glass_panels(time_sec, menu)
            
            # Draw UI Text on top
            if self.ui_text_tex:
                self.ui_text_tex.use(location=0)
                self.ui_overlay_prog["u_texture"].value = 0
                self.ui_overlay_vao.render(moderngl.TRIANGLE_STRIP)

        self.ctx.screen.use()
        if self.state.get("bloom_enabled", getattr(self.config, "BLOOM_ENABLED", False)):
            self._apply_bloom_and_present()
        else:
            if self._scene_tex is not None:
                self._scene_tex.use(location=0)
                self.bg_prog["u_camera"].value = 0
                self.ctx.clear(0.0, 0.0, 0.0, 1.0)
                self.bg_vao.render(moderngl.TRIANGLE_STRIP)

    def _apply_bloom_and_present(self):
        w = self.config.WINDOW_WIDTH
        h = self.config.WINDOW_HEIGHT
        if not self._scene_tex or not self._ping_tex or not self._pong_tex:
            return
        self._scene_tex.use(location=0)
        self.bright_prog["u_tex"].value = 0
        self.bright_prog["u_threshold"].value = self._bloom_threshold
        self._ping_fbo.use()
        self._bright_vao.render(moderngl.TRIANGLE_STRIP)
        for i in range(self._bloom_passes):
            self._ping_tex.use(location=0)
            self.blur_h_prog["u_tex"].value = 0
            self.blur_h_prog["u_texel_size"].value = (1.0 / w, 1.0 / h)
            self._pong_fbo.use()
            self._blur_h_vao.render(moderngl.TRIANGLE_STRIP)
            self._pong_tex.use(location=0)
            self.blur_v_prog["u_tex"].value = 0
            self.blur_v_prog["u_texel_size"].value = (1.0 / w, 1.0 / h)
            self._ping_fbo.use()
            self._blur_v_vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.screen.use()
        self._scene_tex.use(location=0)
        self._ping_tex.use(location=1)
        self.composite_prog["u_scene"].value = 0
        self.composite_prog["u_bloom"].value = 1
        self.composite_prog["u_strength"].value = self._bloom_strength
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self._composite_vao.render(moderngl.TRIANGLE_STRIP)

    def _build_delete_buffers(self):
        p = self.state.get("delete_candidate")
        if not p:
            self._delete_vao = None
            return
        c = self.config.VOXEL_DELETE_COLOR
        offset = np.array([p[0] * self.config.VOXEL_SIZE, p[1] * self.config.VOXEL_SIZE, p[2] * self.config.VOXEL_SIZE], dtype="f4")
        color = np.array([c[0], c[1], c[2]], dtype="f4")
        em = np.array([1.0], dtype="f4")
        mt = np.array([self.voxel_grid.default_metallic], dtype="f4")
        rf = np.array([self.voxel_grid.default_roughness], dtype="f4")
        if self._delete_inst_offset:
            self._delete_inst_offset.release()
        if self._delete_inst_color:
            self._delete_inst_color.release()
        if self._delete_inst_emissive:
            self._delete_inst_emissive.release()
        if getattr(self, "_delete_inst_metallic", None):
            self._delete_inst_metallic.release()
        if getattr(self, "_delete_inst_roughness", None):
            self._delete_inst_roughness.release()
        self._delete_inst_offset = self.ctx.buffer(offset.tobytes())
        self._delete_inst_color = self.ctx.buffer(color.tobytes())
        self._delete_inst_emissive = self.ctx.buffer(em.tobytes())
        self._delete_inst_metallic = self.ctx.buffer(mt.tobytes())
        self._delete_inst_roughness = self.ctx.buffer(rf.tobytes())
        self._delete_vao = self.ctx.vertex_array(
            self.voxel_prog,
            [
                (self._cube_vbo_pos, "3f", "in_pos"),
                (self._cube_vbo_normals, "3f", "in_normal"),
                (self._delete_inst_offset, "3f/i", "in_offset"),
                (self._delete_inst_color, "3f/i", "in_color"),
                (self._delete_inst_emissive, "1f/i", "in_emissive"),
                (self._delete_inst_metallic, "1f/i", "in_metallic"),
                (self._delete_inst_roughness, "1f/i", "in_roughness"),
            ],
        )

    def _draw_delete_candidate(self):
        if self.state.get("delete_candidate") and not self._delete_vao:
            self._build_delete_buffers()
        if not self._delete_vao:
            return
        mvp = self._compute_mvp()
        self.voxel_prog["u_mvp"].write(mvp.astype("f4").tobytes())
        self.voxel_prog["u_alpha"].value = 1.0
        self.voxel_prog["u_tint"].value = (1.0, 1.0, 1.0)
        self._delete_vao.render(moderngl.TRIANGLES, instances=1)
        self._delete_vao = None

    def _compute_mvp(self) -> Matrix44:
        if self.state.get("orbit_active"):
            cen = self.state.get("orbit_center")
            if cen:
                self.cam.set_center(cen)
            d = self.state.get("orbit_delta")
            if d:
                self.cam.apply_delta(d)
                self.state["orbit_delta"] = (0.0, 0.0)
            if self.state.get("orbit_reset"):
                self.cam.reset()
                self.state["orbit_reset"] = False
        self.cam.update()
        aspect = float(self.config.WINDOW_WIDTH) / float(self.config.WINDOW_HEIGHT)
        proj = Matrix44.perspective_projection(60.0, aspect, 0.1, 100.0)
        view = self.cam.view_matrix()
        return proj * view

    def _build_ghost_buffers(self):
        pos = self.state.get("cursor_grid")
        if not pos:
            self._ghost_vao = None
            self._last_ghost_pos = None
            return
        if self._last_ghost_pos == pos and self._ghost_vao:
            return
        c = self.config.VOXEL_DEFAULT_COLOR
        offset = np.array([pos[0] * self.config.VOXEL_SIZE, pos[1] * self.config.VOXEL_SIZE, pos[2] * self.config.VOXEL_SIZE], dtype="f4")
        color = np.array([c[0], c[1], c[2]], dtype="f4")
        em = np.array([1.0], dtype="f4")
        mt = np.array([self.voxel_grid.default_metallic], dtype="f4")
        rf = np.array([self.voxel_grid.default_roughness], dtype="f4")
        self._ghost_vbo_pos = self._cube_vbo_pos
        if self._ghost_vbo_col:
            self._ghost_vbo_col.release()
        if self._ghost_vbo_em:
            self._ghost_vbo_em.release()
        if getattr(self, "_ghost_vbo_metallic", None):
            self._ghost_vbo_metallic.release()
        if getattr(self, "_ghost_vbo_roughness", None):
            self._ghost_vbo_roughness.release()
        self._ghost_vbo_col = self.ctx.buffer(color.tobytes())
        self._ghost_vbo_em = self.ctx.buffer(em.tobytes())
        self._ghost_vbo_metallic = self.ctx.buffer(mt.tobytes())
        self._ghost_vbo_roughness = self.ctx.buffer(rf.tobytes())
        self._ghost_vao = self.ctx.vertex_array(
            self.voxel_prog,
            [
                (self._ghost_vbo_pos, "3f", "in_pos"),
                (self._cube_vbo_normals, "3f", "in_normal"),
                (self.ctx.buffer(offset.tobytes()), "3f/i", "in_offset"),
                (self._ghost_vbo_col, "3f/i", "in_color"),
                (self._ghost_vbo_em, "1f/i", "in_emissive"),
                (self._ghost_vbo_metallic, "1f/i", "in_metallic"),
                (self._ghost_vbo_roughness, "1f/i", "in_roughness"),
            ],
        )
        self._last_ghost_pos = pos

    def _draw_ghost(self):
        self._build_ghost_buffers()
        if not self._ghost_vao:
            return
        mvp = self._compute_mvp()
        self.voxel_prog["u_mvp"].write(mvp.astype("f4").tobytes())
        pulse_alpha = self.config.VOXEL_PREVIEW_ALPHA * (0.4 + 0.6 * (0.5 + 0.5 * np.sin(time.time() * 5.0)))
        self.voxel_prog["u_alpha"].value = pulse_alpha
        self.voxel_prog["u_tint"].value = (1.0, 1.0, 1.0)
        ld = self._light_dir
        ldn = ld / np.linalg.norm(ld)
        self.voxel_prog["u_light_dir"].value = (float(ldn[0]), float(ldn[1]), float(ldn[2]))
        self._ghost_vao.render(moderngl.TRIANGLES, instances=1)

    def _overlay_landmarks(self, frame: np.ndarray, hands: Optional[Dict[str, Any]]):
        if not hands:
            return
        h, w, _ = frame.shape
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]
        for hnd in hands.get("hands", []):
            pts = []
            for (nx, ny, nz) in hnd["landmarks"]:
                x = int((1.0 - nx) * w) # Mirror mapping
                y = int(ny * h)
                pts.append((x, y))
            for a, b in connections:
                if a < len(pts) and b < len(pts):
                    cv2.line(frame, pts[a], pts[b], (0, 255, 100, 255), 1, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(frame, pt, 2, (0, 100, 255, 255), -1, cv2.LINE_AA)

    def _overlay_state_text(self, frame: np.ndarray):
        st = self.state.get("fsm_state")
        if not st:
            return
        text = f"MODE: {st}"
        # Position matching the glass panel (-0.75, 0.85) -> converted to pixels
        # -0.75 is 12.5% from left, 0.85 is 7.5% from top
        # Position matching the glass panel (-0.75, 0.85)
        h, w, _ = frame.shape
        tx, ty = int(w * 0.13), int(h * 0.08)
        cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255, 255), 1, cv2.LINE_AA)

    def _overlay_hud_message(self, frame: np.ndarray):
        msg = self.state.get("hud_message")
        until = self.state.get("hud_until")
        if not msg or not until:
            return
        if time.time() > until:
            self.state["hud_message"] = None
            self.state["hud_until"] = None
            return
        h, w, _ = frame.shape
        tx, ty = int(w * 0.13), int(h * 0.14)
        cv2.putText(frame, msg, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 0, 255), 1, cv2.LINE_AA)

        h, w, _ = frame.shape
        cb = "CONTINUOUS" if self.config.CONTINUOUS_BUILD else "SINGLE"
        gv = "GRID" if self.state.get("grid_visible", True) else "NO GRID"
        bl = "BLOOM" if self.state.get("bloom_enabled", False) else "NO BLOOM"
        mn = self.state.get("material_name", "MATTE")
        text = f"{cb} | {gv} | {bl} | {mn} | UNDO:U REDO:R"
        font = cv2.FONT_HERSHEY_DUPLEX
        scale = 0.5
        thickness = 1
        color = (200, 255, 255, 255) # White-ish Cyan
        t_size = cv2.getTextSize(text, font, scale, thickness)[0]
        tx = (w - t_size[0]) // 2
        ty = int(h * 0.93) # Align with bottom glass panel
        cv2.putText(frame, text, (tx, ty), font, scale, color, thickness, cv2.LINE_AA)

    def _overlay_radial_menu(self, frame: np.ndarray, menu):
        if not menu or not menu.open:
            return
        h, w, _ = frame.shape
        center = (w // 2, h // 2)
        radius = 180
        
        # (Glass background handled in OpenGL shader now)
        
        options = menu.main_options if menu.mode == menu.MAIN else menu.color_options
        for i, opt in enumerate(options):
            name, pos = opt[0], opt[1]
            px = int(center[0] + pos[0] * radius)
            py = int(center[1] - pos[1] * radius)
            
            is_active = (menu.active_index == i)
            color = (0, 255, 255, 255) if is_active else (180, 180, 180, 255)
            
            if menu.mode == menu.COLOR:
                c = opt[2]
                bgr = (int(c[2]*255), int(c[1]*255), int(c[0]*255), 255)
                # Draw selection Glow
                if is_active:
                     cv2.circle(frame, (px, py), 45, (255, 255, 255, 128), -1, cv2.LINE_AA)
                cv2.circle(frame, (px, py), 35, bgr, -1, cv2.LINE_AA)
            else:
                text_size = cv2.getTextSize(name.upper(), cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)[0]
                tx = px - text_size[0] // 2
                ty = py + text_size[1] // 2
                if is_active:
                     # Subtle highlight behind active text
                     cv2.putText(frame, name.upper(), (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255, 50), 4, cv2.LINE_AA)
                cv2.putText(frame, name.upper(), (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.5, color, 1, cv2.LINE_AA)
