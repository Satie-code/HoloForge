#version 430 core
layout(binding = 0) uniform sampler2D u_scene;
layout(binding = 1) uniform sampler2D u_bloom;
uniform float u_strength;
layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;
void main() {
    vec3 s = texture(u_scene, v_uv).rgb;
    vec3 b = texture(u_bloom, v_uv).rgb;
    vec3 c = s + b * u_strength;
    f_color = vec4(c, 1.0);
}
