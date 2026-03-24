import OpenGL
from OpenGL import GL
from OpenGL.GL import shaders
import re

import config


class _ProgramHolder:
  pass


_UniformRe = re.compile('uniform [^;]+ ([A-Za-z0-9_]+);')

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

  def _GetUniforms(self, shader_src):
    u = set()
    for m in _UniformRe.finditer(shader_src):
      u.add(m.group(1))
    return u

  def _PrepShader(self, vert_path, frag_path):
    vert_src = self._AddDefines(open(vert_path, 'rt').read())
    frag_src = self._AddDefines(open(frag_path, 'rt').read())
    uniforms = set(self._GetUniforms(vert_src))
    uniforms.update(self._GetUniforms(frag_src))
    program = _ProgramHolder()
    program.id = shaders.compileProgram(
        shaders.compileShader(vert_src, GL.GL_VERTEX_SHADER),
        shaders.compileShader(frag_src, GL.GL_FRAGMENT_SHADER))
    for u in uniforms:
      setattr(program, u, GL.glGetUniformLocation(program.id, u))
    return program

  def __init__(self):
    self.defines = self._MakeDefines()
    self.terrain = self._PrepShader('terrain.vert', 'terrain.frag')
    self.terrain_shadow = self._PrepShader('terrain.vert', 'shadow_map.frag')

    self.animated_mesh = self._PrepShader('animated_mesh.vert', 'animated_mesh.frag')
    self.animated_mesh_shadow = self._PrepShader('animated_mesh.vert', 'shadow_map.frag')
