import numpy as np
from OpenGL import GL

import matrix
import world_resource


class Trees(world_resource.WorldResource):
  def __init__(self, tree_mesh, tree_count, center, radius):
    super().__init__(center)
    self.vbo = -1
    self.tree_mesh = tree_mesh
    self.tree_count = tree_count
    self.eaten: float = 0.0
    angle = np.random.random_sample(tree_count) * np.pi * 2
    r = np.sqrt(np.random.random_sample(tree_count)) * radius
    x = r * np.cos(angle)
    y = r * np.sin(angle)

    mats = []
    base_transform = matrix.Rotate(90, 1, 0, 0) @ matrix.Scale(1 / 20, 1 / 20, 1 / 20)
    for idx in range(tree_count):
      main_scale = np.random.random() * 0.7 + 0.5
      m = base_transform
      m = m @ matrix.Scale(*((np.random.random(3) * 0.6 + 0.7) * main_scale))
      # TODO: lookup terrain height and follow the terrain
      m = m @ matrix.Translate(center[0] + x[idx], center[1] + y[idx], 0)
      mats.append(m)
    mats = np.stack(mats)

    self.vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, mats.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

  def __del__(self):
    if self.vbo != -1:
      GL.glDeleteBuffers(1, [self.vbo])
      self.vbo = -1

  def Harvest(self, amount):
    if self.eaten == 1.0:
      self.world.RemoveResource(self)
    else:
      self.eaten = min(1.0, self.eaten + amount)

  def Render(self, shadow=False):
    num = int(self.tree_count * (1.0 - self.eaten))
    self.tree_mesh.RenderInstanced(0, num, self.vbo, shadow=shadow)
