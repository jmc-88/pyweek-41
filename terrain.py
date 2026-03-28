import ctypes
import math
import numpy as np
from OpenGL import GL

import config
import trees
import grain
import world_object


# Inspired by https://youtu.be/BFld4EBO2RE
def S(l):
  return 3 * np.power(l, 2) - 2 * np.power(l, 3)

def S_diff(l):
  return 6 * l - 6 * np.power(l, 2)

def f(v):
  ij, vo = np.divmod(v, 1)

  def pseudo(v):
    v = v.astype(np.float64)
    uv = np.divmod(v / np.e, 1)[1] * 123
    a = uv[..., 0] * uv[..., 1] * (uv[..., 0] + uv[..., 1])
    r = np.divmod(a, 1)[1]
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
  ij, vo = np.divmod(v, 1)

  def pseudo(v):
    v = v.astype(np.float64)
    uv = np.divmod(v / np.e, 1)[1] * 123
    a = uv[..., 0] * uv[..., 1] * (uv[..., 0] + uv[..., 1])
    r = np.divmod(a, 1)[1]
    return r * 2 - 1

  aij = pseudo(ij)
  bij = pseudo(ij + [[1, 0]])
  cij = pseudo(ij + [[0, 1]])
  dij = pseudo(ij + [[1, 1]])

  z = ((bij - aij) * S_diff(vo[..., 0])
       + (aij - bij - cij + dij) * S_diff(vo[..., 0]) * S(vo[..., 1]))
  return z

def f_dy(v):
  ij, vo = np.divmod(v, 1)

  def pseudo(v):
    v = v.astype(np.float64)
    uv = np.divmod(v / np.e, 1)[1] * 123
    a = uv[..., 0] * uv[..., 1] * (uv[..., 0] + uv[..., 1])
    r = np.divmod(a, 1)[1]
    return r * 2 - 1

  aij = pseudo(ij)
  bij = pseudo(ij + [[1, 0]])
  cij = pseudo(ij + [[0, 1]])
  dij = pseudo(ij + [[1, 1]])

  z = ((cij - aij) * S_diff(vo[..., 1])
       + (aij - bij - cij + dij) * S(vo[..., 0]) * S_diff(vo[..., 1]))
  return z


def GetSpacedSamples(xv, yv, n, min_dist=1.5):
    points = np.column_stack((xv.ravel(), yv.ravel()))
    np.random.shuffle(points)

    selected = []
    for p in points:
      if not selected or all(np.linalg.norm(p - s) >= min_dist for s in selected):
        selected.append(p)
        if len(selected) >= n:
          break
    return np.array(selected)


class TerrainChunk:
  def __init__(self, world, tree_mesh, grain_mesh, x_offset):
    self.x_offset = x_offset
    self.world = world

    x, y = np.meshgrid(
      np.linspace(0, config.TerrainWidth, config.TerrainResolutionX,
                     dtype=np.float32),
      np.linspace(-config.TerrainHeight / 2, config.TerrainHeight / 2,
                     config.TerrainResolutionY, dtype=np.float32))
    x = x + x_offset  # TODO: change this so each chunk uses "local" coordinates and we line things up elsewhere so we don't get creeping accuracy issues as we move far from the origin (i.e. re-center coordinates periodically)

    # TODO: generate some actually interesting terrain here, and pull in some data across chunks to make it nice and contiuous
    self.resources = []

    rng = np.random.default_rng()
    samples = GetSpacedSamples(x, y, rng.integers(2, 8))
    num_trees = rng.integers(len(samples))
    for sx, sy in samples[:num_trees]:
      num = 1 + rng.integers(15)
      r = trees.Trees(tree_mesh, num, np.array([sx, sy]), num / 15)
      self.resources.append(r)
      world.AddResource(r)
    for sx, sy in samples[num_trees:]:
      num = 5 + rng.integers(15)
      r = grain.Grain(grain_mesh, num, np.array([sx, sy]), num / 50)
      self.resources.append(r)
      world.AddResource(r)

    # Basic sine wave terrain:
    #self.z = np.sin(x * 8) * 0.05 + np.sin(y * 5) * 0.05 - 0.0
    #normals = np.stack([-np.cos(x * 8) * 8 * 0.05, -np.cos(y * 5) * 5 * 0.05, np.ones_like(x)], -1)

    p = np.stack([x, y], -1)
    M = np.array([[4/5, -3/5], [3/5, 4/5]])
    self.z = f(p) * 0.2
    # More high-freq variation, but need some work to compute the normals for this one:
    #M = np.array([[4/5, -3/5], [3/5, 4/5]])
    #self.z = f(p) * 0.2 + f(2 * p @ M) * 0.1
    self.z = self.z.astype(np.float32)
    normals = np.stack([-f_dx(p) * 0.2, -f_dy(p) * 0.2, np.ones_like(x)], -1)
    normals = normals.astype(np.float32)

    normals = normals / np.linalg.norm(normals, axis=2, keepdims=True)
    data = np.concat([self.z.reshape(-1, 1), normals.reshape(-1, 3)], -1)

    vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, data.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    self.vbo = vbo

  def get_height(self, x, y):

    x_idx = int((x - self.x_offset / config.TerrainWidth) * config.TerrainResolutionX)

    y_shifted = y + (config.TerrainHeight / 2)
    y_idx = int((y_shifted / config.TerrainHeight) * config.TerrainResolutionY)

    x_idx = np.clip(x_idx, 0, config.TerrainResolutionX - 1)
    y_idx = np.clip(y_idx, 0, config.TerrainResolutionY - 1)

    return self.z[x_idx, y_idx]

  def Remove(self):
    GL.glDeleteBuffers(1, [self.vbo])
    for r in self.resources:
      self.world.RemoveResource(r)


class BaseTerrain(world_object.WorldObject):
  def __init__(self, shaders):
    self.world = None  # external
    self.tree_mesh = None  # external
    self.grain_mesh = None  # external
    self.shaders = shaders

    row_buffer = [0, config.TerrainResolutionX]
    for x in range(config.TerrainResolutionX - 1):
      row_buffer.append(x + 1)
      row_buffer.append(config.TerrainResolutionX + x + 1)
    row_buffer = np.array(row_buffer, dtype=np.int32)
    all_parts = [row_buffer]
    for i in range(1, config.TerrainResolutionY - 1):
      all_parts.append(np.array([config.PrimitiveRestartIndex], dtype=np.int32))
      all_parts.append(row_buffer + (i * config.TerrainResolutionX))
    self.index_buffer = np.concat(all_parts)

    self.index_vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)
    GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer, GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    self.chunks = []
    self.next_chunk = 0

    self.vao = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(self.vao)

  def get_height(self, x, y):
    target_chunk = None
    for chunk in self.chunks:
      if chunk.x_offset <= x < chunk.x_offset + config.TerrainWidth:
        target_chunk = chunk
        break
    return target_chunk.get_height(x, y)

  def SetOffset(self, x):
    # To debug chunk generation with just one chunk:
    #if not self.chunks:
    #  self.chunks.append(TerrainChunk(self.next_chunk * config.TerrainWidth))
    #return

    assert self.world is not None
    assert self.tree_mesh is not None
    assert self.grain_mesh is not None

    while self.next_chunk * config.TerrainWidth < x + config.TerrainWidth * 3:
      self.chunks.append(TerrainChunk(self.world, self.tree_mesh, self.grain_mesh, self.next_chunk * config.TerrainWidth))
      self.next_chunk += 1
    if len(self.chunks) > 7:
      for c in self.chunks[:-7]:
        c.Remove()
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