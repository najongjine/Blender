import bpy,os,json,math,struct,time
from mathutils import Vector
ROOT=r'E:\Blender\game_character_gyaru'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/gyaru_game_character.blend')
scene=bpy.context.scene;asset=bpy.data.collections['CHARACTER | export'];rig=bpy.data.objects['Gyaru_Rig']
out=ROOT+'/renders_final';os.makedirs(out,exist_ok=True)
parts=[o for o in asset.objects if o.type=='MESH']
def apply(ob,mod):
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
for o in parts:
    if o.name=='Tank_top':
        for v in o.data.vertices:
            p=o.matrix_world@v.co
            if p.z>1.105 and abs(p.x)>.105:
                t=min(1,(abs(p.x)-.105)/.10);p.z-=.015*t;p.x*=1-.045*t;v.co=o.matrix_world.inverted()@p
    ratio=.38 if o.name=='Body_skin' else (.35 if o.name=='Tank_top' else (.18 if any(w in o.name.lower() for w in ['seam','stitch','cuff','hem']) else 1))
    if ratio<1:
        mod=o.modifiers.new('Final polygon budget','DECIMATE');mod.ratio=ratio
        # Put decimation before deformation.
        while o.modifiers.find(mod.name)>0:bpy.ops.object.modifier_move_up({'object':o},modifier=mod.name)
        apply(o,mod)
    for p in o.data.polygons:p.use_smooth=True
    # Prune tiny weights then normalize to a maximum of four influences.
    for v in o.data.vertices:
        weights=sorted([(g.weight,g.group) for g in v.groups],reverse=True)[:4];total=sum(w for w,i in weights)
        for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
        for w,i in weights:
            if total:o.vertex_groups[i].add([v.index],w/total,'REPLACE')

# Keep logical editing parts but avoid dozens of separate engine meshes.
groups={}
for o in parts:
    n=o.name
    if n.startswith(('Hair','Fringe','Face_frame')):cat='Hair'
    elif n.startswith(('Eye','Iris','Pupil','Upper_lash','Lower_lid','Lash_tip','Eyebrow')):cat='Eyes_and_brows'
    elif n.startswith(('Sneaker','Lace','Sole')):cat='Footwear'
    elif n.startswith(('Denim','Shorts','Cuff','Front_pocket','Back_pocket','Side_seam','Waistband','Fly','Waist_button')):cat='Shorts'
    elif n.startswith(('Tank','Top_')):cat='Top'
    elif n.startswith('Earring'):cat='Accessories'
    elif n=='Body_skin':cat='Body'
    else:cat='Face'
    groups.setdefault(cat,[]).append(o)
for cat,obs in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    if len(obs)>1:bpy.ops.object.join()
    obs[0].name=cat
parts=[o for o in asset.objects if o.type=='MESH']
rig.animation_data.action=None
for tr in rig.animation_data.nla_tracks:tr.mute=True
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
scene.frame_set(1)
scene.render.resolution_x=900;scene.render.resolution_y=1000
for label in ['Front','Side','Back','ThreeQuarter']:
    scene.camera=bpy.data.objects[label];scene.render.filepath=out+'/'+label.lower()+'.png';bpy.ops.render.render(write_still=True)
rig.animation_data.action=bpy.data.actions['Rig_Check'];scene.frame_set(16)
scene.camera=bpy.data.objects['ThreeQuarter'];scene.render.filepath=out+'/rig_check.png';bpy.ops.render.render(write_still=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for o in parts+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
# glTF exporter combines matching NLA track names into named clips.
bpy.ops.export_scene.gltf(filepath=ROOT+'/exports/gyaru_game_character.glb',export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_force_sampling=True,export_skins=True,export_all_influences=False)
bpy.ops.export_scene.fbx(filepath=ROOT+'/exports/gyaru_game_character.fbx',use_selection=True,object_types={'MESH','ARMATURE'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,add_leaf_bones=False,armature_nodetype='NULL',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True)
report={'mesh_objects':len(parts),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts),'vertices':sum(len(o.data.vertices) for o in parts),'bones':len(rig.data.bones),'height_m':max((o.matrix_world@v.co).z for o in parts for v in o.data.vertices),'uv_all_meshes':all(len(o.data.uv_layers)>0 for o in parts),'max_influences':max(len(v.groups) for o in parts for v in o.data.vertices),'all_vertices_weighted':all(len(v.groups)>0 for o in parts for v in o.data.vertices),'max_weight_sum_error':max(abs(sum(g.weight for g in v.groups)-1) for o in parts for v in o.data.vertices)}
with open(ROOT+'/exports/gyaru_game_character.glb','rb') as f:
    raw=f.read();length,typ=struct.unpack('<II',raw[12:20]);gltf=json.loads(raw[20:20+length])
report['glb']={'animations':[a.get('name') for a in gltf.get('animations',[])],'skins':len(gltf.get('skins',[])),'meshes':len(gltf.get('meshes',[])),'materials':len(gltf.get('materials',[])),'embedded_images':len(gltf.get('images',[]))}
# Set authoring file to a clear front 3/4 view, without studio light overlays.
from mathutils import Quaternion
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.region_3d.view_distance=2.6;sp.region_3d.view_location=Vector((0,0,.83));sp.region_3d.view_rotation=bpy.data.objects['ThreeQuarter'].rotation_euler.to_quaternion();sp.shading.type='MATERIAL';sp.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/gyaru_game_character.blend')
# Verify actual exported files in clean scenes, including action presence and size.
for extension in ['glb','fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if extension=='glb':bpy.ops.import_scene.gltf(filepath=ROOT+'/exports/gyaru_game_character.glb')
    else:bpy.ops.import_scene.fbx(filepath=ROOT+'/exports/gyaru_game_character.fbx')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    report[extension+'_reimport']={'meshes':len(meshes),'armatures':len(arms),'bones':[len(o.data.bones) for o in arms],'actions':[a.name for a in bpy.data.actions],'height':max(p.z for p in coords)-min(p.z for p in coords),'all_uv':all(len(o.data.uv_layers)>0 for o in meshes),'skinned_meshes':sum(any(m.type=='ARMATURE' for m in o.modifiers) for o in meshes)}
    assert len(arms)==1 and len(meshes)==len(parts) and all(len(o.data.uv_layers)>0 for o in meshes)
with open(ROOT+'/asset_report.json','w') as f:json.dump(report,f,indent=2)
print('FINAL_REPORT',json.dumps(report))
