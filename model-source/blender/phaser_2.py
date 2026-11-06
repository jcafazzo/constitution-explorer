"""Hand Phaser Type II — PDF 104 (TO 01:08:52) + PDF 105 (TO 01:08:53).  Run: Blender -b -P model-source/blender/phaser_2.py
Printed: L.O.A. 221.00 mm, W.O.A. 49.40 mm (the locked-on Type I's width), D.O.A. 157.50 mm (grip butt to the Type I's top).
Colours: br. antimony SF02UC, gl. bluegray SF31UC (aft section — the key's leader points there), gloss black SF32UC,
clear white topaz (P) for the beam shield.  Plate PDF 104 at 67.61 px/cm.
Views on PDF 104: right drawing = side seen from +X (image right = +Z, the Type I side; the grip runs left = -Z and aft);
middle drawing = top seen from +Z (image left = +X); the Type I is a phantom (dash-dot) in every view.
Body: lofted from the side and top silhouettes (profiles/phaser-2-side.json, -top.json written by
model-source/accuracy/helpers/phaser_2_measure.py); barrel parts revolved from profiles/phaser-2-barrel.json;
grip: straight bar between its two measured edges (front y = 1000.5 - 0.396(x-300), rear y = 1263 - 0.396(x-300); 21.6 deg rake),
butt face perpendicular to the grip axis through (188,1085)-(234,1220), corner radius 0.62 cm, lateral width 2.35 cm
(end view 2.07 cm at its own 0.875 drawing scale; VIEW B-B 2.4 cm).
The Type I is the finished phaser_1 model, seated on the concave seat with its face plate in the forward lockplate recess
and its tail against the rear lockplate.  A second GLB without the Type I is written for scoring (the plates draw it as a phantom)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
import phaser_1
from mathutils import Vector

PPC = 67.61
TIP = 236                       # plate row of the beam-shield tip
DRAWN_L = (1745 - 236) / PPC    # 22.32 cm on the plate
SY = 22.10 / DRAWN_L            # scale lengths to the printed L.O.A.
Y0 = -22.10 / 2
yv = lambda py: Y0 + (py - TIP) / PPC * SY          # plate row -> y
zs = lambda px: (px - 1020) / PPC                   # side-view column -> z (+Z = Type I side)
xt = lambda px: -(px - 632) / PPC                   # top-view column -> x (image left = +X)
P_BODY = 4.0

SIDE = kit.load_profile('phaser-2-side'); TOP = kit.load_profile('phaser-2-top'); BARREL = kit.load_profile('phaser-2-barrel')

def section(py, med=0):
    s = (py - TIP) / PPC
    zl, zh = kit.sample(SIDE, s, med); tl, th = kit.sample(TOP, s, med)
    return yv(py), -th, -tl, zl, zh

def face_x(py, z, side=1):
    """x of the body surface on the +X (side=1) or -X face at plate row py and height z."""
    _, x0, x1, z0, z1 = section(py)
    cx, ax, cz, az = (x0 + x1) / 2, (x1 - x0) / 2, (z0 + z1) / 2, (z1 - z0) / 2
    t = min(abs((z - cz) / az), .999)
    return cx + side * ax * (1 - t ** P_BODY) ** (1 / P_BODY)

def body_loft(name, py0, py1, material, step=2):
    rows = list(range(py0, py1, step)) + [py1]
    return kit.loft(name, [section(py) for py in rows], material, p=P_BODY, seg=72)

def mesh_from(name, verts, faces, material, parent=None, smooth_deg=35):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = kit._obj(name, me, material, parent)
    return kit.smooth(o, smooth_deg) if smooth_deg else o

def frame_loft(name, secs, material, p=4.0, seg=56, parent=None):
    """secs: [(centre Vector, U unit, au, V unit, av)] — superellipse rings in arbitrary planes, capped at both ends."""
    verts, faces = [], []
    for C, U, au, V, av in secs:
        for i in range(seg):
            a = 2 * math.pi * i / seg; c, s_ = math.cos(a), math.sin(a)
            verts.append(C + U * (au * math.copysign(abs(c) ** (2 / p), c)) + V * (av * math.copysign(abs(s_) ** (2 / p), s_)))
    n = len(secs)
    for k in range(n - 1):
        for i in range(seg):
            faces.append((k * seg + i, k * seg + (i + 1) % seg, (k + 1) * seg + (i + 1) % seg, (k + 1) * seg + i))
    faces.append(tuple(reversed(range(seg)))); faces.append(tuple(range((n - 1) * seg, n * seg)))
    return mesh_from(name, verts, faces, material, parent, 50)

# ---------- grip frame (plate px along the grip axis) ----------
A = math.atan(0.396)
D = (math.cos(A), -math.sin(A))       # plate direction from butt toward the body
N = (math.sin(A), math.cos(A))        # plate direction from the front edge toward the rear edge
B0 = (215.4, 1165.3)                  # butt-face centre on the grip mid-line
HW = 122.0                            # half the grip's fore-aft width (px) = 1.80 cm
GX = 2.35 / 2                         # half lateral width (cm)
def plate_pt(t, v):                   # t px along the axis from the butt face, v px across (+ = rear edge)
    return (B0[0] + D[0] * t + N[0] * v, B0[1] + D[1] * t + N[1] * v)
def grip_pt(t, v, x=0.0):
    px, py = plate_pt(t, v); return Vector((x, yv(py), zs(px)))

def oriented_box(name, t0, t1, v0, v1, x0, x1, material, parent=None):
    c = [grip_pt(t, v, x) for t in (t0, t1) for v in (v0, v1) for x in (x0, x1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return mesh_from(name, c, faces, material, parent, 0)

def grip_loft(name, t0, t1, material, shrink=0.0, step=6, parent=None):
    R = 0.62 * PPC
    ts = sorted(set([t0 + k * (t1 - t0) / max(1, int((t1 - t0) / step)) for k in range(int((t1 - t0) / step) + 1)] +
                    [t0 + R * (1 - math.cos(math.pi / 2 * k / 10)) for k in range(11) if t0 + R * (1 - math.cos(math.pi / 2 * k / 10)) < t1]))
    secs = []
    for t in ts:
        hw = HW - R + math.sqrt(max(R * R - (R - min(t, R)) ** 2, 0)) if t < R else HW
        hw -= shrink * PPC
        a, b = grip_pt(t, -hw), grip_pt(t, hw)
        C = (a + b) / 2; V = (b - a).normalized()
        secs.append((C, Vector((1, 0, 0)), GX - shrink, V, (b - a).length / 2))
    return frame_loft(name, secs, material, p=4.0, parent=parent)

def stadium_pad(name, t0, t1, v0, v1, x, h, material, parent=None, nseg=10):
    """rounded-end pad on the grip's +X face: axial t0..t1 (px), across v0..v1 (px), raised h (cm) from x."""
    r = (v1 - v0) / 2; vc = (v0 + v1) / 2; outline = []
    for k in range(nseg + 1):   # left (butt-side) round end
        a = math.pi / 2 + math.pi * k / nseg; outline.append((t0 + r + r * math.cos(a), vc - r * math.sin(a)))
    for k in range(nseg + 1):
        a = -math.pi / 2 + math.pi * k / nseg; outline.append((t1 - r + r * math.cos(a), vc - r * math.sin(a)))
    n = len(outline)
    verts = [grip_pt(t, v, x - .02) for t, v in outline] + [grip_pt(t, v, x + h) for t, v in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_from(name, verts, faces, material, parent, 0)

def build():
    root = kit.group('Hand Phaser Type II')
    # ---- barrel: beam shield (P), beam emitter, photon accelerator ----
    rr = lambda py: .266 + (.394 - .266) * (py - 237) / (356 - 237)     # emitter cone radius (linear fit of rows 237-356)
    kit.revolve('Beam shield (P)', [(0, yv(236)), (rr(236), yv(236)), (rr(262), yv(262)), (0, yv(262))], 'topaz', parent=root)
    kit.revolve('Beam emitter', [(0, yv(261)), (rr(261), yv(261)), (rr(357), yv(357)), (0, yv(357))], 'antimony', parent=root)
    acc = kit.group('Photon accelerator', root)
    st = [(357, 1.20), (359, 1.27), (386, 1.29), (387.5, 1.50), (404, 1.50)]
    kit.revolve('front cap', [(0, yv(357))] + [(r, yv(py)) for py, r in st] + [(0, yv(404))], 'antimony', parent=acc)
    kit.revolve('rear collar', [(0, yv(484))] + [(r, yv(py)) for py, r in [(484, 1.50), (530, 1.49), (531.5, 1.30), (546, 1.29)]] + [(0, yv(546))], 'antimony', parent=acc)
    kit.revolve('knurled ring core', [(0, yv(404)), (1.60, yv(404)), (1.60, yv(486)), (0, yv(486))], 'antimony', parent=acc)
    nk = 96
    for i in range(nk):     # fine knurl, broken by 8 smooth lands (end view shows 8 notches round the ring)
        a = 2 * math.pi * i / nk
        land = (i % 12) < 2
        kit.box('knurl' if not land else 'land', (2 * math.pi * 1.6 / nk * (.55 if not land else 1.05), yv(484) - yv(406), .06),
                (1.625 * math.sin(a), (yv(406) + yv(484)) / 2, 1.625 * math.cos(a)), 'antimony' if land else 'dark', rot=(0, a, 0), parent=acc)
    # ---- body: head + main body (gloss black) and aft section (gl. bluegray), lofted from both silhouettes ----
    body = kit.group('Body', root)
    head = body_loft('head and main body', 546, 1344, 'black'); head.parent = body
    aft = body_loft('aft section', 1340, 1738, 'bluegray'); aft.parent = body
    # forward lockplate: antimony plate forming the head's +Z face (side x 1196-1214, rows 556-652; top view white trapezoid)
    _, hx0, hx1, _, _ = section(600)
    kit.box('Forward lockplate', (2.3, yv(652) - yv(560), zs(1213) - zs(1196)), (0, (yv(560) + yv(652)) / 2, (zs(1196) + zs(1213)) / 2), 'antimony', bev=.03, parent=body)
    kit.box('Forward lockplate', (2.0, yv(560) - yv(549), zs(1205) - zs(1196)), (0, (yv(549) + yv(560)) / 2, (zs(1196) + zs(1205)) / 2), 'antimony', bev=.02, parent=body)
    # rear lockplate: ledge between the seat and the aft section (rows 1335-1350)
    _, rx0, rx1, rz0, rz1 = section(1330)
    kit.box('Rear lockplate', (rx1 - rx0 - .25, yv(1350) - yv(1335), zs(1182) - zs(1088)), (0, (yv(1335) + yv(1350)) / 2, (zs(1182) + zs(1088)) / 2), 'antimony', bev=.03, parent=body)
    # +Z spine on the aft section (top view: central strip x 618-648; side view: double line 8 px proud)
    sp = []
    for py in range(1352, 1726, 6):
        _, _, _, _, z1 = section(py); sp.append((yv(py), z1 - .1, z1 + .12))
    verts, faces = [], []
    for y_, za, zb in sp:
        for xx, zz in ((xt(648), za), (xt(618), za), (xt(618), zb), (xt(648), zb)): verts.append(Vector((xx, y_, zz)))
    for k in range(len(sp) - 1):
        for i in range(4): faces.append((4 * k + i, 4 * k + (i + 1) % 4, 4 * (k + 1) + (i + 1) % 4, 4 * (k + 1) + i))
    faces += [(3, 2, 1, 0), tuple(4 * (len(sp) - 1) + i for i in range(4))]
    mesh_from('aft spine', verts, faces, 'black', body, 0)
    # ---- dilithium crystal cell: slotted disc on the head's +X face (side view circle centre 944,645, dia 1.62) ----
    cz, cy = zs(944), yv(645); fx = min(face_x(py, z) for py in range(600, 691, 10) for z in (cz - .6, cz, cz + .6)) + .02
    # the circle is drawn whole, yet the head is wider (top view) above the neck it straddles: it sits in a round pocket
    cutter = kit.cyl('pocket cutter', .84, 3, (fx + 1.5, cy, cz), 'black', 'X')
    m = head.modifiers.new('pocket', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.modifier_move_to_index(modifier='pocket', index=0); bpy.ops.object.modifier_apply(modifier='pocket')
    bpy.data.objects.remove(cutter, do_unlink=True)
    cell = kit.group('Dilithium crystal cell', root)
    kit.cyl('cell', .80, .5, (fx - .2, cy, cz), 'antimony', 'X', parent=cell)
    kit.torus('cell bezel', .76, .035, (fx + .05, cy, cz), 'antimony', 'X', parent=cell)
    kit.box('cell slot', (.04, .08, 1.5), (fx + .06, cy, cz), 'black', parent=cell)
    # ---- deflector shield: three ribs along the barrel line on the +X face (side x 1008/1019/1031, rows 548-1110) ----
    ds = kit.group('Deflector shield', root)
    for px, py_end in ((1005, 1157), (1016, 1128), (1027, 1140)):
        z = zs(px); pts = []
        for py in list(range(548, py_end, 8)) + [py_end]: pts.append((face_x(py, z), yv(py)))
        verts, faces = [], []
        for k, (x_, y_) in enumerate(pts):
            verts += [Vector((x_ - .05, y_, z - .06)), Vector((x_ + .05, y_, z - .06)), Vector((x_ + .05, y_, z + .06)), Vector((x_ - .05, y_, z + .06))]
        for k in range(len(pts) - 1):
            for i in range(4): faces.append((4 * k + i, 4 * k + (i + 1) % 4, 4 * (k + 1) + (i + 1) % 4, 4 * (k + 1) + i))
        faces += [(3, 2, 1, 0), tuple(4 * (len(pts) - 1) + i for i in range(4))]
        mesh_from('deflector rib', verts, faces, 'dark', ds, 0)
    # fluted aft panel: five flutes on the +X face (side x 1062-1117, rows 1470-1741, running past the bottom edge)
    for px in (1062, 1075, 1089, 1103, 1117):
        z = zs(px); y0, y1 = yv(1472), yv(1741)
        x_ = max(face_x(py, z) for py in range(1474, 1730, 10))
        kit.cyl('deflector flute', .085, y1 - y0, (x_ - .07, (y0 + y1) / 2, z), 'bluegray', 'Y', parent=ds)
        kit.sphere('flute end', .085, (x_ - .07, y0, z), 'bluegray', parent=ds)
    # ---- force setting dial on the aft section's +Z face (side: flange x 1192-1212 rows 1417-1551, knob x 1216-1256 rows 1446-1527;
    #      top view: graduated face dia 1.85, hub 0.93) ----
    dial = kit.group('Force setting dial', root)
    dy = yv(1485); dx = xt(628)
    kit.cyl('dial base', .93, zs(1200) - zs(1176), (dx, dy, (zs(1200) + zs(1176)) / 2), 'antimony', 'Z', parent=dial)
    kit.cyl('dial cone', .93, zs(1214) - zs(1200), (dx, dy, (zs(1214) + zs(1200)) / 2), 'antimony', 'Z', r2=.80, parent=dial)
    for i in range(24):
        a = 2 * math.pi * i / 24
        kit.box('dial graduation', (.025, .14, .03), (dx + .84 * math.sin(a), dy + .84 * math.cos(a), zs(1211)), 'black', rot=(0, 0, -a), parent=dial)
    kit.cyl('dial knob', .62, zs(1256) - zs(1213), (dx, dy, (zs(1256) + zs(1213)) / 2), 'antimony', 'Z', seg=6, parent=dial)
    kit.cyl('dial hub', .3, .04, (dx, dy, zs(1256) + .02), 'dark', 'Z', parent=dial)
    # ---- lock release: tab on the +X side of the aft section (top x 535-557, rows 1395-1430; side circle at x 1135) ----
    lr = kit.group('Lock release', root)
    lz = zs(1111); ly = yv(1412); lx0 = face_x(1412, lz)
    kit.box('lock release tab', (xt(535) - lx0 + .1, yv(1430) - yv(1395), .5), ((xt(535) + lx0 - .1) / 2, ly, lz), 'black', bev=.03, parent=lr)
    kit.cyl('lock release button', .22, .06, (xt(535) + .02, ly, lz), 'antimony', 'X', parent=lr)
    # ---- grip (gloss black) with butt section seam, magnatomic adhesion areas and firing triggers ----
    grip = kit.group('Grip', root)
    seam = 130.0
    grip_loft('grip butt', 0, seam - 2, 'black', parent=grip)
    grip_loft('grip seam', seam - 3, seam + 3, 'dark', shrink=.03, parent=grip)
    grip_loft('grip', seam + 2, 800, 'black', parent=grip)
    mag = kit.group('Magnatomic adhesion areas', grip)
    stadium_pad('magnatomic adhesion area', 165, 650, -HW + .67 * PPC, -HW + 1.50 * PPC, GX - .03, .04, 'dark', mag)
    stadium_pad('magnatomic adhesion area', 148, 650, -HW + 2.02 * PPC, -HW + 2.90 * PPC, GX - .03, .04, 'dark', mag)
    trg = kit.group('Firing triggers', grip)   # S (safety) above T (trigger) on the grip's front face, just below the body
    for nm, tc in (('S safety', 722), ('T trigger', 668)):
        oriented_box(nm, tc - .36 * PPC, tc + .36 * PPC, -HW - .07 * PPC, -HW + .05 * PPC, -.37, .37, 'antimony', trg)
    # ---- Hand Phaser Type I, locked on: face plate in the forward lockplate recess (front at row 603), tail at the rear lockplate ----
    side1 = kit.load_profile('phaser-1-side')
    L1 = phaser_1.L_DRAWN * phaser_1.SCALE_L
    oy = yv(603) + L1 / 2
    contact = []
    for k in range(40, 1020, 5):            # T1 underside (its side-profile 'hi' edge) must clear the seat everywhere
        s = k / 100.0
        if s > phaser_1.L_DRAWN - .3: break
        wy = oy + phaser_1.SCALE_L * (-phaser_1.L_DRAWN / 2 + s)
        py = TIP + (wy - Y0) / SY * PPC
        if not 660 <= py <= 1330: continue
        seat = kit.sample(SIDE, (py - TIP) / PPC, 2)[1]
        contact.append(seat + kit.sample(side1, s, 6)[1])
    # the seat follows the Type I's underside: seat + underside depth is ~constant (1.94-2.10 cm) along 9 cm of contact;
    # one local bump of the Type I's underside (s ~2.4 cm) would lift it 0.2 cm, so take the 85th percentile
    contact.sort(); oz = contact[int(.85 * (len(contact) - 1))]
    t1 = phaser_1.build(parent=root, origin=(0, oy, oz))
    print('TYPE I origin', round(oy, 3), round(oz, 3))
    return root, t1

def export_without(item_id, objs, out_dir):
    """write a second GLB without the given objects (and their children) — the plates draw the Type I as a phantom"""
    kill = set()
    for o in objs:
        kill.add(o); kill.update(o.children_recursive)
    for o in kill: bpy.data.objects.remove(o, do_unlink=True)
    os.makedirs(out_dir, exist_ok=True)
    for o in bpy.context.scene.objects: o.select_set(o.type in ('MESH', 'EMPTY'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, item_id + '.glb'), export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_materials='EXPORT', export_extras=False)

if __name__ == '__main__':
    kit.reset(); root, t1 = build(); kit.export('phaser-2')
    export_without('phaser-2', [t1], os.path.join(kit.ROOT, 'model-source', 'accuracy', 'out', 'phaser-2', 'score-glb'))
