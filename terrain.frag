#version 430

layout(location = 5) uniform vec3 sun_direction;

in vec3 normal;

layout(location = 0) out vec4 FragColor;

void main() {
  vec3 light_color = vec3(0.2, 0.2, 0.25);
  float light_level = dot(sun_direction, normal);
  light_color += vec3(0.8, 0.8, 0.75) * clamp(light_level, 0, 1);

  vec3 grass_color = vec3(0.35, 0.9, 0.35);
  vec3 hill_color = vec3(0.8, 0.8, 0.2);
  float grass_mix = clamp((normal.z - 0.93) * 100, 0.0, 1.0);
  vec3 color = mix(hill_color, grass_color, grass_mix);
  FragColor = vec4(light_color * color, 1);
}
