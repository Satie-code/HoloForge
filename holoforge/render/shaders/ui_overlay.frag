#version 430 core
layout(binding = 0) uniform sampler2D u_texture;
layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;
void main() {
    // Legible (non-mirrored) text, corrected for vertical inversion
    f_color = texture(u_texture, vec2(v_uv.x, 1.0 - v_uv.y));
}
