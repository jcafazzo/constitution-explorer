"""Blender modelling kit for the Equipment Locker studies (run inside Blender's Python).

Units: centimetres while modelling; Y = length (front = −Y), Z = up, X = width with +X on the item's left (port) side.
Plate mapping for a view drawn front-up: plan seen from above → x = −(px − mid)/ppc; side view seen from the item's left → z = −(px − mid)/ppc when its left edge is the top.
Each item script builds named objects (one per sub-assembly) and calls export(item_id), which writes
dist/assets/equipment/<id>.glb in metres, glTF Y-up (front → +Z), matching the site viewer.

Accuracy rule: outlines come from the plates. load_profile() reads silhouettes measured by
model-source/accuracy/extract_profile.py; loft_from_profiles() / revolve_profile() turn them into surfaces.
Hand-placed details use coordinates read on the plate (px) through to_cm()."""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PROFILES = os.path.join(ROOT, 'model-source', 'blender', 'profiles')
CM = 0.01

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.objects): pass

# ---------- materials ----------
PALETTE = {  # name: (base colour sRGB hex, roughness, metallic, alpha)
    'black': ('24272a', .45, .1, 1), 'pebbled': ('26282a', .8, .05, 1), 'grey': ('8b9194', .5, .15, 1), 'dark': ('3a3f42', .5, .2, 1),
    'antimony': ('c9cbc6', .32, .35, 1), 'white': ('e8e6de', .55, 0, 1), 'red': ('a8352d', .45, 0, 1), 'blue': ('3a5d9a', .4, 0, 1),
    'bluegray': ('5e6d7e', .3, .15, 1), 'gold': ('c89c4e', .32, .45, 1), 'glass': ('86b3c2', .08, 0, .38), 'screen': ('1c393f', .2, 0, 1),
    'amber': ('d79c38', .4, 0, 1), 'green': ('3f7b52', .45, 0, 1), 'olive': ('6a693d', .6, .05, 1), 'mesh': ('2a2e31', .6, .2, .6),
    'topaz': ('f4f1e6', .05, 0, .55), 'brushed': ('b9bcbb', .28, .5, 1),
}
_mats = {}
def mat(name):
    if name in _mats: return _mats[name]
    hx, rough, metal, alpha = PALETTE[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    srgb = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in srgb]
    b.inputs['Base Color'].default_value = (*lin, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
    _mats[name] = m; return m

def _obj(name, mesh, material, parent=None):
    o = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(o)
    if material: o.data.materials.append(mat(material))
    if parent: o.parent = parent
    return o

def group(name, parent=None):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    if parent: e.parent = parent
    return e

def smooth(o, angle=40):
    for p in o.data.polygons: p.use_smooth = True
    try:
        mod = o.modifiers.new('smooth', 'SMOOTH_BY_ANGLE'); mod['Input_1'] = math.radians(angle)
    except Exception:
        pass
    return o

def bevel(o, width=.05, segments=3, angle=35):
    m = o.modifiers.new('bevel', 'BEVEL'); m.width = width; m.segments = segments; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angle)
    m.harden_normals = False; return o

# ---------- profiles ----------
def load_profile(name):
    return json.load(open(os.path.join(PROFILES, name + '.json')))

def sample(profile, s, median=0):
    """lo, hi (cm) at distance s along a profile (linear interpolation; optional running median window in rows)."""
    rows = profile['rows']
    if median:
        if '_med' not in profile:
            import statistics
            k = median; out = []
            for i in range(len(rows)):
                w = rows[max(0, i - k):i + k + 1]
                out.append([rows[i][0], statistics.median(r[1] for r in w), statistics.median(r[2] for r in w)])
            # then a box filter of the same half-width, so lofts don't band from pixel jitter
            sm = []
            for i in range(len(out)):
                w = out[max(0, i - k):i + k + 1]
                sm.append([out[i][0], sum(r[1] for r in w) / len(w), sum(r[2] for r in w) / len(w)])
            profile['_med'] = sm
        rows = profile['_med']
    if s <= rows[0][0]: return rows[0][1], rows[0][2]
    if s >= rows[-1][0]: return rows[-1][1], rows[-1][2]
    lo, hi = 0, len(rows) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if rows[mid][0] <= s: lo = mid
        else: hi = mid
    a, b = rows[lo], rows[hi]; t = (s - a[0]) / max(b[0] - a[0], 1e-9)
    return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t

