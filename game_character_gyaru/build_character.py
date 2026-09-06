import bpy, math, os, json, time
from mathutils import Vector
from math import sin, cos, pi, exp

ROOT = r'E:\Blender\game_character_gyaru'
BUILD_RENDER=ROOT+'/renders_build_'+str(time.time_ns());os.makedirs(BUILD_RENDER,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
asset=bpy.data.collections.get('Collection'); asset.name='CHARACTER | export'
studio=bpy.data.collections.new('STUDIO | do not export'); bpy.context.scene.collection.children.link(studio)
refs=bpy.data.collections.new('REFERENCES | hidden'); bpy.context.scene.collection.children.link(refs)
parts=[]; rigid={}

def mat(name, color, rough=.65, metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    return m
skin=mat('Skin | warm tan',(.56,.285,.125),.68)
white=mat('Top | ivory cotton',(.91,.92,.89),.82)
denim=mat('Shorts | indigo denim',(.035,.14,.27),.85)
seam=mat('Denim stitching',(.50,.31,.12),.8)
sole=mat('Sneaker soles',(.69,.73,.74),.8)
leather=mat('Sneaker uppers',(.91,.89,.84),.65)
dark=mat('Lashes and pupils',(.018,.009,.014),.6)
brow=mat('Warm brown brows',(.16,.065,.019),.75)
lip=mat('Lips | warm rose',(.49,.12,.095),.6)
eyeWhite=mat('Eye sclera',(.92,.91,.84),.32)
iris=mat('Iris | amber brown',(.24,.075,.018),.3)
irisInner=mat('Iris | honey',(.52,.235,.04),.32)
gold=mat('Gold hardware',(.72,.43,.09),.26,.8)
hair=mat('Hair | blonde to pink texture',(.9,.65,.25),.48)
# Portable UV-driven image: survives FBX and glTF export without procedural nodes.
img=bpy.data.images.new('HairGradient',width=128,height=512,alpha=True)
pixels=[]
for y in range(512):
    t=y/511; f=max(0,min(1,(t-.12)/.70)); f=f*f*(3-2*f)
    lo=(.94,.20,.43); hi=(1,.80,.39)
    for x in range(128):
        streak=1-.045*(.5+.5*sin(x/127*pi*14))
        pixels.extend([((1-f)*lo[k]+f*hi[k])*streak for k in range(3)]+[1])
img.pixels.foreach_set(pixels); img.filepath_raw=ROOT+'/textures/hair_gradient.png'; img.file_format='PNG'; img.save(); img.pack()
nt=hair.node_tree; tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=img
nt.links.new(tex.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])

def move(ob,coll=asset):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll.objects.link(ob)
def finish(ob,name,m,bone=None):
    ob.name=name; move(ob); ob.data.materials.append(m)
    for p in ob.data.polygons:p.use_smooth=True
    parts.append(ob)
    if bone:rigid[name]=bone
    return ob
def mesh(name,vs,fs,m,bone=None):
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],fs); me.update()
    ob=bpy.data.objects.new(name,me); asset.objects.link(ob)
    return finish(ob,name,m,bone)
def apply(ob,mod):
    bpy.context.view_layer.objects.active=ob; bpy.ops.object.modifier_apply(modifier=mod.name)
def smooth(ob,levels=1):
    m=ob.modifiers.new('Surface subdivision','SUBSURF');m.levels=levels;apply(ob,m)
def uv(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.018)
    bpy.ops.object.mode_set(mode='OBJECT')
