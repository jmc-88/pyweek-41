uniform vec3 sun_direction;
uniform sampler2D shadow_map;

in vec3 normal;
in vec3 shadow_map_position;

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

float ShadowLevel() {
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

vec3 LightColor() {
  vec3 ambient = vec3(0.1, 0.1, 0.1);
  vec3 sky_color = vec3(0.2, 0.2, 0.3);
  vec3 sun_color = vec3(0.7, 0.7, 0.6);

  vec3 light_color = ambient;

  float light_level = dot(sun_direction, normal);
  light_level *= ShadowLevel();
  light_color += sun_color * clamp(light_level, 0, 1);

  light_color += sky_color * clamp(normal.z, 0, 1);

  return light_color;
}