# ---------- surfaces ----------
def loft(name, sections, material, p=2.6, seg=64, parent=None, cap=True):
    """sections: [(y, x_lo, x_hi, z_lo, z_hi), ...] — each a superellipse inscribed in that box."""
    bm = bmesh.new(); rings = []
    for (y, x0, x1, z0, z1) in sections:
        cx, cz, ax, az = (x0 + x1) / 2, (z0 + z1) / 2, max((x1 - x0) / 2, 1e-4), max((z1 - z0) / 2, 1e-4)
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg; c, s_ = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((cx + ax * math.copysign(abs(c) ** (2 / p), c), y, cz + az * math.copysign(abs(s_) ** (2 / p), s_))))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            a, b = rings[k][i], rings[k][(i + 1) % seg]; c, d = rings[k + 1][(i + 1) % seg], rings[k + 1][i]
            bm.faces.new((a, b, c, d))
    if cap:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return smooth(_obj(name, me, material, parent), 50)

def loft_from_profiles(name, plan, side, s0, s1, material, n=90, p=2.6, side_flip=True, y0=0.0, median=3, parent=None, x_off=0.0, z_off=0.0, width_scale=1.0, plan_flip=True):
    """Loft a body whose plan (top view) and side-view silhouettes are both measured profiles.
    s runs from s0 to s1 along both profiles (they must share the same origin: the front of the drawn body).
    side_flip: the side view's left edge is the top of the item (image-right = −Z).
    plan_flip: in a plan drawn front-up and seen from above, image-left is +X (the item's port side)."""
    secs = []
    for i in range(n + 1):
        s = s0 + (s1 - s0) * (0.5 - 0.5 * math.cos(math.pi * i / n))  # denser near both ends
        x0, x1 = sample(plan, s, median); z0, z1 = sample(side, s, median)
        if side_flip: z0, z1 = -z1, -z0
        if plan_flip: x0, x1 = -x1, -x0
        secs.append((y0 + s, x0 * width_scale + x_off, x1 * width_scale + x_off, z0 + z_off, z1 + z_off))
    return loft(name, secs, material, p=p, parent=parent)

def revolve(name, pts, material, axis='Y', seg=96, parent=None, loc=(0, 0, 0)):
    """pts: [(r, t), ...] profile revolved about the axis (t along the axis)."""
    bm = bmesh.new(); rings = []
    for r, t in pts:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg; u, v = r * math.cos(a), r * math.sin(a)
            co = {'Y': (u, t, v), 'Z': (u, v, t), 'X': (t, u, v)}[axis]
            ring.append(bm.verts.new(tuple(c + o for c, o in zip(co, loc))))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            a, b = rings[k][i], rings[k][(i + 1) % seg]; c, d = rings[k + 1][(i + 1) % seg], rings[k + 1][i]
            if len({a, b, c, d}) == 4: bm.faces.new((a, b, c, d))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return smooth(_obj(name, me, material, parent), 40)

def revolve_profile(name, prof, material, axis='Y', t_sign=-1, t0=0.0, median=2, step=1, parent=None, loc=(0, 0, 0)):
    """Revolve a measured side-view silhouette: radius = half the drawn width at each row."""
    rows = prof['rows'][::step]
    pts = [(0.0, t0 + t_sign * rows[0][0])]
    for i, r in enumerate(rows):
        lo, hi = sample(prof, r[0], median); pts.append((max((hi - lo) / 2, 0.0), t0 + t_sign * r[0]))
    pts.append((0.0, t0 + t_sign * rows[-1][0]))
    if t_sign < 0: pts = pts[::-1]
    return revolve(name, pts, material, axis, parent=parent, loc=loc)

