import os
import numpy as np
import moderngl


class HolographicGrid:
    def __init__(self, ctx: moderngl.Context, color):
        self.ctx = ctx
        self.color = color
        self.prog = self._load_program("grid.vert", "grid.frag")
        self.vao = self._create_fullscreen_quad(self.prog)

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

    def draw(self, t: float):
        self.prog["u_grid_color"].value = self.color
        self.prog["u_time"].value = t
        self.vao.render(moderngl.TRIANGLE_STRIP)
