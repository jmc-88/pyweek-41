Fullscreen = False
# Warning: Some code kinda assumes that the the world coordinate
# resolution is the same in both dimensions (i.e. TerrainWidth /
# TerrainResolutionX == TerrainHeight / TerrainResolutionY), wonky
# things might happen if this isn't true.
TerrainResolutionX = 64
TerrainResolutionY = 64 * 4
TerrainWidth = 4.0  # Width of one terrain chunk in world coordinates.
TerrainHeight = 16.0  # Height of one terrain chunk in world coordinates.

ShadowMapRes = 2048
ShadowBias = 0.005
PrimitiveRestartIndex = 2000000000  # Arbitrary number higher than any vertex index we plan to use.
