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

    def mix(self, fac, a, b, blend='MIX'):
        n = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_factor=True)
        self.put(n.inputs[0], fac)
        self.put(n.inputs[6], a)
        self.put(n.inputs[7], b)
        return n.outputs[2]

    def bump(self, height, strength, distance, normal=None):
        n = self.node('ShaderNodeBump')
        n.inputs['Strength'].default_value = strength
        n.inputs['Distance'].default_value = distance
        self.put(n.inputs['Height'], height)
        if normal is not None:
            self.put(n.inputs['Normal'], normal)
        return n.outputs['Normal']

    def finish(self, asset_id, color, roughness, normal=None):
        spec = ASSETS.get(asset_id, {})
        b = self.bsdf
        self.put(b.inputs['Base Color'], color)
        self.put(b.inputs['Roughness'], roughness)
        if normal is not None:
            self.put(b.inputs['Normal'], normal)
        b.inputs['Coat Weight'].default_value = spec.get('coat', 0.0)
        b.inputs['Coat Roughness'].default_value = spec.get('coat_rough', .2)
        if spec.get('emission'):
            self.put(b.inputs['Emission Color'], color)
            b.inputs['Emission Strength'].default_value = spec['emission']
        return self.mat


def mat_bun_crust(asset_id, name):
    g = Graph(name)
    co = g.co()
    brown = g.attr('brown')
    low = g.noise(co, 1.7, 3, .55)
    mid = g.noise(co, 7, 5, .6)
    idx = g.add(g.mul(brown, .8), g.add(g.mul(g.sub(low, .5), .7), g.mul(g.sub(mid, .5), .22)))
    col = g.ramp(idx, [(0, 'F2CB86'), (.2, 'ECB760'), (.42, 'E4A245'), (.62, 'D88D2F'), (.8, 'C27524'), (1, 'A05C19')])
    pores = g.voronoi(co, 110)
    col = g.mix(g.remap(pores.outputs['Distance'], .03, .1, .3, 0), col, '8E5A22')
    col = g.mix(g.remap(g.noise(co, 380, 1, .5), .6, .7, 0, .28), col, 'FBE6BF')
    rough = g.add(g.remap(brown, 0, 1, .54, .3), g.mul(g.sub(mid, .5), .14))
    height = g.add(g.mul(pores.outputs['Distance'], .5), g.mul(g.noise(co, 95, 3, .5), .5))
    normal = g.bump(height, .14, .003)
    normal = g.bump(g.noise(co, 4.5, 2, .5), .05, .02, normal)
    return g.finish(asset_id, col, rough, normal)


def mat_crumb():
    g = Graph('Soft potato bun crumb')
    co = g.co()
    big = g.voronoi(co, 38)
    small = g.voronoi(co, 105)
    holes = g.add(g.remap(big.outputs['Distance'], 0, .2, .9, 0, True), g.remap(small.outputs['Distance'], 0, .14, .5, 0, True))
    col = g.ramp(holes, [(0, 'F4E2BA'), (.45, 'EAD19C'), (1, 'CBA66A')])
    col = g.mix(g.mul(g.attr('toast'), .7), col, 'E0A552')
    normal = g.bump(g.math('SUBTRACT', 1.0, holes), .5, .006)
    return g.finish('', col, .86, normal)


def mat_sauce_original(asset_id):
    g = Graph('Salsa original peach sauce ' + asset_id)
    co = g.co()
    var = g.noise(co, 5, 3, .5)
    idx = g.add(g.mul(g.attr('thick'), .6), g.mul(g.sub(var, .5), .5))
    col = g.ramp(idx, [(0, 'D9803F'), (.4, 'E59656'), (.75, 'EDAD70'), (1, 'F2BF88')])
    rough = g.remap(var, .3, .7, .2, .3)
    normal = g.bump(g.noise(co, 13, 2, .5), .05, .01)
    return g.finish(asset_id, col, rough, normal)


def mat_pickle():
    g = Graph('Crinkle cut pickle')
    co = g.co()
    r = g.attr('pickle_r')
    col = g.ramp(r, [(0, 'BDB168'), (.3, 'ACA24F'), (.62, '958D3B'), (.84, '7A762E'), (.94, '5A5E24'), (1, '464C1C')])
    seeds = g.voronoi(co, 44)
    ring = g.mul(g.remap(r, .3, .42, 0, 1, True), g.remap(r, .6, .72, 1, 0, True))
    seed = g.mul(g.remap(seeds.outputs['Distance'], .05, .13, 1, 0, True), ring)
    col = g.mix(g.mul(seed, .7), col, 'D8D2A0')
    col = g.mix(g.attr('pickle_side'), col, '5C6428')
    var = g.noise(co, 9, 3, .5)
    rough = g.remap(var, .3, .7, .2, .32)
    normal = g.bump(g.add(g.mul(seed, .5), g.mul(g.noise(co, 70, 2, .5), .5)), .1, .003)
    return g.finish('pepinillos', col, rough, normal)


