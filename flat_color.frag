#version 410 core

out vec4 FragColor;

uniform vec4 color;
uniform vec4 pulsatingColor;
uniform bool isPulsating;
uniform int ticks;

void main() {
  if (isPulsating) {
    float pulse = sin(ticks * 0.05);
    FragColor = mix(color, pulsatingColor, pulse);
  } else {
    FragColor = color;
  }
}
