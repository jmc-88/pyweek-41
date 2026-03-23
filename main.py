import math
import numpy
import OpenGL
from OpenGL import GL
import pygame
import sys
import time

import shaders as shaders_module


ScreenWidth = 1440
ScreenHeight = 810

PrimitiveRestartIndex = 2000000000  # Arbitrary number higher than any vertex index we plan to use.


TerrainResolutionX = 32
TerrainResolutionY = 32 * 8
TerrainWidth = 1.0  # Width of one terrain chunk in world coordinates.
TerrainHeight = 8.0  # Height of one terrain chunk in world coordinates.


class TerrainChunk:
  def __init__(self, x_offset):
    self.x_offset = x_offset

    # TODO: should be possible to use a vertex shader to compute the x
    # and y coordinates on the fly and only have to use buffers for
    # the z values
    x, y = numpy.meshgrid(
      numpy.linspace(0, TerrainWidth, TerrainResolutionX, dtype=numpy.float32),
      numpy.linspace(-TerrainHeight / 2, TerrainHeight / 2,
                     TerrainResolutionY, dtype=numpy.float32))
    x = x + x_offset  # TODO: change this so each chunk uses "local" coordinates and we line things up elsewhere so we don't get creeping accuracy issues as we move far from the origin (i.e. re-center coordinates periodically)

    # TODO: generate some actually interesting terrain here, and pull in some data across chunks to make it nice and contiuous
    self.z = numpy.sin(x * 8) * 0.05 + numpy.sin(y * 5) * 0.05 - 0.0
    normals = numpy.stack([-numpy.cos(x * 8) * 8 * 0.05, -numpy.cos(y * 5) * 5 * 0.05, numpy.ones_like(x)], -1)
    normals = normals / numpy.linalg.norm(normals, axis=2, keepdims=True)

    data = numpy.concat([self.z.reshape(-1, 1), normals.reshape(-1, 3)], -1)

    vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    self.vbo = vbo

  def __del__(self):
    GL.glDeleteBuffers(1, [self.vbo])


class BaseTerrain:
  def __init__(self, shaders):
    self.shaders = shaders

    row_buffer = [0, TerrainResolutionX]
    for x in range(TerrainResolutionX - 1):
      row_buffer.append(x + 1)
      row_buffer.append(TerrainResolutionX + x + 1)
    row_buffer = numpy.array(row_buffer, dtype=numpy.int32)
    all_parts = [row_buffer]
    for i in range(1, TerrainResolutionY - 1):
      all_parts.append(numpy.array([PrimitiveRestartIndex], dtype=numpy.int32))
      all_parts.append(row_buffer + (i * TerrainResolutionX))
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
    GL.glVertexAttribFormat(0, 1, GL.GL_FLOAT, GL.GL_FALSE, 0)
    GL.glVertexAttribFormat(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 4)

  def SetOffset(self, x):
    while self.next_chunk < x + 4:
      self.chunks.append(TerrainChunk(self.next_chunk))
      self.next_chunk += 1
    if len(self.chunks) > 6:
      del self.chunks[:-6]

  def Render(self, transform_matrix, normal_matrix, sun_direction):
    GL.glColor(1, 1, 1)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)

    GL.glUseProgram(self.shaders.terrain_program)
    GL.glUniformMatrix4fv(0, 1, GL.GL_FALSE, transform_matrix)
    GL.glUniform3f(5, sun_direction[0], sun_direction[1], sun_direction[2])
    GL.glBindVertexArray(self.vao)
    GL.glEnableVertexAttribArray(0)
    GL.glEnableVertexAttribArray(1)

    for chunk in self.chunks:
      # TODO: Why does this not work? Should be equivalent to the below, I thought...
      #GL.glBindBuffer(GL.GL_ARRAY_BUFFER, chunk.vbo)
      #GL.glVertexAttribPointer(0, 1, GL.GL_FLOAT, GL.GL_FALSE, 16, 0)

      GL.glBindVertexBuffer(0, chunk.vbo, 0, 16)
      GL.glVertexAttribBinding(0, 0)
      GL.glVertexAttribBinding(1, 0)
      GL.glUniform1f(1, chunk.x_offset)
      GL.glDrawElements(GL.GL_TRIANGLE_STRIP, self.index_buffer.shape[0], GL.GL_UNSIGNED_INT, None)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableVertexAttribArray(0)
    GL.glDisableVertexAttribArray(1)
    GL.glUseProgram(0)


def main():
  pygame.init()
  screen = pygame.display.set_mode(
    (ScreenWidth, ScreenHeight),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)

  GL.glViewport(0, 0, ScreenWidth, ScreenHeight)

  GL.glPrimitiveRestartIndex(PrimitiveRestartIndex)
  GL.glEnable(GL.GL_PRIMITIVE_RESTART)

  shaders = shaders_module.Shaders()
  base_terrain = BaseTerrain(shaders)

  st = time.time()
  while True:
    x = (time.time() - st) * 0.5
    base_terrain.SetOffset(x)
    GL.glClearColor(0, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # This is ugly but I'm lazy and this kinda works.
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glRotate(-50, 1, 0, 0)
    GL.glTranslate(-x, 2, -1)
    normal_matrix = GL.glGetFloat(GL.GL_PROJECTION_MATRIX)
    normal_matrix = normal_matrix[:3, :3]

    GL.glLoadIdentity()
    GL.glFrustum(-0.16, 0.16, -0.1, 0.1, 0.1, 100.0)
    GL.glRotate(-50, 1, 0, 0)
    GL.glTranslate(-x, 2, -1)
    transform_matrix = GL.glGetFloat(GL.GL_PROJECTION_MATRIX)

    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
    GL.glDisable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_DEPTH_TEST)

    sun_direction = numpy.array([math.sin(0.5), 0, math.cos(0.5)])
    base_terrain.Render(transform_matrix, normal_matrix, sun_direction)

    pygame.display.flip()

    done = False
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        done = True
        break
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          done = True
          break
      else:
        pass
        #print('event=%r' % event)
    if done:
      break


if __name__ == '__main__':
  main()
