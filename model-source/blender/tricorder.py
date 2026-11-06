"""Sciences / Medical Tricorder (shared case) — Sciences PDF 112-114 (TO 02:04:00/01/03), Medical PDF 124-126 (TO 02:11:00/01/02).
Run:  Blender -b -P model-source/blender/sciences_tricorder.py [-- <pose> <out_dir>]
      Blender -b -P model-source/blender/medical_tricorder.py  [-- <pose> <out_dir>]
pose: 'open' (site GLB, default) | 'closed' | 'section' (head open, lids shut: the PDF 126 internal-arrangement pose).
      Non-default poses export as <id>-<pose>.glb (for the accuracy harness), never into dist/.
Plain python (no Blender):  python3 tricorder.py --plates   writes the mirrored half-view plates used by the *-closed views.

Printed: H.O.A. (closed) 177.8 mm, W.O.A. 114.3 mm, D.O.A. 48.3 mm; 8 record/play discs 31.75 dia x 5.58 mm.
Coordinates (cm): X across (+X = item's left/port), Y depth (front = -Y), Z up, Z = 0 at the case top, X = 0 on the centreline,
Y = 0 on the mid-line of the measured side-view silhouette.

Geometry, all measured on the plates:
 * Case envelope: lofted rounded-rectangle sections whose width follows the open front view (PDF 113 / 125) and whose depth
   follows the closed side view (PDF 112 / 124): deepest in the upper third, tapering to the base.
 * Display-control head: its side outline is digitised from the PDF 126 internal section (head drawn open), extruded across the
   head width measured on PDF 113 / 125, and hung on the pivot (18.54 mm below the case top as printed on PDF 114 View C-C;
   ~4.8 mm behind the depth centre as drawn on PDF 112, 114 and 124 — the printed 3.08 mm is not what the views draw).
   Closed -> open is a 125.6 deg swing up and back about that pivot: the angle between the head-tip positions at the two ends
   of the dash-dot swing arc on PDF 112 (the arc is centred on the hub). Open, the faceplate leans back 24.6 deg (PDF 126),
   which is why it projects 4.4 cm tall in the open front views; closed, the head's back face becomes the head-cover band.
 * Front details: positions read on the open front view (px) and mapped onto the case front / the tilted faceplate.
"""
import sys, os, math, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OPEN_ANGLE = 125.6          # deg, closed -> open, PDF 112 swing arc
PIVOT_DROP = 1.854          # cm below case top, PDF 114 View C-C (18.54 mm)

# ---------------------------------------------------------------- per-variant plate data
# Head outline (open pose) digitised on PDF 126 left section (68.01 px/cm), pivot located there at (615, 659):
# case top y533 + 18.54 mm; 2.78 cm behind the drawn case front (x426), the same pivot-to-front distance as PDF 112/124.
P126, PPC126 = (615.0, 659.0), 68.01
HEAD_PX = [(645, 436), (675, 463), (705, 493), (735, 523), (765, 553), (785, 573), (795, 585), (801, 600), (801, 618),
           (790, 640), (772, 668), (752, 700), (735, 730), (715, 762), (692, 788), (665, 804), (637, 811), (612, 806),
           (590, 795), (560, 775), (530, 752), (510, 735)]          # tip T first, faceplate base F last
FP_PX = (637, 522)   # the faceplate runs from F up through this point (30.8 deg back from vertical); above the faceplate's
                     # top (the front-view lip row) the outline steps forward to the tip: the black lip seen on PDF 113/125.
