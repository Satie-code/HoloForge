#version 430 core
layout(location = 0) in vec3 v_color;
layout(location = 1) in float v_emissive;
layout(location = 2) in float v_metallic;
layout(location = 3) in float v_roughness;
layout(location = 4) in vec3 v_normal;
layout(location = 0) out vec4 f_color;
uniform float u_alpha;
uniform vec3 u_light_dir;
uniform vec3 u_tint;
void main() {
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_light_dir);
    float lambert = max(dot(N, -L), 0.0);
    vec3 F0 = mix(vec3(0.04), v_color, v_metallic);
    vec3 V = vec3(0.0, 0.0, 1.0);
    vec3 H = normalize(-L + V);
    float shininess = 2.0 + pow(1.0 - clamp(v_roughness, 0.0, 1.0), 4.0) * 50.0;
    float spec = pow(max(dot(N, H), 0.0), shininess);
    vec3 specCol = F0 * spec;
    vec3 base = v_color * lambert + specCol;
    float glow = mix(0.0, 0.2, v_emissive);
    vec3 col = (base + glow) * u_tint;
    f_color = vec4(col, u_alpha);
}
