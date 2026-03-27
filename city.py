import animated_mesh
import math
import matrix
import world_object
from OpenGL import GL


class City(world_object.WorldObject):
  def __init__(self, terrain, shaders, base_transform):
    self.terrain = terrain
    self.shaders = shaders
    self.mesh_shell = animated_mesh.AnimatedMesh('objs/shell.vbo', shaders)
    self.mesh_head = animated_mesh.AnimatedMesh('objs/head.vbo', shaders)
    self.mesh_legs = [animated_mesh.AnimatedMesh(f'objs/leg{i+1}.vbo', shaders) for i in range(4)]
    self.base_transform = base_transform
    self.x = 5.0
    self.y = 0.0
    self.angle = 0
    self.time = 0
    self.animation_time = 0
    self.last_walk_time = -100
    self.last_stop_time = 0
    self.walking = False
    self.was_walking = False

  def walk(self, dx, dy, delta):
    self.x += dx * delta
    self.y += dy * delta
    self.walking = True
    self.animation_time += delta

  def Update(self, delta):
    if self.walking:
      self.last_walk_time = self.time
    else:
      self.last_stop_time = self.time
    self.was_walking = self.walking
    self.walking = False
    self.time += delta
    self.transform = self.base_transform @ matrix.Rotate(self.angle, 0, 0, 1) @ matrix.Translate(self.x, self.y, 0)

  def Render(self, shadow):
    self.mesh_shell.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
    self.mesh_head.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
    shader = self.shaders.leg_mesh_shadow if shadow else self.shaders.leg_mesh
    GL.glUseProgram(shader.id)
    time_since_stopped = self.time - self.last_stop_time
    time_since_walked = self.time - self.last_walk_time
    ground = 0 # self.terrain.GetHeight(self.x, self.y)
    for i, leg in enumerate(self.mesh_legs):
      lift = math.sin(self.animation_time * 10 + i * math.pi * 0.5)*0.2
      if self.was_walking:
        lift *= min(1, time_since_stopped * 10)
      else:
        lift *= max(0, 1 - time_since_walked * 10)
      GL.glUniform1f(shader.height, ground + lift)
      leg.Render(frame=0, mesh_to_world=self.transform, shader=shader)
