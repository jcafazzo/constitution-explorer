"""Main-bridge wall stations: Command Intelligence (PDF 110-111, TO 02:01:00-01), Communications (PDF 135-136, TO 03:01:00-01)
and Engineering (PDF 140-141, TO 03:08:00-01).
Run: Blender -b -P model-source/blender/bridge_stations.py [-- station ...]
     STATION_STRAIGHT=1 STATION_OUT=<dir> ...   builds them unbent, as the front elevation and View A-A draw them, for scoring.

Measurements come from model-source/blender/bridge_stations_regions.py (profiles/bridge-stations.json):
  the body is View A-A's section carried across the front elevation's outline (each part is the intersection of the two),
  the controls console's plan and every panel, button and lamp on it come from View B-B, mapped onto the sloping top.
View B-B draws the console in two halves meeting at the "centroid of station" at about 8.5° (true plan angle ≈ 8°),
which matches the "circular arc back": each half of the station is turned by that angle about the back wall's centre line.
Frame: x across (+x to the seated operator's right), y depth (back wall 0, operator at -y), z up from the bridge deck; cm."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
from mathutils import Vector, Matrix

kit.PALETTE.update({
    'platinum': ('dcdcd5', .35, .3, 1),     # SF29UC
    'st_black': ('1f2225', .5, .1, 1),      # SF32UC
    'st_red': ('a3302a', .45, 0, 1),        # SF10UC
    'st_grey': ('8a8f92', .55, .1, 1),      # SF30UC
    'panel_blue': ('3d5d8c', .45, .05, 1),  # SF16UC (View B-B key)
    'cd_screen': ('b8c8c3', .25, 0, 1),     # computer data and systems visual read-out screens
    'vi_screen': ('d8e0dc', .2, 0, 1),      # visual intelligence displays
    'vent': ('2a2d30', .7, .1, 1),
    'lamp': ('f1efe6', .3, 0, 1),
    'deck_slot': ('121416', .5, .1, 1),
})
R = json.load(open(os.path.join(kit.PROFILES, 'bridge-stations.json')))
STRAIGHT = os.environ.get('STATION_STRAIGHT') == '1'
OUT = os.environ.get('STATION_OUT') or None
STORAGE = {'command-intelligence': ['right'], 'communications': ['right', 'left'], 'engineering': ['right']}   # record decks storage, per View B-B

def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear(); old = o.data; o.data = me; bpy.data.meshes.remove(old)
    return o

def intersect(o, other):
    m = o.modifiers.new('i', 'BOOLEAN'); m.operation = 'INTERSECT'; m.solver = 'EXACT'; m.object = other
    apply_mods(o); bpy.data.objects.remove(other, do_unlink=True)
    return o

def clip_half(poly, sgn):
    """Sutherland-Hodgman: keep the part of a closed (x, z) polygon with sgn*x >= 0."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ia, ib = sgn * a[0] >= 0, sgn * b[0] >= 0
        if ia: out.append(a)
        if ia != ib:
            t = a[0] / (a[0] - b[0]); out.append((0.0, a[1] + t * (b[1] - a[1])))
    return out

def mesh_from(name, verts, faces, material, parent):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = kit._obj(name, me, material, parent); return o

def plane_frame(p0, p1, outward_y=-1):
    """Frame on the plane through the section line p0 -> p1 (y, z), extended along x: returns origin, along-line unit t, outward normal n."""
    o = Vector((0, p0[0], p0[1])); t = (Vector((0, p1[0], p1[1])) - o).normalized()
    n = Vector((0, -t.z, t.y))
    if n.y * outward_y < 0: n = -n
    return o, t, n

def slab_on(name, frame, x0, x1, s0, s1, off, thick, material, parent, bev=0.0):
    """Box lying on a plane: x in [x0, x1], s (distance along t from origin) in [s0, s1], from off to off+thick along n."""
    o, t, n = frame; v = []
    for x in (x0, x1):
        for s in (s0, s1):
            for h in (off, off + thick):
                v.append(tuple(o + Vector((x, 0, 0)) + t * s + n * h))
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mesh_from(name, v, f, material, parent)
    bpy.context.view_layer.objects.active = ob
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    if bev: kit.bevel(ob, bev, 2, 30)
    return ob

def prism_on(name, frame, pts, off, thick, material, parent):
    """Extrude a polygon given in plane coordinates (x, s) from off to off+thick along the plane normal."""
    o, t, n = frame
    bot = [tuple(o + Vector((x, 0, 0)) + t * s + n * off) for x, s in pts]
    top = [tuple(o + Vector((x, 0, 0)) + t * s + n * (off + thick)) for x, s in pts]
    k = len(pts); faces = [tuple(range(k))[::-1], tuple(range(k, 2 * k))] + [(i, (i + 1) % k, k + (i + 1) % k, k + i) for i in range(k)]
    ob = mesh_from(name, bot + top, faces, material, parent)
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return ob

