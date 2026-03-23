#version 430

layout(location = 0) uniform mat4 transform;
layout(location = 1) uniform float x_offset;

layout(location = 0) in float z;
layout(location = 1) in vec3 in_normal;

out vec3 normal;

void main() {
  float x = (gl_VertexID % TerrainResolutionX) / (TerrainResolutionX - 1.0) * TerrainWidth + x_offset;
  float y = ((gl_VertexID / TerrainResolutionX) / (TerrainResolutionY - 1.0) - 0.5) * TerrainHeight;
  vec4 pos = vec4(x, y, z, 1);
  gl_Position = transform * pos;
  normal = in_normal;
}
