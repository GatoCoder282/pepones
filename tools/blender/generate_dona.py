"""Reproducible Dona Burger asset build. Run with Blender's bundled Python.

blender --background --python tools/blender/generate_dona.py -- --mode preview
blender --background --python tools/blender/generate_dona.py -- --mode build
All geometry/materials are procedural, guided by the supplied Pepones photos.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['preview', 'build'], default='build')
parser.add_argument('--output', type=Path, default=ROOT / 'material/semanal/dona-burger/modelos')
parser.add_argument('--texture-size', type=int, default=2048)
parser.add_argument('--web-texture-size', type=int, default=1024)
parser.add_argument('--resolution', type=int, default=1600)
parser.add_argument('--samples', type=int, default=96)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT = args.output.resolve()
for sub in ['', 'textures', 'textures/web', 'renders', 'glb']:
    (OUT / sub).mkdir(parents=True, exist_ok=True)
rng = random.Random(41027)
TAU = math.tau


def n(x, y, z, scale=1):
    return noise.noise(Vector((x * scale, y * scale, z * scale)), noise_basis='PERLIN_ORIGINAL')


def rgba(hex_color):
    vals = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in vals) + (1,)


def material(name, colors, scale=5, micro=100, bump=.015, rough=(.4, .7), coat=.1):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bs = nodes.get('Principled BSDF')
    bs.inputs['Coat Weight'].default_value = coat
    bs.inputs['Coat Roughness'].default_value = .22
    bs.inputs['IOR'].default_value = 1.45
    coord = nodes.new('ShaderNodeTexCoord')
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 5
    tex.inputs['Roughness'].default_value = .72
    links.new(coord.outputs['Object'], tex.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i, (pos, col) in enumerate(colors):
        e = ramp.color_ramp.elements[0] if i == 0 else ramp.color_ramp.elements.new(pos)
        e.position, e.color = pos, rgba(col)
    links.new(tex.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs[0], bs.inputs['Base Color'])
    remap = nodes.new('ShaderNodeMapRange')
    remap.inputs['To Min'].default_value = rough[0]
    remap.inputs['To Max'].default_value = rough[1]
    links.new(tex.outputs['Fac'], remap.inputs['Value'])
    links.new(remap.outputs[0], bs.inputs['Roughness'])
    fine = nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = micro
    fine.inputs['Detail'].default_value = 3
    links.new(coord.outputs['Object'], fine.inputs['Vector'])
    normal = nodes.new('ShaderNodeBump')
    normal.inputs['Strength'].default_value = .55
    normal.inputs['Distance'].default_value = bump
    links.new(fine.outputs['Fac'], normal.inputs['Height'])
    links.new(normal.outputs[0], bs.inputs['Normal'])
    return mat


def mesh(name, vertices, faces, mats, indices=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    for m in mats:
        data.materials.append(m)
    for i, p in enumerate(data.polygons):
        p.use_smooth = True
        if indices:
            p.material_index = indices[i]
    return obj


def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def apply_modifier(obj, kind, **values):
    select([obj])
    mod = obj.modifiers.new(kind.title(), kind)
    for key, value in values.items():
        setattr(mod, key, value)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def donut_point(a, phi, top, offset=0):
    radius = .665 + .465 * math.cos(phi)
    radius *= 1 + .009 * math.sin(5 * a) + .008 * math.sin(9 * a + 1.2)
    z = (.31 if top else -.255) * math.sin(phi)
    bump = .0035 * n(math.cos(a) * radius, math.sin(a) * radius, z, 34)
    radius += (bump + offset) * math.cos(phi)
    z += (bump + offset) * math.sin(phi) * (1 if top else -1)
    z += .004 * math.sin(4 * a + phi) * math.sin(phi)
    return (radius * math.cos(a), radius * math.sin(a), z)


def donut(top):
    count, arcs, caps = 176, 36, 12
    profiles = [(math.pi * j / arcs, False) for j in range(arcs + 1)]
    profiles += [(j / caps, True) for j in range(1, caps)]
    verts, faces, slots = [], [], []
    for a_i in range(count):
        a = TAU * a_i / count
        for value, cut in profiles:
            if cut:
                r = .2 + .93 * value
                r *= 1 + .009 * math.sin(5 * a) + .008 * math.sin(9 * a + 1.2)
                verts.append((r * math.cos(a), r * math.sin(a), .001 * n(r * math.cos(a), r * math.sin(a), 4, 28)))
            else:
                verts.append(donut_point(a, value, top))
    width = len(profiles)
    for i in range(count):
        for j in range(width):
            face = (i * width + j, ((i + 1) % count) * width + j,
                    ((i + 1) % count) * width + (j + 1) % width, i * width + (j + 1) % width)
            faces.append(face if top else tuple(reversed(face)))
            slots.append(1 if j >= arcs else 0)
    dough = mesh('Dough upper' if top else 'Dough lower', verts, faces, [DOUGH_TOP if top else DOUGH, CRUMB], slots)
    if top:
        return [dough]
    # Thin flakes and drips are real surface geometry, visible when layers separate.
    verts, faces = [], []
    na, np = 216, 90
    grid, field = [], []
    for i in range(na + 1):
        a = TAU * i / na
        drip = .045
        for k in range(19):
            center = TAU * k / 19 + .07 * math.sin(k * 2.2)
            delta = math.atan2(math.sin(a - center), math.cos(a - center))
            drip += (.25 + .52 * (.5 + .5 * math.sin(k * 3.9))) * math.exp(-(delta / .034) ** 2)
        for j in range(np + 1):
            phi = math.pi * j / np
            p = donut_point(a, phi, top, .002)
            grid.append(Vector(p))
            # Clip triangles at a continuous boundary: no square icing patches.
            value = min(drip * .32 - phi, n(*p, 13) + .28) if top else min(drip - phi, n(*p, 13) + .28)
            field.append(value)
    for i in range(na):
        for j in range(np):
            a0 = i * (np + 1) + j
            for tri in [(a0, a0 + np + 1, a0 + np + 2), (a0, a0 + np + 2, a0 + 1)]:
                clipped = []
                for prev, cur in zip(tri[-1:] + tri[:-1], tri):
                    pv, cv = field[prev], field[cur]
                    if (pv > 0) != (cv > 0):
                        clipped.append(grid[prev].lerp(grid[cur], pv / (pv - cv)))
                    if cv > 0:
                        clipped.append(grid[cur])
                if len(clipped) >= 3:
                    base = len(verts)
                    verts.extend(tuple(v) for v in clipped)
                    face = tuple(range(base, base + len(clipped)))
                    faces.append(face if top else tuple(reversed(face)))
    glaze = mesh('Sugar flakes upper' if top else 'Sugar drips lower', verts, faces, [GLAZE])
    bm = bmesh.new()
    bm.from_mesh(glaze.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.00001)
    bm.to_mesh(glaze.data)
    bm.free()
    return [dough, glaze]


def patty():
    rings, count = 24, 176
    verts, faces = [], []
    for side in [1, -1]:
        for j in range(rings + 1):
            t = max(.002, j / rings)
            for i in range(count):
                a = TAU * i / count
                edge = 1.08 + .025 * math.sin(11 * a + side * .35) + .032 * math.sin(19 * a + 2 + side * .8) + .023 * math.sin(31 * a - side * .5)
                x, y = edge * t * math.cos(a), edge * t * math.sin(a)
                height = .125 + .020 * n(x, y, 2 + side, 17) + .010 * n(x, y, side, 65)
                height *= 1 - .22 * t ** 5
                verts.append((x, y, side * height))
    sheet = (rings + 1) * count
    for side in range(2):
        base = side * sheet
        for j in range(rings):
            for i in range(count):
                a, b = base + j * count + i, base + j * count + (i + 1) % count
                f = (a, a + count, b + count, b)
                faces.append(f if side == 0 else tuple(reversed(f)))
    edge_rings = [[rings * count + i for i in range(count)]]
    for row in range(1, 6):
        t = row / 6
        indices = []
        for i in range(count):
            p = Vector(verts[rings * count + i]).lerp(Vector(verts[sheet + rings * count + i]), t)
            r = math.hypot(p.x, p.y)
            offset = .019 * n(p.x, p.y, p.z, 48) * math.sin(t * math.pi)
            p.x *= 1 + offset / r
            p.y *= 1 + offset / r
            indices.append(len(verts))
            verts.append(tuple(p))
        edge_rings.append(indices)
    edge_rings.append([sheet + rings * count + i for i in range(count)])
    for above, below in zip(edge_rings, edge_rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            faces.append((above[i], below[i], below[j], above[j]))
    faces += [tuple(reversed(range(count))), tuple(sheet + i for i in range(count))]
    slots = [0] * len(faces)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
    template = bpy.context.object
    tv = [v.co.copy() for v in template.data.vertices]
    tf = [tuple(p.vertices) for p in template.data.polygons]
    bpy.data.objects.remove(template, do_unlink=True)
    for k in range(460):
        a = rng.random() * TAU
        radius = rng.uniform(.91, 1.12) if k < 330 else math.sqrt(rng.random()) * .94
        center = Vector((math.cos(a) * radius, math.sin(a) * radius, rng.uniform(-.065, .055) if k < 330 else .10))
        size = rng.uniform(.021, .052)
        stretch = Vector((size * rng.uniform(.8, 1.65), size, size * rng.uniform(.4, .8)))
        base = len(verts)
        for v in tv:
            d = 1 + .42 * n(v.x + k, v.y, v.z, 4)
            verts.append(tuple(center + Vector((v.x * stretch.x, v.y * stretch.y, v.z * stretch.z)) * d))
        faces.extend(tuple(base + i for i in f) for f in tf)
        slots.extend([1 if k % 6 == 0 else 0] * len(tf))
    ob = mesh('Smash beef seared crust', verts, faces, [BEEF, CHAR], slots)
    # Fuse the ground-beef clusters into a single irregular crust, avoiding bead-like seams.
    apply_modifier(ob, 'REMESH', mode='VOXEL', voxel_size=.016, use_smooth_shade=True)
    apply_modifier(ob, 'SMOOTH', factor=.62, iterations=3)
    apply_modifier(ob, 'DECIMATE', ratio=.65)
    return [ob]


def cheese():
    verts, faces = [], []
    steps = 44
    for j in range(steps + 1):
        for i in range(steps + 1):
            x, y = (i / steps - .5) * 1.75, (j / steps - .5) * 1.73
            x += .013 * math.sin(y * 9) * (abs(x) / .875) ** 5
            y += .01 * math.sin(x * 13)
            r = math.hypot(x, y)
            z = .035 + .005 * n(x, y, 0, 8) - max(0, r - 1.035) ** 1.35
            z -= .027 * max(0, -y) * max(0, x)
            verts.append((x, y, z))
    for j in range(steps):
        for i in range(steps):
            k = j * (steps + 1) + i
            faces.append((k, k + 1, k + steps + 2, k + steps + 1))
    ob = mesh('American cheese melted corners', verts, faces, [CHEESE])
    apply_modifier(ob, 'SOLIDIFY', thickness=.01)
    apply_modifier(ob, 'BEVEL', width=.004, segments=2)
    return [ob]


def bacon():
    result = []
    for strip in range(4):
        verts, faces = [], []
        nx, ny = 88, 10
        length = [2.28, 2.18, 2.07, 1.94][strip]
        width = [.29, .31, .28, .24][strip]
        for j in range(ny + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / ny
                x = (u - .5) * length
                w = width * (1 + .17 * math.sin(u * 25 + strip) + .07 * math.sin(u * 71))
                y = (v - .5) * w + .046 * math.sin(u * 9 + strip)
                z = .065 * math.sin(u * 17 + strip * 1.8) + .026 * math.sin(u * 39 + v * 4)
                z += .044 * (2 * v - 1) ** 2 * math.sin(u * 12 + strip) + .023 * math.cos(u * 8 + v * 5)
                verts.append((x, y, z))
        for j in range(ny):
            for i in range(nx):
                k = j * (nx + 1) + i
                faces.append((k, k + 1, k + nx + 2, k + nx + 1))
        ob = mesh('Bacon ribbon %02d' % strip, verts, faces, [BACON])
        uv = ob.data.uv_layers.new(name='BaconSurface')
        for poly in ob.data.polygons:
            for loop in poly.loop_indices:
                vi = ob.data.loops[loop].vertex_index
                uv.data[loop].uv = (vi % (nx + 1) / nx, vi // (nx + 1) / ny)
        apply_modifier(ob, 'SOLIDIFY', thickness=.027)
        apply_modifier(ob, 'BEVEL', width=.005, segments=2)
        ob.location = (0, (strip - 1.7) * .32, .017 * strip)
        ob.rotation_euler.z = [-.09, .12, -.18, .20][strip]
        result.append(ob)
    return result


def join(parts, name):
    select(parts)
    if len(parts) > 1:
        bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def bake(ob, asset_id):
    select([ob])
    atlas = ob.data.uv_layers.new(name='WebAtlas')
    ob.data.uv_layers.active = atlas
    atlas.active_render = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.4, island_margin=.001, area_weight=.8, margin_method='FRACTION')
    bpy.ops.object.mode_set(mode='OBJECT')
    images = {}
    for name, bake_type in [('color', 'DIFFUSE'), ('roughness', 'ROUGHNESS'), ('normal', 'NORMAL')]:
        print('BAKE', asset_id, name, flush=True)
        im = bpy.data.images.new(asset_id + '_' + name, width=args.texture_size, height=args.texture_size)
        if name != 'color':
            im.colorspace_settings.name = 'Non-Color'
        for mat in ob.data.materials:
            nodes = mat.node_tree.nodes
            target = nodes.new('ShaderNodeTexImage')
            target.image = im
            target.name = 'Bake target ' + name
            nodes.active = target
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True
        bpy.ops.object.bake(type=bake_type, margin=2, use_clear=True, normal_space='TANGENT')
        im.filepath_raw = str(OUT / 'textures' / (asset_id + '_' + name + '.png'))
        im.file_format = 'PNG'
        im.save()
        images[name] = im
    original = ob.copy()
    original.data = ob.data.copy()
    SOURCE.objects.link(original)
    original.name = 'SOURCE_' + asset_id
    original.hide_render = True
    original.hide_set(True)
    mat = bpy.data.materials.new(asset_id + '_PBR')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bs = nodes.get('Principled BSDF')
    bs.inputs['Coat Weight'].default_value = .16 if 'dona' in asset_id else .08
    bs.inputs['Coat Roughness'].default_value = .25
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'WebAtlas'
    for name, im in images.items():
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = im
        links.new(uv.outputs['UV'], tex.inputs['Vector'])
        if name == 'normal':
            normal = nodes.new('ShaderNodeNormalMap')
            links.new(tex.outputs['Color'], normal.inputs['Color'])
            links.new(normal.outputs[0], bs.inputs['Normal'])
        elif name == 'roughness':
            sep = nodes.new('ShaderNodeSeparateColor')
            links.new(tex.outputs['Color'], sep.inputs[0])
            links.new(sep.outputs['Green'], bs.inputs['Roughness'])
        else:
            links.new(tex.outputs['Color'], bs.inputs['Base Color'])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.material_index = 0
    # Baking used source coordinates; only the atlas is needed by the web asset.
    for uv_layer in list(ob.data.uv_layers):
        if uv_layer.name != 'WebAtlas':
            ob.data.uv_layers.remove(uv_layer)


def point_at(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def export_web_asset(ob, asset_id, path):
    source_mat = ob.data.materials[0]
    web_mat = source_mat.copy()
    web_mat.name = asset_id + '_WebPBR'
    for node in web_mat.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeTexImage' and node.image:
            im = node.image.copy()
            im.scale(args.web_texture_size, args.web_texture_size)
            im.filepath_raw = str(OUT / 'textures/web' / (im.name.split('.')[0] + '.png'))
            im.file_format = 'PNG'
            im.save()
            node.image = im
    ob.data.materials[0] = web_mat
    select([ob])
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_yup=True, export_animations=False, export_cameras=False, export_lights=False,
                              export_texcoords=True, export_normals=True, export_extras=True)
    ob.data.materials[0] = source_mat


def studio():
    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.65, .72, .8, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .28
    for name, pos, energy, size, col in [
        ('Key softbox', (-3, -4, 5), 400, 4, (1, .91, .80)),
        ('Fill softbox', (4, -2, 2.5), 180, 3, (.83, .91, 1)),
        ('Rim softbox', (1, 3, 4), 500, 2.5, (1, .84, .66)),
    ]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.shape, light.size, light.color = energy, 'DISK', size, col
        ob = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(ob)
        ob.location = pos
        point_at(ob, (0, 0, 0))
    cam = bpy.data.objects.new('Review camera', bpy.data.cameras.new('Review camera'))
    bpy.context.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 3.15
    bpy.context.scene.camera = cam
    return cam


def render_views(cam, assembly):
    scene = bpy.context.scene
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = int(args.resolution * .83)
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.cycles.samples = args.samples
    views = [('front', (0, -6, .55)), ('three-quarter', (3.1, -6, 2.05)), ('exploded', (3, -6, 3.1))]
    if args.mode == 'preview':
        views = views[:2]
    for name, pos in views:
        if name == 'exploded':
            for i, ob in enumerate(assembly):
                ob.location.z += (i - 3) * .36
            cam.data.ortho_scale = 5.2
            scene.render.resolution_y = args.resolution
        cam.location = pos
        point_at(cam, (0, 0, -.1))
        scene.render.filepath = str(OUT / 'renders' / (('preview-' if args.mode == 'preview' else '') + name + '.png'))
        bpy.ops.render.render(write_still=True)
        if name == 'exploded':
            for i, ob in enumerate(assembly):
                ob.location.z -= (i - 3) * .36
    cam.location = (3.1, -6, 2.65)
    cam.data.ortho_scale = 3.15
    point_at(cam, (0, 0, -.1))


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 8
bpy.context.preferences.filepaths.save_version = 0
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    if any(d.use for d in prefs.devices):
        scene.cycles.device = 'GPU'
except Exception as exc:
    print('GPU unavailable, using CPU:', exc, flush=True)

SOURCE = bpy.data.collections.new('Procedural originals - hidden during render')
scene.collection.children.link(SOURCE)
DOUGH = material('Golden fried dough', [(.16, '87350A'), (.36, 'AD4E0D'), (.61, 'C67516'), (.82, 'E59A31')], 5, 160, .005, (.22, .42), .35)
DOUGH_TOP = DOUGH.copy()
DOUGH_TOP.name = 'Glazed golden dough crown'
nodes, links = DOUGH_TOP.node_tree.nodes, DOUGH_TOP.node_tree.links
bs = nodes.get('Principled BSDF')
original_color = bs.inputs['Base Color'].links[0].from_socket
coord = nodes.new('ShaderNodeTexCoord')
scale = nodes.new('ShaderNodeVectorMath')
scale.operation = 'MULTIPLY'
scale.inputs[1].default_value = (1, 2.2, 1.5)
links.new(coord.outputs['Object'], scale.inputs[0])
tex = nodes.new('ShaderNodeTexNoise')
tex.inputs['Scale'].default_value = 12
tex.inputs['Detail'].default_value = 3
links.new(scale.outputs[0], tex.inputs['Vector'])
mask = nodes.new('ShaderNodeValToRGB')
mask.color_ramp.elements[0].position = .54
mask.color_ramp.elements[0].color = (.035, .035, .035, 1)
mask.color_ramp.elements[1].position = .68
mask.color_ramp.elements[1].color = (.65, .65, .65, 1)
links.new(tex.outputs['Fac'], mask.inputs[0])
mix = nodes.new('ShaderNodeMixRGB')
links.new(mask.outputs[0], mix.inputs[0])
links.new(original_color, mix.inputs[1])
mix.inputs[2].default_value = rgba('FFF0D3')
links.new(mix.outputs[0], bs.inputs['Base Color'])
CRUMB = material('Cut bread crumb', [(.2, 'D8B16B'), (.43, 'ECCE8D'), (.68, 'F6E2B1'), (.83, 'E5C581')], 34, 140, .019, (.72, .9), 0)
GLAZE = material('Thin crystallized sugar glaze', [(.22, 'E2C994'), (.45, 'F2E4C8'), (.73, 'FFF5DE')], 25, 190, .004, (.2, .39), .3)
BEEF = material('Smash crust and rendered fat', [(.17, '21120C'), (.35, '432319'), (.5, '63331D'), (.66, 'A46634'), (.83, '492414')], 27, 145, .012, (.28, .67), .18)
CHAR = material('Charred sear edges', [(.1, '24140B'), (.47, '432513'), (.77, '6C3A1B')], 28, 130, .018, (.5, .82), .05)
CHEESE = material('Golden American cheese', [(.18, 'E6A009'), (.48, 'F7BA0B'), (.8, 'FFCC27')], 6, 100, .002, (.24, .36), .12)
BACON = material('Rendered bacon meat and fat', [(.15, '42180C'), (.36, '762A15'), (.49, 'A84420'), (.55, 'D59755'), (.64, 'E8C28A'), (.76, '91421D')], 18, 130, .007, (.22, .43), .28)
# Longitudinal fat bands retain their coordinates after multi-strip joining.
nodes, links = BACON.node_tree.nodes, BACON.node_tree.links
uv = nodes.new('ShaderNodeUVMap')
uv.uv_map = 'BaconSurface'
mapping = nodes.new('ShaderNodeVectorMath')
mapping.operation = 'MULTIPLY'
mapping.inputs[1].default_value = (1.5, 6, 1)
links.new(uv.outputs['UV'], mapping.inputs[0])
for node in nodes:
    if node.bl_idname == 'ShaderNodeTexNoise' and node.inputs['Scale'].default_value == 18:
        node.inputs['Scale'].default_value = 1.5
        links.new(mapping.outputs[0], node.inputs['Vector'])

asset_defs = [('dona-bottom', lambda: donut(False)), ('smash-beef', patty), ('american-cheese', cheese), ('bacon', bacon), ('dona-top', lambda: donut(True))]
assets, stats = {}, []
for asset_id, factory in asset_defs:
    print('MODEL', asset_id, flush=True)
    ob = join(factory(), asset_id)
    # Isolate each ingredient while baking, so coincident assets cannot occlude it.
    for prev in assets.values():
        prev.hide_render = True
        prev.hide_set(True)
    if args.mode == 'build':
        bake(ob, asset_id)
        path = OUT / 'glb' / (asset_id + '.glb')
        export_web_asset(ob, asset_id, path)
        ob.data.calc_loop_triangles()
        stats.append({'id': asset_id, 'triangles': len(ob.data.loop_triangles), 'bytes': path.stat().st_size})
    assets[asset_id] = ob

recipe = [
    ('dona-bottom', -.54, 0), ('smash-beef', -.40, -.12), ('american-cheese', -.29, .22),
    ('smash-beef', -.14, .65), ('american-cheese', -.03, -.25), ('bacon', .08, -.04), ('dona-top', .205, 0),
]
assembly = []
used = set()
for i, (asset_id, height, rotation) in enumerate(recipe):
    original = assets[asset_id]
    ob = original if asset_id not in used else original.copy()
    if asset_id in used:
        bpy.context.collection.objects.link(ob)
    used.add(asset_id)
    ob.name = '%02d_%s' % (i + 1, asset_id)
    ob.hide_render = False
    ob.hide_set(False)
    ob.location = (0, 0, height)
    ob.rotation_euler.z = rotation
    ob['ingredient_id'] = asset_id
    ob['layer_index'] = i
    assembly.append(ob)

if args.mode == 'build':
    select(assembly)
    bpy.ops.export_scene.gltf(filepath=str(OUT / 'glb' / 'dona-burger-assembled.glb'), export_format='GLB', use_selection=True,
                              export_yup=True, export_animations=False, export_cameras=False, export_lights=False, export_extras=True)
    manifest = {
        'name': 'Dona Burger', 'version': 1, 'blender': bpy.app.version_string,
        'referenceFiles': ['photos/dona burger.png', 'photos/dona ingrediente.png', 'photos/dona ingredientes dona.png',
                           'photos/dona ingredientes carne.png', 'photos/dona ingredientes carne con tocino.png'],
        'interpretation': 'Procedural reconstruction from supplied references; unseen surfaces and physical scale interpreted.',
        'assets': stats, 'sourceTextureSize': args.texture_size, 'webTextureSize': args.web_texture_size,
        'recipe': [{'ingredientId': aid, 'y': h, 'rotation': [0, rot, 0]} for aid, h, rot in recipe],
        'totalUniqueBytes': sum(s['bytes'] for s in stats),
        'assembledTriangles': sum(next(s['triangles'] for s in stats if s['id'] == aid) for aid, _, _ in recipe),
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

cam = studio()
select(assembly)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / ('dona-burger.blend' if args.mode == 'build' else 'preview-source.blend')), compress=True)
render_views(cam, assembly)
if args.mode == 'build':
    for im in bpy.data.images:
        if im.filepath and im.has_data:
            im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'dona-burger.blend'), compress=True)
print('DONE', str(OUT), flush=True)
