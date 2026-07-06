#version 430 core

layout(location = 0) in vec2 in_position;
layout(location = 1) in vec2 in_uv;

layout(location = 0) out vec2 v_uv;

uniform vec2 u_position; // Center position in screen space (-1 to 1)
uniform vec2 u_size;     // Size in screen space (0 to 2)

void main() {
    v_uv = in_uv;
    // Map local quad coords (-1 to 1) to specified position and size
    vec2 pos = in_position * u_size + u_position;
    gl_Position = vec4(pos, -0.9, 1.0); 
}
