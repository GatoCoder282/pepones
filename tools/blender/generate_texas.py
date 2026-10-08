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
FRONT = -math.pi / 2


def patty_edge(a):
    return PATTY_R * (1 + .036 * nz(math.cos(a) * 1.1, math.sin(a) * 1.1, .4, 1, 51)
                      + .024 * nz(math.cos(a) * 2.8, math.sin(a) * 2.8, 1.3, 1, 52)
                      + .015 * nz(math.cos(a) * 6.5, math.sin(a) * 6.5, 2.2, 1, 53))


def patty_high():
    rng = rng_for('carne')
    seg, rings = 240, 32

    def top_z(x, y, t):
        return .2 * (1 - .3 * t ** 3) + .016 * fbm(x, y, 0, 1.5, 3, 54)

    def bottom_z(x, y, t):
        return .02 * t ** 4 + .003 * nz(x * 8, y * 8, 0, 1, 55)

    def edge(a):
        # Smash patties end in a thin, torn lace: fine jitter on top of the broad outline.
        return patty_edge(a) * (1 + .018 * nz(math.cos(a) * 14, math.sin(a) * 14, 3.1, 1, 59))
    verts, faces = disc_sheet(edge, lambda x, y, t, a: top_z(x, y, t), lambda x, y, t, a: bottom_z(x, y, t), seg, rings)
    bit = template('ico', 2)
    for k in range(330):
        a = rng.random() * TAU
        if k < 220:
            # Crisp flakes along the lacy rim.
            rr = edge(a) * rng.uniform(.95, 1.055)
            z = rng.uniform(.03, .14)
            size = rng.uniform(.016, .04)
            squash = rng.uniform(.3, .55)
        else:
            # Coarse ground-beef clusters on the seared top.
            rr = math.sqrt(rng.random()) * .9 * edge(a)
            z = top_z(rr * math.cos(a), rr * math.sin(a), rr / edge(a)) + rng.uniform(-.014, .002)
            size = rng.uniform(.018, .036)
            squash = rng.uniform(.5, .8)
        m = (Matrix.Translation((rr * math.cos(a), rr * math.sin(a), z)) @ Matrix.Rotation(rng.uniform(0, TAU), 4, 'Z')
             @ Matrix.Diagonal((size * rng.uniform(1.0, 2.0), size, size * squash, 1)))
        lumpy = ([v * (1 + .4 * nz(v.x + k, v.y, v.z, 2.2, 58)) for v in bit[0]], bit[1])
        append_shape(verts, faces, lumpy, m)
    ob = mesh_object('carne high', verts, faces, [MAT['patty']])
    recalc_normals(ob)
    apply_modifier(ob, 'REMESH', mode='VOXEL', voxel_size=.0095, use_smooth_shade=True)
    apply_modifier(ob, 'SMOOTH', factor=.45, iterations=2)
    me = ob.data
    for v in me.vertices:
        p, n = v.co, v.normal
        dist, _ = noise.voronoi(p * 8.0)
        crack = smoothstep(0, .16, dist[1] - dist[0])
        h = .013 * crack + .006 * fbm(p.x, p.y, p.z, 18, 3, 56) + .0025 * nz(p.x, p.y, p.z, 70, 57)
        v.co = p + n * h * (.3 if n.z < -.5 else 1.0)
    me.update()
    recalc_normals(ob)
    me.shade_smooth()

    def rim(co, n):
        a = math.atan2(co.y, co.x)
        return max(smoothstep(.86, 1.02, math.hypot(co.x, co.y) / patty_edge(a)), .7 * (1 - abs(n.z)))
    point_attr(ob, 'rim', rim)
    return ob


def decimated(high, name, target):
    low = high.copy()
    low.data = high.data.copy()
    WORK.objects.link(low)
    low.name = low.data.name = name
    ratio = min(1.0, target / max(1, triangles(high)))
    apply_modifier(low, 'DECIMATE', decimate_type='COLLAPSE', ratio=ratio, use_collapse_triangulate=True)
    low.data.validate()
    low.data.update()
    return low


def patty_top_mean(patty):
    zs = [v.co.z for v in patty.data.vertices if v.normal.z > .7 and math.hypot(v.co.x, v.co.y) < .8]
    return sum(zs) / len(zs)


