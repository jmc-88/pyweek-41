import numpy
import OpenGL
from OpenGL import GL
from OpenGL.arrays import vbo


class AnimatedMesh:
  def __init__(self, path):
    with open(path, 'rb') as f:
      self.frame_index_start = numpy.load(f)
      indices = numpy.load(f)
      verts = numpy.load(f)

    self.vbo, self.index_vbo = GL.glGenBuffers(2)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, verts, GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    self.vbo_helper = vbo.VBO(indices, usage='GL_STATIC_DRAW', target='GL_ELEMENT_ARRAY_BUFFER')

  @property
  def num_frames(self):
    return len(self.frame_index_start) - 1

  def Render(self, frame):
    i0 = self.frame_index_start[frame]
    i1 = self.frame_index_start[frame + 1]

    GL.glColor(1, 1, 1)

    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glVertexPointer(3, GL.GL_FLOAT, 8*4, None)
    with self.vbo_helper:
      GL.glDrawElements(GL.GL_TRIANGLES, i1 - i0, GL.GL_UNSIGNED_INT, self.vbo_helper + int(i0 * 4))
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
