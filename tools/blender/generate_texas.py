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
    'queso-americano': dict(ingredient='queso-americano', web=512, coat=.4, coat_rough=.14, emission=.07),
    'tocino': dict(ingredient='tocino', web=768, coat=.14, coat_rough=.25, emission=.015, ao=.06),
    'salsa-barbacoa': dict(ingredient='salsa-barbacoa', web=512, coat=1., coat_rough=.05, emission=.02),
    'cebolla-crispy': dict(ingredient='cebolla-crispy', web=768, coat=.1, coat_rough=.35, ao=.04),
    'salsa-original-tapa': dict(ingredient='salsa-original', web=512, coat=.6, coat_rough=.12, emission=.05),
    'pan-tapa': dict(ingredient='pan-de-papa', web=1024, coat=.18, coat_rough=.22, ao=.16),
    'papas-cajun': dict(ingredient='papas-cajun', web=512, coat=.08, coat_rough=.3, ao=.08),
}


def rng_for(tag):
    return random.Random(zlib.crc32(tag.encode()))


def nz(x, y, z, scale=1.0, seed=0.0):
    """Signed Perlin noise, roughly in [-1, 1]."""
    p = Vector((x * scale + seed * 31.7, y * scale + seed * 17.3, z * scale - seed * 11.1))
    return 1.2 * noise.noise(p, noise_basis='PERLIN_ORIGINAL')


def fbm(x, y, z, scale=1.0, octaves=4, seed=0.0):
    total, amp, norm = 0.0, 1.0, 0.0
    for i in range(octaves):
        total += amp * nz(x, y, z, scale * 2.03 ** i, seed + i * 7.1)
        norm += amp
        amp *= .5
    return total / norm


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def gauss_angle(a, center, width):
    d = math.atan2(math.sin(a - center), math.cos(a - center))
    return math.exp(-(d / width) ** 2)


def rgba(hex_color):
    vals = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in vals) + (1,)


# ---------------------------------------------------------------- scene helpers

def select(objects, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = active or objects[0]
