import OpenGL
from OpenGL import GL
from OpenGL.GL import shaders


class Shaders:
  def __init__(self):
    self.terrain_program = shaders.compileProgram(
        shaders.compileShader(
            open('terrain.vert', 'rt').read(), GL.GL_VERTEX_SHADER),
        shaders.compileShader(
            open('terrain.frag', 'rt').read(), GL.GL_FRAGMENT_SHADER))
