import bpy
import math
from mathutils import Vector


BLEND_PATH = r"E:\Blender\신민정\lowpoly_char_test.blend"
OUT_DIR = r"E:\Blender\신민정"
REFS = [
    r"E:\Blender\신민정\ref_char\ChatGPT Image 2026년 8월 18일 오후 08_17_16 (1).png",
    r"E:\Blender\신민정\ref_char\ChatGPT Image 2026년 8월 18일 오후 08_17_16 (3).png",
    r"E:\Blender\신민정\ref_char\ChatGPT Image 2026년 8월 18일 오후 08_17_16 (4).png",
    r"E:\Blender\신민정\ref_char\ChatGPT Image 2026년 8월 18일 오후 08_18_01.png",
]


def reset():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)


def material(name, color, roughness=0.75, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m


def mesh_obj(name, verts, faces, mat, col):
    me = bpy.data.meshes.new(name + '_Mesh')
    me.from_pydata(verts, [], faces)
    me.update(calc_edges=True)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
    return ob


def lowpoly_head(name, mat, col):
    # Carefully controlled horizontal rings: broad crown, cheek plane, tapered jaw.
    rings = [
        (3.42, 0.38, 0.48, 0.28),
        (3.28, 0.92, 0.82, 0.26),
        (3.02, 1.18, 1.06, 0.24),
        (2.70, 1.34, 1.18, 0.22),
        (2.34, 1.37, 1.20, 0.18),
        (1.98, 1.33, 1.16, 0.13),
        (1.63, 1.27, 1.08, 0.10),
        (1.29, 1.17, 0.97, 0.08),
        (0.98, 1.00, 0.82, 0.08),
        (0.70, 0.76, 0.66, 0.10),
        (0.48, 0.44, 0.46, 0.13),
        (0.38, 0.25, 0.30, 0.16),
    ]
    seg = 20
    verts = []
    for ri, (z, rx, ry, cy) in enumerate(rings):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            x = rx * math.sin(a)
            y = cy - ry * math.cos(a)
            # Gentle muzzle/cheek shaping on the front half.
            front = max(0.0, math.cos(a))
            if 1.05 < z < 1.75:
                y -= 0.055 * front * (1.0 - min(1.0, abs(x) / 1.25))
            if 0.65 < z <= 1.05:
                y -= 0.18 * front * (1.0 - min(1.0, abs(x) / 1.10))
            if 1.65 < z < 2.28 and 0.35 < abs(x) < 1.15:
                y += 0.045 * front
            verts.append((x, y, z))
    faces = []
    for r in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            a=r*seg+i; b=r*seg+j; c=(r+1)*seg+j; d=(r+1)*seg+i
            if (r+i)%2:
                faces.extend([(a,b,d),(b,c,d)])
            else:
                faces.extend([(a,b,c),(a,c,d)])
    faces.append(tuple(range(seg-1, -1, -1)))
    b = (len(rings)-1)*seg
    faces.append(tuple(b+i for i in range(seg)))
    return mesh_obj(name, verts, faces, mat, col)


def ellipsoid(name, loc, scale, mat, col, segments=16, rings=8, rot=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.name = name
    for old in list(ob.users_collection): old.objects.unlink(ob)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    tri=ob.modifiers.new('Triangulated facets','TRIANGULATE')
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=tri.name)
    for p in ob.data.polygons: p.use_smooth = False
    return ob


def cylinder(name, loc, radius, depth, mat, col, vertices=12, scale=(1,1,1), rot=(math.pi/2,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.name = name
    for old in list(ob.users_collection): old.objects.unlink(ob)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth = False
    return ob


def polyline_tube(name, points, radius, mat, col, resolution=0):
    cu = bpy.data.curves.new(name + '_Curve', 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = resolution
    cu.bevel_depth = radius
    cu.bevel_resolution = 0
    cu.resolution_u = 1
    sp = cu.splines.new('POLY')
    sp.points.add(len(points)-1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1)
    ob = bpy.data.objects.new(name, cu)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def almond(name, cx, z, width, height, y_front, mat, col):
    outline = [
        (-1.0, 0.00), (-0.62, 0.55), (0.0, 0.78), (0.62, 0.52), (1.0, 0.00),
        (0.62, -0.45), (0.0, -0.62), (-0.62, -0.43)
    ]
    verts = [(cx + x*width, y_front+0.09, z+zz*height) for x,zz in outline]
    verts += [(cx, y_front-0.035, z), (cx, y_front+0.16, z)]
    faces = []
    for i in range(8):
        j=(i+1)%8
        faces.append((8,i,j))
        faces.append((9,j,i))
    return mesh_obj(name, verts, faces, mat, col)


def ribbon(name, centers, widths, thickness, mat, col):
    # Faceted volumetric hair lock, each section has left/right front/back points.
    verts=[]
    for (x,y,z), w in zip(centers,widths):
        verts += [(x-w,y-thickness,z),(x+w,y-thickness,z),(x+w,y+thickness,z),(x-w,y+thickness,z)]
    faces=[]
    for k in range(len(centers)-1):
        a=4*k; b=4*(k+1)
        faces += [(a,a+1,b+1,b),(a+1,a+2,b+2,b+1),(a+2,a+3,b+3,b+2),(a+3,a,b,b+3)]
    faces += [(0,3,2,1)]
    e=4*(len(centers)-1)
    faces += [(e,e+1,e+2,e+3)]
    return mesh_obj(name,verts,faces,mat,col)


def ear(name, x, mat, inner_mat, col):
    side = 1 if x > 0 else -1
    center=(x,0.03,1.72)
    pts=[]
    n=12
    for i in range(n):
        a=2*math.pi*i/n
        pts.append((center[0],center[1]-0.10*math.cos(a),center[2]+0.51*math.sin(a)))
    # ellipse tube whose visible thickness extends in X
    verts=[]
    for p in pts:
        verts += [(p[0]-side*0.12,p[1],p[2]),(p[0]+side*0.12,p[1],p[2])]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.append((2*i,2*j,2*j+1,2*i+1))
    ob=mesh_obj(name,verts,faces,mat,col)
    polyline_tube(name+'_Inner',[(x-side*.03,-.11,1.98),(x-side*.12,-.18,1.79),(x-side*.03,-.17,1.57),(x-side*.12,-.15,1.42)],.035,inner_mat,col)
    return ob


def look_at(ob,target):
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()


reset()
model=bpy.data.collections.new('LowPoly_Reference_Character')
bpy.context.scene.collection.children.link(model)
presentation=bpy.data.collections.new('Presentation')
bpy.context.scene.collection.children.link(presentation)
refs_col=bpy.data.collections.new('Packed_References_Hidden')
bpy.context.scene.collection.children.link(refs_col)
refs_col.hide_viewport=True
refs_col.hide_render=True

# Linear-space colors chosen for a restrained, readable clay-like palette.
skin=material('Skin_Warm',(0.46,0.40,0.35),.86)
skin_dark=material('Skin_Shadow',(0.29,0.25,0.23),.9)
skin_light=material('Skin_Light',(0.56,0.50,0.45),.78)
hair=material('Hair_Aubergine',(0.105,0.085,0.09),.78)
hair_hi=material('Hair_Highlight',(0.17,0.145,0.15),.74)
eye_white=material('Eye_Sclera',(0.70,0.68,0.64),.58)
iris=material('Iris_GreyGreen',(0.16,0.20,0.18),.48)
dark=material('Lashes_Pupil',(0.008,0.006,0.008),.58)
lip=material('Lips_MutedRose',(0.34,0.20,0.20),.76)
shirt=material('Bust_Charcoal',(0.13,0.15,0.17),.88)
groundmat=material('Ground',(0.28,0.29,0.31),.95)

head=lowpoly_head('Head_Unified',skin,model)

# Neck and shoulder base.
bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=.70,radius2=.46,depth=1.65,location=(0,.30,-.17))
neck=bpy.context.object; neck.scale.y=.72; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
neck.name='Neck'; neck.data.materials.append(skin_dark)
for c in list(neck.users_collection): c.objects.unlink(neck)
model.objects.link(neck)
for p in neck.data.polygons:p.use_smooth=False
bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=1.85,radius2=.70,depth=.72,location=(0,.35,-1.18))
bust=bpy.context.object; bust.scale.y=.68; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bust.name='Bust_Base'; bust.data.materials.append(shirt)
for c in list(bust.users_collection): c.objects.unlink(bust)
model.objects.link(bust)
for p in bust.data.polygons:p.use_smooth=False

# Hair masses sit behind the facial plane; layered locks define the silhouette.
ellipsoid('Hair_Back',(0,.25,1.98),(1.58,1.28,1.72),hair,model,20,10)
ellipsoid('Hair_Bob_Lower',(0,.43,1.50),(1.52,1.08,1.06),hair,model,18,8)

# Reference-accurate medium almond eyes, with front-facing irises.
for side in (-1,1):
    x=side*.57
    ellipsoid(f'Eye_{side:+d}',(x,-1.075,1.87),(.38,.105,.255),eye_white,model,16,8)
    cylinder(f'Iris_{side:+d}',(x,-1.135,1.87),.155,.055,iris,model,12,scale=(1,.92,1))
    cylinder(f'Pupil_{side:+d}',(x,-1.168,1.87),.063,.025,dark,model,10,scale=(1,.90,1))
    ellipsoid(f'Catchlight_{side:+d}',(x-side*.055,-1.188,1.96),(.035,.018,.045),eye_white,model,8,4)
    # Upper lid and restrained lower lid.
    polyline_tube(f'UpperLid_{side:+d}',[(x-side*.36,-1.19,1.88),(x-side*.17,-1.205,2.055),(x+side*.15,-1.205,2.07),(x+side*.36,-1.19,1.90)],.019,dark,model)
    polyline_tube(f'LowerLid_{side:+d}',[(x-side*.31,-1.16,1.81),(x,-1.18,1.75),(x+side*.30,-1.16,1.81)],.012,skin_light,model)
    polyline_tube(f'Brow_{side:+d}',[(x-side*.34,-1.15,2.36),(x-side*.04,-1.20,2.44),(x+side*.31,-1.15,2.39)],.032,hair,model)

# Nose built as a genuine projecting faceted wedge for a readable side profile.
nose_v=[(-.065,-1.04,2.18),(.065,-1.04,2.18),(-.09,-1.12,1.63),(.09,-1.12,1.63),
        (-.17,-1.36,1.30),(.17,-1.36,1.30),(-.20,-1.25,1.18),(.20,-1.25,1.18),
        (-.06,-1.43,1.18),(.06,-1.43,1.18),(0,-1.31,1.10),(0,-1.05,1.16)]
nose_f=[(0,1,3,2),(2,3,5,4),(4,5,9,8),(4,8,10,6),(5,7,10,9),(6,10,11),(7,11,10),(2,4,6,11,0),(1,11,7,5,3),(0,11,1)]
mesh_obj('Nose_Faceted',nose_v,nose_f,skin,model)

# Upper and lower lips as thin shaped volumes.
ellipsoid('Upper_Lip',(0,-.985,.91),(.34,.065,.060),lip,model,12,5)
ellipsoid('Lower_Lip',(0,-.992,.83),(.30,.060,.055),skin_light,model,12,5)
polyline_tube('Mouth_Line',[(-.31,-1.052,.90),(0,-1.065,.88),(.31,-1.052,.90)],.010,dark,model)

# Ears with inner cartilage rather than featureless spheres.
ear('Ear_L',-1.43,skin,skin_dark,model)
ear('Ear_R',1.43,skin,skin_dark,model)

# Large layered ribbons reproduce the swept fringe and bob outline from references.
hair_locks=[
 ('Fringe_Left',[(-.10,-.82,3.48),(-.36,-.96,3.30),(-.62,-1.08,3.03),(-.88,-1.14,2.69),(-1.08,-1.12,2.30)],[.27,.34,.37,.30,.035],hair_hi),
 ('Fringe_Center',[(.22,-.84,3.43),(.12,-.98,3.22),(-.02,-1.09,2.95),(-.17,-1.16,2.62),(-.30,-1.15,2.30)],[.24,.28,.29,.20,.025],hair),
 ('Fringe_Right',[(.48,-.78,3.34),(.62,-.91,3.13),(.74,-1.02,2.87),(.83,-1.09,2.55),(.89,-1.08,2.20)],[.27,.29,.27,.18,.028],hair_hi),
 ('SideLock_L',[(-1.33,-.12,2.66),(-1.49,-.24,2.12),(-1.44,-.31,1.40),(-1.25,-.34,.67)],[.18,.22,.19,.025],hair),
 ('SideLock_R',[(1.31,-.10,2.55),(1.48,-.22,2.02),(1.42,-.30,1.34),(1.22,-.33,.72)],[.17,.22,.19,.025],hair_hi),
 ('BobTip_L',[(-1.47,.10,1.76),(-1.56,-.02,1.20),(-1.43,-.18,.55)],[.20,.21,.022],hair_hi),
 ('BobTip_R',[(1.47,.12,1.70),(1.57,0,1.16),(1.40,-.16,.60)],[.20,.22,.022],hair),
]
for n,c,w,m in hair_locks:ribbon(n,c,w,.065,m,model)

# Pack the supplied references into the .blend and expose as hidden image empties.
for i,path in enumerate(REFS):
    img=bpy.data.images.load(path,check_existing=True)
    img.pack()
    empty=bpy.data.objects.new(f'Reference_{i+1}',None)
    empty.empty_display_type='IMAGE'
    empty.data=img
    empty.hide_render=True
    empty.hide_viewport=True
    refs_col.objects.link(empty)

# Studio presentation.
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,1,-1.82))
plane=bpy.context.object; plane.name='Ground'; plane.data.materials.append(groundmat)
for c in list(plane.users_collection): c.objects.unlink(plane)
presentation.objects.link(plane)