def ell(name,loc,scale,m,bone=None,seg=24,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,m,bone)
def tube(name,points,radii,m,bone=None,n=12):
    vs=[]
    for i,co in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        tangent.normalize(); u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
        r=radii[i];rx,ry=(r,r) if isinstance(r,(int,float)) else r
        for j in range(n):vs.append(Vector(co)+rx*cos(j*2*pi/n)*u+ry*sin(j*2*pi/n)*v)
    fs=[]
    for i in range(len(points)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs.extend([tuple(reversed(range(n))),tuple((len(points)-1)*n+j for j in range(n))])
    return mesh(name,vs,fs,m,bone)
def curve(name,pts,r,m,bone=None):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=8;cu.bevel_depth=r;cu.bevel_resolution=2
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu);asset.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object,name,m,bone)
def rings(name,rows,m,n=32,bone=None,cap=True):
    vs=[]
    for z,rx,ry,cy in rows:
        for j in range(n):a=j*2*pi/n;vs.append((rx*sin(a),cy-ry*cos(a),z))
    fs=[]
    for k in range(len(rows)-1):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    if cap:fs.extend([tuple(reversed(range(n))),tuple((len(rows)-1)*n+j for j in range(n))])
    return mesh(name,vs,fs,m,bone)

# Organic continuous skin mesh, with real individual fingers and joint loops.
bodyPieces=[]
bodyPieces.append(rings('Torso_base',[(.65,.125,.085,.01),(.72,.19,.125,.012),(.79,.18,.105,.005),(.86,.135,.084,0),(.93,.16,.092,0),(1.01,.19,.105,0),(1.07,.213,.085,0),(1.10,.185,.071,0),(1.13,.07,.056,0),(1.21,.06,.051,0)],skin))
for s,side in [(1,'L'),(-1,'R')]:
    bodyPieces.append(ell('Shoulder_'+side,(s*.205,0,1.065),(.072,.067,.072),skin))
    bodyPieces.append(tube('Arm_'+side,[(s*.204,0,1.075),(s*.264,0,1.005),(s*.33,-.006,.923),(s*.344,-.011,.901),(s*.36,-.008,.87),(s*.40,0,.795),(s*.425,0,.752)],[(.061,.059),(.056,.056),(.042,.043),(.040,.042),(.044,.043),(.034,.032),(.026,.025)],skin,n=16))
    bodyPieces.append(ell('Palm_'+side,(s*.444,-.001,.715),(.033,.023,.047),skin,seg=16,rings=12))
    for f in range(4):
        x=s*(.422+f*.014); z=.692+abs(f-1.3)*.004; length=[.041,.052,.049,.037][f]
        bodyPieces.append(tube('Finger_'+side+str(f),[(x,-.003,z),(x+s*.007,-.005,z-length*.5),(x+s*.01,-.009,z-length)], [.0065,.0055,.004],skin,n=8))
    bodyPieces.append(tube('Thumb_'+side,[(s*.426,-.005,.735),(s*.403,-.012,.709),(s*.399,-.02,.69)],[.012,.01,.007],skin,n=10))
    bodyPieces.append(ell('Hip_'+side,(s*.105,.025,.713),(.115,.12,.12),skin))
    bodyPieces.append(tube('Leg_'+side,[(s*.112,.008,.73),(s*.118,0,.66),(s*.12,-.012,.55),(s*.12,-.025,.427),(s*.12,-.032,.399),(s*.12,-.027,.371),(s*.12,.002,.295),(s*.12,.015,.231),(s*.12,.013,.14),(s*.12,0,.099)],[(.105,.103),(.1,.098),(.083,.081),(.056,.057),(.054,.056),(.055,.054),(.067,.065),(.061,.059),(.037,.041),(.033,.037)],skin,n=20))
bpy.ops.object.select_all(action='DESELECT')
for o in bodyPieces:o.select_set(True)
bpy.context.view_layer.objects.active=bodyPieces[0];bpy.ops.object.join();body=bodyPieces[0];body.name='Body_skin'
parts=[o for o in asset.objects if o.type=='MESH']
rem=body.modifiers.new('Unified anatomy','REMESH');rem.mode='VOXEL';rem.voxel_size=.0045;rem.use_smooth_shade=True;apply(body,rem)
sm=body.modifiers.new('Relax skin','SMOOTH');sm.factor=.65;sm.iterations=4;apply(body,sm)
dc=body.modifiers.new('Game mesh reduction','DECIMATE');dc.ratio=.24;apply(body,dc)

