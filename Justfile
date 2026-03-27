process_city:
  uv run python process_obj_files.py city.obj --filter='Leg1' --output-name=objs/leg1.vbo
  uv run python process_obj_files.py city.obj --filter='Leg2' --output-name=objs/leg2.vbo
  uv run python process_obj_files.py city.obj --filter='Leg3' --output-name=objs/leg3.vbo
  uv run python process_obj_files.py city.obj --filter='Leg4' --output-name=objs/leg4.vbo
  uv run python process_obj_files.py city.obj --filter='Neck|Eye|Hat|Nose' --output-name=objs/head.vbo
  uv run python process_obj_files.py city.obj --filter='Shell|Cube' --output-name=objs/shell.vbo
  # Upgrades
  uv run python process_obj_files.py city.obj --filter='Armor' --output-name=objs/armor.vbo
  uv run python process_obj_files.py city.obj --filter='Cylinder' --output-name=objs/cannons.vbo
  uv run python process_obj_files.py city.obj --filter='Crane|Hook' --output-name=objs/cranes.vbo
  uv run python process_obj_files.py city.obj --filter='Pipe' --output-name=objs/pipe.vbo
  uv run python process_obj_files.py city.obj --filter='Radar' --output-name=objs/radar.vbo
  uv run python process_obj_files.py city.obj --filter='Ruby' --output-name=objs/turret.vbo
