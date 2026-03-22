import math
import numpy
import OpenGL
from OpenGL import GL
import pygame
import time


ScreenWidth = 1440
ScreenHeight = 810


def main():
  pygame.init()
  screen = pygame.display.set_mode(
    (ScreenWidth, ScreenHeight),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)

  GL.glViewport(0, 0, ScreenWidth, ScreenHeight)
  GL.glMatrixMode(GL.GL_PROJECTION)
  GL.glFrustum(-0.16, 0.16, -0.1, 0.1, 0.1, 100.0)
  GL.glMatrixMode(GL.GL_MODELVIEW)
  GL.glLoadIdentity()
  GL.glRotate(-60, 1, 0, 0)
  GL.glTranslate(0, 2, -1)

  primitive_restart_index = 1000000000  # Arbitrary number higher than any index we plan to use.
  GL.glPrimitiveRestartIndex(primitive_restart_index)
  GL.glEnable(GL.GL_PRIMITIVE_RESTART)

  t_w = t_h = 32
  index_buffer = [0, t_w]
  for x in range(t_w - 1):
    index_buffer.append(x + 1)
    index_buffer.append(t_w + x + 1)
  index_buffer = numpy.array(index_buffer, dtype=numpy.int32)
  all_parts = [index_buffer]
  for i in range(1, t_h - 1):
    all_parts.append(numpy.array([primitive_restart_index], dtype=numpy.int32))
    all_parts.append(index_buffer + (i * t_w))
  index_buffer = numpy.concat(all_parts)

  index_vbo = GL.glGenBuffers(1)
  GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_vbo)
  GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer, GL.GL_STATIC_DRAW)
  GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

  x, y = numpy.meshgrid(
    numpy.linspace(-1, 1, t_w, dtype=numpy.float32),
    numpy.linspace(-1, 1, t_h, dtype=numpy.float32))
  z = numpy.sin(x * 8 + y * 5) * 0.05 - 0.0
  positions = numpy.stack((x, y, z), -1)
  positions_vbo = GL.glGenBuffers(1)
  GL.glBindBuffer(GL.GL_ARRAY_BUFFER, positions_vbo)
  GL.glBufferData(GL.GL_ARRAY_BUFFER, positions.flatten(), GL.GL_STATIC_DRAW)
  GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

  st = time.time()
  while True:
    r = (math.sin(time.time() - st) + 1) * 0.1
    GL.glClearColor(r, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
    GL.glDisable(GL.GL_CULL_FACE)

    GL.glColor(1, 1, 1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, positions_vbo)
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glVertexPointer(3, GL.GL_FLOAT, 0, None)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_vbo)
    GL.glDrawElements(GL.GL_TRIANGLE_STRIP, index_buffer.shape[0], GL.GL_UNSIGNED_INT, None)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

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
