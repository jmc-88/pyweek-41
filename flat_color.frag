#version 410 core

uniform vec4 color;

layout(location = 0) out vec4 FragColor;

void main() {
  FragColor = color;
}
