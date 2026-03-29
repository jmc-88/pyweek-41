process_city:
  uv run python tools/process_obj_files.py data/city.obj --filter='Leg1' --output-name=data/objs/leg1.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Leg2' --output-name=data/objs/leg2.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Leg3' --output-name=data/objs/leg3.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Leg4' --output-name=data/objs/leg4.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Neck|Eye|Hat|Nose' --output-name=data/objs/head.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Shell|Cube' --output-name=data/objs/shell.vbo
  # Upgrades
  uv run python tools/process_obj_files.py data/city.obj --filter='Armor' --output-name=data/objs/armor.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Cylinder' --output-name=data/objs/cannons.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Crane|Hook' --output-name=data/objs/cranes.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Pipe' --output-name=data/objs/pipe.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Radar' --output-name=data/objs/radar.vbo
  uv run python tools/process_obj_files.py data/city.obj --filter='Ruby' --output-name=data/objs/turret.vbo

build_mac:
  uv run nuitka --standalone \
    --include-data-dir=data=data \
    --macos-create-app-bundle \
    --output-filename=Spurtle main.py
  mv main.app Spurtle.app

build_linux:
  uv run nuitka \
    --mode=app \
    --include-data-dir=data=data \
    --output-filename=Spurtle.bin \
    --remove-output \
    main.py

build_win:
  uv run nuitka \
    --mode=app \
    --include-data-dir=data=data \
    --output-filename=Spurtle \
    --remove-output \
    --windows-disable-console \
    main.py
