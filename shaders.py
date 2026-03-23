import OpenGL
from OpenGL import GL
from OpenGL.GL import shaders

import config


class Shaders:
  def _MakeDefines(self):
    defines = []
    for key, value in sorted(config.__dict__.items()):
      if key[0] == '_':
        continue
      defines.append('#define %s %r' % (key, value))
    return '\n'.join(defines)

  def _AddDefines(self, shader_src):
    lines = shader_src.split('\n')
    for idx in range(len(lines)):
      if not lines[idx] or lines[idx][0] != '#':
        break
    lines.insert(idx, self.defines)
    return '\n'.join(lines)

  def __init__(self):
    self.defines = self._MakeDefines()

    self.terrain_program = shaders.compileProgram(
        shaders.compileShader(
            self._AddDefines(open('terrain.vert', 'rt').read()),
            GL.GL_VERTEX_SHADER),
        shaders.compileShader(
            self._AddDefines(open('terrain.frag', 'rt').read()),
            GL.GL_FRAGMENT_SHADER))
