import numpy
import os
import sys

files = sys.argv[1:]

output_name = os.path.commonprefix([os.path.basename(f) for f in files])
while output_name[-1].isdigit():
  output_name = output_name[:-1]
output_name += '.vbo'


def ReadMaterials(path):
  material_name = None
  colors = {}
  with open(path, 'rt') as f:
    for line in f:
      line = line.strip()
      if not line or line[0] == '#':
        continue
      cmd, rest = line.split(' ', 1)
      if cmd == 'newmtl':
        material_name = rest
      elif cmd == 'Kd':
        c = [float(x) * 255 for x in rest.split(' ')]
        c = numpy.array(c + [255], dtype=numpy.uint8)
        colors[material_name] = c
      else:
        pass  # Just ignore everything else for now.
  return colors


class ObjFile:
  def __init__(self, path):
    # Raw from the .obj file.
    verts = []
    vert_normals = []
    vert_texcoords = []
    faces = []
    face_colors = []

    colors = None
    current_color = numpy.array([255, 255, 255, 255], dtype=numpy.uint8)

    with open(path, 'rt') as f:
      for line in f:
        line = line.strip()
        if line[0] == '#':
          continue
        cmd, rest = line.split(' ', 1)
        if cmd in ('o', 's'):
          # TODO and/or ignore
          continue
        if cmd == 'mtllib':
          colors = ReadMaterials(rest)
          continue
        if cmd == 'usemtl':
          current_color = colors[rest]
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
          faces.append(numpy.array(
            [[int(x) - 1 for x in corners[i].split('/')] for i in range(3)]))
          face_colors.append(current_color)
          continue
        print('Confused by line %r.' % line)
        sys.exit(1)

    self.verts = numpy.stack(verts)
    self.vert_normals = numpy.stack(vert_normals)
    self.vert_texcoords = numpy.stack(vert_texcoords)
    self.faces = numpy.stack(faces)
    self.face_colors = numpy.stack(face_colors)


objs = []

for index, f in enumerate(files):
  o = ObjFile(f)
  objs.append(o)
  print('Frame %3i: %4i verts, %4i faces'
        % (index, o.verts.shape[0], o.faces.shape[0]))

ref_faces_without_normals = objs[0].faces[:, :, :2]
ref_texcoords = objs[0].vert_texcoords
ref_face_colors = objs[0].face_colors
for fidx, o in enumerate(objs[1:]):
  fwn = o.faces[:, :, :2]
  if not numpy.array_equal(ref_faces_without_normals, fwn):
    print('Mismatch of faces-without-normals in frame %i.' % (fidx + 1))
  if not numpy.array_equal(ref_texcoords, o.vert_texcoords):
    print('Mismatch of texcoords in frame %i.' % (fidx + 1))
  if not numpy.array_equal(ref_face_colors, o.face_colors):
    print('Mismatch of face colors in frame %i.' % (fidx + 1))


combined_verts = []
combined_vert_map = {}

faces = []
vert_colors = {}
for fidx, face in enumerate(ref_faces_without_normals):
  combined_face = []
  for vidx, vert in enumerate(face):
    all_normals = tuple(o.faces[fidx, vidx, 2] for o in objs)
    key = (vert[0], vert[1], all_normals)
    if key not in combined_vert_map:
      combined_vert_map[key] = len(combined_verts)
      combined_verts.append(key)
    combined_face.append(combined_vert_map[key])
  fc = ref_face_colors[fidx]
  for cv_idx, cv in enumerate(combined_face):
    if cv in vert_colors and numpy.array_equal(vert_colors[cv], fc):
      combined_face = numpy.roll(combined_face, 2 - cv_idx)
      assert combined_face[2] == cv
      break
  else:
    for cv_idx, cv in enumerate(combined_face):
      if cv not in vert_colors:
        vert_colors[cv] = fc
        combined_face = numpy.roll(combined_face, 2 - cv_idx)
        break
    else:
      print('Face %i, no free vertex to carry face color.' % fidx)
      # TODO: consider checking colors earlier and creating a new combined vertex of needed to have a vertex that can hold this color
  faces.append(numpy.array(combined_face))
print('%i combined vertices' % len(combined_verts))
print('%i carry a color' % len(vert_colors))

index_buffer = numpy.stack(faces).flatten().astype(numpy.int32)

color_buffer = numpy.zeros((len(combined_verts), 4), dtype=numpy.uint8)
for idx, color in vert_colors.items():
  color_buffer[idx] = color

# For each combined vertex:
# - 2 floats for tex coordinates (constant for all frames)
# - 3 floats for position, per frame
# - 3 floats for normal, per frame
vert_buffer = numpy.zeros(len(combined_verts) * (2 + 6 * len(objs)), dtype=numpy.float32)
tc_size = len(combined_verts) * 2
frame_size = len(combined_verts) * 6
for cv_idx, (v_idx, vt_idx, vn_indices) in enumerate(combined_verts):
  vert_buffer[cv_idx * 2 + 0] = ref_texcoords[vt_idx][0]
  vert_buffer[cv_idx * 2 + 1] = ref_texcoords[vt_idx][1]
  for o_idx, o in enumerate(objs):
    vert_buffer[tc_size + frame_size * o_idx + 6 * cv_idx + 0:
                tc_size + frame_size * o_idx + 6 * cv_idx + 3] = o.verts[v_idx]
    vert_buffer[tc_size + frame_size * o_idx + 6 * cv_idx + 3:
                tc_size + frame_size * o_idx + 6 * cv_idx + 6] = o.vert_normals[vn_indices[o_idx]]

print('Saving to %r.' % output_name)
with open(output_name, 'wb') as f:
  numpy.save(f, numpy.array([len(objs)], dtype=numpy.int32), allow_pickle=False)
  numpy.save(f, numpy.array([len(combined_verts)], dtype=numpy.int32), allow_pickle=False)
  numpy.save(f, index_buffer, allow_pickle=False)
  numpy.save(f, vert_buffer, allow_pickle=False)
  numpy.save(f, color_buffer, allow_pickle=False)