def cheese(patty):
    rng = rng_for('queso-americano')
    cast = raycaster([patty])
    edge_cache = []
    for i in range(360):
        a = TAU * i / 360
        r, last = .5, None
        while r < 1.5:
            hit = cast(r * math.cos(a), r * math.sin(a))
            if hit is None:
                break
            last = (r, hit[0].z)
            r += .01
        edge_cache.append(last)

    def patty_rim(a):
        return edge_cache[int(round(a / TAU * 360)) % 360]
    tongues = [(rng.uniform(0, TAU), rng.uniform(.12, .2), rng.uniform(.1, .18)) for _ in range(4)]
    # The photo shows the melt hanging over the front edge of both patties.
    tongues += [(FRONT - rot + rng.uniform(-.15, .15), rng.uniform(.2, .26), .3) for rot in PATTY_ROTATIONS]

    def edge(a):
        sq = (abs(math.cos(a)) ** 4.5 + abs(math.sin(a)) ** 4.5) ** (-1 / 4.5)
        e = .93 * sq * (1 + .03 * nz(math.cos(a) * 2, math.sin(a) * 2, .7, 1, 61))
        return e + sum(amp * gauss_angle(a, c, w) for c, amp, w in tongues)
    n = 40
    grid, droop = {}, {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = 2 * i / n - 1, 2 * j / n - 1
            rho = max(abs(u), abs(v))
            a = math.atan2(v, u) if rho > 0 else 0.0
            r = rho * edge(a)
            x, y = r * math.cos(a), r * math.sin(a)
            hit = cast(x, y)
            if hit is not None:
                around = [cast(x + dx, y + dy) for dx, dy in ((.025, 0), (-.025, 0), (0, .025), (0, -.025))]
                z, d = max([hit[0].z] + [h[0].z for h in around if h is not None]) + .018, 0.0
            else:
                rim_r, rim_z = patty_rim(a)
                d = max(0.0, r - rim_r)
                z = rim_z + .02 - (.45 * d + 1.8 * d * d)
                r = rim_r + .02 + d * .75
                x, y = r * math.cos(a), r * math.sin(a)
            grid[i, j] = Vector((x, y, z))
            droop[i, j] = d
    # Melted cheese relaxes over small lumps instead of following every crumb.
    relaxed = {}
    for (i, j), p in grid.items():
        acc, w = 0.0, 0.0
        for di in (-2, -1, 0, 1, 2):
            for dj in (-2, -1, 0, 1, 2):
                q = grid.get((i + di, j + dj))
                if q is not None:
                    acc += q.z
                    w += 1
        relaxed[i, j] = Vector((p.x, p.y, max(acc / w, p.z - .002) + .002 * nz(p.x * 6, p.y * 6, 0, 1, 62)))
    verts = [relaxed[i, j] for i in range(n + 1) for j in range(n + 1)]
    faces = []
    for i in range(n):
        for j in range(n):
            a = i * (n + 1) + j
            faces.append((a, a + n + 1, a + n + 2, a + 1))
    ob = mesh_object('queso-americano', verts, faces, [MAT['cheese']])
    apply_modifier(ob, 'WELD', merge_threshold=.0005)
    recalc_normals(ob)
    if sum(p.normal.z for p in ob.data.polygons) < 0:
        apply_modifier(ob, 'SOLIDIFY', thickness=.016, offset=1.0, use_even_offset=True)
    else:
        apply_modifier(ob, 'SOLIDIFY', thickness=.016, offset=-1.0, use_even_offset=True)
    recalc_normals(ob)
    rest = patty_top_mean(patty) + .02
    point_attr(ob, 'droop', lambda co, n: smoothstep(.0, .12, rest - co.z))
    return ob


# ---------------------------------------------------------------- geometry: bacon, barbecue, onions

def bacon():
    rng = rng_for('tocino')
    specs = [(-.5, .12, 2.5, .37, .0), (-.16, -.1, 2.62, .39, .032), (.2, .2, 2.48, .36, .058),
             (.54, -.15, 2.32, .34, .074), (-.02, .66, 2.3, .35, .1)]
    parts = []
    for k, (offset, rot, L, W, z0) in enumerate(specs):
        nx, ny = 76, 6
        phase, lam, amp = rng.uniform(0, TAU), rng.uniform(.26, .4), rng.uniform(.045, .06)
        verts, faces, uvs, crisp = [], [], [], []
        c, s = math.cos(rot), math.sin(rot)
        for j in range(ny + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / ny
                x = (u - .5) * L
                w = W * (1 + .12 * math.sin(u * 23 + k) + .06 * math.sin(u * 61 + 2 * k))
                y = (v - .5) * w + .035 * math.sin(u * 7 + k * 1.3)
                wave = math.sin(TAU * x / lam + phase + .9 * math.sin(x * 1.3 + k))
                z = amp * wave * (.55 + .45 * (fbm(x, k, 0, .9, 2, 71) + 1) * .5)
                z += .014 * math.sin(TAU * x / (lam * .43) + 2 * phase) + .028 * fbm(x, k, 1, 1.6, 3, 72)
                z += .022 * (2 * v - 1) ** 2 * math.sin(TAU * x / (lam * .5) + phase * 1.7)
                z += (v - .5) * w * .22 * math.sin(x * 2.1 + k)
                z += .008 * nz(x * 4, y * 4, k, 1, 70)
                xw, yw = x * c - y * s, x * s + y * c + offset
                rw = math.hypot(xw, yw)
                z += z0 + amp - .55 * max(0.0, rw - 1.0) ** 1.5
                verts.append(Vector((xw, yw, z)))
                uvs.append((u, v))
                crisp.append(min(1.0, (2 * v - 1) ** 6 * .8 + smoothstep(.6, 1, abs(math.sin(TAU * x / lam + phase))) * .3 + smoothstep(.42, .5, abs(u - .5)) * .6))
        for j in range(ny):
            for i in range(nx):
                a = j * (nx + 1) + i
                faces.append((a, a + 1, a + nx + 2, a + nx + 1))
        ob = mesh_object('bacon strip %d' % k, verts, faces, [MAT['bacon']])
        layer = ob.data.uv_layers.new(name='BaconSurface')
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                layer.data[li].uv = uvs[ob.data.loops[li].vertex_index]
        for name, values in [('strip', [k / len(specs)] * len(verts)), ('crisp', crisp)]:
            attr = ob.data.attributes.new(name, 'FLOAT', 'POINT')
            attr.data.foreach_set('value', values)
        apply_modifier(ob, 'SOLIDIFY', thickness=.022, offset=0.0, use_even_offset=True)
        parts.append(ob)
    ob = join(parts, 'tocino')
    recalc_normals(ob)
    return ob


def bbq(bacon_ob):
    rng = rng_for('salsa-barbacoa')
    cast = raycaster([bacon_ob])
    verts, faces = [], []
    blob = template('uv', 2)
    placed = attempts = 0
    while placed < 16 and attempts < 400:
        attempts += 1
        # The photo shows the glaze on the front of the bacon; the rest is spread around.
        if placed < 5:
            a, r = FRONT + rng.uniform(-.9, .9), rng.uniform(.55, .95)
        else:
            a, r = rng.uniform(0, TAU), .85 * math.sqrt(rng.random())
        x, y = r * math.cos(a), r * math.sin(a)
        hit = cast(x, y)
        if hit is None:
            continue
        loc, normal = hit[0], hit[1]
        rx = rng.uniform(.06, .13)
        m = (Matrix.Translation(loc + normal * .004) @ normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
             @ Matrix.Rotation(rng.uniform(0, TAU), 4, 'Z') @ Matrix.Diagonal((rx, rx * rng.uniform(.45, .8), rng.uniform(.011, .018), 1)))
        append_shape(verts, faces, blob, m)
        placed += 1
    for x in (-.12, .22):
        y = -1.3
        hit = None
        while y < 0 and hit is None:
            hit = cast(x, y)
            y += .01
        if hit is not None:
            drip(verts, faces, hit[0] + Vector((0, .01, -.004)), rng.uniform(.09, .13), .022, rng)
    ob = mesh_object('salsa-barbacoa', verts, faces, [MAT['bbq']])
    recalc_normals(ob)
    point_attr(ob, 'thin', lambda co, n: smoothstep(.3, .9, 1 - abs(n.z)))
    return ob


def onions(below):
    """Crispy onions as the photo shows them: broad, flat battered strips cut from onion rings."""
    rng = rng_for('cebolla-crispy')
    cast = raycaster(below)

    def base_height(x, y):
        hit = cast(x, y)
        return hit[0].z if hit is not None else -.15
    field = HeightField(base_height)
    verts, faces, tips, inner = [], [], [], []
    # count, points, section, arc radius, sweep, half width, half thickness, spread, inner pile
    base = field.h.copy()
    groups = [(75, 6, 6, (.12, .24), (.5, 1.0), (.03, .043), (.01, .014), .75, 1.0),
              (130, 9, 6, (.2, .5), (.5, 1.2), (.035, .05), (.011, .015), 1.02, 0.0)]

    def envelope(x, y):
        # The mound the photo suggests: about a quarter unit high, lower at the rim.
        r = math.hypot(x, y)
        i, j = field._ij(x, y)
        i, j = int(min(max(round(i), 0), field.n - 1)), int(min(max(round(j), 0), field.n - 1))
        return base[i, j] + .03 + .22 * max(0.0, 1 - (r / 1.05) ** 2) ** .6
    for count, n, ring, rho_range, sweep_range, width_range, thick_range, spread, depth in groups:
        for k in range(count):
            r = spread * math.sqrt(rng.random()) ** 1.5
            a = rng.uniform(0, TAU)
            cx, cy = r * math.cos(a), r * math.sin(a)
            rho, sweep, start = rng.uniform(*rho_range), rng.uniform(*sweep_range), rng.uniform(0, TAU)
            tilt_axis = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized()
            tilt = Matrix.Rotation(rng.uniform(-.45, .45), 3, tilt_axis)
            local = []
            for i in range(n):
                al = start + sweep * i / (n - 1)
                rr = rho * (1 + .08 * math.sin(i * .9 + k))
                local.append(tilt @ Vector((rr * math.cos(al), rr * math.sin(al), .01 * math.sin(i * 1.3 + k))))
            mid = sum(local, Vector()) / n
            pts = [Vector((cx, cy, 0)) + (p - mid) for p in local]
            half_w, half_t = rng.uniform(*width_range), rng.uniform(*thick_range)
            # Fried strips catch on each other, leaving air in the pile.
            lift = max(field.sample(p.x, p.y) - p.z for p in pts) + half_t * .5 + rng.uniform(-.004, .012)
            # Strips settle into the mound instead of stacking into a tower.
            lift = min(lift, max(min(envelope(p.x, p.y) - p.z for p in pts) + .06,
                                 max(field.sample(p.x, p.y) - p.z for p in pts) - .03))
            pts = [p + Vector((0, 0, lift)) for p in pts]
            pts = [p - Vector((0, 0, .55 * max(0.0, math.hypot(p.x, p.y) - .97) ** 1.3)) for p in pts]
            for p in pts:
                field.stamp(p.x, p.y, p.z + half_t, half_w * 1.1)
            radii = [(half_w * (.6 + .4 * math.sin(math.pi * (i + .5) / n) ** .5), half_t) for i in range(n)]
            twist = [rng.uniform(-.3, .3) + .2 * math.sin(i * .7 + k) for i in range(n)]
            v, f = tube(pts, radii, ring=ring, twist=twist,
                        # Ragged batter: the flat strip's two edges vary most.
                        lump=lambda p, kk, k=k: (.34 if kk % 3 == 0 else .14) * nz(p.x + kk * .37, p.y, p.z + k, 30, 82)
                        + .1 * nz(p.x, p.y + kk, p.z, 90, 83))
            offset = len(verts)
            verts.extend(v)
            faces.extend(tuple(offset + i for i in face) for face in f)
            for i in range(len(v)):
                tips.append(1 - math.sin(math.pi * min(i // ring, n - 1) / (n - 1)))
                inner.append(depth)
    ob = mesh_object('cebolla-crispy', verts, faces, [MAT['onion']])
    recalc_normals(ob)
    for name, values in [('tip', tips), ('core', inner)]:
        attr = ob.data.attributes.new(name, 'FLOAT', 'POINT')
        attr.data.foreach_set('value', values)
    return ob


def sauce_top(onion_ob):
    rng = rng_for('salsa-original-tapa')
    cast = raycaster([onion_ob])

    def pile(x, y):
        hit = cast(x, y)
        return hit[0].z if hit is not None else -.1
    samples = sorted(pile(r * math.cos(a), r * math.sin(a)) for r in (.0, .12, .24, .36) for a in np.linspace(0, TAU, 16))
    z_rim = samples[int(len(samples) * .7)] + .006 - BUN_TOP_HOLLOW

    def under(r):
        # Underside of the hollow crown: the sauce is spread on it.
        return z_rim + BUN_TOP_HOLLOW * (1 - min(1.0, r / .95) ** 1.7)
    lobes = [(rng.uniform(0, TAU), rng.uniform(.03, .07), rng.uniform(.1, .18)) for _ in range(6)] + [(FRONT, .1, .4)]

    def edge(a):
        return .88 + .03 * nz(math.cos(a) * 1.7, math.sin(a) * 1.7, 2.1, 1, 91) + sum(amp * gauss_angle(a, c, w) for c, amp, w in lobes)

    def top(x, y):
        return under(math.hypot(x, y)) - .002 + .0015 * nz(x * 7, y * 7, 1, 1, 93)

    def bottom(x, y, t, a):
        sag = .045 * max(0.0, 1 - t * t) ** .8 + .016 + .06 * gauss_angle(a, FRONT, .4) * smoothstep(.5, 1, t)
        z = top(x, y)
        return min(z - .008, max(pile(x, y) - .004, z - sag) + .002 * nz(x * 9, y * 9, 0, 1, 92))
    verts, faces = disc_sheet(edge, lambda x, y, t, a: top(x, y), bottom, 96, 10)
    bead = template('uv', 2)
    for _ in range(6):
        a = FRONT + rng.uniform(-.8, .8)
        rr = edge(a) - .05
        x, y = rr * math.cos(a), rr * math.sin(a)
        size = rng.uniform(.022, .034)
        m = (Matrix.Translation((x, y, top(x, y) - size * .9)) @ Matrix.Rotation(a, 4, 'Z')
             @ Matrix.Diagonal((size * 1.4, size * 1.6, size, 1)))
        append_shape(verts, faces, bead, m)
    ob = mesh_object('salsa-original-tapa', verts, faces, [MAT['sauce_top']])
    recalc_normals(ob)
    point_attr(ob, 'thick', lambda co, n: smoothstep(.0, .05, under(math.hypot(co.x, co.y)) - co.z))
    return ob, z_rim


# ---------------------------------------------------------------- geometry: fries (side)

def fries():
    rng = rng_for('papas-cajun')
    field = HeightField(lambda x, y: 0.0, half=1.8, n=110)
    verts, faces, ends = [], [], []
    for k in range(12):
        L, T = rng.uniform(.85, 1.2), rng.uniform(.14, .17)
        nl, corner = 12, 3
        section = []
        for q in range(4):
            cx, cy = (1 if q in (0, 3) else -1), (1 if q < 2 else -1)
            for c in range(corner):
                th = (q * math.pi / 2) + (math.pi / 2) * c / (corner - 1)
                section.append((cx * (T / 2 - .03) + .03 * math.cos(th), cy * (T / 2 - .03) + .03 * math.sin(th)))
        bend = rng.uniform(-.08, .08)
        heading = rng.uniform(-.9, .9) + (math.pi / 2 if k % 4 == 0 else 0)
        cx, cy = rng.uniform(-.95, .95), rng.uniform(-.65, .65)
        local = []
        for i in range(nl + 1):
            s = i / nl
            taper = 1 - .08 * abs(2 * s - 1) ** 2
            for (px, py) in section:
                local.append(Vector(((s - .5) * L, px * taper, py * taper + bend * math.sin(math.pi * s))))
        rot = Matrix.Rotation(heading, 3, 'Z') @ Matrix.Rotation(rng.uniform(-.25, .25), 3, 'X') @ Matrix.Rotation(rng.uniform(-.12, .12), 3, 'Y')
        placed = [rot @ p + Vector((cx, cy, 0)) for p in local]
        lift = max(field.sample(p.x, p.y) - p.z for p in placed) + .002
        placed = [p + Vector((0, 0, lift)) for p in placed]
        for p in placed:
            field.stamp(p.x, p.y, p.z, .06)
        base = len(verts)
        ns = len(section)
        verts.extend(placed)
        ends.extend([smoothstep(.12, .0, min(i / nl, 1 - i / nl)) for i in range(nl + 1) for _ in section])
        for i in range(nl):
            for c in range(ns):
                c2 = (c + 1) % ns
                faces.append((base + i * ns + c, base + i * ns + c2, base + (i + 1) * ns + c2, base + (i + 1) * ns + c))
        faces.append(tuple(base + c for c in range(ns)))
        faces.append(tuple(base + nl * ns + c for c in reversed(range(ns))))
    ob = mesh_object('papas-cajun', verts, faces, [MAT['fries']])
    recalc_normals(ob)
    attr = ob.data.attributes.new('fry_end', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', ends)
    return ob