def mat_patty():
    g = Graph('Seared smash patty crust')
    co = g.co()
    rim = g.attr('rim')
    cells = g.voronoi(co, 9, 'DISTANCE_TO_EDGE')
    crev = g.remap(cells.outputs['Distance'], 0, .07, 1, 0, True)
    n1 = g.noise(co, 19, 6, .62)
    n2 = g.noise(co, 58, 4, .55)
    idx = g.add(g.sub(g.mul(n1, 1.2), .05), g.add(g.mul(crev, -.22), g.mul(rim, -.1)))
    col = g.ramp(idx, [(0, '4A2B19'), (.2, '6A4129'), (.38, '825235'), (.54, '976343'), (.7, 'AB7556'), (.85, 'BE8B70'), (1, 'CFA088')])
    specks = g.voronoi(co, 125)
    col = g.mix(g.remap(specks.outputs['Distance'], .02, .045, .8, 0), col, '160D08')
    col = g.mix(g.mul(rim, .3), col, '2A170E')
    rough = g.remap(g.add(g.mul(n2, .5), g.mul(crev, .5)), .2, .8, .34, .74)
    height = g.add(g.mul(g.math('SUBTRACT', 1.0, crev), .55), g.mul(n2, .45))
    normal = g.bump(height, .38, .005)
    return g.finish('carne', col, rough, normal)


def mat_cheese():
    g = Graph('Melted American cheese')
    co = g.co()
    var = g.noise(co, 3.2, 2, .45)
    idx = g.add(g.mul(var, .55), g.mul(g.attr('droop'), .45))
    col = g.ramp(idx, [(0, 'FFC52E'), (.45, 'F7B51C'), (.75, 'EFA612'), (1, 'E3950C')])
    rough = g.remap(var, .3, .7, .22, .3)
    normal = g.bump(g.noise(co, 22, 2, .5), .03, .01)
    return g.finish('queso-americano', col, rough, normal)


def mat_bacon():
    g = Graph('Crisp bacon lean and fat')
    co = g.co()
    u, v = g.uv('BaconSurface')
    strip = g.attr('strip')
    wob = g.noise(g.combine(g.mul(u, 7.0), g.mul(strip, 9.0), 0.0), 1.0, 2, .5)
    vv = g.math('FRACT', g.add(g.add(v, g.mul(g.sub(wob, .5), .22)), g.mul(strip, .37)))
    bands = g.ramp(vv, [(0, '000000'), (.12, 'FFFFFF'), (.24, '000000'), (.48, '000000'), (.56, 'FFFFFF'),
                        (.68, '000000'), (.82, '000000'), (.9, 'FFFFFF'), (1, '000000')])
    marble = g.noise(g.combine(g.mul(u, 12.0), g.mul(v, 3.0), g.mul(strip, 5.0)), 1.0, 4, .6)
    fat = g.add(g.mul(bands, g.remap(marble, .35, .6, .15, 1)), g.remap(marble, .66, .78, 0, .6))
    lean = g.ramp(g.noise(co, 16, 4, .55), [(0, '86301F'), (.5, 'A84432'), (1, 'BD5843')])
    fat_color = g.ramp(g.noise(co, 11, 3, .5), [(0, 'D19A72'), (1, 'EDC49E')])
    col = g.mix(fat, lean, fat_color)
    col = g.mix(g.mul(g.attr('crisp'), .7), col, '3E120A')
    fiber = g.noise(g.combine(g.mul(u, 55.0), g.mul(v, 5.0), g.mul(strip, 3.0)), 1.0, 4, .6)
    rough = g.remap(fiber, .3, .7, .36, .56)
    normal = g.bump(fiber, .22, .003)
    return g.finish('tocino', col, rough, normal)


