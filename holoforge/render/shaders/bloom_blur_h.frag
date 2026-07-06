#version 430 core
layout(binding = 0) uniform sampler2D u_tex;
uniform vec2 u_texel_size;
layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;
void main() {
    vec2 t = u_texel_size;
    vec3 sum = vec3(0.0);
    sum += texture(u_tex, v_uv + vec2(-4.0 * t.x, 0)).rgb * 0.05;
    sum += texture(u_tex, v_uv + vec2(-3.0 * t.x, 0)).rgb * 0.09;
    sum += texture(u_tex, v_uv + vec2(-2.0 * t.x, 0)).rgb * 0.12;
    sum += texture(u_tex, v_uv + vec2(-1.0 * t.x, 0)).rgb * 0.15;
    sum += texture(u_tex, v_uv).rgb * 0.18;
    sum += texture(u_tex, v_uv + vec2(1.0 * t.x, 0)).rgb * 0.15;
    sum += texture(u_tex, v_uv + vec2(2.0 * t.x, 0)).rgb * 0.12;
    sum += texture(u_tex, v_uv + vec2(3.0 * t.x, 0)).rgb * 0.09;
    sum += texture(u_tex, v_uv + vec2(4.0 * t.x, 0)).rgb * 0.05;
    f_color = vec4(sum, 1.0);
}
