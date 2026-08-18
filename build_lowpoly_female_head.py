import bpy
import math
import os
from mathutils import Vector


BLEND_PATH = r"E:\Blender\신민정\lowpoly_char_test.blend"
PREVIEW_PATH = r"E:\Blender\신민정\lowpoly_char_head_preview.png"


def clear_scene():
    # Direct datablock removal is reliable in background mode even without an
    # initialized 3D-view operator context.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def mat(name, color, roughness=0.72, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return m


def finish(obj, name, material, collection, flat=True):
    obj.name = name
    if material:
        obj.data.materials.append(material)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    if obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = not flat
    return obj


def ico(name, loc, scale, material, collection, subdivisions=2, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=loc, rotation=rotation)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, material, collection, flat=True)


def uv(name, loc, scale, material, collection, segments=16, rings=8, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc, rotation=rotation)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, material, collection, flat=True)


def cone(name, loc, radius1, radius2, depth, material, collection, vertices=6, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc, rotation=rotation)
    return finish(bpy.context.object, name, material, collection, flat=True)


def cube(name, loc, scale, material, collection, rotation=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rotation)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Tiny planar bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o, name, material, collection, flat=True)


def wedge(name, points_front, depth, material, collection):
    # A tapered six-sided lock, front face toward -Y.
    y_front = -1.56
    y_back = y_front + depth
    verts = [(x, y_front, z) for x, z in points_front] + [(x, y_back, z) for x, z in points_front]
    n = len(points_front)
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n+j, n+i))
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


clear_scene()

char = bpy.data.collections.new('LP_FemaleHead')
bpy.context.scene.collection.children.link(char)
rig = bpy.data.collections.new('Presentation')
bpy.context.scene.collection.children.link(rig)

skin = mat('Skin_Peach', (0.92, 0.55, 0.43), 0.82)
skin_light = mat('Skin_Highlight', (1.00, 0.67, 0.55), 0.78)
skin_shadow = mat('Skin_Shadow', (0.66, 0.29, 0.25), 0.86)
hair = mat('Hair_Chestnut', (0.032, 0.009, 0.005), 0.64)
hair_hi = mat('Hair_Warm_Highlight', (0.105, 0.022, 0.009), 0.68)
white = mat('Eye_White', (0.96, 0.94, 0.89), 0.54)
iris = mat('Iris_Emerald', (0.055, 0.35, 0.25), 0.48)
iris_hi = mat('Iris_Highlight', (0.45, 0.95, 0.72), 0.35)
dark = mat('Pupil_Lashes', (0.012, 0.008, 0.01), 0.58)
lip = mat('Lip_Rose', (0.64, 0.09, 0.13), 0.72)
blush = mat('Blush', (0.94, 0.27, 0.31), 0.83)
shirt = mat('Collar_Sage', (0.18, 0.42, 0.36), 0.86)
gold = mat('Earring_Gold', (0.82, 0.47, 0.10), 0.34, 0.35)

# Neck and stylized bust anchor.
cone('Neck', (0, 0.12, -0.15), 0.48, 0.38, 1.25, skin_shadow, char, vertices=8)
cone('Shoulder_Bust', (0, 0.35, -0.95), 1.65, 0.62, 1.10, shirt, char, vertices=8)

# Back hair mass first; the face sits forward to expose a clean facial plane.
ico('Hair_Back_Mass', (0, 0.30, 1.72), (1.72, 1.22, 2.05), hair, char, subdivisions=2)
ico('Hair_Back_Lower', (0, 0.50, 0.55), (1.48, 0.92, 1.55), hair, char, subdivisions=2)

# Deformed youthful face: broad cranium, tapered lower face, compact chin.
ico('Face_Main', (0, -0.40, 1.65), (1.48, 1.13, 1.72), skin, char, subdivisions=3)
ico('Chin', (0, -0.58, 0.48), (0.78, 0.73, 0.60), skin, char, subdivisions=2)

# Ears and simple earrings.
for side in (-1, 1):
    ico(f'Ear_{side:+d}', (side * 1.47, -0.25, 1.38), (0.26, 0.18, 0.50), skin_light, char, subdivisions=2)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.035, major_segments=8, minor_segments=4,
                                    location=(side * 1.54, -0.35, 0.89), rotation=(math.radians(90), 0, 0))
    finish(bpy.context.object, f'Earring_{side:+d}', gold, char, flat=True)

# Eyes, irises, pupils, catchlights and upper lash bars.
for side in (-1, 1):
    x = side * 0.57
    uv(f'EyeWhite_{side:+d}', (x, -1.49, 1.83), (0.53, 0.16, 0.53), white, char, 16, 8)
    uv(f'Iris_{side:+d}', (x, -1.646, 1.82), (0.255, 0.055, 0.31), iris, char, 12, 6)
    uv(f'Pupil_{side:+d}', (x, -1.700, 1.81), (0.105, 0.025, 0.16), dark, char, 10, 5)
    ico(f'Catchlight_{side:+d}', (x - side * 0.065, -1.732, 1.94), (0.065, 0.018, 0.080), white, char, subdivisions=1)
    cube(f'UpperLash_{side:+d}', (x, -1.665, 2.22), (0.48, 0.035, 0.055), dark, char,
         rotation=(0, side * math.radians(2), side * math.radians(7)), bevel=0.035)
    # Outer lash triangle.
    points = [(x + side*0.42, 2.23), (x + side*0.68, 2.29), (x + side*0.43, 2.15)]
    wedge(f'OuterLash_{side:+d}', points, 0.08, dark, char)
    # Eyebrow, higher toward the center for a gentle expression.
    cube(f'Brow_{side:+d}', (x, -1.59, 2.52), (0.39, 0.035, 0.055), hair, char,
         rotation=(0, 0, -side * math.radians(9)), bevel=0.04)