# Shaped head rings: large cranium, tapered jaw, flattened face and rounded cheeks.
rows=[(1.184,.018,.026,-.044),(1.198,.060,.067,-.017),(1.23,.103,.093,-.004),(1.27,.143,.111,.008),(1.31,.163,.122,.012),(1.36,.168,.125,.015),(1.41,.168,.124,.017),(1.46,.155,.117,.02),(1.51,.13,.103,.024),(1.55,.088,.073,.026),(1.572,.024,.027,.027)]
head=rings('Head',rows,skin,n=40,bone='head');smooth(head,2)
# Low-relief sculpted facial features, designed for actual side silhouette.
nose=ell('Nose',(0,-.119,1.297),(.020,.029,.025),skin,'head',24,16)
ell('Nose_bridge',(0,-.109,1.323),(.014,.016,.035),skin,'head',20,12)
for s,side in [(1,'L'),(-1,'R')]:
    ell('Ear_'+side,(s*.161,.004,1.292),(.025,.017,.045),skin,'head')
    ell('Ear_inner_'+side,(s*.177,-.010,1.295),(.010,.005,.024),lip,'head',16,12)
    x=s*.073
    ell('Eye_white_'+side,(x,-.105,1.355),(.052,.023,.032),eyeWhite,'head',32,20)
    ell('Iris_rim_'+side,(x,-.127,1.355),(.024,.005,.027),brow,'head')
    ell('Iris_'+side,(x,-.130,1.354),(.020,.003,.023),irisInner,'head')
    ell('Pupil_'+side,(x,-.133,1.358),(.011,.002,.017),dark,'head')
    ell('Eye_glint_'+side,(x-.007,-.136,1.369),(.006,.0015,.007),eyeWhite,'head',12,8)
    curve('Upper_lash_'+side,[(x-s*.052,-.112,1.355),(x-s*.03,-.124,1.381),(x,-.129,1.387),(x+s*.031,-.122,1.379),(x+s*.057,-.108,1.361)],.004,dark,'head')
    curve('Lower_lid_'+side,[(x-s*.047,-.111,1.35),(x,-.125,1.325),(x+s*.049,-.11,1.35)],.0025,skin,'head')
    for k in range(2):curve('Lash_tip_'+side+str(k),[(x+s*(.04+k*.007),-.117,1.373-k*.007),(x+s*(.059+k*.006),-.113,1.378-k*.005)],.0024,dark,'head')
    curve('Eyebrow_'+side,[(s*.033,-.105,1.416),(s*.072,-.111,1.426),(s*.113,-.093,1.412)],.006,brow,'head')
    bpy.ops.mesh.primitive_torus_add(major_radius=.019,minor_radius=.0035,major_segments=24,minor_segments=8,location=(s*.174,-.006,1.248),rotation=(pi/2,0,0))
    finish(bpy.context.object,'Earring_'+side,gold,'head')
curve('Upper_lip',[(-.036,-.095,1.246),(-.014,-.11,1.25),(0,-.112,1.247),(.014,-.11,1.25),(.036,-.095,1.246)],.005,lip,'head')
curve('Lower_lip',[(-.033,-.095,1.243),(0,-.111,1.234),(.033,-.095,1.243)],.0055,lip,'head')
curve('Mouth_line',[(-.031,-.099,1.244),(0,-.116,1.243),(.031,-.099,1.244)],.0015,brow,'head')

