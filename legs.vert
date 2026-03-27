#version 410 core

uniform mat4 world_to_clip;
uniform mat4 world_to_shadow;
uniform mat4 mesh_to_world;
uniform float height;

layout(location = 0) in vec3 mesh_pos;
layout(location = 1) in vec3 mesh_normal;
layout(location = 2) in vec2 texcoord;
layout(location = 3) in vec4 in_color;

out vec3 shadow_map_position;
out vec3 normal;
flat out vec4 color;

void main() {
  vec4 pos = vec4(mesh_pos, 1);
  vec4 world_pos = mesh_to_world * pos;
  world_pos.z += height * (pos.y * 0.5 - 0.5);
  gl_Position = world_to_clip * world_pos;
  shadow_map_position = (world_to_shadow * world_pos).xyz;
  normal = normalize((mesh_to_world * vec4(mesh_normal, 0)).xyz);
  color = in_color;
}