VARIANTS = {
    'sciences-tricorder': dict(
        side='sciences-tricorder-side', front='sciences-tricorder-front',
        front2='sciences-tricorder-front-closed',  # PDF 112 closed half view (mirrored); case width = mean of 112 and 113
        side_px=(1111.0, 468, 67.61),            # PDF 112 side view: profile mid-line x, case-top y, px/cm
        pivot_px=(1148, 595),                    # hub (dashed circle) on PDF 112
        fv=(685.0, 475, 67.94),                  # PDF 113 open front: centreline x, shell-top y, px/cm
        head_w=8.85, frame=(4.425, 4.645),
        top_lip=395,                             # faceplate starts below this row (PDF 113)
        bezel=(400, 413, 755, 664), screen=(418, 428, 745, 648), sensor=(812, 420, 900, 515),
        leds=[(797, 548), (866, 548), (935, 548)], knobs=[(797, 622), (866, 622), (935, 622)],
        frame_member=(680, 765), comp=(765, 1012), discs=(392, 712, 785), holder=(975, 1012), ledge=(1012, 1020),
        disc_bar=(712, 726, 783),                # PDF 113: vertical holder bar right of the stack (x0, x1, top row)
        rim='antimony',                          # PDF 113: plain (white) rim 378-407 above the faceplate; PDF 125 draws it pebbled
        sill=671,                                # faceplate's drawn lower edge; white down to the frame member (680)

        speaker_plate=728, speaker=(862, 885, 108, 88), grille='star',
        rc_lid=dict(hinge=1020, length=4.60, open=103.5), lower_seam=1092,
        screw_px=(1113, 665),
        # outlined bracket (PDF 112 side): band centreline from the left curl tip, down the left arm, across behind the
        # strap tab, up the right arm to the right curl tip; band width in cm
        bracket=[(1045, 512), (1030, 505), (1012, 512), (1004, 530), (1008, 560), (1050, 690), (1060, 702), (1175, 702), (1186, 690),
                 (1214, 560), (1218, 530), (1211, 512), (1202, 505), (1188, 512)], bracket_w=0.30,
        strap_y=(1055, 1180), tab=(690, 1057),   # PDF 112 side: strap tab top row, break-line row (5.43 cm)
        # strap centreline (offset out from the shell side, depth below the top), traced on the plates' ink
        strap_open=[(0, 3.30), (.20, 3.25), (.35, 3.30), (.42, 3.50), (.47, 3.72), (.51, 3.95), (.54, 4.2), (.56, 4.43)],   # PDF 113
        strap_closed=[(0, 3.10), (.35, 3.43), (.61, 3.88), (.74, 4.32), (.84, 4.76), (.96, 5.65), (1.0, 6.54), (1.0, 7.42), (.95, 8.31), (.89, 8.9)],  # PDF 112
    ),
    'medical-tricorder': dict(
        side='medical-tricorder-side', front='medical-tricorder-front',
        side_px=(1077.0, 385, 68.35), pivot_px=(1120, 512), fv=(848.5, 457, 68.35),
        head_w=8.82, frame=(4.41, 4.66), top_lip=392,
        bezel=(553, 393, 928, 662), screen=(572, 408, 912, 648), sensor=(980, 405, 1065, 490),
        leds=[(955, 530), (1030, 530), (1105, 530)], knobs=[(955, 612), (1030, 612), (1105, 612)],
        frame_member=(655, 748), comp=(748, 1000), discs=(550, 875, 752), holder=(958, 1000), ledge=(1000, 1015),
        disc_bar=(875, 888, 752), disc_grooves=True,   # PDF 125: separator strips between the discs
        sill=648,

        speaker_plate=880, speaker=(1020, 878, 109, 85), grille='wave',
        rc_lid=dict(hinge=1015, length=3.88, open=100.3, plate=(1.02, 1.68)),
        bay=(1015, 1062), analyzer=(550, 668, 1062, 1095),
        lower_lid=dict(hinge=-17.6, top=-8.16, open=56.9, plate=(1.94, 2.63)),   # PDF 124 closed lid, PDF 125 projection
        screw_px=(1086, 585),
        bracket=[(1012, 430), (998, 423), (988, 432), (986, 455), (1022, 610), (1030, 622), (1150, 622), (1158, 610),
                 (1194, 455), (1190, 435), (1180, 424), (1167, 428)], bracket_w=0.10,   # PDF 124: single heavy line
        strap_y=(1027, 1150), tab=(611, 777), lugs=[770, 1100],   # PDF 124 side: tab 2.43 cm
        strap_open=[(0, 3.45), (.20, 3.40), (.30, 3.50), (.32, 3.65), (.30, 3.85)],          # PDF 125
        strap_closed=[(0, 3.15), (.16, 3.29), (.42, 3.58), (.56, 3.88), (.66, 4.17), (.75, 4.46), (.80, 4.75), (.85, 5.05), (.86, 5.34), (.87, 5.56)],  # PDF 124
    ),
}
# PDF 114 View C-C (67.94 px/cm; frame centre x1046.5, top y482): 3 mm vent holes, 11 each side, in the side frame.
VENTS_PX = [(958, 1500), (1000, 1500), (1043, 1500), (1086, 1500), (1130, 1500),
            (960, 1028), (988, 996), (1016, 965), (1044, 932), (1072, 897), (1100, 866)]

# ---------------------------------------------------------------- mirrored half-view plates (plain python)
def make_plates():
    """PDF 112 / 124 draw the closed front as a half view about the marked centreline (SYMMETRY / CL SYM).
    Mirror the drawn right half about that line so the closed front can be scored as a whole silhouette."""
    from PIL import Image
    for item, page, cl, right in (('sciences-tricorder', 112, 381, 850), ('medical-tricorder', 124, 322, 800)):
        im = Image.open(os.path.join(ROOT, 'dist', 'assets', 'equipment', f'page-{page}.webp')).convert('L')
        half = im.crop((cl, 0, right, im.height)); w = right - cl
        out = Image.new('L', (2 * w, im.height), 255); out.paste(half.transpose(Image.FLIP_LEFT_RIGHT), (0, 0)); out.paste(half, (w, 0))
        d = os.path.join(ROOT, 'model-source', 'accuracy', 'helpers', 'plates'); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f'plate-{page}-front-mirrored.png'); out.save(p); print(p, out.size, 'centreline at x', w)

if __name__ == '__main__' and '--plates' in sys.argv:
    make_plates(); sys.exit(0)

# ---------------------------------------------------------------- Blender part
import bpy, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, HERE)
import kit

def clean(prof, drop_thin=0.5, win=45, tol=0.04):
    """Drop stray rows at the ends (phantom lines, base edge) and replace isolated bumps (leaders, lugs) by the running median."""
    rows = prof['rows']; W = max(r[2] - r[1] for r in rows)
    while rows and rows[0][2] - rows[0][1] < drop_thin: rows = rows[1:]
    while rows and rows[-1][2] - rows[-1][1] < drop_thin * W: rows = rows[:-1]
    import statistics
    out = []
    for i, r in enumerate(rows):
        k = min(win, i, len(rows) - 1 - i); w = rows[i - k:i + k + 1]
        ml, mh = statistics.median(x[1] for x in w), statistics.median(x[2] for x in w)
        out.append([r[0], r[1] if abs(r[1] - ml) < tol else ml, r[2] if abs(r[2] - mh) < tol else mh])
    s0 = out[0][0]
    prof['rows'] = [[r[0] - s0, r[1], r[2]] for r in out]
    prof['s0'] = s0
    return prof

