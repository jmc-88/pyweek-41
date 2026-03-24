import numpy
import OpenGL
from OpenGL import GL
from OpenGL.arrays import vbo


class AnimatedMesh:
  def __init__(self, path, shaders):
    self.shaders = shaders
    with open(path, 'rb') as f:
      self.frame_index_start = numpy.load(f)
      indices = numpy.load(f)
      verts = numpy.load(f)

    self.vbo, self.index_vbo = GL.glGenBuffers(2)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, verts, GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    self.vbo_helper = vbo.VBO(indices, usage='GL_STATIC_DRAW', target='GL_ELEMENT_ARRAY_BUFFER')
    #self.vao = GL.glGenVertexArrays(1)

  @property
  def num_frames(self):
    return len(self.frame_index_start) - 1

  def Render(self, frame, render_state, mesh_to_world,
             shadow=False):
    i0 = self.frame_index_start[frame]
    i1 = self.frame_index_start[frame + 1]

    if shadow:
      GL.glUseProgram(self.shaders.animated_mesh_shadow.id)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh_shadow.mesh_to_world,
        1, GL.GL_FALSE, mesh_to_world)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh_shadow.world_to_view,
        1, GL.GL_FALSE, render_state.shadow_transform_matrix)
    else:
      GL.glUseProgram(self.shaders.animated_mesh.id)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh.mesh_to_world,
        1, GL.GL_FALSE, mesh_to_world)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh.world_to_view,
        1, GL.GL_FALSE, render_state.transform_matrix)
      GL.glUniformMatrix4fv(
        self.shaders.animated_mesh.world_to_shadow,
        1, GL.GL_FALSE, render_state.shadow_transform_matrix)

    #GL.glBindVertexArray(self.vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)

    GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 8*4, None)
    GL.glEnableVertexAttribArray(0)

    with self.vbo_helper:
      GL.glDrawElements(GL.GL_TRIANGLES, i1 - i0, GL.GL_UNSIGNED_INT, self.vbo_helper + int(i0 * 4))
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableVertexAttribArray(0)
