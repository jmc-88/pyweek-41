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
    self.mesh_shell_upgrades = {
      name: animated_mesh.AnimatedMesh(f'objs/{name}.vbo', shaders)
      for name in ['cannons', 'armor', 'cranes', 'pipe', 'turret']}
    self.mesh_head_upgrades = {
      name: animated_mesh.AnimatedMesh(f'objs/{name}.vbo', shaders)
      for name in ['radar']}
    self.upgrades = set()
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
    self.trees = 1.0

  def walk(self, dx, dy, delta):
    self.x += dx * delta
    self.y += dy * delta
    self.walking = True
    self.animation_time += delta

  def Update(self, delta):
    if self.walking:
      self.last_walk_time = self.time
      self.trees -= delta * 0.05
    else:
      self.last_stop_time = self.time
      self.trees -= delta * 0.01
    self.trees = max(self.trees, 0)
    self.was_walking = self.walking
    self.walking = False
    self.time += delta
    self.transform = self.base_transform @ matrix.Rotate(self.angle, 0, 0, 1) @ matrix.Translate(self.x, self.y, 1)

  def Render(self, shadow):
    self.mesh_shell.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
    for name, mesh in self.mesh_shell_upgrades.items():
      if name in self.upgrades:
        mesh.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
    shader = self.shaders.leg_mesh_shadow if shadow else self.shaders.leg_mesh
    GL.glUseProgram(shader.id)
    GL.glUniform1f(shader.left, 0)
    time_since_stopped = self.time - self.last_stop_time
    time_since_walked = self.time - self.last_walk_time
    ground = 0 # self.terrain.GetHeight(self.x, self.y)
    if self.was_walking:
      walk_factor = min(1, time_since_stopped * 10)
    else:
      walk_factor = max(0, 1 - time_since_walked * 10)
    # Legs stepping.
    for i, leg in enumerate(self.mesh_legs):
      lift = 0.4 * math.sin(self.animation_time * 10 + i * math.pi * 0.5) * walk_factor
      GL.glUniform1f(shader.up, -ground - lift)
      leg.Render(frame=0, mesh_to_world=self.transform, shader=shader)
    # Head bopping.
    GL.glUniform1f(shader.up, -0.2*math.sin(self.animation_time * 10) * walk_factor * 0.5)
    GL.glUniform1f(shader.left, math.sin(self.animation_time * 5) * walk_factor * 0.5)
    self.mesh_head.Render(frame=0, mesh_to_world=self.transform, shader=shader)
    for name, mesh in self.mesh_head_upgrades.items():
      if name in self.upgrades:
        mesh.Render(frame=0, mesh_to_world=self.transform, shader=shader)