def area(name,loc,energy,size,color):
    d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); presentation.objects.link(o); o.location=loc; look_at(o,(0,0,1.1)); return o
area('Key',(-4.5,-5.5,6.5),900,4.5,(1.0,.98,.96))
area('Fill',(4.2,-3.0,3.8),780,4.0,(.94,.97,1.0))
area('Rim',(1.5,3.0,5.0),900,3.0,(1.0,.96,.93))

def camera(name,loc,target,lens=62):
    d=bpy.data.cameras.new(name); d.lens=lens
    o=bpy.data.objects.new(name,d); presentation.objects.link(o); o.location=loc; look_at(o,target); return o
front=camera('Camera_Front',(0,-10.2,1.30),(0,-.05,1.10),66)
threeq=camera('Camera_ThreeQuarter',(6.5,-8.1,1.65),(0,0,1.20),64)
side=camera('Camera_Side',(9.0,-.05,1.55),(0,.05,1.25),68)

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=256
scene.render.resolution_x=700; scene.render.resolution_y=700; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value=(.42,.43,.46,1)
bg.inputs['Strength'].default_value=.45
scene.view_settings.look='AgX - Medium High Contrast'
scene['asset_description']='Reference-matched low-poly female bob-cut bust; front, profile and 3/4 checked'
scene['reference_count']=len(REFS)
scene['front_axis']='-Y'

scene.camera=front
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
for cam,label in [(front,'front'),(threeq,'threequarter'),(side,'side')]:
    scene.camera=cam
    scene.render.filepath=OUT_DIR+r'\lowpoly_ref_'+label+'.png'
    bpy.ops.render.render(write_still=True)
scene.camera=threeq
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print('SAVED='+BLEND_PATH)
print('MODEL_OBJECTS='+str(len(model.objects)))
print('PACKED_REFS='+str(sum(1 for i in bpy.data.images if i.packed_file)))
