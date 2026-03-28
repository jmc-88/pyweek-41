import math
import numpy as np
from OpenGL import GL
import pygame
import sys
import time

import animated_mesh
import city as city_module
import config
import grain
import hud as hud_module
import matrix
import shaders as shaders_module
import shadows
import terrain
import world_resource


ScreenWidth = 1440
ScreenHeight = 810

class World:
  def __init__(self, city, terrain):
    self.city = city
    self.terrain = terrain
    self.resources: list[world_resource.WorldResource] = []

  def AddResource(self, res: world_resource.WorldResource):
    self.resources.append(res)
    res.world = self

  def RemoveResource(self, res: world_resource.WorldResource):
    if res in self.resources:
      self.resources.remove(res)

  def Update(self, delta):
    self.city.Update(delta)
    self.terrain.Update(delta)
    for res in self.resources:
      res.Update(delta)

  def Render(self, shadow):
    self.city.Render(shadow)
    self.terrain.Render(shadow)
    for res in self.resources:
      res.Render(shadow=shadow)

  def NearestResource(self, pos, max_distance):
    nearest = None
    nearest_dist = math.inf
    for res in self.resources:
      dist = np.linalg.norm(pos - res.center)
      if dist > max_distance:
        continue
      if dist < nearest_dist:
        nearest = res
        nearest_dist = dist
    return nearest


def main():
  pygame.init()

  pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
  pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
  pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

  screen_flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE
  screen_res = (ScreenWidth, ScreenHeight)

  if config.Fullscreen:
    dpy_info = pygame.display.Info()
    if dpy_info.current_w == -1 or dpy_info.current_h == -1:
      raise RuntimeError(
          "Couldn't determine the current screen resolution "
          "to enter fullscreen mode."
      )
    screen_flags |= pygame.FULLSCREEN
    screen_res = (dpy_info.current_w, dpy_info.current_h)

  pygame.display.set_mode(screen_res, screen_flags)
  pygame.display.set_caption("Spurtle City")

  GL.glEnable(GL.GL_PRIMITIVE_RESTART)
  GL.glPrimitiveRestartIndex(config.PrimitiveRestartIndex)

  vao = GL.glGenVertexArrays(1)
  GL.glBindVertexArray(vao)

  GL.glDisable(GL.GL_CULL_FACE)
  GL.glEnable(GL.GL_DEPTH_TEST)
  GL.glClearColor(0, 0, 0, 0)
  GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

  shaders = shaders_module.Shaders()

  tree_mesh = animated_mesh.AnimatedMesh('objs/Tree3.obj.vbo', shaders)
  grain_mesh = animated_mesh.AnimatedMesh('objs/grain.vbo', shaders)
  sounds = {
    'eat': pygame.mixer.Sound('sounds/eat-long-1.flac'),
    'eat_fail': pygame.mixer.Sound('sounds/um1.flac'),
  }
  last_eat_sound = 0.0

  base_terrain = terrain.BaseTerrain(shaders)
  base_terrain.tree_mesh = tree_mesh
  base_terrain.grain_mesh = grain_mesh

  city = city_module.City(
    base_terrain, shaders,
    matrix.Rotate(-90, 0, 1, 0) @ matrix.Rotate(90, 1, 0, 0) @ matrix.Scale(0.2, 0.2, 0.2))

  world = World(city, base_terrain)
  base_terrain.world = world
  base_terrain.SetOffset(0)

  shadow_map = shadows.ShadowMap()
  # Arbitrarily keep the shadow map always in texture slot 5.
  GL.glActiveTexture(GL.GL_TEXTURE0 + 5)
  GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_map.tex)
  shaders.SetUniformInAllShaders('shadow_map', 5)

  hud = hud_module.HUD(shaders, world)

  st = time.time()
  prev_frame = time.time()
  night_progress = 0.0
  while True:
    now = time.time()
    delta = now - prev_frame
    prev_frame = now

    night_progress += 0.5 * delta
    distance_to_night = city.x - night_progress
    sun_angle_min = 5
    sun_angle_max = 80
    sun_angle = sun_angle_min + (distance_to_night - 0.2) / 20 * (sun_angle_max - sun_angle_min)
    sun_angle = max(sun_angle_min, sun_angle)
    sun_angle = min(sun_angle_max, sun_angle)
    sun_angle_rad = sun_angle / 180 * math.pi
    sun_direction = np.array([math.cos(sun_angle_rad), 0, math.sin(sun_angle_rad)])
    shaders.SetUniformInAllShaders('sun_direction', sun_direction)
    base_terrain.SetOffset(city.x)
    world.Update(delta)

    # Shadow map
    """
    Camera can see the ground in roughly the range:
    x - 9.5 to x + 9.5
    y - 2 to y + 7
    """
    mat = matrix.Ortho(-9.5, 9.5, -2, 7, -12, 12)
    mat = matrix.Rotate(90 - sun_angle, 0, -1, 0) @ mat
    mat = matrix.Translate(-city.x, -city.y, 0) @ mat
    shaders.SetUniformInAllShaders('world_to_clip', mat)
    shaders.SetUniformInAllShaders('world_to_shadow', mat)
    GL.glViewport(0, 0, config.ShadowMapRes, config.ShadowMapRes)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_map.fbo)
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    world.Render(shadow=True)

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    ## Actual rendering
    GL.glViewport(0, 0, *screen_res)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    mat = matrix.Frustum(-0.16, 0.16, -0.1, 0.1, 0.1, 100.0)
    mat = matrix.Rotate(-30, 1, 0, 0) @ mat
    mat = matrix.Translate(-city.x, 1 - city.y, -2) @ mat
    shaders.SetUniformInAllShaders('world_to_clip', mat)

    world.Render(shadow=False)

    hud.Update()
    hud.Render()

    pygame.display.flip()

    done = False
    for event in pygame.event.get():
      match event:
        case (
            pygame.Event(type=pygame.QUIT)
            | pygame.Event(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)
        ):
          done = True
        case pygame.Event(type=pygame.KEYDOWN, key=pygame.K_f):
          pygame.display.toggle_fullscreen()
          screen_res = pygame.display.get_window_size()
    if done:
      break

    pressed = pygame.key.get_pressed()

    if pressed[pygame.K_SPACE]:
      nearest_resource = world.NearestResource(
        np.array([city.x, city.y]), 0.8)
      if nearest_resource:
        nearest_resource.Harvest(delta * 0.3)
        # TODO: animation!
        # TODO: sound effect! in a less hacky way
        if now - last_eat_sound > 1.9:
          last_eat_sound = now
          sounds['eat'].play()
      else:
        if now - last_eat_sound > 1.9:
          last_eat_sound = now
          sounds['eat_fail'].play()

    moving = np.array([0, 0])
    if pressed[pygame.K_LEFT]:
      moving[0] = -1
    if pressed[pygame.K_RIGHT]:
      moving[0] = +1
    if pressed[pygame.K_UP]:
      moving[1] = +1
    if pressed[pygame.K_DOWN]:
      moving[1] = -1
    if np.any(moving):
      city.walk(moving, delta)


if __name__ == '__main__':
  try:
    main()
  except Exception as e:
    import traceback
    traceback.print_exception(sys.exception(), colorize=True)
    sys.exit(1)
