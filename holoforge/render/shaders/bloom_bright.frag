#version 430 core
layout(binding = 0) uniform sampler2D u_tex;
uniform float u_threshold;
layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;
void main() {
    vec3 c = texture(u_tex, v_uv).rgb;
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    float m = step(u_threshold, l);
    f_color = vec4(c * m, 1.0);
}