def section_x_extrude(name, poly, sgn, material, parent, width=220):
    """A View A-A polygon (y, z) carried across one half (x from 0 to sgn*width)."""
    o = kit.extrude(name, poly, width, material, plane='YZ', parent=parent)
    o.location = (sgn * width / 2, 0, 0)
    return o

def build_station(sid):
    S = R[sid]; root = kit.group(sid.replace('-', '_'))
    sec = S['section']; front = [tuple(p) for p in S['front']]
    con = S['console']; halves = con['halves']
    F, B = S['slope'][0], S['slope'][1]                                # console front edge (tip) and back edge, (y, z)
    L_sec = math.dist(F, B)
    alpha = math.atan2(B[1] - F[1], B[0] - F[0])
    bb_angle = sum(h['angle_deg'] for h in halves.values()) / 2
    theta = 0.0 if STRAIGHT else math.degrees(math.atan(math.tan(math.radians(bb_angle)) * math.cos(alpha)))
    for side, sgn in (('right', 1), ('left', -1)):
        H = halves[side]
        half = kit.group(f'{sid}_{side}', root)
        k_d = L_sec / H['depth']                                     # B-B depth -> section slope length
        fpoly = clip_half(front, sgn)
        # housing, readout band and pedestal: section x front outline
        for part, material in (('housing', 'platinum'), ('band', 'st_black'), ('pedestal', 'platinum')):
            body = section_x_extrude(f'{sid}_{part}_{side}', sec[part], sgn, material, half)
            cut = kit.extrude('cut', fpoly, 600, material, plane='XZ', loc=(0, -100, 0))
            intersect(body, cut)
        # controls console and its red lip: section x the plan of View B-B (front edge shorter than the back edge)
        yF, yB = F[0], B[0]
        plan = [(0, 5), (sgn * H['back_len'], 5), (sgn * H['back_len'], yB), (sgn * H['front_len'], yF - 3), (0, yF - 3)]
        for part, material in (('console', 'st_black'), ('lip', 'st_red')):
            body = section_x_extrude(f'{sid}_{part}_{side}', sec[part], sgn, material, half)
            cut = kit.extrude('cut', plan, 400, material, plane='XY', loc=(0, 0, 100))
            intersect(body, cut)
        # visual intelligence panel and its two displays on the upper sloping face
        fo, ft, fn = plane_frame(S['face'][1], S['face'][0])                  # origin at the face's foot, t up the face
        fl = math.dist(S['face'][0], S['face'][1]); zf0 = S['face'][1][1]
        zs = lambda z: (z - zf0) / (ft.z if abs(ft.z) > 1e-6 else 1)
        vx0, vx1, vz0, vz1 = S['vi_panel']
        a0, a1 = (max(vx0, 0), vx1) if sgn > 0 else (vx0, min(vx1, 0))
        slab_on(f'{sid}_vi_panel_{side}', (fo, ft, fn), a0, a1, max(zs(vz0), 0.5), min(zs(vz1), fl - .5), -.2, 1.2, 'st_grey', half, bev=.4)
        for i, (x0, x1, z0, z1) in enumerate(S['displays']):
            if sgn * (x0 + x1) < 0: continue
            slab_on(f'{sid}_vi_display_{i}', (fo, ft, fn), x0, x1, zs(z0), zs(z1), 1.0, .5, 'vi_screen', half, bev=.8)
        # computer data screens on the readout band's face
        bo, bt, bn = plane_frame(S['band_face'][1], S['band_face'][0]); zb0 = S['band_face'][1][1]
        for i, (x0, x1, z0, z1) in enumerate(S['cds']):
            if sgn * (x0 + x1) < 0: continue
            slab_on(f'{sid}_cd_{i}', (bo, bt, bn), x0, x1, (z0 - zb0) / bt.z, (z1 - zb0) / bt.z, -.1, .5, 'cd_screen', half)
        # bridge ventilation grilles on the pedestal face
        po, pt, pn = plane_frame(S['ped_face'][1], S['ped_face'][0]); zp0 = S['ped_face'][1][1]
        for i, (x0, x1, z0, z1) in enumerate(S['vents']):
            if sgn * (x0 + x1) < 0: continue
            slab_on(f'{sid}_vent_{i}', (po, pt, pn), x0, x1, (z0 - zp0) / pt.z, (z1 - zp0) / pt.z, -.1, .4, 'vent', half)
        # View B-B: panels, buttons and lamps on the console top (d measured back from the front edge)
        so, st_, sn = plane_frame(F, B, outward_y=-1)
        if sn.z < 0: sn = -sn
        frame = (so, st_, sn)
        for i, p in enumerate(con['panels']):
            if p['side'] != side: continue
            if sum(abs(q[0]) for q in p['pts']) / len(p['pts']) > 100: continue      # record decks storage: built below
            prism_on(f'{sid}_panel_{side}_{i}', frame, [(a, d * k_d) for a, d in p['pts']], 0, .6, 'panel_blue', half)
        for i, b in enumerate(con['buttons']):
            if b['side'] != side or abs(b['a']) > 100: continue
            w, h = max(b['w'], .8), max(b['h'], .8)
            if b['round']:
                c = kit.cyl(f'{sid}_lamp_{side}_{i}', min(w, h) / 2, .5, (0, 0, 0), 'lamp', axis='Z', seg=12, parent=half)
                c.location = so + Vector((b['a'], 0, 0)) + st_ * (b['d'] * k_d) + sn * .85
                c.rotation_euler = sn.to_track_quat('Z', 'Y').to_euler()
            else:
                slab_on(f'{sid}_button_{side}_{i}', frame, b['a'] - w / 2, b['a'] + w / 2, b['d'] * k_d - h / 2, b['d'] * k_d + h / 2, .6, .45, 'lamp', half)
        if side in STORAGE[sid]:
            for j in range(5):   # five record-deck slots across the end of the console
                a0 = sgn * (106 + j * 7.2); a1 = sgn * (106 + j * 7.2 + 6.2)
                slab_on(f'{sid}_record_decks_{side}_{j}', frame, min(a0, a1), max(a0, a1), 5 * k_d, 58 * k_d, -.2, .5, 'deck_slot', half)
        sc = S.get('scanner')
        if sc and sc['side'] == side:   # hooded scanner viewer standing on the console (front elevation and View B-B)
            c = so + Vector((sc['a'], 0, 0)) + st_ * (sc['d'] * k_d)
            (bw, bd), (tw, td), hh = sc['base'], sc['top'], sc['h']
            z0 = c.z - 3; v = []
            for (w_, d_, z) in ((bw, bd, z0), (tw, td, z0 + hh)):
                for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    v.append((c.x + sx * w_ / 2, c.y + sy * d_ / 2 + (bd - d_) / 2, z))
            faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            hood = mesh_from(f'{sid}_scanner', v, faces, 'platinum', half); kit.bevel(hood, .5, 2, 30)
            kit.box(f'{sid}_scanner_viewer', (tw * .6, td * .6, .4), (c.x, c.y + (bd - td) / 2, z0 + hh + .1), 'screen', parent=half)
    # bend the two halves into the shallow V of View B-B: a mitre at x = 0, so lengths measured from the seam stay true
    # (x' = x cos th, y' = y / cos th - |x| sin th; linear within each half, so every flat face stays flat)
    bpy.context.view_layer.update()
    th = math.radians(theta); c, s_ = math.cos(th), math.sin(th)
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        if o.modifiers: apply_mods(o)
        o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
        for v in o.data.vertices:
            x, y, z = v.co; v.co = (x * c, y / c - abs(x) * s_, z)
        o.parent = root
    # operator's chair: View A-A outline x the front elevation's widths, rounded
    side_poly = [tuple(p) for p in S['chair_side']]
    cf = S['chair_front']
    def hw(z):   # front half-width at height z (linear between the tabulated rows, held at the ends)
        if z <= cf[0][0]: return cf[0][1]
        for (za, wa), (zb, wb) in zip(cf, cf[1:]):
            if z <= zb: return wa + (wb - wa) * (z - za) / (zb - za)
        return cf[-1][1]
    for part, (z0, z1), material in (('base', (-1, 37), 'st_grey'), ('seat', (37, 71), 'platinum'), ('back', (71, 200), 'st_black')):
        rows = [z0] + [z for z, _ in cf if z0 < z < z1] + [z1]
        band = [(hw(z), z) for z in rows] + [(-hw(z), z) for z in reversed(rows)]
        o = kit.extrude(f'{sid}_chair_{part}', side_poly, 60, material, plane='YZ', parent=root)
        cut = kit.extrude('cut', band, 600, material, plane='XZ', loc=(0, -100, 0))
        intersect(o, cut)
        r = o.modifiers.new('r', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = .6
        s = o.modifiers.new('s', 'CORRECTIVE_SMOOTH'); s.factor = .5; s.iterations = 6
        apply_mods(o); d = o.modifiers.new('d', 'DECIMATE'); d.ratio = .35; apply_mods(o); kit.smooth(o, 50)
    return root

if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(R)
    for sid in only:
        kit.reset(); kit._mats.clear()
        build_station(sid)
        kit.export(sid, OUT)
