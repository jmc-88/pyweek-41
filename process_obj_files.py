import numpy
import os
import sys

files = sys.argv[1:]

output_name = os.path.commonprefix([os.path.basename(f) for f in files]) + '.vbo'


class ObjFile:
  def __init__(self, path):
    # Raw from the .obj file.
    verts = []
    vert_normals = []
    vert_texcoords = []

    # Map tuple of indices (v, vn, vt) to the 'opengl' VBO index.
    obj_index_to_gl_index = {}
    self.vert_buffer = []

    def _MapToGLIndex(v, vn, vt):
      k = (v, vn, vt)
      if k not in obj_index_to_gl_index:
        obj_index_to_gl_index[k] = len(self.vert_buffer)
        self.vert_buffer.append(numpy.concat([
          verts[v], vert_normals[vn], vert_texcoords[vt]]))
      return obj_index_to_gl_index[k]

    self.index_buffer = []

    with open(path, 'rt') as f:
      for line in f:
        line = line.strip()
        if line[0] == '#':
          continue
        cmd, rest = line.split(' ', 1)
        if cmd in ('o', 's', 'usemtl', 'mtllib'):
          # TODO and/or ignore
          continue
        if cmd == 'v':
          coords = [float(x) for x in rest.split(' ')]
          verts.append(numpy.array(coords, dtype=numpy.float32))
          continue
        if cmd == 'vn':
          coords = [float(x) for x in rest.split(' ')]
          vert_normals.append(numpy.array(coords, dtype=numpy.float32))
          continue
        if cmd == 'vt':
          coords = [float(x) for x in rest.split(' ')]
          vert_texcoords.append(numpy.array(coords, dtype=numpy.float32))
          continue
        if cmd == 'f':
          corners = rest.split(' ')
          if len(corners) != 3:
            print('Non-triangle face, not implemented.')
            sys.exit(1)
          for f in corners:
            v, vt, vn = [int(x) - 1 for x in f.split('/')]
            self.index_buffer.append(_MapToGLIndex(v, vn, vt))
          continue
        print('Confused by line %r.' % line)
        sys.exit(1)

    self.vert_buffer = numpy.stack(self.vert_buffer)
    self.index_buffer = numpy.array(self.index_buffer, dtype=numpy.int32)

objs = []
total_indices = 0
total_verts = 0

frame_index_start = []
start_index = 0
start_vert = 0

all_indices = []
all_verts = []
for index, f in enumerate(files):
  o = ObjFile(f)
  objs.append(o)
  frame_index_start.append(start_index)
  all_indices.append(o.index_buffer + start_vert)
  all_verts.append(o.vert_buffer.reshape(-1))
  start_vert += o.vert_buffer.shape[0]
  start_index += o.index_buffer.shape[0]
  print('frame %3i: %4i indices, %4i verts'
        % (index, o.index_buffer.shape[0], o.vert_buffer.shape[0]))
frame_index_start.append(start_index)
print('%i total indices, %i total verts' % (start_index, start_vert))

frame_index_start = numpy.array(frame_index_start, dtype=numpy.int32)
all_indices = numpy.concat(all_indices)
all_verts = numpy.concat(all_verts)

assert frame_index_start.dtype == numpy.int32
assert all_indices.dtype == numpy.int32
assert all_verts.dtype == numpy.float32

print('Saving to %r.' % output_name)
with open(output_name, 'wb') as f:
  numpy.save(f, frame_index_start, allow_pickle=False)
  numpy.save(f, all_indices, allow_pickle=False)
  numpy.save(f, all_verts, allow_pickle=False)