# Tank top lower shell with paired front fullness, and separate shoulder straps.
top=rings('Tank_top',[(.847,.139,.088,0),(.856,.14,.089,0),(.89,.147,.091,-.002),(.94,.174,.114,-.015),(.979,.190,.127,-.027),(1.013,.197,.12,-.019),(1.042,.186,.1,-.004)],white,cap=False)
smooth(top,2)
sol=top.modifiers.new('Cotton thickness','SOLIDIFY');sol.thickness=.003;apply(top,sol)
# Front and back yoke, armpit gaps left open.
for back in [False,True]:
    vs=[];fs=[]; nx=20;ny=5
    for j in range(ny):
        t=j/(ny-1)
        for i in range(nx+1):
            x=-.198+.396*i/nx; a=abs(x)/.198
            ztop=1.14-(.054 if not back else .025)*exp(-(x/.075)**4)
            z=1.039*(1-t)+ztop*t
            ybase=(.091 if back else -.104)*math.sqrt(max(.08,1-(x/.197)**2))
            ytop=(.075 if back else -.082)*(1-.25*a)
            y=ybase*(1-t)+ytop*t
            vs.append((x,y,z))
    for j in range(ny-1):
        for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
    o=mesh('Tank_yoke_'+str(back),vs,fs,white);smooth(o,1)
    sol=o.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.003;apply(o,sol)
for s,side in [(1,'L'),(-1,'R')]:
    strap=mesh('Shoulder_strap_'+side,[(s*.105,-.071,1.14),(s*.198,-.061,1.14),(s*.198,.056,1.14),(s*.105,.065,1.14)],[(0,1,2,3)],white)
    sol=strap.modifiers.new('Strap thickness','SOLIDIFY');sol.thickness=.004;apply(strap,sol)
curve('Top_hem',[(.14*sin(i*2*pi/48),-.09*cos(i*2*pi/48),.857) for i in range(49)],.002,white)

# Closed shorts: joined hips and legs, hollowed at waist and hems after union.
shortpieces=[ell('Shorts_hip',(0,.015,.746),(.205,.132,.128),denim,seg=32,rings=20)]
for s,side in [(1,'L'),(-1,'R')]:
    shortpieces.append(ell('Shorts_leg_'+side,(s*.108,.009,.675),(.108,.112,.116),denim))
bpy.ops.object.select_all(action='DESELECT')
for o in shortpieces:o.select_set(True)
bpy.context.view_layer.objects.active=shortpieces[0];bpy.ops.object.join();shorts=shortpieces[0];shorts.name='Denim_shorts'
parts=[o for o in asset.objects if o.type=='MESH']
rem=shorts.modifiers.new('Tailored joined shorts','REMESH');rem.mode='VOXEL';rem.voxel_size=.005;rem.use_smooth_shade=True;apply(shorts,rem)
# Trim top and bottom flat with bmesh bisect, preserving an open garment surface.
import bmesh
bm=bmesh.new();bm.from_mesh(shorts.data)
for h,normal in [(.836,(0,0,1)),(.632,(0,0,-1))]:
    local=shorts.matrix_world.inverted()@Vector((0,0,h))
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=local,plane_no=normal,clear_outer=True,clear_inner=False)
bm.to_mesh(shorts.data);bm.free()
dc=shorts.modifiers.new('Shorts optimization','DECIMATE');dc.ratio=.4;apply(shorts,dc)
sm=shorts.modifiers.new('Smooth denim','SMOOTH');sm.factor=.5;sm.iterations=3;apply(shorts,sm)
for s,side in [(1,'L'),(-1,'R')]:
    curve('Shorts_cuff_'+side,[(s*.108+.10*sin(i*2*pi/40),.009-.107*cos(i*2*pi/40),.637) for i in range(41)],.006,denim)
    curve('Cuff_stitch_'+side,[(s*.108+.10*sin(i*2*pi/40),.009-.108*cos(i*2*pi/40),.647) for i in range(41)],.0012,seam)
    curve('Front_pocket_'+side,[(s*.15,-.086,.823),(s*.145,-.108,.787),(s*.185,-.084,.767)],.0017,seam)
    curve('Back_pocket_'+side,[(s*.05,.142,.78),(s*.15,.119,.78),(s*.145,.126,.716),(s*.104,.149,.699),(s*.056,.149,.718),(s*.05,.142,.78)],.0018,seam)
    curve('Side_seam_'+side,[(s*.19,.006,.811),(s*.211,.01,.73),(s*.207,.01,.65)],.0014,seam)
