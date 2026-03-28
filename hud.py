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
  def __init__(self, x, y, w, h, fill_color, border_color=np.array([1.0, 1.0, 1.0, 1.0])):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.level = h
    self.fill_color = fill_color
    self.border_color = border_color


class HUD:
  def __init__(self, shaders, world, border_width=3.0):
    self.shaders = shaders
    self.world = world
    self.border_width = border_width

    self.tree_texture = texture.Texture('trees.png')
    self.grain_texture = texture.Texture('grain.png')
    self.madness_texture = texture.Texture('madness.png')

    quad = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float32)
    self.quad_fill_vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_fill_vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, quad.flatten(), GL.GL_STATIC_DRAW)

    quad = np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.float32)
    self.quad_border_vbo = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_border_vbo)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, quad.flatten(), GL.GL_STATIC_DRAW)

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    self.colored_quads = {}
    self.textured_quads = {}

    self.textured_quads['tree_meter_header'] = _TexturedQuad(-0.95, -0.95, 0.2, 0.1, self.tree_texture)
    self.colored_quads['tree_meter'] = _ColoredQuad(-0.9, -0.75, 0.1, 0.5, np.array([0.2, 0.9, 0.2, 0.9]))

    self.textured_quads['grain_meter_header'] = _TexturedQuad(-0.70, -0.95, 0.2, 0.1, self.grain_texture)
    self.colored_quads['grain_meter'] = _ColoredQuad(-0.65, -0.75, 0.1, 0.5, np.array([0.8, 0.8, 0.2, 0.9]))

    self.textured_quads['madness_meter_header'] = _TexturedQuad(-0.45, -0.95, 0.2, 0.1, self.madness_texture)
    self.colored_quads['madness_meter'] = _ColoredQuad(-0.4, -0.75, 0.1, 0.5, np.array([1.0, 0.0, 0.0, 0.9]))

  def Update(self):
    self.colored_quads['tree_meter'].level = self.world.city.trees * 0.5
    self.colored_quads['grain_meter'].level = self.world.city.grain * 0.5
    self.colored_quads['madness_meter'].level = self.world.city.madness_level * 0.5

  def Render(self):
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_BLEND)

    GL.glEnableVertexAttribArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_fill_vbo)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)
    GL.glUseProgram(self.shaders.hud_colored.id)
    for cq in self.colored_quads.values():
      GL.glUniform4f(self.shaders.hud_colored.corners, cq.x, cq.y, cq.w, cq.level)
      GL.glUniform4f(self.shaders.hud_colored.color, *cq.fill_color)
      GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    GL.glEnableVertexAttribArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_border_vbo)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)
    GL.glLineWidth(self.border_width)
    GL.glUseProgram(self.shaders.hud_colored.id)
    for cq in self.colored_quads.values():
      GL.glUniform4f(self.shaders.hud_colored.corners, cq.x, cq.y, cq.w, cq.h)
      GL.glUniform4f(self.shaders.hud_colored.color, *cq.border_color)
      GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 4)

    GL.glEnableVertexAttribArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_fill_vbo)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)
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