# Tiny faceted nose and soft mouth.
cone('Nose', (0, -1.67, 1.28), 0.13, 0.035, 0.42, skin_light, char, vertices=5,
     rotation=(math.radians(90), 0, 0))
cube('Nose_Shadow', (0.08, -1.80, 1.12), (0.09, 0.018, 0.025), skin_shadow, char,
     rotation=(0, 0, math.radians(-8)), bevel=0.02)
cube('Mouth', (0, -1.62, 0.82), (0.32, 0.045, 0.055), lip, char, bevel=0.055)
cube('LowerLip_Highlight', (0, -1.67, 0.75), (0.20, 0.025, 0.025), skin_light, char, bevel=0.02)

# Faceted blush patches.
for side in (-1, 1):
    ico(f'Blush_{side:+d}', (side*0.91, -1.52, 1.08), (0.26, 0.035, 0.13), blush, char, subdivisions=1,
        rotation=(0, 0, side*math.radians(8)))

# Graphic fringe wedges layered on the forehead.
bangs = [
    ('Bang_L_outer', [(-1.38, 3.15), (-0.62, 3.45), (-0.42, 2.25), (-0.92, 2.43)], hair_hi),
    ('Bang_L_inner', [(-0.84, 3.45), (-0.16, 3.55), (-0.10, 2.33), (-0.48, 2.12)], hair),
    ('Bang_Center', [(-0.28, 3.55), (0.33, 3.53), (0.22, 2.05), (-0.05, 2.32)], hair_hi),
    ('Bang_R_inner', [(0.13, 3.52), (0.84, 3.40), (0.52, 2.15), (0.18, 2.34)], hair),
    ('Bang_R_outer', [(0.62, 3.40), (1.40, 3.12), (0.92, 2.38), (0.47, 2.24)], hair_hi),
]
for name, points, material in bangs:
    wedge(name, points, 0.28, material, char)

# Chunky side locks framing the jaw, asymmetric tips for charm.
for side in (-1, 1):
    x0 = side * 1.33
    pts = [(x0-side*0.23, 2.75), (x0+side*0.28, 2.63), (x0+side*0.22, 0.18),
           (x0-side*0.04, -0.15), (x0-side*0.33, 0.55)]
    wedge(f'SideLock_{side:+d}', pts, 0.36, hair if side < 0 else hair_hi, char)

# Small polygonal cowlick silhouette.
cone('Cowlick', (0.34, 0.12, 3.75), 0.18, 0.015, 0.72, hair_hi, char, vertices=5,
     rotation=(0, math.radians(17), math.radians(-15)))

# Presentation ground, camera and lights.
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0.8, -1.52))
ground = finish(bpy.context.object, 'Ground', mat('Ground_Matte', (0.055, 0.065, 0.08), 0.92), rig, flat=True)

bpy.ops.object.camera_add(location=(0, -10.8, 1.35))
camera = bpy.context.object
camera.name = 'Portrait_Camera'
camera.data.lens = 58
camera.data.sensor_width = 36
look_at(camera, (0, -0.20, 1.15))
for c in list(camera.users_collection): c.objects.unlink(camera)
rig.objects.link(camera)
bpy.context.scene.camera = camera

def area_light(name, loc, energy, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    rig.objects.link(obj)
    obj.location = loc
    look_at(obj, (0, 0, 1.2))
    return obj

area_light('Key_Softbox', (-4.5, -5.0, 6.5), 1050, 5.0, (1.0, 0.73, 0.58))
area_light('Fill_Softbox', (4.2, -3.2, 3.6), 720, 4.0, (0.55, 0.72, 1.0))
area_light('Hair_Rim', (0.8, 2.6, 5.6), 1250, 3.0, (1.0, 0.35, 0.18))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 700
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = PREVIEW_PATH
scene.render.film_transparent = False
scene.render.image_settings.color_mode = 'RGBA'
scene.eevee.taa_render_samples = 256
scene.world.color = (0.018, 0.023, 0.035)
scene.view_settings.look = 'AgX - Medium High Contrast'

# Make editing pleasant when opened interactively.
scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
for obj in char.objects:
    obj.select_set(False)
head = bpy.data.objects.get('Face_Main')
if head:
    head.select_set(True)
    bpy.context.view_layer.objects.active = head

scene['asset_description'] = 'Stylized low-poly deformed female character head, generated with Blender 5.2 LTS'
scene['front_axis'] = '-Y'

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.render.render(write_still=True)
print(f'SAVED={BLEND_PATH}')
print(f'PREVIEW={PREVIEW_PATH}')
print(f'CHAR_OBJECTS={len(char.objects)}')
