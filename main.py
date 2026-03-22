import math
import numpy
import OpenGL
from OpenGL import GL
import pygame
import time


ScreenWidth = 1440
ScreenHeight = 810

PrimitiveRestartIndex = 2000000000  # Arbitrary number higher than any vertex index we plan to use.


TerrainResolutionX = 32
TerrainResolutionY = 32 * 8
TerrainWidth = 1.0  # Width of one terrain chunk in world coordinates.
TerrainHeight = 8.0  # Height of one terrain chunk in world coordinates.

class TerrainChunk:
  def __init__(self, global_x_offset):
    # TODO: should be possible to use a vertex shader to compute the x
    # and y coordinates on the fly and only have to use buffers for
    # the z values
    x, y = numpy.meshgrid(
      numpy.linspace(0, TerrainWidth, TerrainResolutionX, dtype=numpy.float32),
      numpy.linspace(-TerrainHeight / 2, TerrainHeight / 2,
                     TerrainResolutionY, dtype=numpy.float32))
    x = x + global_x_offset  # TODO: change this so each chunk uses "local" coordinates and we line things up elsewhere so we don't get creeping accuracy issues as we move far from the origin (i.e. re-center coordinates periodically)

    # TODO: generate some actually interesting terrain here, and pull in some data across chunks to make it nice and contiuous
    z = numpy.sin(x * 8 + y * 5) * 0.05 - 0.0
    positions = numpy.stack((x, y, z), -1)
    positions_vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, positions_vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, positions.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    self.positions_vbo = positions_vbo

  def __del__(self):
    GL.glDeleteBuffers(1, [self.positions_vbo])
    self.positions_vbo = -1


class BaseTerrain:
  def __init__(self):
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

  def SetOffset(self, x):
    while self.next_chunk < x + 4:
      self.chunks.append(TerrainChunk(self.next_chunk))
      self.next_chunk += 1
    if len(self.chunks) > 6:
      del self.chunks[:-6]

  def Render(self):
    GL.glColor(1, 1, 1)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

    for chunk in self.chunks:
      GL.glBindBuffer(GL.GL_ARRAY_BUFFER, chunk.positions_vbo)
      GL.glVertexPointer(3, GL.GL_FLOAT, 0, None)
      GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
      GL.glDrawElements(GL.GL_TRIANGLE_STRIP, self.index_buffer.shape[0], GL.GL_UNSIGNED_INT, None)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)


def main():
  pygame.init()
  screen = pygame.display.set_mode(
    (ScreenWidth, ScreenHeight),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)

  GL.glViewport(0, 0, ScreenWidth, ScreenHeight)
  GL.glMatrixMode(GL.GL_PROJECTION)
  GL.glFrustum(-0.16, 0.16, -0.1, 0.1, 0.1, 100.0)

  GL.glPrimitiveRestartIndex(PrimitiveRestartIndex)
  GL.glEnable(GL.GL_PRIMITIVE_RESTART)

  base_terrain = BaseTerrain()

  st = time.time()
  while True:
    x = (time.time() - st) * 0.5
    base_terrain.SetOffset(x)
    GL.glClearColor(0, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    GL.glRotate(-60, 1, 0, 0)
    GL.glTranslate(-x, 2, -1)

    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
    GL.glDisable(GL.GL_CULL_FACE)

    base_terrain.Render()

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
