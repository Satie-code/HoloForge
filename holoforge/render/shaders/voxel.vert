#version 430 core
layout (location = 0) in vec3 in_pos;
layout (location = 1) in vec3 in_color;
layout (location = 2) in float in_emissive;
layout (location = 3) in vec3 in_offset;
layout (location = 4) in float in_metallic;
layout (location = 5) in float in_roughness;
layout (location = 6) in vec3 in_normal;
uniform mat4 u_mvp;
uniform vec3 u_skip_pos;
layout(location = 0) out vec3 v_color;
layout(location = 1) out float v_emissive;
layout(location = 2) out float v_metallic;
layout(location = 3) out float v_roughness;
layout(location = 4) out vec3 v_normal;
void main() {
    v_color = in_color;
    v_emissive = in_emissive;
    v_metallic = in_metallic;
    v_roughness = in_roughness;
    v_normal = in_normal;
    
    if (length(in_offset - u_skip_pos) < 0.001) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0); // Outside clip space
    } else {
        gl_Position = u_mvp * vec4(in_pos + in_offset, 1.0);
    }
}
