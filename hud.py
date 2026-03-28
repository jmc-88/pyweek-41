import numpy as np
from OpenGL import GL
import random

import texture


class _TexturedQuad:
  def __init__(self, x, y, w, h, tex):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.tex = tex


class _ColoredQuad:
  def __init__(self, x, y, w, h, fill_color, pulsating_color, border_color=np.array([1.0, 1.0, 1.0, 1.0]), hasReachedCriticality=None):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.level = h
    self.fill_color = fill_color
    self.pulsating_color = pulsating_color
    self.border_color = border_color
    assert hasReachedCriticality is not None
    self.hasReachedCriticality = hasReachedCriticality

  @property
  def pulsating(self):
    value = self.level / self.h
    return self.hasReachedCriticality(value)


class HUD:
  def __init__(self, shaders, world, play_sound, border_width=1.0):
    self.shaders = shaders
    self.world = world
    self.play_sound = play_sound
    self.border_width = border_width

    self.tree_texture = texture.Texture('trees.png')
    self.grain_texture = texture.Texture('grain.png')
    self.madness_texture = texture.Texture('madness.png')
    self.space_to_gather = texture.Texture('space_to_gather.png')

    self.upgrades = ['cannons', 'armor', 'cranes', 'pipe', 'turret', 'radar']
    self.upgrade_textures = {name: texture.Texture('upgrades/%s.png' % name)
                             for name in self.upgrades}
    self.buy_upgrade_texture = texture.Texture('upgrades/buy.png')
    self.buy_cancel_texture = texture.Texture('upgrades/cancel.png')
    self.upgrade_list_open = False

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

    self.textured_quads['space_to_gather'] = _TexturedQuad(-0.3, -0.95, 0.5, 0.2, self.space_to_gather)

    self.textured_quads['tree_meter_header'] = _TexturedQuad(-0.98, -0.95, 0.2, 0.1, self.tree_texture)
    self.colored_quads['tree_meter'] = _ColoredQuad(-0.93, -0.75, 0.1, 0.5, np.array([0.2, 0.9, 0.2, 0.9]), np.array([1.0, 0.0, 0.0, 0.9]), hasReachedCriticality=lambda value: value <= 0.4)

    self.textured_quads['grain_meter_header'] = _TexturedQuad(-0.80, -0.95, 0.2, 0.1, self.grain_texture)
    self.colored_quads['grain_meter'] = _ColoredQuad(-0.75, -0.75, 0.1, 0.5, np.array([0.8, 0.8, 0.2, 0.9]), np.array([1.0, 0.0, 0.0, 0.9]), hasReachedCriticality=lambda value: value <= 0.4)

    self.textured_quads['madness_meter_header'] = _TexturedQuad(-0.62, -0.95, 0.2, 0.1, self.madness_texture)
    self.colored_quads['madness_meter'] = _ColoredQuad(-0.57, -0.75, 0.1, 0.5, np.array([1.0, 0.0, 0.0, 0.9]), np.array([1.0, 0.0, 0.0, 0.9]), hasReachedCriticality=lambda value: value >= 0.6)
    self._UpdateUpgradeButtons()

  def _UpdateUpgradeButtons(self):
    remove = []
    for name in self.textured_quads:
      if name.startswith('upgrade_'):
        remove.append(name)
    for name in remove:
      del self.textured_quads[name]

    if self.upgrade_list_open:
      self.textured_quads['buy_upgrade'] = _TexturedQuad(0.5, -0.95, 0.45, 0.2, self.buy_cancel_texture)
      available_upgrades = self.world.city.all_upgrades - self.world.city.upgrades
      available_upgrades = sorted(available_upgrades)
      y = -0.95 + 0.25
      for u in available_upgrades:
        self.textured_quads['upgrade_%s' % u] = _TexturedQuad(0.5, y, 0.45, 0.2, self.upgrade_textures[u])
        y += 0.22
    else:
      if 'upgrade_buy_mask' in self.colored_quads:
        del self.colored_quads['upgrade_buy_mask']
      self.textured_quads['buy_upgrade'] = _TexturedQuad(0.5, -0.95, 0.45, 0.2, self.buy_upgrade_texture)

  def Click(self, x, y):
    if self.upgrade_list_open:
      for name, tq in self.textured_quads.items():
        if x > tq.x and y > tq.y and x - tq.x < tq.w and y - tq.y < tq.h:
          if not name.startswith('upgrade_'):
            break
          upgrade_name = name[len('upgrade_'):]
          self.play_sound('cute', count=3)
          self.world.city.AddUpgrade(upgrade_name)
          break
      self.upgrade_list_open = False
      self._UpdateUpgradeButtons()
    else:
      tq = self.textured_quads['buy_upgrade']
      if x > tq.x and y > tq.y and x - tq.x < tq.w and y - tq.y < tq.h:
        self.upgrade_list_open = True
        self._UpdateUpgradeButtons()

  def Update(self):
    self.colored_quads['tree_meter'].level = self.world.city.trees * 0.5
    self.colored_quads['grain_meter'].level = self.world.city.grain * 0.5
    self.colored_quads['madness_meter'].level = self.world.city.madness_level * 0.5

  def Render(self):
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_BLEND)
    GL.glDisable(GL.GL_DEPTH_TEST)

    GL.glEnableVertexAttribArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_fill_vbo)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)
    GL.glUseProgram(self.shaders.hud_colored.id)
    for cq in self.colored_quads.values():
      GL.glUniform4f(self.shaders.hud_colored.corners, cq.x, cq.y, cq.w, cq.level)
      GL.glUniform4f(self.shaders.hud_colored.color, *cq.fill_color)
      GL.glUniform4f(self.shaders.hud_colored.pulsatingColor, *cq.pulsating_color)
      GL.glUniform1i(self.shaders.hud_colored.isPulsating, cq.pulsating)
      GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    GL.glEnableVertexAttribArray(0)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_border_vbo)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)
    GL.glLineWidth(self.border_width)
    GL.glUseProgram(self.shaders.hud_colored.id)
    for cq in self.colored_quads.values():
      GL.glUniform4f(self.shaders.hud_colored.corners, cq.x, cq.y, cq.w, cq.h)
      GL.glUniform4f(self.shaders.hud_colored.color, *cq.border_color)
      GL.glUniform4f(self.shaders.hud_colored.pulsatingColor, *cq.pulsating_color)
      GL.glUniform1i(self.shaders.hud_colored.isPulsating, False)
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
    GL.glEnable(GL.GL_DEPTH_TEST)
