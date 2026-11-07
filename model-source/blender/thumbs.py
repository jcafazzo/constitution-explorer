"""Catalogue thumbnails + envelope check for every Equipment Locker GLB.
Run: Blender -b -P model-source/blender/thumbs.py [-- id ...]
Writes dist/assets/equipment/thumb-<id>.png (converted to webp by the caller) and model-source/accuracy/envelopes.json."""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
items = json.load(open(os.path.join(ROOT, 'dist/assets/equipment/equipment.json')))
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
env = {}
for it in items:
    if only and it['id'] not in only: continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'dist/assets/equipment', it['id'] + '.glb'))
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]   # true vertex extents
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    size = [round((mx[i] - mn[i]) * 100, 2) for i in range(3)]; env[it['id']] = size
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.show_cavity = True; sh.cavity_type = 'BOTH'
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.86, 0.84, 0.78)
    sc.view_settings.view_transform = 'Standard'; sc.display.render_aa = '16'
    sc.render.resolution_x, sc.render.resolution_y = 640, 480
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 70
    c = (mn + mx) / 2; r = (mx - mn).length / 2; d = Vector((.9, -1.1, .7)).normalized()
    dist = r / math.sin(math.atan(13.5 / 70)) * 1.02
    cam.location = c + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = dist * 4
    sc.render.filepath = os.path.join(ROOT, 'dist/assets/equipment', 'thumb-' + it['id'] + '.png'); bpy.ops.render.render(write_still=True)
    print('THUMB', it['id'], size)
p = os.path.join(ROOT, 'model-source/accuracy/envelopes.json')
old = json.load(open(p)) if os.path.exists(p) else {}; old.update(env); json.dump(old, open(p, 'w'), indent=1)
