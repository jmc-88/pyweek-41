import animated_mesh
import matrix
import world_object


class City(world_object.WorldObject):
  def __init__(self, shaders, base_transform):
    self.mesh_shell = animated_mesh.AnimatedMesh('objs/shell.vbo', shaders)
    self.mesh_head = animated_mesh.AnimatedMesh('objs/head.vbo', shaders)
    self.mesh_legs = [animated_mesh.AnimatedMesh(f'objs/leg{i+1}.vbo', shaders) for i in range(4)]
    self.base_transform = base_transform
    self.x = 5.0
    self.y = 0.0
    self.angle = 0
    self.animation_time = 0

  def Update(self):
    self.transform = self.base_transform @ matrix.Rotate(self.angle, 0, 0, 1) @ matrix.Translate(self.x, self.y, 0.5)

  def Render(self, shadow):
    self.mesh_shell.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
    for leg in self.mesh_legs:
      leg.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
    self.mesh_head.Render(frame=0, mesh_to_world=self.transform, shadow=shadow)
