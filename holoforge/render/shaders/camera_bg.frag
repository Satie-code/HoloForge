#version 430 core
layout(binding = 0) uniform sampler2D u_camera;
layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;
void main() {
    // Mirrored background, corrected for vertical inversion
    vec3 c = texture(u_camera, vec2(1.0 - v_uv.x, 1.0 - v_uv.y)).rgb;
    f_color = vec4(c, 1.0);
}