curve('Waistband_stitch',[(.16*sin(i*2*pi/48),.015-.098*cos(i*2*pi/48),.827) for i in range(49)],.002,seam)
curve('Fly_seam',[(0,-.086,.829),(0,-.111,.793),(0,-.113,.751)],.0016,seam)
ell('Waist_button',(0,-.091,.822),(.007,.003,.007),gold,'pelvis',16,8)

for s,side in [(1,'L'),(-1,'R')]:
    ell('Sneaker_sole_'+side,(s*.12,-.032,.032),(.055,.107,.027),sole,'foot.'+side)
    ell('Sneaker_upper_'+side,(s*.12,-.025,.065),(.052,.099,.044),leather,'foot.'+side)
    ell('Sneaker_collar_'+side,(s*.12,.016,.095),(.039,.047,.032),leather,'foot.'+side)
    for k in range(4):
        y=-.018-k*.016;z=.101-k*.006
        curve('Lace_'+side+str(k),[(s*.12-.022,y,z),(s*.12,y-.003,z+.004),(s*.12+.022,y,z)],.0023,eyeWhite,'foot.'+side)
    curve('Sole_seam_'+side,[(s*.12+.053*sin(i*2*pi/40),-.032-.102*cos(i*2*pi/40),.043) for i in range(41)],.0013,white,'foot.'+side)

# Hair cap with open face; layered curved solid locks (not a solid helmet).
vs=[];fs=[];n=48;nr=13
for k in range(nr):
    t=k/(nr-1)
    for j in range(n):
        a=j*2*pi/n;front=max(0,cos(a));end=2.00-.98*(front**4)
        theta=.035+t*end
        vs.append((.18*sin(theta)*sin(a),.027-.145*sin(theta)*cos(a),1.391+.202*cos(theta)))
for k in range(nr-1):
    for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
cap=mesh('Hair_cap',vs,fs,hair,'head');smooth(cap,1)
sol=cap.modifiers.new('Cap thickness','SOLIDIFY');sol.thickness=.008;apply(cap,sol)
def lock(name,pts,widths):
    o=tube(name,pts,[(w,w*.33) for w in widths],hair,'head',n=8);smooth(o,2);return o
for j in range(13):
    a=.82+j*(2*pi-1.64)/12
    pts=[]
    for k in range(7):
        t=k/6; ang=a+.09*sin(t*pi*2+j*.7)
        r=.155+.026*sin(t*pi)+.009*cos(j*2+t*8)
        pts.append((r*sin(ang),.031-r*.80*cos(ang),1.475-.325*t))
    lock('Hair_wave_%02d'%j,pts,[.023,.034,.036,.031,.033,.026,.0015])
lock('Fringe_sweep_R',[(-.045,-.04,1.588),(.018,-.105,1.567),(.079,-.139,1.522),(.127,-.14,1.46),(.168,-.119,1.39),(.177,-.10,1.327)],[.025,.038,.04,.035,.027,.002])
lock('Fringe_sweep_L',[(-.055,-.04,1.583),(-.097,-.103,1.545),(-.131,-.132,1.49),(-.154,-.129,1.419),(-.169,-.109,1.36)],[.025,.031,.028,.021,.002])
for s,side in [(1,'L'),(-1,'R')]:
    lock('Face_frame_'+side,[(s*.15,-.065,1.47),(s*.181,-.078,1.394),(s*.182,-.071,1.31),(s*.17,-.057,1.25),(s*.195,-.031,1.192),(s*.176,-.028,1.163)],[.02,.025,.026,.029,.022,.0015])

# Replace the temporary panel construction with one continuous tank-top surface.
for ob in list(asset.objects):
    if ob.name.startswith(('Tank_','Shoulder_strap_')):bpy.data.objects.remove(ob,do_unlink=True)
