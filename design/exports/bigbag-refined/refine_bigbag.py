"""Derive a clean, separated bag/strap asset; never modify the supplied GLB."""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'design/source/бигбег.glb';original_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# Rebuild a clean cloth shell with rounded corners; keep supplied GLB untouched.
verts=[];faces=[];n=32
for axis in range(3):
 for sign in (-1,1):
  start=len(verts)
  for j in range(n+1):
   for i in range(n+1):
    co=Vector((0,0,0));co[axis]=sign;co[(axis+1)%3]=-1+2*i/n;co[(axis+2)%3]=-1+2*j/n
    core=Vector(tuple(max(-.90,min(.90,k)) for k in co));delta=co-core;co=core+delta.normalized()*.10
    x,y,z=co;h=(z+1)*.5
    # Slight fullness and fine wrinkles; corner silhouettes remain smooth.
    fullness=1+.018*math.sin(math.pi*h)
    xx=x*39.5*fullness;yy=y*39*fullness;zz=(z+1)*40
    if axis in (0,1):
     fade=math.sin(math.pi*h)**2*(1-abs(co[(axis+1)%2]))
     wave=.20*math.sin(zz*.52+co[(axis+1)%2]*11)*fade
     if axis==0:xx+=sign*wave
     else:yy+=sign*wave
    if axis==2 and sign>0:zz+=1.5*(1-x*x)*(1-y*y)
    verts.append((xx,yy,zz))
  for j in range(n):
   for i in range(n):
    k=start+j*(n+1)+i;faces.append((k,k+1,k+n+2,k+n+1))
mesh=bpy.data.meshes.new('Clean_rounded_cloth_shell');mesh.from_pydata(verts,[],faces);mesh.update()
body=bpy.data.objects.new('Bigbag_White_Body',mesh);bpy.context.collection.objects.link(body)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
bpy.context.view_layer.objects.active=body;body.select_set(True)
# A small folded filling neck above the tied centre.
verts=[];faces=[];nr=40
rings=[(80.8,4,4),(82,3,3),(83.5,2.2,2.0),(85,4.8,3),(88,7,4),(91.5,7.7,3.8),(94,6,2.6),(95,2,.8)]
for row,(z,rx,ry) in enumerate(rings):
 for k in range(nr):
  a=math.tau*k/nr;r=1+.09*math.sin(5*a+row*.3)
  verts.append((rx*math.cos(a)*r-(z-81)*.18,ry*math.sin(a)*r,z+.45*math.sin(3*a)*row/7))
for j in range(len(rings)-1):
 for k in range(nr):faces.append((j*nr+k,j*nr+(k+1)%nr,(j+1)*nr+(k+1)%nr,(j+1)*nr+k))
faces.append(tuple(reversed(range(nr))));faces.append(tuple((len(rings)-1)*nr+k for k in range(nr)))
neck_mesh=bpy.data.meshes.new('Folded_filling_neck');neck_mesh.from_pydata(verts,[],faces);neck_mesh.update()
neck=bpy.data.objects.new('White_Filling_Neck',neck_mesh);bpy.context.collection.objects.link(neck)
body.data.materials.clear()
def material(name,color,roughness):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=0;p.inputs['Specular IOR Level'].default_value=.25
 return mat
white=material('White_woven_polypropylene',(.82,.81,.78),.87)
blue=material('Blue_woven_lifting_straps',(.006,.045,.16),.80)
stitchmat=material('White_stitch_thread',(.90,.89,.85),.92)
# Matte PBR constants export directly to glTF.
body.data.materials.append(white)
neck.data.materials.clear();neck.data.materials.append(white)
for p in neck.data.polygons:p.use_smooth=True
for p in body.data.polygons:p.use_smooth=True
mod=body.modifiers.new('Web_geometry_reduction','DECIMATE');mod.ratio=.85;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name)
# BVH lets each vertical strap conform to the reconstructed cloth surface.
bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
def surface(axis,sign,fixed,z):
 origin=Vector((fixed,sign*100,z)) if axis=='front' else Vector((sign*100,fixed,z))
 direction=Vector((0,-sign,0)) if axis=='front' else Vector((-sign,0,0))
 hit,n,idx,dist=bvh.ray_cast(origin,direction,200)
 if hit is None:
  # Above the top corner: continue the attachment plane at a sampled lower height.
  origin.z=74;hit,n,idx,dist=bvh.ray_cast(origin,direction,200)
 if hit is None:raise RuntimeError(('Surface ray missed',axis,sign,fixed,z))
 hit.z=z
 return hit+Vector((0,sign*.40,0)) if axis=='front' else hit+Vector((sign*.40,0,0))
objects=[body,neck];leggrids={}
def meshobj(name,verts,faces,mat,solid=.15):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=True
 if solid:
  m=obj.modifiers.new('Webbing_thickness','SOLIDIFY');m.thickness=solid;m.offset=0
  bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=m.name)
 objects.append(obj);return obj
