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

  def _Preprocess(self, shader_src):
    lines = shader_src.split('\n')
    for idx in range(len(lines)):
      if not lines[idx] or not lines[idx].startswith('#version'):
        break
    lines.insert(idx, self.defines)
    idx += 1
    while idx < len(lines):
      if lines[idx] == '#include light':
        lines[idx] = self.common_light_src
      idx += 1
    return '\n'.join(lines)

  def _GetUniforms(self, shader_src):
    u = set()
    for m in _UniformRe.finditer(shader_src):
      u.add(m.group(1))
    return u

  def _PrepShader(self, vert_path, frag_path):
    vert_src = self._Preprocess(open(vert_path, 'rt').read())
    frag_src = self._Preprocess(open(frag_path, 'rt').read())
    uniforms = set(self._GetUniforms(vert_src))
    uniforms.update(self._GetUniforms(frag_src))
    program = _ProgramHolder()
    program.id = shaders.compileProgram(
        shaders.compileShader(vert_src, GL.GL_VERTEX_SHADER),
        shaders.compileShader(frag_src, GL.GL_FRAGMENT_SHADER))
    for u in uniforms:
      setattr(program, u, GL.glGetUniformLocation(program.id, u))
    self.all_programs.append(program)
    return program

  def SetUniformInAllShaders(self, name, value):
    for p in self.all_programs:
      if not hasattr(p, name):
        continue
      loc = getattr(p, name)
      if isinstance(value, int):
        GL.glProgramUniform1i(p.id, loc, value)
      elif value.shape == (3, ):
        GL.glProgramUniform3f(p.id, loc, *value)
      elif value.shape == (4, 4):
        GL.glProgramUniformMatrix4fv(p.id, loc, 1, GL.GL_FALSE, value)
      else:
        assert False, ('Unimplemented uniform type: %r' % value)

  def __init__(self):
    self.all_programs = []

    with open('light.frag', 'rt') as f:
      self.common_light_src = f.read()

    self.defines = self._MakeDefines()
    self.terrain = self._PrepShader('terrain.vert', 'terrain.frag')
    self.terrain_shadow = self._PrepShader('terrain.vert', 'shadow_map.frag')

    self.animated_mesh = self._PrepShader('animated_mesh.vert', 'mesh.frag')
    self.animated_mesh_shadow = self._PrepShader('animated_mesh.vert', 'shadow_map.frag')

    self.leg_mesh = self._PrepShader('legs.vert', 'mesh.frag')
    self.leg_mesh_shadow = self._PrepShader('legs.vert', 'shadow_map.frag')

    self.mesh = self._PrepShader('mesh.vert', 'mesh.frag')
    self.mesh_shadow = self._PrepShader('mesh.vert', 'shadow_map.frag')

    self.mesh_instanced = self._PrepShader('mesh_instanced.vert', 'mesh.frag')
    self.mesh_instanced_shadow = self._PrepShader('mesh_instanced.vert', 'shadow_map.frag')
