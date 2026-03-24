import math
import numpy


def Ortho(left, right, bottom, top, nearval, farval):
  return numpy.array(
    [[2 / (right - left), 0, 0, -(right + left) / (right - left)],
     [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
     [0, 0, -2 / (farval - nearval), -(farval + nearval) / (farval - nearval)],
     [0, 0, 0, 1]], dtype=numpy.float32).T


def Frustum(left, right, bottom, top, nearval, farval):
  return numpy.array(
    [[2 * nearval / (right - left), 0, (right + left) / (right - left), 0],
     [0, 2 * nearval / (top - bottom), (top + bottom) / (top - bottom), 0],
     [0, 0, -(farval + nearval) / (farval - nearval), - 2 * farval * nearval / (farval - nearval)],
     [0, 0, -1, 0]], dtype=numpy.float32).T


def Rotate(angle, x, y, z):
  sa = math.sin(angle / 180 * math.pi)
  ca = math.cos(angle / 180 * math.pi)
  return numpy.array(
    [[x*x*(1-ca)+1*ca, x*y*(1-ca)-z*sa, x*z*(1-ca)+y*sa, 0],
     [x*y*(1-ca)+z*sa, y*y*(1-ca)+1*ca, y*z*(1-ca)-x*sa, 0],
     [x*z*(1-ca)-y*sa, y*z*(1-ca)+x*sa, z*z*(1-ca)+1*ca, 0],
     [0, 0, 0, 1]], dtype=numpy.float32).T


def Translate(x, y, z):
  return numpy.array(
    [[1, 0, 0, x],
     [0, 1, 0, y],
     [0, 0, 1, z],
     [0, 0, 0, 1]], dtype=numpy.float32).T
