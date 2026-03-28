import math
import matrix
import numpy as np
from OpenGL import GL

import animated_mesh
import config
import world_object


class City(world_object.WorldObject):
  def __init__(self, terrain, shaders, base_transform):
    self.world = None
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
    self.all_upgrades = set(self.mesh_shell_upgrades) | set(self.mesh_head_upgrades)
    self.upgrades = set()
    self.base_transform = base_transform
    self.x = 10.0
    self.y = 0.0
    self.angle = 0
    self.time = 0
    self.animation_time = 0
    self.last_walk_time = -100
    self.last_stop_time = 0
    self.walking = False
    self.was_walking = False
    self.trees = 1.0
    self.grain = 1.0
    self.madness_level = 0.0

  def AddUpgrade(self, name):
    self.upgrades.add(name)

  def walk(self, moving, delta):
    if 'armor' in self.upgrades:
      upgrade = 2
    else:
      upgrade = 1
    target_angle = np.arctan2(moving[1], moving[0]) / math.pi * 180
    if abs(self.angle - target_angle) > abs(self.angle + 360 - target_angle):
      self.angle += 360
    elif abs(self.angle - target_angle) > abs(self.angle - 360 - target_angle):
      self.angle -= 360
    if self.angle < target_angle:
      self.angle += delta * 90 * upgrade
      if self.angle > target_angle:
        self.angle = target_angle
    else:
      self.angle -= delta * 90 * upgrade
      if self.angle < target_angle:
        self.angle = target_angle

    if self.trees > 0.3:
      hunger_slowdown = 1.0
    else:
      hunger_slowdown = (self.trees * 4) * 0.85 + 0.15
    cur_mountain = self.world.terrain.IsMountain(self.x, self.y, 0.8)
    check_step = 1.5 * config.TerrainWidth / config.TerrainResolutionX
    next_mountain = self.world.terrain.IsMountain(self.x + moving[0] * check_step, self.y + moving[1] * check_step, 0.8)

    moving = moving * 1.4 * hunger_slowdown * delta * upgrade
    if next_mountain > cur_mountain:
      # Slow down a lot if the player tries to move up a mountain.
      # 0.0 at 0.2, 0.9 at 0.4
      moving *= max(min(1 - (cur_mountain - 0.2) / 0.1, 0.9), 0)
    self.x += moving[0]
    self.y += moving[1]
    self.walking = True
    self.animation_time += delta * hunger_slowdown

  def Update(self, delta, height):
    self.grain = max(self.grain - delta * 0.025, 0)
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
    self.transform = self.base_transform @ matrix.Rotate(self.angle, 0, 0, 1) @ matrix.Translate(self.x, self.y, 0.25 + height)

    near_night = max(0, min(1, 1 - (self.x - self.world.night_progress) / 5))
    if near_night > 0:
      self.madness_level += 0.1 * near_night * delta
    else:
      self.madness_level -= 0.1 * delta
    self.madness_level = float(max(0, min(1, self.madness_level)))
    # TODO: increase madness level when we are in the dark
    # Slowly decrease madness level while staying in the light?

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
