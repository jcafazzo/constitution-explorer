"""Blender (run with: Blender -b -P render_views.py -- <glb> <views.json> <item-id> <outdir>)
Renders, for each defined plate view, an exact-scale orthographic silhouette mask and a shaded image."""
import bpy, sys, json, math, os
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
glb, views_path, item_id, out = argv
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
spec = json.load(open(views_path))
if spec.get('raw_zup'):   # fleet GLBs store the viewer's Z-up frame untouched; undo the importer's Y-up conversion
    R = Matrix.Rotation(-math.pi / 2, 4, 'X')
    for o in bpy.context.scene.objects:
        if o.parent is None: o.matrix_world = R @ o.matrix_world
    bpy.context.view_layer.update()
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centre = (mn + mx) / 2
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'FLAT'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (1, 1, 1)
scene.display.shading.background_type = 'VIEWPORT'
scene.display.shading.background_color = (0, 0, 0)
scene.view_settings.view_transform = 'Standard'
scene.render.film_transparent = False
scene.display.render_aa = 'OFF'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
AX = {'+X': Vector((1, 0, 0)), '-X': Vector((-1, 0, 0)), '+Y': Vector((0, 1, 0)), '-Y': Vector((0, -1, 0)), '+Z': Vector((0, 0, 1)), '-Z': Vector((0, 0, -1))}
for v in spec['views']:
    w, h = v['crop'][2] - v['crop'][0], v['crop'][3] - v['crop'][1]
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = w, h, 100
    cam.data.ortho_scale = max(w, h) / v['pxPerCm'] / 100.0
    d = AX[v['from']]; up = AX[v['up']]
    # camera looks along -d toward the model; its local +Y is image-up
    z = d.normalized(); y = up.normalized(); x = y.cross(z)
    far = max(10.0, (mx - mn).length + 1)   # outside the model whatever its size (fleet hulls are hundreds of metres)
    cam.matrix_world = Matrix.Translation(centre + d * far) @ Matrix((x, y, z)).transposed().to_4x4()
    cam.data.clip_end = max(100.0, far * 3)
    scene.display.shading.light = 'FLAT'; scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.background_color = (0, 0, 0)
    scene.render.filepath = os.path.join(out, f"{v['name']}-mask.png"); bpy.ops.render.render(write_still=True)
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.background_color = (1, 1, 1)
    scene.render.filepath = os.path.join(out, f"{v['name']}-shaded.png"); bpy.ops.render.render(write_still=True)
print('RENDERED', item_id, len(spec['views']))