def fair(prof, lam_mid=1e7, lam_end=3.0, edge=0.9, ramp=0.6, tol=0.035, iters=5):
    """Fair a measured silhouette for lofting: robust Whittaker smoother (3rd differences) on lo and hi.
    The plates draw the case sides as straight-ish ink lines; 2-px rows step the slope in ~0.1 jumps, and the loft
    rings, sampled every 1-2 mm, turn that into horizontal shading bands. The penalty is strong along the straight run
    and relaxed over the last `edge` cm at each end so the rounded top/base corners keep their drawn shape.
    Rows further than `tol` cm from the fit (held values where the strap or a leader crosses the outline) are down-weighted."""
    import numpy as np
    r = np.array(prof['rows'], float); s = r[:, 0]; n = len(s); H = s[-1]
    D = np.diff(np.eye(n), 3, axis=0); sm = (s[:-3] + s[3:]) / 2
    t = np.clip((np.minimum(sm, H - sm) - edge) / ramp, 0, 1); t = t * t * (3 - 2 * t)
    lam = np.exp(np.log(lam_end) + (np.log(lam_mid) - np.log(lam_end)) * t)
    P = D.T @ (lam[:, None] * D)
    for c in (1, 2):
        y = r[:, c]; w = np.ones(n)
        for _ in range(iters):
            z = np.linalg.solve(np.diag(w) + P, w * y)
            e = np.abs(z - y) / tol; w = np.where(e < 1, 1.0, 1.0 / (e * e))
        r[:, c] = z
    prof['rows'] = r.tolist()
    return prof

class Case:
    def __init__(self, V):
        self.V = V
        self.side = fair(clean(kit.load_profile(V['side']), drop_thin=0.3))
        self.front = fair(clean(kit.load_profile(V['front'])))
        self.front2 = fair(clean(kit.load_profile(V['front2']))) if V.get('front2') else None
        # side rows start at the case top: the first row kept is z = 0
        self.H = self.side['rows'][-1][0]
        sx, sy, sp = V['side_px']
        self.ppc_side = sp
    def half(self, s):
        lo, hi = kit.sample(self.front, max(s, 0))
        if self.front2:
            lo2, hi2 = kit.sample(self.front2, max(s, 0)); return ((hi - lo) + (hi2 - lo2)) / 4
        return (hi - lo) / 2
    def yr(self, s):
        return kit.sample(self.side, min(max(s, 0), self.H))
    def yfront(self, s): return self.yr(s)[0]

def rrect(a, y0, y1, r, n=5, x0=None, x1=None):
    """Rounded rectangle in XY: x in [-a, a] (or [x0, x1]), y in [y0, y1]."""
    x0 = -a if x0 is None else x0; x1 = a if x1 is None else x1
    r = max(1e-3, min(r, (x1 - x0) / 2 - 1e-4, (y1 - y0) / 2 - 1e-4))
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            t = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts

def loft_z(name, sections, material, parent=None):
    """sections: [(z, [(x, y), ...]), ...] top to bottom, equal point counts; capped."""
    bm = bmesh.new(); rings = [[bm.verts.new((x, y, z)) for x, y in pts] for z, pts in sections]
    n = len(rings[0])
    for k in range(len(rings) - 1):
        for i in range(n):
            bm.faces.new((rings[k][i], rings[k][(i + 1) % n], rings[k + 1][(i + 1) % n], rings[k + 1][i]))
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kit.mat(material))
    if parent: o.parent = parent
    return o

def s_steps(H, n=140):
    return [H * (0.5 - 0.5 * math.cos(math.pi * i / n)) for i in range(n + 1)]

def envelope(C, name, material, r=0.7, grow=0.0, xr=None):
    secs = []
    for s in s_steps(C.H):
        y0, y1 = C.yr(s); a = C.half(s)
        if xr: pts = rrect(None, y0 - grow, y1 + grow, 0.05, 2, xr[0], xr[1])
        else: pts = rrect(a + grow, y0 - grow, y1 + grow, r)
        secs.append((-s, pts))
    return loft_z(name, secs, material)

def apply_bool(obj, cutter, op='DIFFERENCE'):
    m = obj.modifiers.new('b', 'BOOLEAN'); m.operation = op; m.object = cutter; m.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev); obj.modifiers.clear(); old = obj.data; obj.data = me
    bpy.data.meshes.remove(old)

def delete(o):
    bpy.data.objects.remove(o, do_unlink=True)

def prism(name, poly, x0, x1, material, parent=None):
    """Polygon in (y, z) extruded along X from x0 to x1."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in poly]; b = [bm.verts.new((x1, y, z)) for y, z in poly]
    n = len(poly); bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kit.mat(material))
    if parent: o.parent = parent
    return o

def prism_y(name, poly, y0, y1, material, parent=None):
    """Polygon in (x, z) extruded along Y from y0 to y1."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y1, z)) for x, z in poly]
    n = len(poly); bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kit.mat(material)); o.parent = parent
    return o

def plate_xy(name, pts, z0, z1, material, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Outline in local XY extruded along local Z (z0..z1)."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y, z0)) for x, y in pts]; b = [bm.verts.new((x, y, z1)) for x, y in pts]
    n = len(pts); bm.faces.new(list(reversed(a))); bm.faces.new(b)
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kit.mat(material)); o.parent = parent; o.location = loc; o.rotation_euler = rot
    return o

