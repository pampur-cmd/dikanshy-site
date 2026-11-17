import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/pampur/Projects/dikanshy site')
OUT=ROOT/'design/exports/bigbag-refined'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'design/source/бигбег.glb'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
coords=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);center=(lo+hi)/2
print('WORLD_BOUNDS',tuple(lo),tuple(hi),flush=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.world.color=(.23,.23,.23);scene.view_settings.view_transform='AgX'
for name,loc,energy,size in [('Key',(80,-100,160),180000,100),('Fill',(-100,-50,80),100000,100),('Rim',(30,100,120),150000,80)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.name=name;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=135;scene.camera=cam
for name,loc in [('original-front',(140,-180,120)),('original-back',(-140,180,120)),('original-bottom',(100,-160,-100))]:
 cam.location=loc;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
