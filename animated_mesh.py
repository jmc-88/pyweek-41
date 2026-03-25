import ctypes
import numpy
import OpenGL
from OpenGL import GL
from OpenGL.arrays import vbo


class AnimatedMesh:
  def __init__(self, path, shaders):
    self.shaders = shaders
    with open(path, 'rb') as f:
      self.num_frames = numpy.load(f).item()
      self.num_verts = numpy.load(f).item()
      indices = numpy.load(f)
      verts = numpy.load(f)
      colors = numpy.load(f)

    self.num_indices = indices.shape[0]
    self.vbo, self.index_vbo, self.color_vbo = GL.glGenBuffers(3)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, verts, GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.color_vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, colors, GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    self.vbo_helper = vbo.VBO(indices, usage='GL_STATIC_DRAW', target='GL_ELEMENT_ARRAY_BUFFER')
    #self.vao = GL.glGenVertexArrays(1)

  def Render(self, frame, render_state, mesh_to_world,
             shadow=False):
    if shadow:
      GL.glUseProgram(self.shaders.mesh_shadow.id)
      GL.glUniformMatrix4fv(
        self.shaders.mesh_shadow.mesh_to_world,
        1, GL.GL_FALSE, mesh_to_world)
    else:
      GL.glUseProgram(self.shaders.mesh.id)
      GL.glUniformMatrix4fv(
        self.shaders.mesh.mesh_to_world,
        1, GL.GL_FALSE, mesh_to_world)

    # TODO: figure out why this causes segfaults
    #GL.glBindVertexArray(self.vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.color_vbo)
    GL.glVertexAttribPointer(
      3, 4, GL.GL_UNSIGNED_BYTE, GL.GL_TRUE, 0, None)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    # Positions and normals, stored in blocks per frame:
    ofs = 2 * 4 * self.num_verts + frame * self.num_verts * 6 * 4
    GL.glVertexAttribPointer(
      0, 3, GL.GL_FLOAT, GL.GL_FALSE, 6*4,
      ctypes.c_void_p(ofs))
    GL.glVertexAttribPointer(
      1, 3, GL.GL_FLOAT, GL.GL_FALSE, 6*4,
      ctypes.c_void_p(ofs + 3 * 4))
    # Texcoords, stored at the start of the buffer:
    GL.glVertexAttribPointer(
      2, 2, GL.GL_FLOAT, GL.GL_FALSE, 2*4, None)
    GL.glEnableVertexAttribArray(0)
    GL.glEnableVertexAttribArray(1)
    GL.glEnableVertexAttribArray(2)
    GL.glEnableVertexAttribArray(3)

    with self.vbo_helper:
      GL.glDrawElements(GL.GL_TRIANGLES, self.num_indices, GL.GL_UNSIGNED_INT, None)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableVertexAttribArray(0)
    GL.glDisableVertexAttribArray(1)
    GL.glDisableVertexAttribArray(2)

  def RenderFrameMix(self, frame0, frame1, mix,
                     render_state, mesh_to_world, shadow=False):
    if shadow:
      GL.glUseProgram(self.shaders.animated_mesh_shadow.id)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh_shadow.mesh_to_world,
        1, GL.GL_FALSE, mesh_to_world)
      GL.glUniform1f(self.shaders.animated_mesh_shadow.frame_mix, mix)
    else:
      GL.glUseProgram(self.shaders.animated_mesh.id)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh.mesh_to_world,
        1, GL.GL_FALSE, mesh_to_world)
      GL.glUniform1f(self.shaders.animated_mesh.frame_mix, mix)

    # TODO: figure out why this causes segfaults
    #GL.glBindVertexArray(self.vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.color_vbo)
    GL.glVertexAttribPointer(
      3, 4, GL.GL_UNSIGNED_BYTE, GL.GL_TRUE, 0, None)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    # Positions and normals, stored in blocks per frame:
    ofs = 2 * 4 * self.num_verts + frame0 * self.num_verts * 6 * 4
    GL.glVertexAttribPointer(
      0, 3, GL.GL_FLOAT, GL.GL_FALSE, 6*4,
      ctypes.c_void_p(ofs))
    GL.glVertexAttribPointer(
      1, 3, GL.GL_FLOAT, GL.GL_FALSE, 6*4,
      ctypes.c_void_p(ofs + 3 * 4))
    # Second frame:
    ofs = 2 * 4 * self.num_verts + frame1 * self.num_verts * 6 * 4
    GL.glVertexAttribPointer(
      4, 3, GL.GL_FLOAT, GL.GL_FALSE, 6*4,
      ctypes.c_void_p(ofs))
    GL.glVertexAttribPointer(
      5, 3, GL.GL_FLOAT, GL.GL_FALSE, 6*4,
      ctypes.c_void_p(ofs + 3 * 4))
    # Texcoords, stored at the start of the buffer:
    GL.glVertexAttribPointer(
      2, 2, GL.GL_FLOAT, GL.GL_FALSE, 2*4, None)
    GL.glEnableVertexAttribArray(0)
    GL.glEnableVertexAttribArray(1)
    GL.glEnableVertexAttribArray(2)
    GL.glEnableVertexAttribArray(3)
    GL.glEnableVertexAttribArray(4)
    GL.glEnableVertexAttribArray(5)

    with self.vbo_helper:
      GL.glDrawElements(GL.GL_TRIANGLES, self.num_indices, GL.GL_UNSIGNED_INT, None)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableVertexAttribArray(0)
    GL.glDisableVertexAttribArray(1)
    GL.glDisableVertexAttribArray(2)
    GL.glDisableVertexAttribArray(3)
    GL.glDisableVertexAttribArray(4)
