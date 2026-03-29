#version 410 core

#include light

layout(location = 0) out vec4 FragColor;

in float height;

void main() {
  vec3 light_color = LightColor();

  vec3 snow_color = vec3(1, 1, 1);
  vec3 mountain_color1 = vec3(0.5, 0.5, 0.5);
  vec3 mountain_color2 = vec3(0.6, 0.6, 0.6);

  float mountain_mix = clamp((height - 0.3) * 3, 0, 1);
  /*
  big if normal.z is small, < 0.85 say
  */
  mountain_mix = max(mountain_mix, clamp((0.85 - normal.z) * 4, 0.0, 1.0));
  vec3 mountain_color = mix(mountain_color1, mountain_color2, sin(normal.y + 3 * normal.x + height * 7));
  mountain_color = mix(mountain_color, snow_color, clamp((normal.z - 0.75) * 50, 0, 1));

  vec3 grass_color = vec3(0.35, 0.9, 0.35);
  vec3 hill_color = vec3(0.8, 0.8, 0.2);
  float grass_mix = clamp((normal.z - 0.93) * 100, 0.0, 1.0);
  vec3 color = mix(
    mix(hill_color, grass_color, grass_mix),
    mountain_color,
    mountain_mix);

  FragColor = vec4(light_color * color, 1);
}
