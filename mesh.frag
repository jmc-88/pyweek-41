#version 410 core

#include light

layout(location = 0) out vec4 FragColor;

void main() {
  vec3 light_color = LightColor();

  vec3 color = vec3(1, 1, 1);

  FragColor = vec4(light_color * color, 1);
}
