#version 410 core

uniform vec3 sun_direction;
uniform sampler2D shadow_map;

in vec3 normal;
in vec3 shadow_map_position;

layout(location = 0) out vec4 FragColor;

#define NumSamplePoints 9
struct SamplePoint {
  float weight;
  vec2 ofs;
} sample_points[NumSamplePoints] = SamplePoint[](
  SamplePoint(2./14, vec2(0, 0)),
  SamplePoint(2./14, vec2(1.0 / ShadowMapRes, 0)),
  SamplePoint(2./14, vec2(-1.0 / ShadowMapRes, 0)),
  SamplePoint(2./14, vec2(0, 1.0 / ShadowMapRes)),
  SamplePoint(2./14, vec2(0, -1.0 / ShadowMapRes)),
  SamplePoint(1./14, vec2(1.0 / ShadowMapRes, 1.0 / ShadowMapRes)),
  SamplePoint(1./14, vec2(-1.0 / ShadowMapRes, 1.0 / ShadowMapRes)),
  SamplePoint(1./14, vec2(1.0 / ShadowMapRes, -1.0 / ShadowMapRes)),
  SamplePoint(1./14, vec2(-1.0 / ShadowMapRes, -1.0 / ShadowMapRes))
);

float shadow_level() {
  vec3 s = shadow_map_position * 0.5 + 0.5;
  float shadow = 0.0;
  for (int i = 0; i < NumSamplePoints; i++) {
    float d = texture(shadow_map, s.xy + sample_points[i].ofs).r;
    shadow += d + ShadowBias > s.z? sample_points[i].weight : 0;
  }
  //float d = texture(shadow_map, s.xy).r;
  //float shadow = d + ShadowBias > s.z? 1 : 0;
  return shadow;
}

void main() {
  vec3 light_color = vec3(0.2, 0.2, 0.25);

  float light_level = dot(sun_direction, normal);
  light_level *= shadow_level();
  light_color += vec3(0.8, 0.8, 0.75) * clamp(light_level, 0, 1);

  vec3 grass_color = vec3(0.35, 0.9, 0.35);
  vec3 hill_color = vec3(0.8, 0.8, 0.2);
  float grass_mix = clamp((normal.z - 0.93) * 100, 0.0, 1.0);
  vec3 color = mix(hill_color, grass_color, grass_mix);

  FragColor = vec4(light_color * color, 1);
}
