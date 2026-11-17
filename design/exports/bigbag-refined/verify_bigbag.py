"""Check derived geometry and render a fresh import of the delivered GLB."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'bigbag-refined.blend'))
body=bpy.data.objects['Bigbag_White_Body'];bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
clearances=[]
for obj in bpy.context.scene.objects:
 if obj.type=='MESH' and obj.name.startswith('Strap_'):
  for v in obj.data.vertices:
   point=obj.matrix_world@v.co;hit,n,idx,dist=bvh.find_nearest(point)
   clearances.append((point-hit).dot(n))
assert min(clearances)>0, ('Strap penetrates body',min(clearances))
for obj in list(bpy.context.scene.objects):
 if obj.type=='MESH':bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'bigbag-refined.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==1
assert all(math.isfinite(c) for o in meshes for v in o.data.vertices for c in v.co)
colors={m.name:list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value) for o in meshes for m in o.data.materials}
assert len(colors)==3
scene=bpy.context.scene;camera=scene.camera
for name,loc in [('verified-front',(1.5,-1.9,1)),('verified-bottom',(1.2,-1.7,-1.2))]:
 camera.location=loc;camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'fresh_glb_import':'passed','finite_coordinates':True,'mesh_objects':len(meshes),'materials':colors,'minimum_vertical_strap_clearance_metres':min(clearances),'file_bytes':(OUT/'bigbag-refined.glb').stat().st_size,'sha256':hashlib.sha256((OUT/'bigbag-refined.glb').read_bytes()).hexdigest(),'limitations':'No browser FPS, touch input or physics tests; visual review still required by owner.'}
(OUT/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
