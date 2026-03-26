import ctypes
import math
import numpy
import OpenGL
from OpenGL import GL
import pygame
import sys
import time

import animated_mesh
import city as city_module
import config
import matrix
import shaders as shaders_module
import shadows
import trees


ScreenWidth = 1440
ScreenHeight = 810

PrimitiveRestartIndex = 2000000000  # Arbitrary number higher than any vertex index we plan to use.


# Inspired by https://youtu.be/BFld4EBO2RE
def S(l):
  return 3 * numpy.power(l, 2) - 2 * numpy.power(l, 3)

def S_diff(l):
  return 6 * l - 6 * numpy.power(l, 2)

def f(v):
  ij, vo = numpy.divmod(v, 1)

  def pseudo(v):
    v = v.astype(numpy.float64)
    uv = numpy.divmod(v / numpy.e, 1)[1] * 123
    a = uv[..., 0] * uv[..., 1] * (uv[..., 0] + uv[..., 1])
    r = numpy.divmod(a, 1)[1]
    return r * 2 - 1

  aij = pseudo(ij)
  bij = pseudo(ij + [[1, 0]])
  cij = pseudo(ij + [[0, 1]])
  dij = pseudo(ij + [[1, 1]])

  z = (aij
       + (bij - aij) * S(vo[..., 0])
       + (cij - aij) * S(vo[..., 1])
       + (aij - bij - cij + dij) * S(vo[..., 0]) * S(vo[..., 1]))
  return z

def f_dx(v):
  ij, vo = numpy.divmod(v, 1)

  def pseudo(v):
    v = v.astype(numpy.float64)
    uv = numpy.divmod(v / numpy.e, 1)[1] * 123
    a = uv[..., 0] * uv[..., 1] * (uv[..., 0] + uv[..., 1])
    r = numpy.divmod(a, 1)[1]
    return r * 2 - 1

  aij = pseudo(ij)
  bij = pseudo(ij + [[1, 0]])
  cij = pseudo(ij + [[0, 1]])
  dij = pseudo(ij + [[1, 1]])

  z = ((bij - aij) * S_diff(vo[..., 0])
       + (aij - bij - cij + dij) * S_diff(vo[..., 0]) * S(vo[..., 1]))
  return z

def f_dy(v):
  ij, vo = numpy.divmod(v, 1)

  def pseudo(v):
    v = v.astype(numpy.float64)
    uv = numpy.divmod(v / numpy.e, 1)[1] * 123
    a = uv[..., 0] * uv[..., 1] * (uv[..., 0] + uv[..., 1])
    r = numpy.divmod(a, 1)[1]
    return r * 2 - 1

  aij = pseudo(ij)
  bij = pseudo(ij + [[1, 0]])
  cij = pseudo(ij + [[0, 1]])
  dij = pseudo(ij + [[1, 1]])

  z = ((cij - aij) * S_diff(vo[..., 1])
       + (aij - bij - cij + dij) * S(vo[..., 0]) * S_diff(vo[..., 1]))
  return z


class TerrainChunk:
  def __init__(self, x_offset):
    self.x_offset = x_offset

    x, y = numpy.meshgrid(
      numpy.linspace(0, config.TerrainWidth, config.TerrainResolutionX,
                     dtype=numpy.float32),
      numpy.linspace(-config.TerrainHeight / 2, config.TerrainHeight / 2,
                     config.TerrainResolutionY, dtype=numpy.float32))
    x = x + x_offset  # TODO: change this so each chunk uses "local" coordinates and we line things up elsewhere so we don't get creeping accuracy issues as we move far from the origin (i.e. re-center coordinates periodically)

    # TODO: generate some actually interesting terrain here, and pull in some data across chunks to make it nice and contiuous

    # Basic sine wave terrain:
    #self.z = numpy.sin(x * 8) * 0.05 + numpy.sin(y * 5) * 0.05 - 0.0
    #normals = numpy.stack([-numpy.cos(x * 8) * 8 * 0.05, -numpy.cos(y * 5) * 5 * 0.05, numpy.ones_like(x)], -1)

    p = numpy.stack([x, y], -1)
    M = numpy.array([[4/5, -3/5], [3/5, 4/5]])
    self.z = f(p) * 0.2
    # More high-freq variation, but need some work to compute the normals for this one:
    #M = numpy.array([[4/5, -3/5], [3/5, 4/5]])
    #self.z = f(p) * 0.2 + f(2 * p @ M) * 0.1
    self.z = self.z.astype(numpy.float32)
    normals = numpy.stack([-f_dx(p) * 0.2, -f_dy(p) * 0.2, numpy.ones_like(x)], -1)
    normals = normals.astype(numpy.float32)

    normals = normals / numpy.linalg.norm(normals, axis=2, keepdims=True)
    data = numpy.concat([self.z.reshape(-1, 1), normals.reshape(-1, 3)], -1)

    vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    self.vbo = vbo

  def get_height(self, x, y):
    return self.z[int(x), int(y)]

  def __del__(self):
    if hasattr(self, 'vbo'):
      GL.glDeleteBuffers(1, [self.vbo])