def mat_bbq():
    g = Graph('Glossy barbecue sauce')
    co = g.co()
    var = g.noise(co, 8, 3, .5)
    col = g.ramp(var, [(0, '4A1007'), (.5, '68190B'), (1, '842413')])
    col = g.mix(g.mul(g.attr('thin'), .6), col, 'A23A18')
    normal = g.bump(g.noise(co, 30, 2, .5), .02, .005)
    return g.finish('salsa-barbacoa', col, .09, normal)


def mat_onion():
    g = Graph('Crispy fried onion batter')
    co = g.co()
    n1 = g.noise(co, 26, 5, .6)
    batter = g.voronoi(co, 80)
    idx = g.add(g.sub(g.mul(n1, 1.55), .16), g.add(g.mul(g.attr('tip'), -.2), g.mul(g.attr('core'), -.22)))
    col = g.ramp(idx, [(0, '8C5A24'), (.18, 'B07434'), (.38, 'CD9A55'), (.58, 'DFB574'), (.78, 'EAC991'), (1, 'F3DFB4')])
    crisp = g.voronoi(co, 60)
    col = g.mix(g.remap(crisp.outputs['Distance'], .03, .08, .55, 0), col, '7A4718')
    rough = g.remap(n1, .3, .7, .58, .8)
    height = g.add(g.mul(batter.outputs['Distance'], .6), g.mul(g.noise(co, 150, 2, .5), .4))
    normal = g.bump(height, .3, .004)
    return g.finish('cebolla-crispy', col, rough, normal)


def mat_fries():
    g = Graph('Cajun seasoned fries')
    co = g.co()
    base = g.ramp(g.noise(co, 4.5, 3, .5), [(0, 'D99231'), (.5, 'E4A644'), (1, 'EDBA5C')])
    base = g.mix(g.mul(g.attr('fry_end'), .55), base, 'B87428')
    specks = g.voronoi(co, 55)
    density = g.remap(g.noise(co, 9, 2, .5), .3, .6, .45, 1)
    speck = g.mul(g.remap(specks.outputs['Distance'], .09, .2, 1, 0, True), density)
    seasoning = g.ramp(specks.outputs['Color'], [(0, '8E2A12'), (.5, 'B53E1A'), (1, 'D2662A')])
    col = g.mix(g.mul(speck, .85), base, seasoning)
    normal = g.bump(g.add(g.mul(speck, .4), g.mul(g.noise(co, 70, 3, .5), .6)), .14, .003)
    return g.finish('papas-cajun', col, .5, normal)


# ---------------------------------------------------------------- geometry: buns

BUN_BASE_HEIGHT = .42
BUN_TOP_HEIGHT = .92
BUN_TOP_HOLLOW = .1


def bun_bottom():
    H = BUN_BASE_HEIGHT
    prof = [(.78 * i / 9, 0.0, 0) for i in range(10)]
    for i in range(1, 11):
        th = -math.pi / 2 + (math.pi / 2) * i / 10
        prof.append((.78 + .19 * math.cos(th), .19 + .19 * math.sin(th), 0))
    prof += [(.995, .24, 0), (1.02, .29, 0), (1.042, .335, 0), (1.058, .37, 0), (1.062, .395, 0),
             (1.05, .41, 0), (1.03, .417, 0), (1.005, H, 1)]
    prof += [(.99 * (i / 14) ** .85, H, 1) for i in range(13, -1, -1)]

    def deform(x, y, z, a):
        r = math.hypot(x, y)
        if r > 1e-6:
            k = 1 + .008 * nz(math.cos(a) * 1.4, math.sin(a) * 1.4, z * 2, 1, 2) + .004 * nz(x * 3, y * 3, z * 3, 1, 3)
            crease = .013 * math.exp(-((z - .25) / .015) ** 2) * (.55 + .45 * nz(math.cos(a) * 2, math.sin(a) * 2, 0, 1, 9))
            k -= crease / max(r, .2)
            x, y = x * k, y * k
        if z > H - .002:
            z += .004 * nz(x * 4, y * 4, 0, 1, 4) * smoothstep(.98, .5, r)
        return Vector((x, y, z))

    ob = revolve('pan-base', prof, 96, deform, [MAT['bun_base'], MAT['crumb']])

    def brown(co, n):
        if co.z > H - .01 and n.z > .6:
            return 0.0
        zn = co.z / H
        return (.56 if co.z < .02 else .34 - .1 * zn) + .05 * nz(co.x * 2, co.y * 2, co.z * 2, 1, 5)
    point_attr(ob, 'brown', brown)
    point_attr(ob, 'toast', lambda co, n: smoothstep(.8, .99, math.hypot(co.x, co.y)) if co.z > H - .01 else 0.0)
    return ob


