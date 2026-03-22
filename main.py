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
  GL.glFrustum(-1.6, 1.6, -1.0, 1.0, 0.1, 100.0)
  GL.glMatrixMode(GL.GL_MODELVIEW)

  st = time.time()
  while True:
    r = math.sin(time.time() - st) * 0.5 + 0.5
    GL.glClearColor(r, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

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
