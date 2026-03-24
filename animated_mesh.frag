#version 410 core

in vec3 shadow_map_position;

layout(location = 0) out vec4 FragColor;

void main() {
  FragColor = vec4(1, 1, 1, 1);
}