def sweep_xz(name, path, y0, y1, thick, material, parent=None):
    """Flat band: path [(x, z), ...] in XZ, constant Y span, thickness across the path."""
    bm = bmesh.new(); rings = []
    for i, (x, z) in enumerate(path):
        a = path[max(i - 1, 0)]; b = path[min(i + 1, len(path) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, tz) or 1; nx, nz = -tz / L * thick / 2, tx / L * thick / 2
        rings.append([bm.verts.new(c) for c in ((x - nx, y0, z - nz), (x + nx, y0, z + nz), (x + nx, y1, z + nz), (x - nx, y1, z - nz))])
    for k in range(len(rings) - 1):
        for i in range(4): bm.faces.new((rings[k][i], rings[k][(i + 1) % 4], rings[k + 1][(i + 1) % 4], rings[k + 1][i]))
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kit.mat(material)); o.parent = parent
    return o

def tube(name, pts, r, material, parent=None, seg=8):
    """Round wire along a 3-D polyline (local coords)."""
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)]); b = Vector(pts[min(i + 1, len(pts) - 1)]); t = (b - a).normalized()
        u = t.cross(Vector((0, 0, 1))) if abs(t.z) < .9 else t.cross(Vector((1, 0, 0))); u.normalize(); v = t.cross(u)
        rings.append([bm.verts.new(Vector(p) + r * (math.cos(2 * math.pi * k / seg) * u + math.sin(2 * math.pi * k / seg) * v)) for k in range(seg)])
    for k in range(len(rings) - 1):
        for i in range(seg): bm.faces.new((rings[k][i], rings[k][(i + 1) % seg], rings[k + 1][(i + 1) % seg], rings[k + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(kit.mat(material)); o.parent = parent
    return kit.smooth(o, 60)

# ---------------------------------------------------------------- build
def build(item, pose='open'):
    V = VARIANTS[item]; C = Case(V)
    sx, stop, sp = V['side_px']; cx, ftop, fp = V['fv']
    X = lambda px: (px - cx) / fp                    # open front view px -> x (image right = +X: viewed from -Y)
    Zf = lambda py: -(py - ftop) / fp                # open front view px -> z
    Ys = lambda px: (px - sx) / sp                   # side view px -> y (front drawn at left: viewed from +X)
    Zs = lambda py: -(py - stop) / sp + C.side['s0']
    head_open = pose in ('open', 'section'); lids_open = pose == 'open'
    hw = V['head_w'] / 2; fr0, fr1 = V['frame']
    pv = (Ys(V['pivot_px'][0]), -PIVOT_DROP)

    root = kit.group('Tricorder')
    # ---- case envelope (side storage shells + core), head slot and front compartments cut out
    body = envelope(C, 'case body (pebbled)', 'pebbled'); body.parent = root
    yf_top = C.yfront(3.0)
    slope = 0.195                                    # slot floor rises toward the back so the shut head leaves no gap
    zf = lambda y: -3.0 + (y - yf_top) * slope
    slot = prism('slot', [(-4, zf(-4)), (4, zf(4)), (4, 4), (-4, 4)], -hw - .005, hw + .005, 'dark')
    apply_bool(body, slot); delete(slot)
    def recess(z0, z1, depth, x0=-fr0, x1=fr0):
        y0 = min(C.yfront(-z0), C.yfront(-z1)) - 1
        c = prism('cut', [(y0, z0), (C.yfront(-(z0 + z1) / 2) + depth, z0), (C.yfront(-(z0 + z1) / 2) + depth, z1), (y0, z1)], x0, x1, 'dark')
        apply_bool(body, c); delete(c)
    zc0, zc1 = Zf(V['comp'][1]), Zf(V['comp'][0])           # record-compare compartment
    if lids_open:
        recess(zc0, zc1, 3.95)
        if 'bay' in V: recess(-17.45, Zf(V['bay'][0]) - .02, 3.4)
    kit.smooth(body, 35)
    # ---- brushed case frames (C-channel strip between core and each shell, full height)
    for sgn in (1, -1):
        f = envelope(C, 'case frame (brushed)', 'brushed', grow=0.025, xr=(fr0 - .006, fr1) if sgn > 0 else (-fr1, -fr0 + .006)); f.parent = root
    # ---- display-control head
    head = kit.group('display-control head', root); head.location = (0, pv[0], pv[1])
    uv = lambda px, py: ((px - P126[0]) / PPC126, -(py - P126[1]) / PPC126)
    pts = [uv(*p) for p in HEAD_PX]
    F = Vector((0, *pts[-1])); d = (Vector((0, *uv(*FP_PX))) - F).normalized()
    # faceplate top: the front-view lip row, but no higher than 0.95 cm above the case top — beyond that the 30.8 deg
    # faceplate would leave the drawn head outline (Sciences draws a thinner lip than the Medical sheet; same head).
    t_lip = (min(Zf(V['top_lip']), 0.95) - pv[1] - F.z) / d.z
    P1 = F + d * t_lip; pts.append((P1.y, P1.z))
    shell = prism('head shell (pebbled)', pts, -hw + .002, hw - .002, 'pebbled', parent=head)
    parts = [shell]
    if V.get('rim'):     # PDF 113 draws the rim above the faceplate plain (white antimony), not pebbled: skin the lip P1 -> T
        T = Vector((0, *pts[0])); e = (T - P1); n = Vector((0, e.z, -e.y)).normalized()
        if n.y > 0: n = -n                                     # outward = toward the front of the open head
        ext = (T - Vector((0, *pts[1]))).normalized() * 0.02    # wrap a hair over the tip
        k = 0.015
        poly = [(P1.y - d.y * 0.02, P1.z - d.z * 0.02), (T.y + ext.y, T.z + ext.z),
                (T.y + ext.y + n.y * k, T.z + ext.z + n.z * k), (P1.y - d.y * 0.02 + n.y * k, P1.z - d.z * 0.02 + n.z * k)]
        parts.append(prism('head top rim (antimony)', poly, -hw + .001, hw - .001, V['rim'], parent=head))
    env = envelope(C, 'env', 'dark', r=0.7, grow=0.12)   # keeps the drawn tip, trims the corner that would stand proud when shut
    head.rotation_euler = (math.radians(OPEN_ANGLE), 0, 0); bpy.context.view_layer.update()
    for o in parts: apply_bool(o, env, 'INTERSECT')           # trimmed to the case where it is housed when shut
    delete(env)
    kit.smooth(shell, 35)
    head.rotation_euler = (0 if head_open else math.radians(OPEN_ANGLE), 0, 0)
    # faceplate frame: local X = x, local Y = up the faceplate (F -> T), local Z = outward normal (front-up)
    fpf = kit.group('faceplate frame', head); fpf.location = F
    # Rx(theta) maps local Y to (0, cos, sin): we need d -> theta = atan2(d.z, d.y)
    fpf.rotation_euler = (math.atan2(d.z, d.y), 0, 0)
    t_of = lambda py: (Zf(py) - pv[1] - F.z) / d.z     # open-front row -> distance up the faceplate
    def fbox(name, x0, x1, py0, py1, h0, h1, material, r=0.0):
        pts2 = rrect(None, t_of(py1), t_of(py0), r, 4, X(x0), X(x1)) if r else [(X(x0), t_of(py1)), (X(x1), t_of(py1)), (X(x1), t_of(py0)), (X(x0), t_of(py0))]
        return plate_xy(name, pts2, h0, h1, material, parent=fpf)
    def fcyl(name, px, py, r, h0, h1, material, r2=None, seg=40):
        o = kit.cyl(name, r, h1 - h0, (X(px), t_of(py), (h0 + h1) / 2), material, 'Z', r2=r2, seg=seg, parent=fpf); return o
    t_hi = t_of(V['top_lip'])
    plate_xy('video/controls faceplate (antimony)', [(-hw + .06, 0.04), (hw - .06, 0.04), (hw - .06, t_hi), (-hw + .06, t_hi)], -0.02, 0.04, 'antimony', parent=fpf)
    b = V['bezel']; s_ = V['screen']; sn = V['sensor']
    fbox('video display bezel', b[0], b[2], b[1], b[3], 0.04, 0.10, 'antimony', r=0.45)
    fbox('video display', s_[0], s_[2], s_[1], s_[3], 0.10, 0.13, 'olive', r=0.6)
    fbox('sensor array window', sn[0], sn[2], sn[1], sn[3], 0.02, 0.06, 'dark')
    # cross-hatched lattice: diagonal bars both ways, clipped to the window
    w0, w1, t0, t1 = X(sn[0]), X(sn[2]), t_of(sn[3]), t_of(sn[1])
    for k in range(-6, 7):
        for sg in (1, -1):
            c = (w0 + w1) / 2 + k * 0.22
            # recompute the clipped segment end so it stays on the 45 deg line
            (xa, ta), (xb, tb) = [(c + sg * (tt - (t0 + t1) / 2), tt) for tt in (t0, t1)]
            seg = []
            for f_ in [i / 20 for i in range(21)]:
                xx, tt = xa + (xb - xa) * f_, ta + (tb - ta) * f_
                if w0 <= xx <= w1: seg.append((xx, tt, 0.075))
            if len(seg) > 1: tube('sensor array lattice', seg, 0.018, 'antimony', parent=fpf, seg=6)
    for (px, py), col, nm in zip(V['leds'], ('blue', 'amber', 'red'), ('matched comparison light (blue)', 'sub-normal light (amber)', 'danger-alarm light (red)')):
        fcyl(nm + ' bezel', px, py, 0.30, 0.0, 0.16, 'antimony')
        kit.sphere(nm, 0.22, (X(px), t_of(py), 0.16), col, scale=(1, 1, .7), parent=fpf)
    for (px, py), nm in zip(V['knobs'], ('disc selector w/light', 'channel selector w/light', 'record/play w/vol. & light')):
        fcyl(nm + ' bezel', px, py, 0.42, 0.0, 0.06, 'antimony')
        fcyl(nm + ' knob', px, py, 0.34, 0.06, 0.52, 'black', r2=0.27)
        for k in range(16):                           # knurling
            a = 2 * math.pi * k / 16
            o = kit.box(nm + ' knurl', (0.05, 0.05, 0.42), (X(px) + 0.31 * math.cos(a), t_of(py) + 0.31 * math.sin(a), 0.29), 'black', parent=fpf)
            o.rotation_euler = (0, 0, a)
        kit.sphere(nm + ' (green L.E.D.)', 0.09, (X(px), t_of(py), 0.53), 'green', parent=fpf)
    # head side plates: pivot hub (12.70 mm O.D.) each end, on the pivot axis
    for sg in (1, -1):
        kit.cyl('head pivot hub', 0.635, 0.12, (sg * (hw - 0.04), 0, 0), 'brushed', 'X', parent=head)

    # ---- core front, open arrangement (front-view rows mapped onto the drawn front face)
    def front_plate(name, x0, x1, py0, py1, depth, material, proud=0.02):
        z0, z1 = Zf(py1), Zf(py0)
        y = min(C.yfront(-z0), C.yfront(-z1))
        return kit.box(name, (x1 - x0, depth, z1 - z0), ((x0 + x1) / 2, y - proud + depth / 2, (z0 + z1) / 2), material, parent=root)
    fm = V['frame_member']
    if head_open:
        front_plate('frame member (antimony)', -fr0, fr0, fm[0], fm[1], 0.6, 'antimony')
        # neither plate draws the case lip between the faceplate's lower edge and the frame member dark: carry the
        # antimony up behind the faceplate so no pebbled strip shows there
        # the head slot's floor rises toward the faceplate base and showed from the front as a pebbled strip: cover it up to the
        # floor height under the faceplate (no higher than needed, so the faceplate itself is not hidden)
        z0 = Zf(fm[0]); z1 = max(Zf(V['sill']), zf(pv[0] + F.y) + 0.02)
        kit.box('frame member upper lip (antimony)', (2 * fr0, 0.4, z1 - z0), (0, C.yfront(-z0) - 0.02 + 0.2, (z0 + z1) / 2), 'antimony', parent=root)
    else:         # shut, the head's tip (3.4 cm below the top) laps over the upper edge of the frame member
        kit.box('frame member (antimony)', (2 * fr0, 0.6, Zf(fm[0]) + 3.45), (0, C.yfront(3.8) - 0.02 + 0.3, (Zf(fm[1]) - 3.45) / 2), 'antimony', parent=root)
    rcl = V['rc_lid']; zh = Zf(rcl['hinge']); yh = C.yfront(-zh)
    if lids_open:
        xs = X(V['speaker_plate'])
        front_plate('speaker faceplate', xs, fr0, V['comp'][0], V['comp'][1], 0.5, 'pebbled', proud=-0.05)
        yb = C.yfront(-(zc0 + zc1) / 2) + 3.95
        kit.box('compartment back', (2 * fr0, 0.1, zc1 - zc0), (0, yb - 0.05, (zc0 + zc1) / 2), 'dark', parent=root)
        d0, d1, dtop = V['discs']; pitch = (d1 - d0) / 8; rd = 1.5875; zd = Zf(dtop) - rd; yd = C.yfront(-zd) + 2.25
        for i in range(8):                         # flat-faced discs (the plates draw plain rectangles edge-on)
            xd = X(d0 + pitch * (i + .5))
            kit.cyl('removable play/record disc', rd, 0.558, (xd, yd, zd), 'white', 'X', seg=72, parent=root)
            if V.get('disc_grooves') and i < 7:    # PDF 125: separator strip between neighbouring discs
                xb = X(d0 + pitch * (i + 1)); g = max(pitch / fp - 0.558 - 0.004, 0.02)
                kit.cyl('disc separator', rd - 0.12, g, (xb, yd, zd), 'dark', 'X', seg=48, parent=root)   # recessed: reads as a groove
        if V.get('disc_bar'):                      # vertical holder bar at the right of the stack
            bx0, bx1, btop = V['disc_bar']; zt, zb = Zf(btop), Zf(V['holder'][0])
            kit.box('disc holder bar', (X(bx1) - X(bx0), 2.2, zt - zb), ((X(bx0) + X(bx1)) / 2, C.yfront(-(zt + zb) / 2) + 0.1 + 1.1, (zt + zb) / 2), 'antimony', parent=root)
        h = V['holder']
        front_plate('disc holder frame', -fr0, xs, h[0], h[1], 2.2, 'antimony', proud=-0.1)
        kit.box('compression plate', (0.08, 3.4, Zf(V['discs'][2]) - Zf(h[1])), (X(d0) - 0.05, yd, (Zf(V['discs'][2]) + Zf(h[1])) / 2), 'antimony', parent=root)
        lg = V['ledge']; front_plate('disc holder ledge', -fr0, fr0, lg[0], lg[1], 0.8, 'antimony')
        # speaker / mic grille
        spx, spy, ro, ri = V['speaker']; xsp, zsp = X(spx), Zf(spy); ysp = C.yfront(-zsp) - 0.06
        kit.cyl('speaker/mic ring', ro / fp, 0.08, (xsp, ysp, zsp), 'antimony', 'Y', seg=64, parent=root)
        kit.cyl('speaker/mic grille', ri / fp, 0.04, (xsp, ysp - 0.05, zsp), 'dark', 'Y', seg=64, parent=root) if V['grille'] != 'star' else None
        R = ri / fp
        if V['grille'] == 'star':
            # PDF 113: white grille inside a black rim line; in each half ~13 nested arcs concentric about the star point at the
            # rim (top half about the top point, bottom half about the bottom point) fill the disc; a solid black four-pointed
            # star with concave sides lies over them, a white inner outline and a white "C" mark at its centre.
            kit.cyl('speaker/mic grille rim line', R, 0.04, (xsp, ysp - 0.05, zsp), 'black', 'Y', seg=72, parent=root)
            kit.cyl('speaker/mic grille (white)', R - 0.03, 0.01, (xsp, ysp - 0.075, zsp), 'white', 'Y', seg=72, parent=root)
            Rin = R - 0.035; yarc = ysp - 0.083
            for sgn in (1, -1):
                cz = zsp + sgn * R
                for k in range(1, 20):
                    rr = k * R / 13.5; run = []
                    for j in range(91):
                        th = -math.pi / 2 + math.pi * j / 90
                        x_, z_ = xsp + rr * math.sin(th), cz - sgn * rr * math.cos(th)
                        ok = math.hypot(x_ - xsp, z_ - zsp) <= Rin and sgn * (z_ - zsp) >= 0
                        if ok: run.append((x_, yarc, z_))
                        if (not ok or j == 90) and run:
                            if len(run) > 2: tube('speaker grille arc', run, 0.011, 'black', parent=root, seg=5)
                            run = []
            def astroid(sc, q=3.2, n=128):
                out = []
                for k in range(n):
                    a = 2 * math.pi * k / n; c_, s2 = math.cos(a), math.sin(a)
                    out.append((xsp + sc * math.copysign(abs(c_) ** q, c_), zsp + sc * math.copysign(abs(s2) ** q, s2)))
                return out
            prism_y('speaker grille star', astroid(R * 0.985), ysp - 0.11, ysp - 0.07, 'black', parent=root)
            line = [(x_, ysp - 0.112, z_) for x_, z_ in astroid(R * 0.66)]
            tube('speaker grille star inner line', line + line[:2], 0.011, 'white', parent=root, seg=5)
            tube('speaker grille "C" mark', [(xsp + 0.075 * math.cos(math.radians(a)), ysp - 0.112, zsp + 0.075 * math.sin(math.radians(a))) for a in range(40, 325, 15)],
                 0.016, 'white', parent=root, seg=6)
        else:                                     # PDF 125: wavy horizontal lines
            for k in range(-9, 10):
                zz = zsp + k * R / 9.5; half = math.sqrt(max(R * R - (zz - zsp) ** 2, 0)) - 0.03
                if half < 0.1: continue
                tube('speaker grille wave', [(xsp + xx, ysp - 0.08, zz + 0.035 * math.sin(xx * 9)) for xx in [-half + 2 * half * j / 30 for j in range(31)]],
                     0.014, 'antimony', parent=root, seg=5)
        if 'bay' in V:                             # Medical: life-form functions sensor/analyzer bay below the R/P lid
            a = V['analyzer']; za0, za1 = -17.4, Zf(a[2]); yfa = C.yfront(-(za0 + za1) / 2)
            kit.box('life form functions sensor/analyzer', (X(a[1]) - X(a[0]), 1.6, za1 - za0), ((X(a[0]) + X(a[1])) / 2, yfa + 0.3 + 0.8, (za0 + za1) / 2), 'pebbled', bev=.03, parent=root)
            kit.box('sensor/analyzer cap', (X(a[1]) - X(a[0]) - 0.04, 1.62, Zf(a[2]) - Zf(a[3])), ((X(a[0]) + X(a[1])) / 2, yfa + 1.1, (Zf(a[2]) + Zf(a[3])) / 2), 'antimony', parent=root)
            zb1 = Zf(V['bay'][0])
            kit.box('analyzer bay back (circuitry, classified)', (2 * fr0, 0.1, zb1 + 17.45), (0, C.yfront(10) + 3.35, (zb1 - 17.45) / 2), 'white', parent=root)   # drawn blank (white) on PDF 125
    # ---- lids (hinged at the front edge, as PDF 126 draws them); open angles from the open front views
    def lid(name, z_h, L, ang, plate=None):
        y_h = C.yfront(-z_h); y_t = C.yfront(-(z_h + L))
        base = math.atan2(-(y_t - y_h), L)
        g = kit.group(name, root); g.location = (0, y_h, z_h); g.rotation_euler = (base + math.radians(ang), 0, 0)
        kit.box(name + ' panel', (2 * fr0 - .04, 0.14, L - .02), (0, -0.07, L / 2), 'pebbled', bev=.02, parent=g)
        kit.cyl(name + ' hinge pin', 0.07, 2 * fr0 - .1, (0, -0.07, 0.05), 'brushed', 'X', parent=g)
        if plate:
            # light, non-metallic finish: a metallic antimony plate on a lid hanging face-down mirrors the floor and reads dark grey
            kit.box(name + ' plate (antimony)', (3.06, 0.03, plate[1] - plate[0]), (0, -0.15, L - (plate[0] + plate[1]) / 2), 'white', parent=g)
        return g
    lid('record-compare section lid', zh, rcl['length'], rcl['open'] if lids_open else 0, rcl.get('plate'))
    if 'lower_lid' in V:
        ll = V['lower_lid']; lid('analyzer compartment lid (lower)', ll['hinge'], ll['top'] - ll['hinge'], ll['open'] if lids_open else 0, ll.get('plate'))
    elif 'lower_seam' in V:
        zz = Zf(V['lower_seam']); kit.box('circuitry/power supply section lid seam', (2 * fr0, 0.03, 0.03), (0, C.yfront(-zz) - 0.005, zz), 'dark', parent=root)
    # ---- narrow sides: outlined hinge bracket, cross-head pivot screw, strap tab, lugs; vent holes in the side frames
    def side_x(s): return C.half(s)
    for sg in (1, -1):
        # the plates draw the hinge bracket as an outline (a band with curled top ends), not a solid plate
        pk = [(Ys(px), Zs(py)) for px, py in V['bracket']]; hw_b = V['bracket_w'] / 2
        path = []                                  # resample (<= 1 mm) so the band follows the side's curvature
        for (y0_, z0_), (y1_, z1_) in zip(pk, pk[1:]):
            m = max(1, int(math.hypot(y1_ - y0_, z1_ - z0_) / 0.1))
            path += [(y0_ + (y1_ - y0_) * j / m, z0_ + (z1_ - z0_) * j / m) for j in range(m)]
        path.append(pk[-1])
        bm = bmesh.new(); rings = []
        for i, (y, z) in enumerate(path):
            a_ = path[max(i - 1, 0)]; b_ = path[min(i + 1, len(path) - 1)]
            ty, tz = b_[0] - a_[0], b_[1] - a_[1]; L = math.hypot(ty, tz) or 1; ny, nz = -tz / L * hw_b, ty / L * hw_b
            ring = []
            for (dy, dz), off in (((-ny, -nz), -0.06), ((ny, nz), -0.06), ((ny, nz), 0.02), ((-ny, -nz), 0.02)):
                ring.append(bm.verts.new((sg * (side_x(-(z + dz)) + off), y + dy, z + dz)))
            rings.append(ring)
        for k in range(len(rings) - 1):
            for i in range(4): bm.faces.new((rings[k][i], rings[k][(i + 1) % 4], rings[k + 1][(i + 1) % 4], rings[k + 1][i]))
        bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new('hinge bracket'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new('hinge bracket (outline)', me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(kit.mat('black')); o.parent = root
        ysc, zsc = Ys(V['screw_px'][0]), Zs(V['screw_px'][1]); xsc = sg * (side_x(-zsc) + 0.05)
        kit.cyl('pivot screw (oval head)', 0.32, 0.08, (xsc, ysc, zsc), 'antimony', 'X', parent=root)
        for rot in (0, math.pi / 2):
            o = kit.box('screw cross recess', (0.03, 0.42, 0.08), (xsc + sg * 0.04, ysc, zsc), 'dark', parent=root); o.rotation_euler = (rot, 0, 0)
        # strap: from the tab top (just below the screw head) along the traced path; the side views draw a 1.9 cm wide tab
        # hanging to a break line (PDF 112: 5.43 cm, PDF 124: 2.43 cm), so every pose carries it down to that depth
        d_top, d_brk = -Zs(V['tab'][0]), -Zs(V['tab'][1])
        tr = [(o_, d) for o_, d in V['strap_open' if lids_open or pose == 'section' else 'strap_closed'] if d > d_top + 0.05]
        cut = [(o_, d) for o_, d in tr if d <= d_brk]
        if len(cut) < len(tr):                    # trace runs past the break: end it there
            (oa, da), (ob, db) = cut[-1], tr[len(cut)]; f = (d_brk - da) / max(db - da, 1e-6); cut.append((oa + (ob - oa) * f, d_brk))
        else:                                     # trace stops short of the break: hang on down at its last offset
            ol, dl = cut[-1]; m = max(2, int((d_brk - dl) / 0.25))
            cut += [(ol, dl + (d_brk - dl) * j / m) for j in range(1, m + 1)]
        path = [(sg * (side_x(d) + o_), -d) for o_, d in [(0.0, d_top)] + cut]
        sweep_xz('127 cm naugahyde shoulder strap', path, Ys(V['strap_y'][0]), Ys(V['strap_y'][1]), 0.18, 'black', parent=root)
        for px, py in VENTS_PX:
            kit.cyl('vent hole 3 mm (side frame)', 0.15, (fr1 - fr0) + 0.06, (sg * (fr0 + fr1) / 2, (px - 1046.5) / 67.94, -(py - 482) / 67.94), 'dark', 'X', parent=root)
        for py in V.get('lugs', []):
            zl = Zs(py); kit.cyl('front lug', 0.17, 0.3, (sg * (fr0 + fr1) / 2, C.yfront(-zl) - 0.12, zl), 'brushed', 'Y', parent=root)
    return root, body, C

def bake():
    """Bake every object's world transform into its mesh (tight bounding boxes for the harness), drop the helper empties."""
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    mw = {o: o.matrix_world.copy() for o in meshes}
    for o in meshes:
        if o.data.users > 1: o.data = o.data.copy()
        o.data.transform(mw[o]); o.parent = None; o.matrix_world = Matrix.Identity(4)
    for o in [o for o in bpy.context.scene.objects if o.type == 'EMPTY']: bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()

def run(item):
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    pose = argv[0] if argv else 'open'
    out = argv[1] if len(argv) > 1 else None
    kit.reset(); root, body, C = build(item, pose)
    bake()
    pts = [o.matrix_world @ Vector(c) for o in (body,) for c in o.bound_box]
    mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
    print('CASE', item, pose, 'W x D x H cm', [round(mx[i] - mn[i], 3) for i in range(3)])
    name = item if pose == 'open' else f'{item}-{pose}'
    if pose != 'open' and out is None: raise SystemExit('non-default poses need an out_dir')
    allp = [o.matrix_world @ Vector(c) for o in bpy.context.scene.objects if o.type == 'MESH' for c in o.bound_box]
    print('ALL', [round(max(p[i] for p in allp) - min(p[i] for p in allp), 3) for i in range(3)], 'top z', round(max(p.z for p in allp), 3))
    kit.export(name, out)
