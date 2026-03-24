#version 410 core

uniform mat4 world_to_view;
uniform mat4 world_to_shadow;
uniform mat4 mesh_to_world;

layout(location = 0) in vec3 mesh_pos;

out vec3 shadow_map_position;

void main() {
  vec4 pos = vec4(mesh_pos, 1);
  vec4 world_pos = mesh_to_world * pos;
  gl_Position = world_to_view * world_pos;
  shadow_map_position = (world_to_shadow * world_pos).xyz;
}
