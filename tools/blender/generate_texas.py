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


def mesh_object(name, verts, faces, materials=(), slots=None, collection=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in materials:
        me.materials.append(m)
    if slots is not None:
        me.polygons.foreach_set('material_index', slots)
    me.validate()
    me.update()
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    (collection or WORK).objects.link(ob)
    return ob


def recalc_normals(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def apply_modifier(ob, kind, **values):
    select([ob])
    mod = ob.modifiers.new(kind.title(), kind)
    for key, value in values.items():
        setattr(mod, key, value)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def join(parts, name):
    select(parts)
    if len(parts) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def point_attr(ob, name, fn):
    me = ob.data
    attr = me.attributes.get(name) or me.attributes.new(name, 'FLOAT', 'POINT')
    attr.data.foreach_set('value', [float(fn(v.co, v.normal)) for v in me.vertices])


def triangles(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


def template(kind='ico', level=2):
    bm = bmesh.new()
    if kind == 'ico':
        bmesh.ops.create_icosphere(bm, subdivisions=level, radius=1.0)
    else:
        bmesh.ops.create_uvsphere(bm, u_segments=level * 6, v_segments=level * 3, radius=1.0)
    bm.verts.index_update()
    verts = [v.co.copy() for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces


def append_shape(verts, faces, shape, matrix, deform=None):
    base = len(verts)
    for v in shape[0]:
        p = matrix @ v
        verts.append(deform(p) if deform else p)
    faces.extend(tuple(base + i for i in f) for f in shape[1])


def tube(points, radii, ring=6, up=UP, lump=None, twist=None):
    """Closed tube with an elliptical section: radii are (half width, half thickness)."""
    verts, faces = [], []
    n = len(points)
    for i, p in enumerate(points):
        t = (points[min(i + 1, n - 1)] - points[max(i - 1, 0)]).normalized()
        side = t.cross(up)
        if side.length < 1e-5:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        normal = side.cross(t).normalized()
        if twist:
            c, s = math.cos(twist[i]), math.sin(twist[i])
            side, normal = side * c + normal * s, normal * c - side * s
        a, b = radii[i]
        for k in range(ring):
            th = TAU * k / ring
            s = 1 + (lump(p, k) if lump else 0)
            verts.append(p + side * (math.cos(th) * a * s) + normal * (math.sin(th) * b * s))
    for i in range(n - 1):
        for k in range(ring):
            k2 = (k + 1) % ring
            faces.append((i * ring + k, i * ring + k2, (i + 1) * ring + k2, (i + 1) * ring + k))
    start = len(verts)
    verts.append(points[0] - (points[1] - points[0]).normalized() * radii[0][1] * .7)
    verts.append(points[-1] + (points[-1] - points[-2]).normalized() * radii[-1][1] * .7)
    last = (n - 1) * ring
    for k in range(ring):
        k2 = (k + 1) % ring
        faces.append((start, k2, k))
        faces.append((start + 1, last + k, last + k2))
    return verts, faces


def revolve(name, profile, segments, deform, materials):
    """Profile points (r, z, material slot) from the bottom pole to the top pole."""
    verts, faces, slots, rings = [], [], [], []
    for k, (r, z, _) in enumerate(profile):
        if r <= 1e-9:
            verts.append(deform(0.0, 0.0, z, 0.0))
            rings.append([len(verts) - 1])
            continue
        ring = []
        for i in range(segments):
            a = TAU * i / segments
            ring.append(len(verts))
            verts.append(deform(r * math.cos(a), r * math.sin(a), z, a))
        rings.append(ring)
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        slot = profile[k + 1][2] if len(B) > 1 else profile[k][2]
        for i in range(segments):
            j = (i + 1) % segments
            if len(A) == 1:
                faces.append((A[0], B[i], B[j]))
            elif len(B) == 1:
                faces.append((A[i], A[j], B[0]))
            else:
                faces.append((A[i], A[j], B[j], B[i]))
            slots.append(slot)
    ob = mesh_object(name, verts, faces, materials, slots)
    recalc_normals(ob)
    return ob


def raycaster(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(ob, depsgraph) for ob in objects]

    def cast(x, y, top=3.0):
        best = None
        for tree in trees:
            hit = tree.ray_cast(Vector((x, y, top)), Vector((0, 0, -1)), 10.0)
            if hit[0] is not None and (best is None or hit[0].z > best[0].z):
                best = hit
        return best
    return cast


class HeightField:
    """Top surface of a pile, used to drop strands so they rest on what lies below."""

    def __init__(self, fn, half=1.45, n=120):
        self.half, self.n = half, n
        xs = np.linspace(-half, half, n)
        self.h = np.array([[fn(x, y) for y in xs] for x in xs])

    def _ij(self, x, y):
        return ((x + self.half) / (2 * self.half) * (self.n - 1), (y + self.half) / (2 * self.half) * (self.n - 1))

    def sample(self, x, y):
        fi, fj = self._ij(x, y)
        i, j = int(min(max(fi, 0), self.n - 2)), int(min(max(fj, 0), self.n - 2))
        u, v = min(max(fi - i, 0), 1), min(max(fj - j, 0), 1)
        h = self.h
        return (h[i, j] * (1 - u) * (1 - v) + h[i + 1, j] * u * (1 - v) + h[i, j + 1] * (1 - u) * v + h[i + 1, j + 1] * u * v)

    def stamp(self, x, y, z, radius):
        fi, fj = self._ij(x, y)
        cell = 2 * self.half / (self.n - 1)
        k = int(radius / cell) + 1
        for i in range(max(0, int(fi) - k), min(self.n, int(fi) + k + 2)):
            for j in range(max(0, int(fj) - k), min(self.n, int(fj) + k + 2)):
                d = math.hypot((i - fi) * cell, (j - fj) * cell)
                if d < radius:
                    self.h[i, j] = max(self.h[i, j], z - .35 * radius * (d / radius) ** 2)


# ---------------------------------------------------------------- procedural materials

class Graph:
    def __init__(self, name):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links
        self.bsdf = self.nodes['Principled BSDF']
        self._co = None

    def put(self, socket, value):
        if isinstance(value, bpy.types.NodeSocket):
            self.links.new(value, socket)
        elif isinstance(value, str):
            socket.default_value = rgba(value)
        else:
            socket.default_value = value

    def node(self, kind, **props):
        n = self.nodes.new(kind)
        for key, value in props.items():
            setattr(n, key, value)
        return n

    def co(self):
        if self._co is None:
            self._co = self.node('ShaderNodeTexCoord').outputs['Object']
        return self._co

    def attr(self, name):
        n = self.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name)
        return n.outputs['Fac']

    def uv(self, name):
        n = self.node('ShaderNodeUVMap', uv_map=name)
        sep = self.node('ShaderNodeSeparateXYZ')
        self.links.new(n.outputs['UV'], sep.inputs[0])
        return sep.outputs['X'], sep.outputs['Y']

    def combine(self, x, y, z):
        n = self.node('ShaderNodeCombineXYZ')
        for socket, value in zip(n.inputs, (x, y, z)):
            self.put(socket, value)
        return n.outputs[0]

    def noise(self, vec, scale, detail=4.0, rough=.5, distortion=0.0):
        n = self.node('ShaderNodeTexNoise', noise_type='FBM')
        self.put(n.inputs['Vector'], vec)
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = distortion
        return n.outputs['Fac']

    def voronoi(self, vec, scale, feature='F1', randomness=1.0):
        n = self.node('ShaderNodeTexVoronoi', feature=feature)
        self.put(n.inputs['Vector'], vec)
        n.inputs['Scale'].default_value = scale
        n.inputs['Randomness'].default_value = randomness
        return n

    def math(self, op, a, b=0.0, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(n.inputs[0], a)
        self.put(n.inputs[1], b)
        return n.outputs[0]

    def add(self, a, b):
        return self.math('ADD', a, b)

    def mul(self, a, b):
        return self.math('MULTIPLY', a, b)

    def sub(self, a, b):
        return self.math('SUBTRACT', a, b)

    def remap(self, value, a, b, c, d, smooth=False):
        n = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP' if smooth else 'LINEAR', clamp=True)
        self.put(n.inputs['Value'], value)
        for key, v in zip(['From Min', 'From Max', 'To Min', 'To Max'], (a, b, c, d)):
            n.inputs[key].default_value = v
        return n.outputs['Result']

    def ramp(self, fac, stops):
        n = self.node('ShaderNodeValToRGB')
        els = n.color_ramp.elements
        els[0].position, els[0].color = stops[0][0], rgba(stops[0][1])
        els[1].position, els[1].color = stops[-1][0], rgba(stops[-1][1])
        for pos, col in stops[1:-1]:
            els.new(pos).color = rgba(col)
        self.put(n.inputs['Fac'], fac)
        return n.outputs['Color']