def bun_top(z_rim):
    # The crown is hollow underneath: the onion pile and sauce push up into the crumb, so the
    # rim sits lower than the centre, as the front photo shows.
    H, hollow = BUN_TOP_HEIGHT, BUN_TOP_HOLLOW
    prof = [(.95 * (i / 14) ** .85, hollow * (1 - (i / 14) ** 1.7), 1) for i in range(15)]
    prof += [(.975, -.004, 0), (.996, .004, 0), (1.011, .022, 0)]
    p = 2.25
    for i in range(1, 41):
        phi = (math.pi / 2) * i / 40
        r = 0.0 if i == 40 else 1.022 * math.cos(phi) ** (2 / p)
        prof.append((r, .045 + (H - .045) * math.sin(phi) ** (2 / p), 0))

    def deform(x, y, z, a):
        zn = z / H
        r = math.hypot(x, y)
        if r > 1e-6:
            k = 1 + .011 * nz(math.cos(a) * 1.3, math.sin(a) * 1.3, zn, 1, 13) + .005 * nz(x * 2.6, y * 2.6, z * 2.6, 1, 14)
            x, y = x * k * 1.006, y * k * .994
        dz = (.024 * nz(x * 1.3, y * 1.3, 0, 1, 15) + .008 * nz(x * 3.5, y * 3.5, 0, 1, 16)) * smoothstep(.15, .7, zn)
        dz += .018 * smoothstep(.5, 1.0, zn) * (x * .25 - y * .12)
        if r > .9 and z < .08:
            dz += .016 * nz(x * 2.2, y * 2.2, 0, 1, 18)
        return Vector((x, y, z + dz))

    ob = revolve('pan-tapa', prof, 96, deform, [MAT['bun_top'], MAT['crumb']])

    def crumb(co, n):
        return n.z < -.3 and math.hypot(co.x, co.y) < .955

    def brown(co, n):
        if crumb(co, n):
            return 0.0
        zn = co.z / H
        return .1 + smoothstep(.04, .5, zn) * .34 + smoothstep(.45, 1.0, zn) * .18 + .05 * nz(co.x * 2, co.y * 2, co.z * 2, 1, 17)
    point_attr(ob, 'brown', brown)
    point_attr(ob, 'toast', lambda co, n: smoothstep(.8, .95, math.hypot(co.x, co.y)) if crumb(co, n) else 0.0)
    for v in ob.data.vertices:
        v.co.z += z_rim
    return ob


# ---------------------------------------------------------------- geometry: sauces and pickles

def disc_sheet(edge, top_z, bottom_z, seg=144, rings=16):
    """Closed sheet over a polar grid: top and bottom surfaces joined at the rim."""
    verts, faces = [], []
    grids = []
    for surface in (top_z, bottom_z):
        center = len(verts)
        verts.append(Vector((0, 0, surface(0.0, 0.0, 0.0, 0.0))))
        rows = []
        for j in range(1, rings + 1):
            t = j / rings
            row = []
            for i in range(seg):
                a = TAU * i / seg
                r = t * edge(a)
                x, y = r * math.cos(a), r * math.sin(a)
                row.append(len(verts))
                verts.append(Vector((x, y, surface(x, y, t, a))))
            rows.append(row)
        grids.append((center, rows))
    for g, (center, rows) in enumerate(grids):
        flip = g == 1
        for i in range(seg):
            j = (i + 1) % seg
            f = (center, rows[0][i], rows[0][j])
            faces.append(tuple(reversed(f)) if flip else f)
            for k in range(rings - 1):
                f = (rows[k][i], rows[k + 1][i], rows[k + 1][j], rows[k][j])
                faces.append(tuple(reversed(f)) if flip else f)
    top_rim, bottom_rim = grids[0][1][-1], grids[1][1][-1]
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((top_rim[i], bottom_rim[i], bottom_rim[j], top_rim[j]))
    return verts, faces


def drip(verts, faces, start, length, radius, rng):
    """A drop hanging from a sauce edge: tapering tube ending in a bulb."""
    pts = [start + Vector((0, 0, -length * i / 6)) + Vector((rng.uniform(-.004, .004), rng.uniform(-.004, .004), 0)) for i in range(7)]
    radii = [(radius * (1 - .2 * math.sin(math.pi * i / 6)) * (1.35 if i >= 5 else 1),) * 2 for i in range(7)]
    v, f = tube(pts, radii, ring=8)
    base = len(verts)
    verts.extend(v)
    faces.extend(tuple(base + i for i in face) for face in f)


