#version 430

layout(location = 5) uniform vec3 sun_direction;

in vec3 normal;

layout(location = 0) out vec4 FragColor;

void main() {
  vec3 base = vec3(0.2, 0.2, 0.2);
  float light = dot(sun_direction, normal);
  base += vec3(0.8, 0.8, 0.8) * clamp(light, 0, 1);
  FragColor = vec4(base, 1);
}