class BaseTerrain:
  def __init__(self, shaders):
    self.shaders = shaders

    row_buffer = [0, config.TerrainResolutionX]
    for x in range(config.TerrainResolutionX - 1):
      row_buffer.append(x + 1)
      row_buffer.append(config.TerrainResolutionX + x + 1)
    row_buffer = numpy.array(row_buffer, dtype=numpy.int32)
    all_parts = [row_buffer]
    for i in range(1, config.TerrainResolutionY - 1):
      all_parts.append(numpy.array([PrimitiveRestartIndex], dtype=numpy.int32))
      all_parts.append(row_buffer + (i * config.TerrainResolutionX))
    self.index_buffer = numpy.concat(all_parts)

    self.index_vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)
    GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer, GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    self.chunks = []
    self.next_chunk = 0
    self.SetOffset(0)

    self.vao = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(self.vao)

  def get_height(self, x, y):
    target_chunk = None
    for chunk in self.chunks:
      if chunk.x_offset <= x < chunk.x_offset + config.TerrainWidth:
        print(f"we found {chunk.x_offset} for {x}")
        target_chunk = chunk
        break
    return target_chunk.get_height(x, y)

  def SetOffset(self, x):
    # To debug chunk generation with just one chunk:
    #if not self.chunks:
    #  self.chunks.append(TerrainChunk(self.next_chunk * config.TerrainWidth))
    #return
    while self.next_chunk * config.TerrainWidth < x + config.TerrainWidth * 3:
      self.chunks.append(TerrainChunk(self.next_chunk * config.TerrainWidth))
      self.next_chunk += 1
    if len(self.chunks) > 7:
      del self.chunks[:-7]

  def Render(self, shadow=False):
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)

    if shadow:
      GL.glUseProgram(self.shaders.terrain_shadow.id)
    else:
      GL.glUseProgram(self.shaders.terrain.id)

    GL.glBindVertexArray(self.vao)
    GL.glEnableVertexAttribArray(0)
    GL.glEnableVertexAttribArray(1)

    for chunk in self.chunks:
      GL.glBindBuffer(GL.GL_ARRAY_BUFFER, chunk.vbo)
      GL.glVertexAttribPointer(0, 1, GL.GL_FLOAT, GL.GL_FALSE, 16, None)
      GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 16, ctypes.c_void_p(4))

      if shadow:
        GL.glUniform1f(self.shaders.terrain_shadow.x_offset, chunk.x_offset)
      else:
        GL.glUniform1f(self.shaders.terrain.x_offset, chunk.x_offset)
      GL.glDrawElements(GL.GL_TRIANGLE_STRIP, self.index_buffer.shape[0], GL.GL_UNSIGNED_INT, None)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableVertexAttribArray(0)
    GL.glDisableVertexAttribArray(1)
    GL.glUseProgram(0)


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

  GL.glEnable(GL.GL_PRIMITIVE_RESTART)
  GL.glPrimitiveRestartIndex(PrimitiveRestartIndex)

  vao = GL.glGenVertexArrays(1)
  GL.glBindVertexArray(vao)

  GL.glDisable(GL.GL_CULL_FACE)
  GL.glEnable(GL.GL_DEPTH_TEST)
  GL.glClearColor(0, 0, 0, 0)
  GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

  shaders = shaders_module.Shaders()
  base_terrain = BaseTerrain(shaders)

  tree_mesh = animated_mesh.AnimatedMesh('objs/Tree3.obj.vbo', shaders)
  some_trees = trees.Trees(tree_mesh, 15, [4.0, 0.0, 0.0], 1.0)
  eat_sound = pygame.mixer.Sound('sounds/eat-long-1.flac')
  last_eat_sound = 0.0

  if True:
    city = city_module.City(
      animated_mesh.AnimatedMesh('cube_with_legs.vbo', shaders),
      matrix.Rotate(90, 0, 1, 0) @ matrix.Rotate(90, 1, 0, 0) @ matrix.Scale(0.2, 0.2, 0.2))
  else:
    city = city_module.City(
      animated_mesh.AnimatedMesh('objs/city2.obj.vbo', shaders),
      matrix.Rotate(-90, 0, 1, 0) @ matrix.Rotate(90, 1, 0, 0) @ matrix.Scale(0.2, 0.2, 0.2))

  shadow_map = shadows.ShadowMap()
  GL.glActiveTexture(GL.GL_TEXTURE0)
  GL.glBindTexture(GL.GL_TEXTURE_2D, shadow_map.tex)
  shaders.SetUniformInAllShaders('shadow_map', 0)

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
    sun_direction = numpy.array([math.cos(sun_angle_rad), 0, math.sin(sun_angle_rad)])
    shaders.SetUniformInAllShaders('sun_direction', sun_direction)
    base_terrain.SetOffset(city.x)
    city.Update()

    # Shadow map
    """
    Want to figure out what part of ground plane this can see:

    GL.glFrustum(-0.16, 0.16, -0.1, 0.1, 0.1, 100.0)
    GL.glRotate(-30, 1, 0, 0)
    GL.glTranslate(-x, 3 - y, -2)

    but it's going to be centered on x, y roughly so just go with that for now
    x-4 to x+4, y-4 to y+4
    """
    current_height = base_terrain.get_height(city.x, city.y)
    mat = matrix.Ortho(-4, 4, -4, 4, -10, 10)
    mat = matrix.Rotate(90 - sun_angle, 0, -1, 0) @ mat
    mat = matrix.Translate(-city.x, -city.y, current_height) @ mat
    shaders.SetUniformInAllShaders('world_to_clip', mat)
    shaders.SetUniformInAllShaders('world_to_shadow', mat)
    GL.glViewport(0, 0, config.ShadowMapRes, config.ShadowMapRes)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, shadow_map.fbo)
    GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    base_terrain.Render(shadow=True)
    city.Render(shadow=True)
    some_trees.Render(shadow=True)

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    if False:
      data = numpy.zeros([config.ShadowMapRes, config.ShadowMapRes], dtype=numpy.float32)
      GL.glGetTextureImage(shadow_map.tex, 0, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, 1024*1024*4, data)
      data = (data * 255).astype(numpy.uint8)
      from PIL import Image
      im = Image.fromarray(data)
      im.save('depth.png')
      sys.exit(1)

    ## Actual rendering
    GL.glViewport(0, 0, *screen_res)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    current_height = base_terrain.get_height(city.x, city.y)
    mat = matrix.Frustum(-0.16, 0.16, -0.1, 0.1, 0.1, 100.0)
    mat = matrix.Rotate(-30, 1, 0, 0) @ mat
    mat = matrix.Translate(-city.x, 1 - city.y, -current_height) @ mat
    shaders.SetUniformInAllShaders('world_to_clip', mat)

    base_terrain.Render(shadow=False)
    city.Render(shadow=False)
    some_trees.Render(shadow=False)

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
      # TODO: check that we're actually close to some trees
      some_trees.Eat(delta * 0.3)
      # TODO: animation!
      # TODO: sound effect! in a less hacky way
      if now - last_eat_sound > 1.9:
        last_eat_sound = now
        eat_sound.play()
    moving = numpy.array([0, 0])
    if pressed[pygame.K_LEFT]:
      moving[0] = -1
    if pressed[pygame.K_RIGHT]:
      moving[0] = +1
    if pressed[pygame.K_UP]:
      moving[1] = +1
    if pressed[pygame.K_DOWN]:
      moving[1] = -1
    if numpy.any(moving):
      city.x += moving[0] * 2 * delta
      city.y += moving[1] * 2 * delta
      city.animation_time += delta

      target_angle = numpy.arctan2(moving[1], moving[0]) / math.pi * 180
      if abs(city.angle - target_angle) > abs(city.angle + 360 - target_angle):
        city.angle += 360
      elif abs(city.angle - target_angle) > abs(city.angle - 360 - target_angle):
        city.angle -= 360
      if city.angle < target_angle:
        city.angle += delta * 60
        if city.angle > target_angle:
          city.angle = target_angle
      else:
        city.angle -= delta * 60
        if city.angle < target_angle:
          city.angle = target_angle


if __name__ == '__main__':
  main()
