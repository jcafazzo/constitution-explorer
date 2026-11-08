"""Compare-page silhouette + printable STL from a fleet display GLB.
Run: Blender -b -P model-source/blender/fleet_outputs.py -- <ship-id> [<ship-id> ...]
Writes:
  dist/assets/fleet/<id>-silhouette.png  1600 x 450 transparent side projection, 5 px/m (320 m across), bow at the left
  dist/assets/fleet/<id>-100mm.stl       binary STL, exactly 100 mm along Y, lowest point at Z = 0, one closed voxel-remeshed body
  dist/assets/fleet/<id>.stl             same mesh (kept for the 'model' field)
Printing changes, recorded in the console report: surface details (ports, lettering, grilles) are dropped; thin supports
(pylons, struts, dorsal) are thickened to >= 2 mm at the 100 mm print size; everything is unioned by voxel remesh."""
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ids = sys.argv[sys.argv.index('--') + 1:]
DROP = ('window', 'port window', 'registry', 'pennant', 'grille', 'lettering', 'text', 'name', 'grid', 'panel line', 'hatch', 'vent', 'decal', 'stripe', 'chevron')
THICK = ('pylon', 'strut', 'dorsal', 'neck', 'connector', 'support', 'boom', 'spar')
report = {}
PRINTED_L = {'constitution': 288.6, 'saladin': 242.5, 'hermes': 242.5, 'ptolemy': 222.0, 'federation': 320.0}

def load(ship):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'dist/assets/detail', ship + '.glb'))
    R = Matrix.Rotation(-math.pi / 2, 4, 'X')               # GLB stores the viewer's raw Z-up frame
    for o in bpy.context.scene.objects:
        if o.parent is None: o.matrix_world = R @ o.matrix_world
    bpy.context.view_layer.update()
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']

def bounds(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def silhouette(ship, objs):
    sc = bpy.context.scene; mn, mx = bounds(objs)
    k = PRINTED_L[ship] / (mx.y - mn.y)                  # draw at the printed length so it matches the figure beside it
    for o in bpy.context.scene.objects:
        if o.parent is None: o.matrix_world = Matrix.Scale(k, 4) @ o.matrix_world
    bpy.context.view_layer.update(); mn, mx = bounds(objs)
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = tuple(((c / 255 + .055) / 1.055) ** 2.4 for c in (32, 35, 33))   # sRGB #202321 in linear
    sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'; sc.display.render_aa = '16'
    sc.render.resolution_x, sc.render.resolution_y = 1600, 450
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 320.0
    yc = mn.y + 160.0; zc = (mn.z + mx.z) / 2
    d = Vector((1, 0, 0)); up = Vector((0, 0, 1)); z = d; y = up; x = y.cross(z)
    cam.matrix_world = Matrix.Translation(Vector((mx.x + 50, yc, zc))) @ Matrix((x, y, z)).transposed().to_4x4()
    cam.data.clip_end = 2000
    sc.render.filepath = os.path.join(ROOT, 'dist/assets/fleet', ship + '-silhouette.png'); bpy.ops.render.render(write_still=True)

def pca_thicken(o, min_t, any_size=False):
    me = o.data; mw = o.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    if len(pts) < 4: return None
    c = sum(pts, Vector()) / len(pts)
    import numpy as np
    A = np.array([list(p - c) for p in pts]); w, V = np.linalg.eigh(A.T @ A)
    ax = Vector(V[:, 0]); t = max(abs((p - c).dot(ax)) for p in pts) * 2
    big = max(abs((p - c).dot(Vector(V[:, 2]))) for p in pts) * 2
    if t >= min_t or (not any_size and big < 4 * min_t): return None          # only long, thin supports; small fittings stay as modelled
    k = min_t / max(t, 1e-6)
    S = Matrix.Identity(4)
    for i in range(3):
        for j in range(3): S[i][j] += (k - 1) * ax[i] * ax[j]
    o.matrix_world = Matrix.Translation(c) @ S @ Matrix.Translation(-c) @ mw
    return round(t, 2)

def printable(ship, objs):
    mn, mx = bounds(objs); L = mx.y - mn.y
    min_t = 2.0 / 100 * L                                   # 2 mm at a 100 mm print
    dropped, thick = 0, {}
    for o in list(objs):
        n = o.name.lower()
        if any(k in n for k in DROP):
            bpy.data.objects.remove(o); dropped += 1; continue
        if any(k in n for k in THICK):
            t = pca_thicken(o, min_t)
            if t is not None: thick[o.name] = t; continue
        t = pca_thicken(o, L * .0016 * 2.2, any_size=True)         # thin plates (dishes, fins) must outlive the voxel grid
        if t is not None: thick[o.name] = t
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects: o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join(); body = bpy.context.view_layer.objects.active; body.name = ship + '-print'
    m = body.modifiers.new('voxel', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = L * .0016; m.use_smooth_shade = False
    bpy.ops.object.modifier_apply(modifier='voxel')
    # keep the largest connected piece (report the rest)
    bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen: continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            u = stack.pop(); comp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen: seen.add(w.index); stack.append(w)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    removed = [[len(c)] + [round(sum((v.co[i] for v in c), 0) / len(c), 1) for i in range(3)] for c in comps[1:]]
    for comp in comps[1:]: bmesh.ops.delete(bm, geom=comp, context='VERTS')
    bm.to_mesh(body.data); bm.free()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    m = body.modifiers.new('dec', 'DECIMATE'); m.ratio = min(1.0, 180000 / max(len(body.data.polygons), 1))
    bpy.ops.object.modifier_apply(modifier='dec')
    mn, mx = bounds([body]); s = 100.0 / (mx.y - mn.y)
    body.matrix_world = Matrix.Scale(s, 4) @ Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in bpy.context.scene.objects: o.select_set(o is body)
    path = os.path.join(ROOT, 'dist/assets/fleet', ship + '-100mm.stl')
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, ascii_format=False, apply_modifiers=True, global_scale=1.0, forward_axis='Y', up_axis='Z')
    import shutil; shutil.copyfile(path, os.path.join(ROOT, 'dist/assets/fleet', ship + '.stl'))
    # closedness: every edge shared by exactly two faces
    bm = bmesh.new(); bm.from_mesh(body.data)
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2); bm.free()
    mn, mx = bounds([body])
    return dict(triangles=len(body.data.polygons), pieces_removed=removed, open_edges=open_edges, dropped_details=dropped,
                thickened={k: f'{v} m -> {round(min_t, 2)} m' for k, v in thick.items()},
                size_mm=[round(mx[i] - mn[i], 3) for i in range(3)], voxel_m=round(L * .0016, 3))

for ship in ids:
    objs = load(ship); silhouette(ship, objs)
    objs = load(ship)
    report[ship] = printable(ship, objs)
    print('FLEET_OUT', ship, json.dumps(report[ship]))
