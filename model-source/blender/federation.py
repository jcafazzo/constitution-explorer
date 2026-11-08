"""Federation-class dreadnought (Class I Dreadnought, MK-X), NCC-2100 — PDF 88, TO 01:04:24.
Run: /Applications/Blender.app/Contents/MacOS/Blender -b -P model-source/blender/federation.py
Printed (PARTICULARS): L.O.A. 320, breadth 140, height 87, primary hull dia. 140, sec. hull length 122 / max dia. 30,
prop. unit L.O.A. 153.6 / dia. 17.3 metres.  Frame: metres, Z up, bow -Y (y = -160), starboard -X.

Plate p-088.png at 300 dpi.  Scale 5.994 px/m: drawn plan length 1918 px = printed L.O.A. 320 m (side view 1921 px;
0-50 m bar 301 px = 6.02 px/m, 0.4 % apart).  Views: plan (bow image-left, image-up = starboard), side (seen from +X,
bow left), front (from -Y, image-right = port).  Silhouette profiles measured by model-source/fleet/federation_measure.py
-> profiles/federation.json (plate px); px -> metres through the lambdas below.  Details are placed at plate-read
positions and seated on the hull by ray casts along the view direction they were read in.
Notes on reading the plate:
* The saucer is revolved from the side-view half-profile (bow edge to the centre column 781) about the centre found
  in plan (775.5, 923.5); radius scaled to the plan diameter (847 px).
* The three propulsion units are lofted from their own drawn outlines (side view: top/bottom; plan: both edges).
  The dorsal unit's plan outline is hidden by the secondary hull, so it takes the side units' plan widths.
* Where views disagree (front view puts the dorsal unit ~1.9 m lower and the main sensor dish ~2 m lower than the
  side view) the side view governs Z and Y, the plan and front views govern X."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

PPM = 5.994
Y = lambda px: (px - 1314.0) / PPM        # plan column -> y   (plan length 355..2273)
X = lambda py: (py - 923.5) / PPM         # plan row -> x      (centre line row 923.5; image-down = port = +X)
Ys = lambda px: (px - 1319.5) / PPM       # side column -> y   (side length 359..2280)
Z = lambda py: (1763.5 - py) / PPM        # side row -> z      (z = 0 at the mid-thickness of the saucer rim)
Xf = lambda px: (px - 778.0) / PPM        # front column -> x  (image-right = port)
Zf = lambda py: (2426.0 - py) / PPM       # front row -> z
YC = (Y(775.5) + Ys(781)) / 2             # saucer centre (plan / side)
R_SAUCER = 423.5 / PPM                    # plan radius (847 px dia.)
# The side view puts the dorsal unit's axis at z 25.1, the front view at 23.2. The side view governs (DZ_DORSAL = 0):
# hulls span 87.4 m (printed 87); the drawn after fairing (+1.0 m) and ventral phaser bank give an 88.45 m envelope.
DZ_DORSAL = 0.0

P = json.load(open(os.path.join(kit.PROFILES, 'federation.json')))
kit.PALETTE['hull'] = ('dcdad2', .5, .05, 1)
kit.PALETTE['grille'] = ('8a8f91', .6, .1, 1)    # hatched grilles: mid-grey panel + dark checker

def smooth1d(vals, k):
    if k <= 1: return list(vals)
    out = []
    for i in range(len(vals)):
        w = vals[max(0, i - k):i + k + 1]; out.append(sum(w) / len(w))
    return out

def interp(rows, c):
    """rows [[col, a, b], ...] sorted by col -> (a, b) at column c (clamped)."""
    if c <= rows[0][0]: return rows[0][1], rows[0][2]
    if c >= rows[-1][0]: return rows[-1][1], rows[-1][2]
    lo, hi = 0, len(rows) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if rows[m][0] <= c: lo = m
        else: hi = m
    a, b = rows[lo], rows[hi]; t = (c - a[0]) / (b[0] - a[0])
    return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t

def smoothed_ends(rows, k, keep):
    """Moving average of half-width k inside, tapering to no smoothing over `keep` rows at each end (domed tips)."""
    out = []
    n = len(rows)
    for i, r in enumerate(rows):
        kk = max(0, min(k, (min(i, n - 1 - i) * k) // keep))
        w = rows[max(0, i - kk):i + kk + 1]
        out.append([r[0], sum(x[1] for x in w) / len(w), sum(x[2] for x in w) / len(w)])
    return out

def smoothed(rows, k):
    a = smooth1d([r[1] for r in rows], k); b = smooth1d([r[2] for r in rows], k)
    return [[r[0], x, y] for r, x, y in zip(rows, a, b)]

# ---------- accumulated meshes (many small parts -> one object per kind) ----------
class Acc:
    def __init__(self, name, material):
        self.name, self.material, self.bm = name, material, bmesh.new()
    def add_bm(self, src, M=Matrix.Identity(4)):
        me = bpy.data.meshes.new('tmp'); src.to_mesh(me); me.transform(M); self.bm.from_mesh(me); bpy.data.meshes.remove(me)
    def add_tris(self, verts, faces):
        vs = [self.bm.verts.new(v) for v in verts]
        for f in faces:
            try: self.bm.faces.new([vs[i] for i in f])
            except ValueError: pass
    def done(self, parent=None, angle=40):
        if not self.bm.faces: return None
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        return kit.smooth(kit._obj(self.name, me, self.material, parent), angle)

def bvh_of(*objs):
    verts, polys = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); M = o.matrix_world; n = len(verts)
        verts += [M @ v.co for v in me.vertices]; polys += [[n + i for i in p.vertices] for p in me.polygons]
        oe.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)

def hit(bvh, origin, d):
    loc, nrm, _, _ = bvh.ray_cast(Vector(origin), Vector(d).normalized(), 1000)
    if loc is None: return None, None
    if nrm.dot(Vector(d)) > 0: nrm = -nrm
    return loc, nrm

def seat_box(acc, bvh, origin, d, size, along=None, sink=0.5):
    """Small box (length, height, depth) seated on the surface hit by a ray; length runs along `along`
    (projected into the tangent plane; default horizontal), depth along the surface normal, `sink` of it buried."""
    p, n = hit(bvh, origin, d)
    if p is None: print('MISS', acc.name, origin); return
    if along is None:
        a = Vector((0, 0, 1)).cross(n)
        if a.length < 1e-6: a = Vector((1, 0, 0))
    else:
        a = Vector(along); a = a - n * a.dot(n)
    a.normalize(); b = n.cross(a)
    M = Matrix((a, b, n)).transposed().to_4x4(); M.translation = p + n * (size[2] * (0.5 - sink))
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    acc.add_bm(bm, M); bm.free()

def seat_dot(acc, bvh, origin, d, r, sink=0.45, seg=20):
    p, n = hit(bvh, origin, d)
    if p is None: print('MISS', acc.name, origin); return
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    M = Matrix.Translation(p + n * r * (1 - 2 * sink)); acc.add_bm(bm, M); bm.free()

def decal(acc, bvh, polys, frame, d, off=0.15, cuts=2, mesh=None):
    """Project flat outlines onto a surface. polys: list of 2-D outlines (u, v); frame(u, v) -> 3-D start point
    outside the hull; the points are cast along d and lifted `off` along the normal. mesh=(verts2d, faces) instead
    of polys for text. Faces are triangulated and subdivided so the decal follows the curvature."""
    bm = bmesh.new()
    if mesh:
        vs = [bm.verts.new(frame(*v)) for v in mesh[0]]
        for f in mesh[1]:
            try: bm.faces.new([vs[i] for i in f])
            except ValueError: pass
    for poly in polys:
        bm.faces.new([bm.verts.new(frame(*v)) for v in poly])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    if cuts: bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        p, n = hit(bvh, v.co, d)
        if p is not None: v.co = p + n * off
    acc.add_bm(bm); bm.free()

def text_mesh(s, size, spacing=None):
    """Flat glyph outlines of `s` (Blender's built-in font), centred on the origin; returns (verts2d, faces).
    spacing: place each glyph at this pitch instead of the font's advance."""
    out_v, out_f = [], []
    chars = list(s) if spacing else [s]
    for i, ch in enumerate(chars):
        cu = bpy.data.curves.new('t', 'FONT'); cu.body = ch; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
        cu.fill_mode = 'BOTH'
        ob = bpy.data.objects.new('t', cu); bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).to_mesh()
        dx = (i - (len(chars) - 1) / 2) * spacing if spacing else 0
        n = len(out_v); out_v += [(v.co.x + dx, v.co.y) for v in me.vertices]
        out_f += [[n + k for k in p.vertices] for p in me.polygons]
        ob.evaluated_get(dg).to_mesh_clear(); bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    return out_v, out_f

