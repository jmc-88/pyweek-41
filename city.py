import math

import matrix


class City:
  def __init__(self, mesh, base_transform):
    self.mesh = mesh
    self.base_transform = base_transform
    self.x = 5.0
    self.y = 0.0
    self.angle = 0
    self.animation_time = 0

  def Update(self):
    self.frame_mix, self.frame0 = math.modf(self.animation_time * 30)
    self.frame0 = int(self.frame0) % self.mesh.num_frames
    self.frame1 = (self.frame0 + 1) % self.mesh.num_frames
    self.transform = self.base_transform @ matrix.Rotate(self.angle, 0, 0, 1) @ matrix.Translate(self.x, self.y, 0.5)

  def Render(self, shadow):
    self.mesh.RenderFrameMix(
      self.frame0, self.frame1, self.frame_mix,
      self.transform, shadow=shadow)
