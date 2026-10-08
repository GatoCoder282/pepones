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