def rect(u0, u1, v0, v1): return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

# ======================================================================================================
def build():
    kit.reset()
    G = {k: kit.group(k) for k in ('Primary hull', 'Secondary hull', 'Dorsal propulsion unit', 'Port propulsion unit',
                                   'Starboard propulsion unit', 'Markings')}
    # ---------- PRIMARY HULL: saucer revolved from the side-view half profile ----------
    K = R_SAUCER / ((781 - 359) / PPM)
    rows = P['saucer_side']
    top = smooth1d(smooth1d([r[1] for r in rows], 18), 18); bot = smooth1d(smooth1d([r[2] for r in rows], 18), 18)   # px-quantised edges: wide average so the revolve does not band
    t6 = smooth1d([r[1] for r in rows], 4); b6 = smooth1d([r[2] for r in rows], 4)
    for i in range(30):                                     # rim: keep the drawn tip and the knuckle where the upper surface lifts
        w = i / 30; top[i] = t6[i] * (1 - w) + top[i] * w; bot[i] = b6[i] * (1 - w) + bot[i] * w
    for i in range(4): top[i], bot[i] = rows[i][1], rows[i][2]          # keep the drawn rim tip
    prof_t = [((781 - r[0]) / PPM * K, Z(t)) for r, t in zip(rows, top)][::-3]   # centre -> rim
    prof_b = [((781 - r[0]) / PPM * K, Z(b)) for r, b in zip(rows, bot)][::3]    # rim -> centre
    prof_t[0] = (0.0, prof_t[0][1]); prof_b[-1] = (0.0, prof_b[-1][1])
    if prof_t[-1][0] < R_SAUCER - 1e-3: prof_t.append((R_SAUCER, prof_t[-1][1]))
    if prof_b[0][0] < R_SAUCER - 1e-3: prof_b.insert(0, (R_SAUCER, prof_b[0][1]))
    saucer = kit.revolve('Primary hull (saucer)', prof_t + prof_b, 'hull', axis='Z', seg=128, loc=(0, YC, 0), parent=G['Primary hull'])
    def ztop(r):  # saucer upper surface height at radius r (m)
        for (r0, z0), (r1, z1) in zip(prof_t, prof_t[1:]):
            if r0 <= r <= r1: return z0 + (z1 - z0) * (r - r0) / max(r1 - r0, 1e-9)
        return prof_t[-1][1]
    # Bridge / sensor array T (dome on the flat deck, side x 742-826, top row 1642) and sensor array B (row 1880).
    dome_t = [(0, Z(1642)), (2.0, Z(1643)), (3.0, Z(1646)), (3.9, Z(1651)), (4.6, Z(1653.5)), (5.2, Z(1655.5)),
              (6.0, Z(1658)), (6.6, Z(1661)), (7.2, Z(1665)), (7.6, Z(1669)), (7.7, Z(1672))]
    kit.revolve('Bridge dome (sensor array T)', [(r, z) for r, z in dome_t] + [(0, Z(1672))], 'hull', axis='Z', seg=96, loc=(0, YC, 0), parent=G['Primary hull'])
    dome_b = [(0, Z(1847)), (7.0, Z(1847)), (6.6, Z(1853)), (6.0, Z(1858)), (5.0, Z(1864)), (4.0, Z(1869)), (3.0, Z(1874)),
              (2.0, Z(1877.5)), (0, Z(1880))]
    kit.revolve('Sensor array B (ventral dome)', dome_b, 'hull', axis='Z', seg=96, loc=(0, YC, 0), parent=G['Primary hull'])
    kit.torus('Bridge deck ring', 6.9, 0.18, (0, YC, Z(1668) + .05), 'dark', axis='Z', parent=G['Primary hull'], seg=96)
    # Impulse power: block on the after rim (side x 1183-1218, rows 1740-1768), exhaust face aft.
    y0, y1, z0, z1 = Ys(1183), Ys(1218), Z(1768), Z(1740)
    kit.box('Impulse power', (22.0, y1 - y0 + 3.0, z1 - z0), (0, (y0 + y1) / 2 - 1.5, (z0 + z1) / 2), 'hull', bev=.8, parent=G['Primary hull'])
    kit.box('Impulse power exhaust', (17.0, .3, (z1 - z0) - 1.6), (0, y1 + .05, (z0 + z1) / 2), 'red', bev=.1, parent=G['Primary hull'])

    # ---------- SECONDARY HULL ----------
    ss = smoothed(P['sec_side'], 4); sp = smoothed(P['sec_plan'], 4)
    secs = []
    yf, ya = Ys(1108), Ys(1815)
    def sec_at(px, k=1.0):
        t, b = interp(ss, px); lo, hi = interp(sp, px - 5.5)
        hw = (hi - lo) / 2 / PPM; zt, zb = Z(t), Z(b); zc = (zt + zb) / 2; hz = (zt - zb) / 2
        return (-hw * k, hw * k, zc - hz * k, zc + hz * k)
    for dy, k in ((0, .80), (.25, .90), (.6, .96), (1.1, .99)):
        secs.append((yf + dy, *sec_at(1108, k)))
    for px in range(1116, 1808, 6): secs.append((Ys(px), *sec_at(px)))
    for dy, k in ((1.1, .99), (.6, .96), (.25, .90), (0, .80)):
        secs.append((ya - dy, *sec_at(1815, k)))
    secs = [(s[0], s[1], s[2], s[3], s[4]) for s in secs]
    sec = kit.loft('Secondary hull', [(y, x0, x1, z0, z1) for y, x0, x1, z0, z1 in secs], 'hull', p=2.0, seg=64, parent=G['Secondary hull'])
    # Interconnecting neck (side outline; 10 m wide as the front view, rows 2535-2575)
    neck = [(Ys(988), Z(1790)), (Ys(1175), Z(1905)), (Ys(1351), Z(1905)), (Ys(1210), Z(1770)), (Ys(1150), Z(1760)), (Ys(1000), Z(1760))]
    kit.extrude('Interconnecting dorsal (neck)', neck, 9.8, 'hull', plane='YZ', bev=1.4, parent=G['Secondary hull'])
    # Shuttlecraft hangar: rounded bay on the forward face, side x 1098-1125, rows 1895-1960; front view arc 720-845.
    hangar = kit.sphere('Shuttlecraft hangar', 1.0, (0, yf + .9, Z(1922)), 'hull', scale=((845 - 720) / 2 / PPM, 2.6, (1960 - 1895) / 2 / PPM), parent=G['Secondary hull'])
    # Main sensor F/A: forward dish (side x 1078-1108, rows 1979-2074) and after dish (x 1812-1852, rows 1912-1992).
    def dish(name, yb, yr, ztip, r, zc, parent, sign):
        d = abs(yr - yb); b = lambda x: yr - sign * x      # sign -1: dish faces -Y; b(x) moves x back toward the hull
        pts = [(0, yb), (r * .4, yb), (r, yr), (r * .92, b(.35)), (r * .5, b(d * .4)), (0, b(d * .5))]
        o = kit.revolve(name, pts, 'grey', axis='Y', seg=64, loc=(0, 0, zc), parent=parent)
        kit.cyl(name + ' emitter', r * .12, abs(ztip - b(d * .5)), (0, (ztip + b(d * .5)) / 2, zc), 'dark', 'Y', r2=r * .04, seg=24, parent=parent)
        return o
    zfd = (Z(1979) + Z(2074)) / 2 - 0.4
    dish('Main sensor F (forward dish)', yf + .3, Ys(1078), Ys(1058), (2074 - 1979) / 2 / PPM + .3, zfd, G['Secondary hull'], -1)
    dish('Main sensor A (after dish)', ya - .3, Ys(1850), Ys(1878), (1992 - 1912) / 2 / PPM, Z(1951), G['Secondary hull'], 1)
    # Tractor beam (starboard) and navigational deflector (port): front-view circles at x 700 / 853, row 2660, r 17 px.
    for name, px in (('Tractor beam', 700), ('Navigational deflector', 853)):
        kit.cyl(name, 17 / PPM, .8, (Xf(px), yf - .1, Zf(2660) + 2.0), 'dark', 'Y', seg=32, parent=G['Secondary hull'])
        kit.torus(name + ' rim', 17 / PPM, .25, (Xf(px), yf - .5, Zf(2660) + 2.0), 'grey', axis='Y', parent=G['Secondary hull'], seg=48)

    # ---------- PROPULSION UNITS (space/warp, 3 units) ----------
    # Each unit is a clean surface of revolution with stations read on the plate (s = metres from the forward tip):
    #   forward cap  s 0-8.5, ellipse to r 9.4 (side/plan 9.3-9.4 at s 10);  forward section r 9.4 to s 22,
    #   eased over 22-26 m into the body, body tapering linearly r 9.0 -> 7.6 as drawn (side view 17.8 -> 15.4 m; mean
    #   dia. 16.6 m, the printed 17.3 is not held so the plan/side outlines stay on the drawing) to s 141, eased to the after section r 7.2 (drawn 7.1-7.3) and an elliptic after dome.
    #   The raised fairing (side x 1640-1800 / 2030-2180, plan flare) is a separate saddle part, +1.0 m, s 112-141.
    def r_body(s, L):
        if s <= 8.5: return 9.4 * math.sqrt(max(0.0, 1 - ((8.5 - s) / 8.5) ** 2))
        if s <= 22: return 9.4
        if s <= 26: return 9.4 + (9.0 - 9.4) * (1 - math.cos(math.pi * (s - 22) / 4)) / 2
        if s <= 141: return 9.0 + (7.6 - 9.0) * (s - 26) / (141 - 26)
        if s <= 143.5: return 7.6 + (7.2 - 7.6) * (1 - math.cos(math.pi * (s - 141) / 2.5)) / 2
        e = L - 6.3
        if s <= e: return 7.2
        return 7.2 * math.sqrt(max(0.0, 1 - ((s - e) / 6.3) ** 2))
    def unit_profile(L):
        ss = [8.5 - 8.5 * math.cos(math.pi / 2 * i / 20) for i in range(21)] + [9 + i for i in range(14)]
        ss += [22 + 4 * i / 8 for i in range(1, 9)] + [26 + (141 - 26) * i / 23 for i in range(1, 24)] + [141 + 2.5 * i / 8 for i in range(1, 9)]
        e = L - 6.3
        ss += [e] + [e + 6.3 * math.sin(math.pi / 2 * i / 20) for i in range(1, 21)]
        return [(r_body(x, L), x) for x in ss]
    def sleeve(name, ytip, L, cx, cz, parent):
        """Raised after fairing: drawn over the top (side view, +1.0 m) and both flanks (plan flare, +1.0 m) but not
        underneath, so it is a saddle: r = body + 1.0 m * w(angle) * ramp(s), fading into the body below the flanks."""
        bm = bmesh.new(); n = 72; ss = [112 + 29 * i / 40 for i in range(41)]
        ramp = lambda s_: min(1.0, (s_ - 112) / 1.8, (141 - s_) / 1.8)
        def w(a):   # a: angle from +X in the XZ plane; full over the top half, fading out 35 deg below horizontal
            d = math.degrees(a) % 360
            if d <= 180: return 1.0
            dd = min(d - 180, 360 - d)
            return max(0.0, 1 - dd / 35) ** 2 * (3 - 2 * max(0.0, 1 - dd / 35))
        rings = []
        for s_ in ss:
            rb = r_body(s_, L); ring = []
            for i in range(n):
                a = 2 * math.pi * i / n; r_ = rb - .06 + (1.0 + .4 * math.cos(a) ** 2) * max(0.0, ramp(s_)) * w(a)   # +1.0 top (side), +1.4 flanks (plan)
                ring.append(bm.verts.new((r_ * math.cos(a), ytip + s_, r_ * math.sin(a))))
            rings.append(ring)
        for j in range(len(rings) - 1):
            for i in range(n):
                bm.faces.new((rings[j][i], rings[j][(i + 1) % n], rings[j + 1][(i + 1) % n], rings[j + 1][i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = kit._obj(name, me, 'hull', parent); o.location = (cx, 0, cz)
        return kit.smooth(o, 50)
    # Tips / ends (plan & side px) and axes. Side units: tip y 5.3 (plan 1346 / side 1351), end 160.1 (2271 / 2282),
    # x = +-51.65 (plan rows 1230 / 610.5, front 471 / 1093). Dorsal: side x 961-1890.  The drawn units keep a straight
    # top line while the body tapers, so each axis is pitched up aft by TILT (1.4 m over the 115 m body) and set so
    # the top meets the drawn top line (side units row 1758, dorsal row 1563.5 then DZ_DORSAL).
    TILT = 1.4 / 115
    XS = 1.0
    def axis_z(ytip, top_row, dz=0.0):
        return Z(top_row) + dz - 9.0 - (ytip + 26) * TILT      # z of the axis at y = 0 (the revolve's pivot)
    UNITS = {'Dorsal': (Ys(961), Ys(1890) - Ys(961), 0.0, axis_z(Ys(961), 1563.5, DZ_DORSAL)),
             'Port': (5.3, 159.9 - 5.3, 51.65, axis_z(5.3, 1758)), 'Starboard': (5.3, 159.9 - 5.3, -51.65, axis_z(5.3, 1758))}
    unit_z = lambda k, y: UNITS[k][3] + y * TILT
    nac = {}; sleeves = {}
    for k, (ytip, L, cx, cz) in UNITS.items():
        g = G[k + ' propulsion unit']
        prof = [(r, ytip + s_) for r, s_ in unit_profile(L)]
        prof[0] = (0.0, prof[0][1]); prof[-1] = (0.0, prof[-1][1])
        parts = [kit.revolve(k + ' space/warp propulsion unit', prof, 'hull', axis='Y', seg=64, loc=(cx, 0, cz), parent=g)]
        parts.append(sleeve(k + ' unit raised sleeve', ytip, L, cx, cz, g))
        # dark collar band behind the forward cap (plan 1415-1430 / side 1030-1045, s = 12.0-14.4 m)
        parts.append(kit.revolve(k + ' unit collar band', [(9.3, ytip + 12.0), (9.5, ytip + 12.2), (9.5, ytip + 14.2), (9.3, ytip + 14.4)], 'dark', axis='Y', seg=64, loc=(cx, 0, cz), parent=g))
        # lateral lugs at the forward section (plan flare to +-10.3 m at s 8-24; front-view "ears" below the axis)
        for sgn in (1, -1):
            parts.append(kit.box(k + ' unit forward lug ' + ('P' if sgn > 0 else 'S'), (3.0, 16.0, 4.2),
                                 (cx + sgn * 9.0, ytip + 16.0, cz - 5.6), 'hull', bev=.5, parent=g))
        for o in parts:
            o.rotation_euler = (o.rotation_euler[0] + TILT, o.rotation_euler[1], o.rotation_euler[2]) if o.type == 'MESH' else o.rotation_euler
        for o in parts[:3]:          # plan widths run XS x the side-view depths on the plate (body 9.3 / 8.6 at s 60-110)
            c0 = cx - o.location.x   # revolve() bakes its location into the vertices; sleeve() keeps it on the object
            o.data.transform(Matrix.Translation((c0, 0, 0)) @ Matrix.Diagonal((XS, 1, 1, 1)) @ Matrix.Translation((-c0, 0, 0)))
        nac[k], sleeves[k] = parts[0], parts[1]
    # Forward fins/brackets ("L" in the side view): side units -> ventral skid (side x 1395-1490 down to row 1875,
    # front view 438-502 / 1054-1118 wide); dorsal unit -> lateral lugs (front view x 717-735 / 830-846, rows 2300-2335).
    # (skid bottom 0.8 m below the side view's row 1875, between it and the front view's foot at row 2548)
    for k in ('Port', 'Starboard'):
        cx = UNITS[k][2]
        kit.box(k + ' unit ventral bracket', (64 / PPM, Ys(1490) - Ys(1395), 5.4), (cx, (Ys(1395) + Ys(1490)) / 2, Z(1875) + 2.7 - .8), 'hull', bev=.6, parent=G[k + ' propulsion unit'])

    # ---------- PYLONS ----------
    pts = [(Ys(1065.5), Z(1750)), (Ys(1148.5), Z(1645)), (Ys(1276.8), Z(1645)), (Ys(1184.4), Z(1750))]
    dpyl = kit.extrude('Dorsal pylon', pts, 4.0, 'hull', plane='YZ', bev=.5, parent=G['Dorsal propulsion unit'])
    # Side pylons: plates from the unit (plan chord x 1500-1640) down to the hull side, at the front-view strut angle
    # (centre line through front (589.5, 2555), dx/dz = 1.725; 24 px thick normal to the strut = 4.1 m).
    ang = math.atan2(1, 1.725); xm, zm = Xf(589.5), Zf(2555)
    yA, yB = Y(1500), Y(1640)
    struts = {}
    for k, sgn in (('Port', 1), ('Starboard', -1)):
        xo = sgn * 51.7; zo = zm + (51.7 - (-xm)) / 1.725    # outer end on the unit axis line
        xi = sgn * 9.0; zi = zm - (-xm - 9.0) / 1.725
        L = math.hypot(xo - xi, zo - zi)
        struts[k] = kit.box(k + ' pylon', (L, yB - yA, 4.1), ((xo + xi) / 2, (yA + yB) / 2, (zo + zi) / 2), 'hull',
                            rot=(0, -sgn * ang, 0), bev=.6, parent=G[k + ' propulsion unit'])
    bpy.context.view_layer.update()

    # ---------- MARKINGS & SMALL DETAILS (seated by ray casts) ----------
    B_sau = bvh_of(saucer); B_sec = bvh_of(sec); B_hang = bvh_of(sec, hangar)
    dark = Acc('Deck lines (primary hull)', 'dark')
    for rr in (9.2, 16.2, 24.4, 32.8, 40.5, 49.0, 67.7):        # plan rings (radii 55..406 px)
        n = 220; poly_o = []; poly_i = []
        verts = []; faces = []
        for i in range(n):
            a = 2 * math.pi * i / n
            for r_ in (rr - .22, rr + .22):
                verts.append((r_ * math.cos(a), YC + r_ * math.sin(a), 60))
        for i in range(n):
            j = (i + 1) % n; faces.append([2 * i, 2 * j, 2 * j + 1, 2 * i + 1])
        bm = bmesh.new(); vs = [bm.verts.new(v) for v in verts]
        for f in faces: bm.faces.new([vs[q] for q in f])
        for v in bm.verts:
            p, nn = hit(B_sau, v.co, (0, 0, -1))
            if p: v.co = p + nn * .12
        dark.add_bm(bm); bm.free()
    for k in range(24):                                     # 24 radials, 15 deg apart (plan)
        a = math.radians(15 * k); ca, sa = math.cos(a), math.sin(a)
        poly = []
        r0, r1 = 9.4, 67.5; m = 60
        verts = []
        for i in range(m + 1):
            r_ = r0 + (r1 - r0) * i / m
            for w in (-.22, .22):
                verts.append((r_ * sa - w * ca, YC - r_ * ca - w * sa, 60))   # a = 0 points to the bow (-Y)
        faces = [[2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2] for i in range(m)]
        bm = bmesh.new(); vs = [bm.verts.new(v) for v in verts]
        for f in faces: bm.faces.new([vs[q] for q in f])
        for v in bm.verts:
            p, nn = hit(B_sau, v.co, (0, 0, -1))
            if p: v.co = p + nn * .12
        dark.add_bm(bm); bm.free()
    dark.done(G['Markings'], 60)

    # Registry NCC-2100 on the saucer: centred on radius 218 px, from image angle 220.4 (N) to 141.0 (last 0),
    # glyph tops toward the centre (reads from ahead of the bow), cap height 40 px.
    reg = Acc('Registry NCC-2100 (primary hull)', 'black')
    Rr = 218 / PPM; cap = 40 / PPM
    for i, ch in enumerate('NCC-2100'):
        if ch == '1':
            gv, gf = [(-.07 * cap, -.5 * cap), (.07 * cap, -.5 * cap), (.07 * cap, .5 * cap), (-.07 * cap, .5 * cap)], [[0, 1, 2, 3]]   # drawn as a single thin stroke
        else:
            gv, gf = text_mesh(ch, cap / .72)
        a = math.radians(220.4 - i * (220.4 - 141.0) / 7)
        cy_, cx_ = YC + Rr * math.cos(a), Rr * math.sin(a)          # image angle: dx -> +Y, dy -> +X
        t = Vector((math.sin(a), -math.cos(a)))                     # reading direction in (Y, X)
        up = Vector((-math.cos(a), -math.sin(a)))                   # toward the centre
        frame = lambda u, v, cy_=cy_, cx_=cx_, t=t, up=up: (cx_ + u * t[1] + v * up[1], cy_ + u * t[0] + v * up[0], 60)
        decal(reg, B_sau, [], frame, (0, 0, -1), off=.16, cuts=1, mesh=(gv, gf))
    reg.done(G['Markings'], 60)

    # Plan marks: four square ports, after hatches (plan px), seated from above.
    marks = Acc('Saucer ports and hatches', 'dark')
    for px, py in ((541, 713), (1012, 713), (541, 1122), (1012, 1122)):
        a = Vector((Y(px) - YC, X(py), 0)); a.normalize()
        seat_box(marks, B_sau, (X(py), Y(px), 60), (0, 0, -1), (20 / PPM, 20 / PPM, .5), along=(a[1], a[0], 0))
    for px0, px1, py0, py1 in ((1075, 1090, 845, 862), (1140, 1165, 851, 870), (1075, 1090, 985, 1002), (1140, 1165, 977, 996)):
        seat_box(marks, B_sau, (X((py0 + py1) / 2), Y((px0 + px1) / 2), 60), (0, 0, -1), ((py1 - py0) / PPM, (px1 - px0) / PPM, .5), along=(1, 0, 0))
    marks.done(G['Markings'])

    # Phaser banks (5 banks / 2 each): P/S on the saucer top (plan dots), ventral pair (front view 765/795, row 2512),
    # T/B on the secondary hull (side view circles at (1400, 1890) and (1155, 2083)).
    for name, pts_ in (('Phaser bank S (primary hull)', ((761, 733), (791, 733))), ('Phaser bank P (primary hull)', ((761, 1110), (791, 1110)))):
        a_ = Acc(name, 'dark')
        for px, py in pts_: seat_dot(a_, B_sau, (X(py), Y(px), 60), (0, 0, -1), .85)
        a_.done(G['Primary hull'], 60)
    a_ = Acc('Phaser bank (ventral, primary hull)', 'dark')
    for xx in (-2.5, 2.5): seat_dot(a_, B_sau, (xx, YC - 7.6, -40), (0, 0, 1), .9)
    a_.done(G['Primary hull'], 60)
    a_ = Acc('Phaser bank T (secondary hull)', 'dark'); seat_dot(a_, B_sec, (0, Ys(1400), -12), (0, 0, -1), 1.3, sink=.83); a_.done(G['Secondary hull'], 60)
    a_ = Acc('Phaser bank B (secondary hull)', 'dark'); seat_dot(a_, B_sec, (0, Ys(1185), -80), (0, 0, 1), 1.3, sink=.83); a_.done(G['Secondary hull'], 60)   # side circle (1185, 2086); 0.45 m proud (the printed 87 m height is taken over the hulls)
    # Photon torpedoes P/S: plan dots (593, 914 / 944) = front-view tubes either side of the centre line.
    for name, xx in (('Photon torpedo S', -2.5), ('Photon torpedo P', 2.5)):
        p, n = hit(B_sau, (xx, Y(593), 60), (0, 0, -1))
        o = kit.cyl(name, .9, 1.2, (0, 0, 0), 'black', 'Z', seg=24, parent=G['Primary hull'])
        o.matrix_world = Matrix.Translation(p + n * .1) @ n.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    # Forward rim ports: front view circles at x 750 / 781 / 812, row 2428.
    a_ = Acc('Forward rim ports', 'dark')
    for px in (750, 781, 812):
        p, n = hit(B_sau, (Xf(px), -200, Zf(2428)), (0, 1, 0))
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=10 / PPM, radius2=10 / PPM, depth=.5)
        M = Matrix.Translation(p) @ n.to_track_quat('Z', 'Y').to_matrix().to_4x4(); a_.add_bm(bm, M); bm.free()
    a_.done(G['Primary hull'])

    # ---------- WINDOW ROWS (dashes as drawn) ----------
    win = Acc('Window rows', 'black')
    for px in (445, 461, 500, 513, 528, 1023, 1037, 1054, 1090, 1103):           # front view, rim row 2421
        seat_box(win, B_sau, (Xf(px), -200, Zf(2421)), (0, 1, 0), (1.6, .75, .4))
    for px in (435, 447, 511, 524, 1085, 1097):                                  # side view, rim row 1755 (both sides)
        for s in (1, -1): seat_box(win, B_sau, (s * 200, Ys(px), Z(1755)), (-s, 0, 0), (1.6, .75, .4))
    for (px0, px1), row in (((722, 746), 1805), ((766, 778), 1805), ((782, 793), 1805), ((813, 823), 1805), ((827, 838), 1805),
                            ((745, 768), 1823), ((793, 803), 1823), ((808, 816), 1823), ((650, 667), 1826)):   # lower saucer
        for s in (1, -1): seat_box(win, B_sau, (s * 200, Ys((px0 + px1) / 2), Z(row)), (-s, 0, 0), ((px1 - px0) / PPM, .8, .4))
    for px0, px1 in ((1154, 1164), (1168, 1178), (1198, 1210), (1212, 1223), (1250, 1260), (1263, 1274)):   # secondary hull, row 1933
        for s in (1, -1): seat_box(win, B_sec, (s * 200, Ys((px0 + px1) / 2), Z(1933)), (-s, 0, 0), ((px1 - px0) / PPM, .8, .4))
    win.done(G['Markings'])

    # ---------- HULL / UNIT MARKINGS (side view, both sides) ----------
    mk = Acc('Pennants and panels', 'dark')
    grille = Acc('Grille panels (hatched on the plate)', 'grille')
    stip = Acc('Grille hatching', 'dark')
    def inside(pt, poly):
        x, y = pt; c = False
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
        return c
    def hatch(poly, pitch=5.0, dot=2.4):
        """The plate's checker hatching: small dark squares on a grid inside the panel outline (px)."""
        us = [q[0] for q in poly]; vs = [q[1] for q in poly]; out = []
        u = min(us) + pitch / 2
        while u < max(us):
            v = min(vs) + pitch / 2; k = 0
            while v < max(vs):
                uu = u + (pitch / 2 if k % 2 else 0)
                if all(inside(c, poly) for c in ((uu - dot / 2, v - dot / 2), (uu + dot / 2, v + dot / 2), (uu - dot / 2, v + dot / 2), (uu + dot / 2, v - dot / 2))):
                    out.append(rect(uu - dot / 2, uu + dot / 2, v - dot / 2, v + dot / 2))
                v += pitch; k += 1
            u += pitch
        return out
    def side_decal(bvh, polys_px, sides=(1, -1), mesh=None, dz=0.0, acc=None, off=.12):
        for s in sides:
            fr = lambda u, v, s=s: (s * 200, Ys(u), Z(v) + dz)
            decal(acc or mk, bvh, polys_px, fr, (-s, 0, 0), off=off, cuts=2)
    def side_grille(bvh, polys_px, sides=(1, -1), dz=0.0):
        side_decal(bvh, polys_px, sides, dz=dz, acc=grille, off=.12)
        for p_ in polys_px: side_decal(bvh, hatch(p_), sides, dz=dz, acc=stip, off=.2)
    # secondary hull pennant: chevron (1125-1172, rows 1972-2000) + three pin-stripes
    chev = [[(1125, 1973), (1140, 1973), (1152, 1990), (1146, 2000), (1131, 2000)], [(1146, 1973), (1172, 1973), (1172, 1999), (1157, 1999), (1158, 1990)]]
    side_decal(B_hang, chev + [rect(1176, 1405, 1965, 1969), rect(1176, 1530, 1975, 1979), rect(1176, 1340, 1984, 1988)])
    # dorsal unit: window slot (outlined, with a centre line) and the two hatched grilles
    B_d = bvh_of(nac['Dorsal'], sleeves['Dorsal'])
    side_decal(B_d, [rect(1100, 1370, 1594, 1608)], dz=DZ_DORSAL, acc=grille)
    side_decal(B_d, [rect(1104, 1366, 1600, 1602)], dz=DZ_DORSAL, off=.2)
    side_grille(B_d, [rect(1385, 1612, 1590, 1612), rect(1740, 1812, 1590, 1612)], dz=DZ_DORSAL)
    # side units, outer faces: chevron, bars (solid), after grille (hatched)
    B_p, B_s = bvh_of(nac['Port'], sleeves['Port']), bvh_of(nac['Starboard'], sleeves['Starboard'])
    unit_marks = [[(1530, 1786), (1546, 1786), (1556, 1798), (1548, 1810), (1532, 1810)], [(1550, 1786), (1578, 1786), (1578, 1809), (1560, 1809), (1561, 1798)],
                  rect(1582, 1680, 1788, 1808), rect(1845, 1975, 1794, 1803)]
    side_decal(B_p, unit_marks, sides=(1,)); side_decal(B_s, unit_marks, sides=(-1,))
    side_grille(B_p, [rect(2130, 2200, 1795, 1815)], sides=(1,)); side_grille(B_s, [rect(2130, 2200, 1795, 1815)], sides=(-1,))
    # dorsal pylon hatched panels (side view parallelograms) and side pylon panels (plan, 4 per pylon)
    B_dp = bvh_of(dpyl)
    side_grille(B_dp, [[(1120, 1697), (1210, 1697), (1233, 1669), (1143, 1669)], [(1092, 1734), (1180, 1734), (1203, 1707), (1114, 1707)]])
    for k, rowsets in (('Starboard', ((674, 712), (716, 754), (758, 796), (800, 834))), ('Port', ((1013, 1047), (1051, 1089), (1093, 1131), (1135, 1173)))):
        B_st = bvh_of(struts[k])
        for r0, r1 in rowsets:
            fr = lambda u, v: (X(u), Y(v), 60)
            decal(grille, B_st, [rect(r0, r1, 1507, 1576)], fr, (0, 0, -1), off=.12, cuts=1)
            decal(stip, B_st, hatch(rect(r0, r1, 1507, 1576)), fr, (0, 0, -1), off=.2, cuts=0)
    grille.done(G['Markings'], 60); stip.done(G['Markings'], 60)
    mk.done(G['Markings'], 60)
    # NCC-2100 on the side units' outer faces (side x 1690-1835, rows 1790-1812), reading from outside.
    txt = Acc('Registry NCC-2100 (propulsion units)', 'black')
    gv, gf = text_mesh('NCC-2100', 22 / PPM / .72)
    w = max(v[0] for v in gv) - min(v[0] for v in gv); sc = (1835 - 1690) / PPM / w
    gv = [(u * sc, v) for u, v in gv]
    yc_, zc_ = Ys((1690 + 1835) / 2), Z(1801)
    decal(txt, B_p, [], lambda u, v: (200, yc_ + u, zc_ + v), (-1, 0, 0), off=.14, cuts=1, mesh=(gv, gf))
    decal(txt, B_s, [], lambda u, v: (-200, yc_ - u, zc_ + v), (1, 0, 0), off=.14, cuts=1, mesh=(gv, gf))
    txt.done(G['Markings'], 60)
    return G

if __name__ == '__main__':
    build()
    kit.export_ship('federation')
