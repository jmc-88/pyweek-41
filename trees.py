import numpy
import OpenGL
from OpenGL import GL

import matrix


class Trees:
  def __init__(self, tree_mesh, num, center, radius):
    self.vbo = -1
    self.tree_mesh = tree_mesh
    self.num = num
    self.eaten = 0
    self.center = center
    angle = numpy.random.random_sample(num) * numpy.pi * 2
    r = numpy.sqrt(numpy.random.random_sample(num)) * radius
    x = r * numpy.cos(angle)
    y = r * numpy.sin(angle)

    mats = []
    base_transform = matrix.Rotate(90, 1, 0, 0) @ matrix.Scale(1 / 20, 1 / 20, 1 / 20)
    for idx in range(num):
      # TODO: lookup terrain height and follow the terrain
      m = matrix.Translate(center[0] + x[idx], center[1] + y[idx], center[2])
      m = base_transform @ m
      mats.append(m)
    mats = numpy.stack(mats)

    self.vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, mats.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

  def __del__(self):
    if self.vbo != -1:
      GL.glDeleteBuffers(1, [self.vbo])
      self.vbo = -1

  def Eat(self, amount):
    self.eaten += amount
    self.eaten = min(1, self.eaten)

  def Render(self, shadow=False):
    num = int(self.num * (1 - self.eaten))
    self.tree_mesh.RenderInstanced(0, num, self.vbo, shadow=shadow)
