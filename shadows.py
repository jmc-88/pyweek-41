import OpenGL
from OpenGL import GL

import config


class ShadowMap:
  def __init__(self):
    self.fbo = GL.glGenFramebuffers(1)
    self.tex = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT,
                    config.ShadowMapRes, config.ShadowMapRes,
                    0, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, None)
    GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER)
    GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_BORDER_COLOR, [1, 1, 1, 1])

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
    GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT,
                              GL.GL_TEXTURE_2D, self.tex, 0)
    GL.glDrawBuffer(GL.GL_NONE)
    GL.glReadBuffer(GL.GL_NONE)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
