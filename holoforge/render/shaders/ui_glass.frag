#version 430 core

layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 f_color;

uniform vec4 u_color;       // Base color
uniform float u_blur;       // Blur amount (simulated with noise or just opacity)
uniform float u_border;     // Border width
uniform vec2 u_resolution;
uniform float u_time;

// Simple distance function for a rounded rect (approx)
float roundedRect(vec2 uv, vec2 size, float radius) {
    vec2 d = abs(uv) - size + radius;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - radius;
}

void main() {
    // Center UVs for shape math
    vec2 uv = v_uv * 2.0 - 1.0;
    
    // Glass background
    float dist = roundedRect(uv, vec2(0.95), 0.1);
    float mask = smoothstep(0.01, 0.0, dist);
    
    if (mask <= 0.0) discard;

    // Suble noise / frost effect
    float noise = fract(sin(dot(v_uv, vec2(12.9898, 78.233))) * 43758.5453);
    
    // Glassy gradient
    float grad = v_uv.y * 0.2 + 0.1;
    
    // Border
    float border_dist = abs(dist);
    float border_mask = smoothstep(0.02, 0.0, border_dist);
    
    vec4 glass_color = vec4(u_color.rgb * (1.0 + grad), u_color.a);
    glass_color.rgb += noise * 0.03; // Subtle frost
    
    vec3 border_color = mix(glass_color.rgb, vec3(1.0), 0.5);
    
    f_color = mix(glass_color, vec4(border_color, u_color.a * 1.5), border_mask);
    
    // Subtle sheen animation
    float sheen = smoothstep(0.1, 0.0, abs(v_uv.x - 0.5 + sin(u_time * 0.5) * 0.8));
    f_color.rgb += sheen * 0.1;
}
