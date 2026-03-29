#version 410 core

#include light

layout(location = 0) out vec4 FragColor;

flat in vec4 color;

void main() {
  vec3 light_color = LightColor();
  FragColor = vec4(light_color * color.rgb, 1);
}
