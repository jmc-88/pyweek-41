import numpy as np
from OpenGL import GL

import texture


class _TexturedQuad:
  def __init__(self, x, y, w, h, tex):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.tex = tex


class _ColoredQuad:
  def __init__(self, x, y, w, h, color):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.color = color


class HUD:
  def __init__(self, shaders, world):
    self.shaders = shaders
    self.world = world

    self.placeholder = texture.Texture('placeholder.png')

    quad = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float32)
    self.quad_vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, quad.flatten(), GL.GL_STATIC_DRAW)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    self.colored_quads = {}
    self.textured_quads = {}

    self.textured_quads['tree_meter_header'] = _TexturedQuad(-0.95, -0.95, 0.2, 0.1, self.placeholder)
    self.colored_quads['tree_meter'] = _ColoredQuad(-0.9, -0.75, 0.1, 0.5, np.array([0.2, 0.9, 0.2, 0.8]))

  def Update(self):
    self.colored_quads['tree_meter'].h = self.world.city.trees * 0.5

  def Render(self):
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_BLEND)
    GL.glEnableVertexAttribArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_vbo)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)

    GL.glUseProgram(self.shaders.hud_colored.id)
    for cq in self.colored_quads.values():
      GL.glUniform4f(self.shaders.hud_colored.corners, cq.x, cq.y, cq.w, cq.h)
      GL.glUniform4f(self.shaders.hud_colored.color, *cq.color)
      GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    GL.glUseProgram(self.shaders.hud_textured.id)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glUniform1i(self.shaders.hud_textured.tex, 0)
    for tq in self.textured_quads.values():
      GL.glBindTexture(GL.GL_TEXTURE_2D, tq.tex.id)
      GL.glUniform4f(self.shaders.hud_textured.corners, tq.x, tq.y, tq.w, tq.h)
      GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glDisableVertexAttribArray(0)
    GL.glUseProgram(0)
    GL.glDisable(GL.GL_BLEND)
