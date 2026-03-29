#version 410 core

// Has one corner in x and y, and width and height in z and w.
uniform vec4 corners;

layout(location = 0) in vec2 pos;

out vec2 texcoord;

void main() {
  texcoord = vec2(pos.x, 1 - pos.y);
  vec2 p = vec2(corners.x + pos.x * corners.z,
                corners.y + pos.y * corners.w);
  gl_Position = vec4(p, 0, 1);
}