rows=[(.849,.145,.093,0),(.858,.145,.093,0),(.90,.154,.101,-.003),(.949,.182,.123,-.014),(.99,.200,.129,-.019),(1.035,.202,.112,-.006),(1.095,.225,.086,0),(1.136,.067,.062,0)]
vs=[];fs=[];n=48
for k,(z,rx,ry,cy) in enumerate(rows):
    for j in range(n):
        a=j*2*pi/n;zz=z
        if k==6:zz+=.045*sin(a)**4
        if k==7:zz-=.047*max(0,cos(a))**2
        vs.append((rx*sin(a),cy-ry*cos(a),zz))
for k in range(len(rows)-1):
    for j in range(n):
        a=(j+.5)*2*pi/n
        if k==5 and abs(sin(a))>.80:continue
        v=k*n+j;w=k*n+(j+1)%n;fs.append((v,w,w+n,v+n))
top=mesh('Tank_top',vs,fs,white);smooth(top,2)
sol=top.modifiers.new('Cotton shell','SOLIDIFY');sol.thickness=.003;apply(top,sol)
# Reduce the covered skin volume continuously: retain clean garment edges.
for v in body.data.vertices:
    p=body.matrix_world@v.co
    if .59<p.z<.857 and abs(p.x)<.235:
        f=min(1,(p.z-.59)/.035,(.857-p.z)/.022);f=f*f*(3-2*f)
        p.x*=1-.16*f;p.y*=1-.19*f
        v.co=body.matrix_world.inverted()@p
    elif .857<p.z<1.047 and abs(p.x)<.19:
        p.x*=.96;p.y*=.90;v.co=body.matrix_world.inverted()@p
sm=body.modifiers.new('Final skin relaxation','SMOOTH');sm.factor=.65;sm.iterations=7;apply(body,sm)
# All materials use exportable principled values; every mesh receives UVs.
parts=[o for o in asset.objects if o.type=='MESH']
for o in parts:
    if len(o.data.polygons)>450 and o!=body:
        dec=o.modifiers.new('Game triangle budget','DECIMATE');dec.ratio=.28;apply(o,dec)
    uv(o)
    if o.data.materials[0]==hair:
        layer=o.data.uv_layers.active
        for p in o.data.polygons:
            for li in p.loop_indices:
                co=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
                layer.data[li].uv=((math.atan2(co.x,co.y-.025)/(2*pi))%1,max(0,min(1,(co.z-1.15)/.445)))

# Engine-friendly deform skeleton, root at ground, A pose. Names are custom.
armdata=bpy.data.armatures.new('Gyaru_skeleton');rig=bpy.data.objects.new('Gyaru_Rig',armdata);asset.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
bones={}
def bone(name,h,t,parent=None):
    b=armdata.edit_bones.new(name);b.head=h;b.tail=t
    if parent:b.parent=armdata.edit_bones[parent]
    bones[name]=(Vector(h),Vector(t));return b
