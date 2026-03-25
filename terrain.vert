#version 410 core

uniform mat4 world_to_clip;
uniform mat4 world_to_shadow;

uniform float x_offset;

layout(location = 0) in float z;
layout(location = 1) in vec3 in_normal;

out vec3 normal;
out vec3 shadow_map_position;

void main() {
  float x = (gl_VertexID % TerrainResolutionX) / (TerrainResolutionX - 1.0) * TerrainWidth + x_offset;
  float y = ((gl_VertexID / TerrainResolutionX) / (TerrainResolutionY - 1.0) - 0.5) * TerrainHeight;
  vec4 pos = vec4(x, y, z, 1);
  gl_Position = world_to_clip * pos;
  shadow_map_position = (world_to_shadow * pos).xyz;
  normal = in_normal;
}