# ---------- primitives (all centimetres) ----------
def box(name, size, loc, material, rot=(0, 0, 0), bev=0.0, parent=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = _obj(name, me, material, parent); o.location = loc; o.rotation_euler = rot
    if bev: bevel(o, bev)
    return o

def cyl(name, r, length, loc, material, axis='Y', r2=None, seg=48, rot=None, bev=0.0, parent=None):
    """Cylinder/cone; r at the negative end of the axis, r2 at the positive end."""
    r2 = r if r2 is None else r2
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r2, depth=length)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = _obj(name, me, material, parent); o.location = loc
    o.rotation_euler = rot or {'Z': (0, 0, 0), 'Y': (-math.pi / 2, 0, 0), 'X': (0, math.pi / 2, 0)}[axis]
    if bev: bevel(o, bev)
    return smooth(o, 40)

def sphere(name, r, loc, material, scale=(1, 1, 1), parent=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = _obj(name, me, material, parent); o.location = loc; o.scale = scale
    return smooth(o, 60)

def torus(name, R, r, loc, material, axis='Y', parent=None, seg=64):
    bm = bmesh.new(); verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(12):
            b = 2 * math.pi * j / 12; x = (R + r * math.cos(b)) * math.cos(a); z = (R + r * math.cos(b)) * math.sin(a); y = r * math.sin(b)
            co = {'Y': (x, y, z), 'Z': (x, z, y), 'X': (y, x, z)}[axis]; ring.append(bm.verts.new(co))
        verts.append(ring)
    for i in range(seg):
        for j in range(12):
            bm.faces.new((verts[i][j], verts[(i + 1) % seg][j], verts[(i + 1) % seg][(j + 1) % 12], verts[i][(j + 1) % 12]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = _obj(name, me, material, parent); o.location = loc
    return smooth(o, 60)

def extrude(name, pts, depth, material, plane='XY', loc=(0, 0, 0), bev=0.0, parent=None, rot=None):
    """Extrude a closed 2-D outline. plane 'XY' → thickness along Z; 'YZ' (side profile, pts=(y,z)) → along X; 'XZ' → along Y."""
    bm = bmesh.new()
    vs = []
    for a, b in pts:
        co = {'XY': (a, b, -depth / 2), 'YZ': (-depth / 2, a, b), 'XZ': (a, -depth / 2, b)}[plane]
        vs.append(bm.verts.new(co))
    f = bm.faces.new(vs)
    vec = {'XY': (0, 0, depth), 'YZ': (depth, 0, 0), 'XZ': (0, depth, 0)}[plane]
    r = bmesh.ops.extrude_face_region(bm, geom=[f]); top = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=vec)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = _obj(name, me, material, parent); o.location = loc
    if rot: o.rotation_euler = rot
    if bev: bevel(o, bev, 3, 30)
    return o

def array_line(fn, n, start, step):
    """Call fn(i, position) for n evenly spaced positions from start by step (tuples)."""
    return [fn(i, tuple(s + i * d for s, d in zip(start, step))) for i in range(n)]

# ---------- export ----------
def export(item_id, out_dir=None):
    out_dir = out_dir or os.path.join(ROOT, 'dist', 'assets', 'equipment')
    scene = bpy.context.scene
    root = bpy.data.objects.new(item_id, None); scene.collection.objects.link(root)
    for o in list(scene.objects):
        if o is not root and o.parent is None: o.parent = root
    root.scale = (CM, CM, CM)
    bpy.context.view_layer.update()
    for o in scene.objects: o.select_set(o.type in ('MESH', 'EMPTY'))
    path = os.path.join(out_dir, item_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_extras=False)
    # bounds in cm for the envelope check
    pts = [o.matrix_world @ Vector(c) for o in scene.objects if o.type == 'MESH' for c in o.bound_box]
    mn = [min(p[i] for p in pts) / CM for i in range(3)]; mx = [max(p[i] for p in pts) / CM for i in range(3)]
    size = [round(mx[i] - mn[i], 3) for i in range(3)]
    print('EXPORTED', item_id, 'size_cm', size, os.path.getsize(path), 'bytes')
    return size
