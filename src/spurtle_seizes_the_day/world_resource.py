from . import world_object


class WorldResource(world_object.WorldObject):
  def __init__(self, center):
    self.center = center

  def Harvest(self, amount):
    raise NotImplementedError()