bone('root',(0,0,0),(0,0,.16))
bone('pelvis',(0,0,.68),(0,0,.80),'root')
bone('spine',(0,0,.80),(0,0,.95),'pelvis')
bone('chest',(0,0,.95),(0,0,1.105),'spine')
bone('neck',(0,0,1.105),(0,0,1.218),'chest')
bone('head',(0,0,1.218),(0,0,1.53),'neck')
for s,side in [(1,'L'),(-1,'R')]:
    bone('clavicle.'+side,(0,0,1.077),(s*.21,0,1.075),'chest')
    bone('upper_arm.'+side,(s*.21,0,1.075),(s*.34,-.01,.91),'clavicle.'+side)
    bone('forearm.'+side,(s*.34,-.01,.91),(s*.425,0,.754),'upper_arm.'+side)
    bone('hand.'+side,(s*.425,0,.754),(s*.451,-.002,.695),'forearm.'+side)
    for f in range(4):
        x=s*(.422+f*.014);z=.692+abs(f-1.3)*.004;length=[.041,.052,.049,.037][f]
        bone('finger%d.01.'%f+side,(x,-.003,z),(x+s*.007,-.005,z-length*.5),'hand.'+side)
        bone('finger%d.02.'%f+side,(x+s*.007,-.005,z-length*.5),(x+s*.01,-.009,z-length),'finger%d.01.'%f+side)
    bone('thumb.01.'+side,(s*.426,-.005,.735),(s*.403,-.012,.709),'hand.'+side)
    bone('thumb.02.'+side,(s*.403,-.012,.709),(s*.399,-.02,.69),'thumb.01.'+side)
    bone('thigh.'+side,(s*.11,0,.73),(s*.12,-.032,.40),'pelvis')
    bone('shin.'+side,(s*.12,-.032,.40),(s*.12,0,.105),'thigh.'+side)
    bone('foot.'+side,(s*.12,0,.105),(s*.12,-.09,.045),'shin.'+side)
    bone('toe.'+side,(s*.12,-.09,.045),(s*.12,-.135,.042),'foot.'+side)
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True;rig.display_type='WIRE'
def distance(p,a,b):
    d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-(a+t*d)).length
def candidates(p):
    side='L' if p.x>=0 else 'R'
    if abs(p.x)>.385 and p.z<.77 and p.z>.62:
        return ['hand.'+side,'forearm.'+side]+[n for n in bones if (n.startswith('finger') or n.startswith('thumb')) and n.endswith(side)]
    if abs(p.x)>.215 and p.z>.70:return ['clavicle.'+side,'upper_arm.'+side,'forearm.'+side,'hand.'+side,'chest']
    if p.z<.70:return ['thigh.'+side,'shin.'+side,'foot.'+side,'pelvis']
    if p.z<.84:return ['pelvis','spine','thigh.'+side]
    if p.z>1.13:return ['neck','head','chest']
    return ['pelvis','spine','chest','neck','clavicle.'+side]
for o in parts:
    forced=rigid.get(o.name)
    if forced:
        g=o.vertex_groups.new(name=forced);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
    else:
        groups={n:o.vertex_groups.new(name=n) for n in bones if n!='root'}
        for v in o.data.vertices:
            p=o.matrix_world@v.co; ds=sorted([(distance(p,*bones[n]),n) for n in candidates(p)])[:4]
            # Exponential compact weights keep a maximum of four influences.
            sharp=85 if abs(p.x)>.39 else 43
            vals=[exp(-(d-ds[0][0])*sharp) for d,n in ds];total=sum(vals)
            for (d,n),w in zip(ds,vals):groups[n].add([v.index],w/total,'REPLACE')
    mod=o.modifiers.new('Armature deformation','ARMATURE');mod.object=rig;o.parent=rig
    o['asset_role']='skinned game mesh';o['max_bone_influences']=4

# Two short demonstration clips, useful for checking deformation after import.
rig.animation_data_create()
def reset_pose():
    for p in rig.pose.bones:p.rotation_mode='XYZ';p.rotation_euler=(0,0,0);p.location=(0,0,0)
def key_all(frame):
    for p in rig.pose.bones:p.keyframe_insert(data_path='rotation_euler',frame=frame,group=p.name)
for actionname in ['Idle','Rig_Check']:
    act=bpy.data.actions.new(actionname);rig.animation_data.action=act;act.use_fake_user=True
    for f in [1,16,31]:
        reset_pose()
        if f==16:
            if actionname=='Idle':
                rig.pose.bones['chest'].rotation_euler.x=.025;rig.pose.bones['head'].rotation_euler.z=.025
            else:
                rig.pose.bones['upper_arm.L'].rotation_euler.y=-.4
                rig.pose.bones['forearm.L'].rotation_euler.x=-.7
                rig.pose.bones['thigh.R'].rotation_euler.x=-.30
                rig.pose.bones['shin.R'].rotation_euler.x=.58
        key_all(f)
    track=rig.animation_data.nla_tracks.new();track.name=actionname;track.strips.new(actionname,1,act);track.mute=True
