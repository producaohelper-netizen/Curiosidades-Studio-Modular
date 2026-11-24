import bpy, math, random, os
from mathutils import Vector
from pathlib import Path
random.seed(42)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=720
sc.render.resolution_y=1280
sc.render.resolution_percentage=100
sc.render.fps=30
sc.frame_start=1
sc.frame_end=540
sc.world=bpy.data.worlds.new("Space")
sc.world.color=(0,0,0)
def mat(name,color,power):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;n.clear()
    e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(*color,1);e.inputs[1].default_value=power
    o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],o.inputs[0]);return m
black=mat("Event horizon",(0,0,0),0)
gold=mat("Hot plasma",(1,.23,.025),5)
white=mat("Hot inner ring",(1,.75,.35),8)
red=mat("Cool plasma",(.9,.06,.005),2)
blue=mat("Stars",(.5,.7,1),3)
def sphere(name,r,loc,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=r,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(m);return o
sphere("Black hole",1,(0,0,0),black)
def curve(name,pts,thick,m):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=thick;c.bevel_resolution=1
    s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);sc.collection.objects.link(o);o.data.materials.append(m);return o
disk=bpy.data.objects.new("Accretion disk",None);sc.collection.objects.link(disk)
for k in range(220):
    r=random.uniform(1.12,4.4);a=random.uniform(0,6.28);length=random.uniform(.15,2.8)
    pts=[]
    for j in range(65):
        u=j/64;th=a+u*length;rr=r*(1-.12*u)
        pts.append((rr*math.cos(th),rr*math.sin(th),.035*math.sin(th*9+k)+random.uniform(-.025,.025)))
    o=curve("Plasma filament",pts,random.uniform(.006,.025),white if r<1.5 else gold if r<2.8 else red);o.parent=disk
# stylized lensed photon arcs, not ray-traced relativity
for k in range(12):
    r=1.03+k*.018
    curve("Photon arc",[(r*math.cos(a),0,r*math.sin(a)) for a in [j*math.pi/100 for j in range(201)]],.009,white if k<4 else gold)
# mesh starfield with small triangular emitters
verts=[];faces=[]
for k in range(6500):
    v=Vector((random.gauss(0,1),random.gauss(0,1),random.gauss(0,1))).normalized()*45
    d=random.uniform(.015,.065);i=len(verts)
    verts.extend([v+Vector((d,0,0)),v+Vector((0,d,0)),v+Vector((0,0,d))]);faces.append((i,i+1,i+2))
mesh=bpy.data.meshes.new("Star mesh");mesh.from_pydata(verts,[],faces);mesh.materials.append(blue)
o=bpy.data.objects.new("Deep space",mesh);sc.collection.objects.link(o)
# distant spiral galaxies
for k in range(9):
    cx=random.uniform(-15,15);cy=random.uniform(10,25);cz=random.uniform(-14,14)
    for arm in range(3):
        pts=[(cx+.025*j*math.cos(j*.065+arm*2.094),cy+.15*math.sin(j*.08),cz+.025*j*math.sin(j*.065+arm*2.094)) for j in range(100)]
        curve("Primordial galaxy",pts,.035,blue)
bpy.ops.object.camera_add()
cam=bpy.context.object;sc.camera=cam;cam.data.lens=36;cam.data.clip_end=100
for f,loc,target in [(1,(0,-12,4),(0,0,0)),(31,(0,-7,2.6),(0,0,0)),(91,(3,-11,4),(0,0,0)),(211,(8,-24,9),(0,5,0)),(270,(5,-22,8),(3,12,3)),(331,(0,-12,4),(0,0,0)),(451,(-2,-7,2.5),(0,0,0)),(540,(0,-12,4),(0,0,0))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f)
disk.rotation_euler.z=0;disk.keyframe_insert(data_path='rotation_euler',frame=1)
disk.rotation_euler.z=math.tau*2;disk.keyframe_insert(data_path='rotation_euler',frame=540)
# Blender 5 compositor API changed; glow is applied in FFmpeg instead.
sc.render.film_transparent=False
sc.render.image_settings.file_format='PNG';Path('frames').mkdir(exist_ok=True);sc.render.filepath=str(Path('frames').resolve())+'/'
sc.frame_start=int(os.environ.get("FRAME_START","1"))
sc.frame_end=int(os.environ.get("FRAME_END","540"))
bpy.ops.render.render(animation=True)
expected=[Path("frames")/f"{i:04d}.png" for i in range(sc.frame_start,sc.frame_end+1)]
assert all(p.is_file() and p.stat().st_size>0 for p in expected), "Missing rendered frames"

