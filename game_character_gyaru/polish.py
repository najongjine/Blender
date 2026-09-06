import bpy,os,json,struct,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=r'E:\Blender\game_character_gyaru'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/gyaru_game_character.blend')
scene=bpy.context.scene;rig=bpy.data.objects['Gyaru_Rig'];parts=[o for o in bpy.data.collections['CHARACTER | export'].objects if o.type=='MESH']
shorts=bpy.data.objects['Shorts'];me=shorts.data
denim_faces=[p for p in me.polygons if me.materials[p.material_index].name.startswith('Shorts |')]
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[list(p.vertices) for p in denim_faces],all_triangles=False)
stitch_verts=set()
for p in me.polygons:
    if me.materials[p.material_index].name=='Denim stitching':stitch_verts.update(p.vertices)
for vi in stitch_verts:
    v=me.vertices[vi];co,normal,idx,dist=tree.find_nearest(v.co)
    if co is not None:
        v.co=co+normal*.0015
        # Transfer deformation from garment surface to stitching.
        weights={};face=denim_faces[idx]
        factors=[1/max((co-me.vertices[i].co).length,.0001) for i in face.vertices];total=sum(factors)
        for i,factor in zip(face.vertices,factors):
            for g in me.vertices[i].groups:weights[g.group]=weights.get(g.group,0)+g.weight*factor/total
        for g in list(v.groups):shorts.vertex_groups[g.group].remove([vi])
        chosen=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(w for i,w in chosen)
        for i,w in chosen:shorts.vertex_groups[i].add([vi],w/total,'REPLACE')
me.update()
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data)
verts=[v for v in bm.verts if .48<(body.matrix_world@v.co).z<.65]
for i in range(18):bmesh.ops.smooth_vert(bm,verts=verts,factor=.4,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(body.data);bm.free();body.data.update()
out=ROOT+'/preview';os.makedirs(out,exist_ok=True)
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
bpy.ops.export_scene.gltf(filepath=ROOT+'/exports/gyaru_game_character.glb',export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_force_sampling=True,export_skins=True,export_all_influences=False)
bpy.ops.export_scene.fbx(filepath=ROOT+'/exports/gyaru_game_character.fbx',use_selection=True,object_types={'MESH','ARMATURE'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,add_leaf_bones=False,armature_nodetype='NULL',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/gyaru_game_character.blend')
with open(ROOT+'/asset_report.json') as f:report=json.load(f)
report['max_influences']=max(len(v.groups) for o in parts for v in o.data.vertices)
report['max_weight_sum_error']=max(abs(sum(g.weight for g in v.groups)-1) for o in parts for v in o.data.vertices)
report['polish']='Stitches projected onto garment with transferred weights; thigh surface relaxed.'
for ext in ['glb','fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext=='glb':bpy.ops.import_scene.gltf(filepath=ROOT+'/exports/gyaru_game_character.glb')
    else:bpy.ops.import_scene.fbx(filepath=ROOT+'/exports/gyaru_game_character.fbx')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    assert len(meshes)==8 and len(arms)==1 and len(arms[0].data.bones)==42
    assert all(any(m.type=='ARMATURE' for m in o.modifiers) and len(o.data.uv_layers)>0 for o in meshes)
    assert len(bpy.data.actions)==2
    report[ext+'_final_validation']='PASS: 8 skinned meshes, 42 bones, UVs, 2 animation clips'
with open(ROOT+'/asset_report.json','w') as f:json.dump(report,f,indent=2)
print('FINAL VALIDATION PASS')