rig.animation_data.action=None;reset_pose()

# Reference images embedded in the authoring file, excluded from exports.
for label in ['front','side','back','three_quarter']:
    im=bpy.data.images.load('E:/Blender/references/gyaru_20260905/'+label+'.png');im.pack()
    ob=bpy.data.objects.new('Reference_'+label,None);refs.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=im;ob.empty_display_size=1.8;ob.hide_render=True;ob.hide_viewport=True
refs.hide_viewport=True;refs.hide_render=True

scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.fps=30;scene.frame_start=1;scene.frame_end=31;scene.frame_set(1)
scene['README']='1 unit = 1 meter. -Y front, Z up. Custom deform skeleton; retarget required for Unreal mannequin. See README.md. No collision or physics assets included.'
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def camera(name,loc):
    d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=1.86
    o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;aim(o,(0,0,.80));return o
cams=[camera('Front',(0,-4,.83)),camera('Side',(4,0,.83)),camera('Back',(0,4,.83)),camera('ThreeQuarter',(3,-4,1.3))]
for name,loc,power,size in [('Key',(-3,-4,5),450,4),('Fill',(3,-2,2.5),220,3),('Rim',(0,3,3),350,3)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;aim(o,(0,0,.9))
ground=mat('Studio ground',(.10,.13,.17),.9)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.001));o=bpy.context.object;o.name='Studio_ground';move(o,studio);o.data.materials.append(ground)
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.21,.28,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.render.engine='BLENDER_EEVEE';scene.eevee.use_gtao=True;scene.eevee.gtao_distance=.12;scene.eevee.gtao_factor=1.1;scene.eevee.taa_render_samples=96
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.camera=cams[3]
# Useful initial viewport, material colors, rig hidden from silhouette until selected.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=2.5;area.spaces.active.region_3d.view_location=Vector((0,0,.83));area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
blend=ROOT+'/gyaru_game_character.blend';bpy.ops.wm.save_as_mainfile(filepath=blend)
for cam in cams:
    scene.camera=cam;scene.render.filepath=BUILD_RENDER+'/'+cam.name.lower()+'.png';bpy.ops.render.render(write_still=True)
scene.camera=cams[3]
# Export only skinned character objects and rig, no studio or reference images.
bpy.ops.object.select_all(action='DESELECT')
for o in parts+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=ROOT+'/exports/gyaru_game_character.glb',export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_force_sampling=True,export_skins=True,export_all_influences=False)
bpy.ops.export_scene.fbx(filepath=ROOT+'/exports/gyaru_game_character.fbx',use_selection=True,object_types={'MESH','ARMATURE'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,add_leaf_bones=False,armature_nodetype='NULL',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True)
stats={'mesh_objects':len(parts),'vertices':sum(len(o.data.vertices) for o in parts),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts),'bones':len(rig.data.bones),'materials':len(set(m.name for o in parts for m in o.data.materials)),'height_m':max((o.matrix_world@v.co).z for o in parts for v in o.data.vertices),'animations':['Idle','Rig_Check'],'validation':{}}
stats['validation']['uv_all_meshes']=all(len(o.data.uv_layers)>0 for o in parts)
stats['validation']['all_vertices_weighted']=all(len(v.groups)>0 for o in parts for v in o.data.vertices)
stats['validation']['max_influences']=max(len(v.groups) for o in parts for v in o.data.vertices)
stats['validation']['max_weight_sum_error']=max(abs(sum(g.weight for g in v.groups)-1) for o in parts for v in o.data.vertices)
with open(ROOT+'/asset_report.json','w') as f:json.dump(stats,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=blend)
print('ASSET_REPORT',json.dumps(stats))


