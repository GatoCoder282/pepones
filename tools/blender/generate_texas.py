"""Reproducible Texas burger asset build. Run with Blender's bundled Python.

macOS:
  /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
    --python-exit-code 1 --python tools/blender/generate_texas.py -- --mode build
Windows (PowerShell):
  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup `
    --python-exit-code 1 --python tools/blender/generate_texas.py -- --mode build

Geometry and materials are procedural, interpreted from photos/texas_burguer_pepones.jpeg.
Every ingredient is a separate, named object. Base and top bun, both patties and both cheese
slices are independent layers. Hidden faces and physical sizes are artistic decisions.
"""
import argparse
import json
import math
import random
import sys
import zlib
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = 'photos/texas_burguer_pepones.jpeg'
parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['preview', 'build'], default='build')
parser.add_argument('--output', type=Path, default=ROOT / 'material/semanal/texas/modelos')
parser.add_argument('--texture-size', type=int, default=2048)
parser.add_argument('--resolution', type=int, default=1600)
parser.add_argument('--samples', type=int, default=96)
parser.add_argument('--views', default='front,three-quarter,exploded')
parser.add_argument('--only', default='', help='Comma-separated asset ids to bake and export.')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT = args.output.resolve()
for sub in ['', 'textures', 'textures/web', 'renders', 'glb']:
    (OUT / sub).mkdir(parents=True, exist_ok=True)
ONLY = {s for s in args.only.split(',') if s}
TAU = math.tau
UP = Vector((0, 0, 1))

# Web texture size and glTF finish per exported asset. Emission fakes the translucency of
# cheese, sauces and pickles, which glTF viewers cannot scatter.
ASSETS = {
    'pan-base': dict(ingredient='pan-de-papa', web=1024, coat=.06, coat_rough=.35, ao=.16),
    'salsa-original-base': dict(ingredient='salsa-original', web=512, coat=.6, coat_rough=.12, emission=.05),
    'pepinillos': dict(ingredient='pepinillos', web=512, coat=.5, coat_rough=.12, emission=.04),
    'carne': dict(ingredient='carne', web=1024, coat=.16, coat_rough=.32, ao=.06),
}