def sauce_base():
    rng = rng_for('salsa-original-base')
    lobes = [(rng.uniform(0, TAU), rng.uniform(.02, .06), rng.uniform(.08, .15)) for _ in range(9)]

    def edge(a):
        e = .93 + .03 * nz(math.cos(a) * 1.6, math.sin(a) * 1.6, .2, 1, 31)
        return e + sum(amp * gauss_angle(a, c, w) for c, amp, w in lobes)

    def floor(r):
        return -1.2 * max(0.0, r - .975) ** 1.4

    def thick(a, t):
        return (.024 + .007 * nz(math.cos(a) * 3, math.sin(a) * 3, 1.3, 1, 32)) * max(0.0, 1 - t ** 6) ** .4 + .004

    verts, faces = disc_sheet(
        edge,
        lambda x, y, t, a: floor(math.hypot(x, y)) + thick(a, t) + .002 * nz(x * 12, y * 12, 0, 1, 33),
        lambda x, y, t, a: floor(math.hypot(x, y)) - .001,
        96, 10)
    bead = template('uv', 2)
    for i in range(30):
        a = TAU * i / 30 + rng.uniform(-.09, .09)
        rr = edge(a) - .015
        if rr < .93 or rng.random() < .25:
            continue
        size = rng.uniform(.014, .03)
        m = (Matrix.Translation((rr * math.cos(a), rr * math.sin(a), floor(rr) + size * .4))
             @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Diagonal((size * 1.2, size * rng.uniform(1.0, 1.6), size * 1.05, 1)))
        append_shape(verts, faces, bead, m)
    ob = mesh_object('salsa-original-base', verts, faces, [MAT['sauce_base']])
    recalc_normals(ob)
    point_attr(ob, 'thick', lambda co, n: smoothstep(-.01, .028, co.z - floor(math.hypot(co.x, co.y))))
    return ob


def pickle_slice(rng, R, t, lam, amp, phi):
    seg, rings = 32, 5

    def edge(a):
        return R * (1 + .025 * nz(math.cos(a) * 2, math.sin(a) * 2, R * 7 + phi, 1, 41) + .01 * math.sin(7 * a + phi))

    def corr(x, y):
        return amp * math.sin(TAU * (x * math.cos(phi) + y * math.sin(phi)) / lam)
    verts, faces = disc_sheet(
        edge,
        lambda x, y, tt, a: t / 2 + corr(x, y) + .0015 * nz(x * 20, y * 20, phi, 1, 42),
        lambda x, y, tt, a: -t / 2 + corr(x, y),
        seg, rings)
    return verts, faces


def pickles():
    rng = rng_for('pepinillos')
    layout = [(a + rng.uniform(-.12, .12), .84 + rng.uniform(-.03, .03)) for a in (.35, 1.3, 2.25, 3.2, 4.2, 5.25)]
    layout.append((rng.uniform(0, TAU), .12))
    parts = []
    for k, (a, rr) in enumerate(layout):
        R = rng.uniform(.29, .33)
        thick = rng.uniform(.04, .048)
        verts, faces = pickle_slice(rng, R, thick, rng.uniform(.085, .1), .01, rng.uniform(0, math.pi))
        ob = mesh_object('pickle %d' % k, verts, faces, [MAT['pickle']])
        recalc_normals(ob)
        point_attr(ob, 'pickle_r', lambda co, n, R=R: min(1.0, math.hypot(co.x, co.y) / R))
        point_attr(ob, 'pickle_side', lambda co, n: smoothstep(.55, .9, 1 - abs(n.z)))
        tilt = .1 * smoothstep(.3, .7, rr)
        ob.matrix_world = (Matrix.Translation((rr * math.cos(a), rr * math.sin(a), thick / 2 + .006 + .003 * (k % 3)))
                           @ Matrix.Rotation(-tilt, 4, Vector((-math.sin(a), math.cos(a), 0)))
                           @ Matrix.Rotation(rng.uniform(0, TAU), 4, 'Z'))
        parts.append(ob)
    for ob in parts:
        select([ob])
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return join(parts, 'pepinillos')


# ---------------------------------------------------------------- geometry: patty and cheese

PATTY_R = 1.115
# Stack rotation of the lower and upper patty; their cheese slices share it so the drape fits.
PATTY_ROTATIONS = (.35, 2.6)
