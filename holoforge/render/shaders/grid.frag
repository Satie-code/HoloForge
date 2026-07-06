#version 430 core
layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;
uniform vec4 u_grid_color;
uniform float u_time;
void main() {
    vec2 uv = v_uv * 100.0;
    float line_x = 1.0 - smoothstep(0.0, 0.02, abs(fract(uv.x) - 0.5));
    float line_y = 1.0 - smoothstep(0.0, 0.02, abs(fract(uv.y) - 0.5));
    float grid = max(line_x, line_y);
    float pulse = 0.9 + 0.1 * sin(u_time * 2.0);
    float alpha = u_grid_color.a * grid * pulse;
    f_color = vec4(u_grid_color.rgb, alpha);
}