# Four corner loops, with two straight and surface-fitted legs each.
for sx in (-1,1):
 for sy in (-1,1):
  key=f'{"R" if sx>0 else "L"}{"B" if sy>0 else "F"}'
  grids=[]
  for axis,sign,fixed in [('front',sy,sx*29.5),('side',sx,sy*29.5)]:
   verts=[];rows=26;cols=3
   for j in range(rows):
    z=53+(79.5-53)*j/(rows-1)
    for k in range(cols):verts.append(tuple(surface(axis,sign,fixed+(k/(cols-1)-.5)*5.8,z)))
   faces=[(j*cols+k,j*cols+k+1,(j+1)*cols+k+1,(j+1)*cols+k) for j in range(rows-1) for k in range(cols-1)]
   # Reverse side-facing orientation where required; Blender recalc below handles all closed strips.
   meshobj('Strap_'+key+'_'+axis,verts,faces,blue,.20);grids.append((axis,sign,fixed))
  A=surface('front',sy,sx*29.5,79.3);B=surface('side',sx,sy*29.5,79.3)
  span=B-A;outward=Vector((sx,sy,0)).normalized();loopverts=[];steps=41;widthsteps=3
  for j in range(steps):
   t=j/(steps-1);q=1-t;C=A+Vector((0,0,25));D=B+Vector((0,0,25))
   center=A*q**3+C*(3*q*q*t)+D*(3*q*t*t)+B*t**3
   tangent=(C-A)*(3*q*q)+(D-C)*(6*q*t)+(B-D)*(3*t*t);tangent.normalize()
   # Twist webbing smoothly from the front-face attachment to the adjacent side.
   w=Vector((1,0,0)).lerp(Vector((0,sx*sy,0)),t);w=w-tangent*w.dot(tangent);w.normalize()
   for k in range(widthsteps):loopverts.append(tuple(center+w*((k/(widthsteps-1)-.5)*5.8)))
  faces=[(j*widthsteps+k,j*widthsteps+k+1,(j+1)*widthsteps+k+1,(j+1)*widthsteps+k) for j in range(steps-1) for k in range(widthsteps-1)]
  meshobj('Lifting_loop_'+key,loopverts,faces,blue,.22)
  # Neat white stitch lines follow the surface at constant offsets from strap edges.
  for axis,sign,fixed in grids:
   for edge in (-2.25,2.25):
    points=[surface(axis,sign,fixed+edge,54.1+(77.3-54.1)*j/17) for j in range(18)]
    n=Vector((0,sign*.17,0)) if axis=='front' else Vector((sign*.17,0,0))
    points=[p+n for p in points]
    curve=bpy.data.curves.new('Straight_stitch','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=.065;curve.bevel_resolution=0
    spl=curve.splines.new('POLY');spl.points.add(len(points)-1)
    for co,p in zip(spl.points,points):co.co=(*p,1)
    ob=bpy.data.objects.new('Stitch_'+key+'_'+axis,curve);bpy.context.collection.objects.link(ob);ob.data.materials.append(stitchmat)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');objects.append(bpy.context.object);ob.select_set(False)
# Uniform white shell has no blue bottom or painted blue seam outlines.
# Normalize all derived meshes to a ~1 metre object and put the pivot near its centre.
for ob in objects:
 if ob.type!='MESH':continue
 for v in ob.data.vertices:v.co=(v.co-Vector((0,0,49.8)))*.01
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 ob.location=(0,0,0);ob.rotation_euler=(0,0,0);ob.scale=(1,1,1)
 bpy.context.view_layer.objects.active=ob;ob.select_set(False)
# Keep independently editable body, loops and stitching in the working .blend.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world.color=(.19,.19,.19);scene.view_settings.view_transform='AgX'
for name,loc,energy,size in [('Key',(1.3,-1.8,2),180,2),('Fill',(-1.8,-.5,1),100,2),('Rim',(.4,1.8,1.5),180,1.5),('Bottom',(0,-.5,-1.8),70,1.5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.name=name;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=1.42;scene.camera=camera
for name,loc in [('refined-front',(1.5,-1.9,1.0)),('refined-back',(-1.5,1.9,.9)),('refined-bottom',(1.2,-1.7,-1.2)),('refined-top',(1.3,-1.7,2.0))]:
 camera.location=loc;camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bigbag-refined.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=body
triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects if o.type=='MESH')
editable_count=len(objects)
bpy.ops.object.join()
objects=[bpy.context.object]
bpy.ops.export_scene.gltf(filepath=str(OUT/'bigbag-refined.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects if o.type=='MESH')
report={'source_sha256':original_hash,'source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==original_hash,'derived_file':'bigbag-refined.glb','triangles':triangles,'editable_mesh_objects':editable_count,'export_mesh_objects':len(objects),'notes':['White body and bottom','Clean reconstructed shell, filling neck and corner webbing; smoother than original','Surface fitted straight strap legs with stand-off','White straight stitch lines','Origin centered; normalized model dimensions'],'rendered_views':['front','back','bottom','top']}
(OUT/'refinement-report.json').write_text(json.dumps(report,indent=2)+'\n');print('REFINEMENT_REPORT',json.dumps(report),flush=True)
