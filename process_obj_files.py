import click
import re
import numpy as np
import os
import sys


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
        c = np.array(c + [255], dtype=np.uint8)
        colors[material_name] = c
      else:
        pass  # Just ignore everything else for now.
  return colors


class ObjFile:
  def __init__(self, path, filter):
    # Raw from the .obj file.
    current_name = ''
    verts = []
    vert_normals = []
    vert_texcoords = []
    faces = []
    face_colors = []
    skipped_v = 0
    skipped_vt = 0
    skipped_vn = 0

    colors = None
    current_color = np.array([255, 255, 255, 255], dtype=np.uint8)

    with open(path, 'rt') as f:
      for line in f:
        line = line.strip()
        if line[0] == '#':
          continue
        cmd, rest = line.split(' ', 1)
        if cmd == 's':
          continue  # Just ignore smoothing groups for now.
        if cmd == 'o':
          current_name = rest
          if filter != '.*' and re.match(filter, current_name):
            print(f'FILTER: including {current_name}.')
          continue
        match = re.match(filter, current_name)
        if cmd == 'mtllib':
          colors = ReadMaterials(rest)
          continue
        if cmd == 'usemtl':
          current_color = colors[rest]
          continue
        if cmd == 'v':
          if match:
            coords = [float(x) for x in rest.split(' ')]
            verts.append(np.array(coords, dtype=np.float32))
          else:
            skipped_v += 1
          continue
        if cmd == 'vn':
          if match:
            coords = [float(x) for x in rest.split(' ')]
            vert_normals.append(np.array(coords, dtype=np.float32))
          else:
            skipped_vn += 1
          continue
        if cmd == 'vt':
          if match:
            coords = [float(x) for x in rest.split(' ')]
            vert_texcoords.append(np.array(coords, dtype=np.float32))
          else:
            skipped_vt += 1
          continue
        if cmd == 'f':
          if not match:
            continue
          corners = rest.split(' ')
          if len(corners) != 3:
            print('Non-triangle face, not implemented.')
            sys.exit(1)
          skipped = skipped_v, skipped_vt, skipped_vn
          faces.append(np.array(
            [[int(x) - 1 - s for x, s in zip(corners[j].split('/'), skipped)] for j in range(3)]))
          face_colors.append(current_color)
          continue
        print('Confused by line %r.' % line)
        sys.exit(1)

    self.verts = np.stack(verts)
    self.vert_normals = np.stack(vert_normals)
    self.vert_texcoords = np.stack(vert_texcoords)
    self.faces = np.stack(faces)
    self.face_colors = np.stack(face_colors)

@click.command()
@click.argument('files', nargs=-1)
@click.option('--filter', default='.*', help='Regex filter for object names.')
@click.option('--output-name', default=None, help='Output file name (default: based on input files).')
def main(files, filter, output_name=None):
  if output_name is None:
    output_name = 'objs/' + os.path.commonprefix([os.path.basename(f) for f in files])
    while output_name[-1].isdigit():
      output_name = output_name[:-1]
    output_name += '.vbo'

  objs = []

  for index, f in enumerate(files):
    o = ObjFile(f, filter)
    objs.append(o)
    print('Frame %3i: %4i verts, %4i faces  (%4i normals, %4i texcoords)'
          % (index, o.verts.shape[0], o.faces.shape[0],
             o.vert_normals.shape[0], o.vert_texcoords.shape[0]))

  ref_faces_without_normals = objs[0].faces[:, :, :2]
  ref_texcoords = objs[0].vert_texcoords
  ref_face_colors = objs[0].face_colors
  for fidx, o in enumerate(objs[1:]):
    fwn = o.faces[:, :, :2]
    if not np.array_equal(ref_faces_without_normals, fwn):
      print('Mismatch of faces-without-normals in frame %i.' % (fidx + 1))
    if not np.array_equal(ref_texcoords, o.vert_texcoords):
      print('Mismatch of texcoords in frame %i.' % (fidx + 1))
    if not np.array_equal(ref_face_colors, o.face_colors):
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
      if cv in vert_colors and np.array_equal(vert_colors[cv], fc):
        combined_face = np.roll(combined_face, 2 - cv_idx)
        assert combined_face[2] == cv
        break
    else:
      for cv_idx, cv in enumerate(combined_face):
        if cv not in vert_colors:
          vert_colors[cv] = fc
          combined_face = np.roll(combined_face, 2 - cv_idx)
          break
      # else:
        # print('Face %i, no free vertex to carry face color.' % fidx)
        # TODO: consider checking colors earlier and creating a new combined vertex of needed to have a vertex that can hold this color
    faces.append(np.array(combined_face))
  print('%i combined vertices' % len(combined_verts))
  print('%i carry a color' % len(vert_colors))

  index_buffer = np.stack(faces).flatten().astype(np.int32)

  color_buffer = np.zeros((len(combined_verts), 4), dtype=np.uint8)
  for idx, color in vert_colors.items():
    color_buffer[idx] = color

  # For each combined vertex:
  # - 2 floats for tex coordinates (constant for all frames)
  # - 3 floats for position, per frame
  # - 3 floats for normal, per frame
  vert_buffer = np.zeros(len(combined_verts) * (2 + 6 * len(objs)), dtype=np.float32)
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
    np.savez_compressed(
      f, allow_pickle=False,
      **{
        'num_frames': np.array([len(objs)], dtype=np.int32),
        'num_verts': np.array([len(combined_verts)], dtype=np.int32),
        'index_buffer': index_buffer,
        'vert_buffer': vert_buffer,
        'color_buffer': color_buffer,
      })

if __name__ == '__main__':
  main()
