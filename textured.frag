#version 410 core

layout(location = 0) out vec4 FragColor;

in vec2 texcoord;
uniform sampler2D tex;

void main() {
  FragColor = texture(tex, texcoord);
}
