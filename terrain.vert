#version 430

layout(location = 0) uniform mat4 transform;
layout(location = 1) uniform float x_offset;

layout(location = 0) in float z;
layout(location = 1) in vec3 in_normal;

out vec3 normal;

void main() {
  float x = (gl_VertexID % 32) / 31.0 + x_offset;
  float y = (gl_VertexID / 32) / (32*8 - 1.0) * 8 - 4;
  vec4 pos = vec4(x, y, z, 1);
  gl_Position = transform * pos;
  normal = in_normal;
}
