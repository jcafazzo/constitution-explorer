"""Constitution-class heavy cruiser — PDF 75, TO 01:04:10.  Run: Blender -b -P model-source/blender/constitution.py
Built from profiles measured on the plate (model-source/fleet/constitution_measure.py -> profiles/constitution.json):
primary hull revolved from the side view's forward half, secondary hull lofted from side height + plan breadth, dorsal
lofted between its drawn front/aft edges, nacelles lofted from plan + side, pylons laid along the front view's strut lines.
Frame: metres, Z up, bow at -Y, starboard -X (the site viewer's frame; exported without Y-up conversion)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
from mathutils import Vector

kit.PALETTE.setdefault('hull', ('dcdcd6', .55, .05, 1))
kit.PALETTE.setdefault('hullshade', ('c4c6c2', .5, .08, 1))
kit.PALETTE.setdefault('port', ('2a2e33', .35, .1, 1))
kit.PALETTE.setdefault('deflector', ('b07a3c', .35, .55, 1))
kit.PALETTE.setdefault('dome', ('e9a45a', .4, .1, 1))
D = json.load(open(os.path.join(kit.ROOT, 'model-source/blender/profiles/constitution.json')))
PPM, L = D['ppm'], D['L']
SX0, PX0, SZ0, PYC, FXC, FZ0 = 434, 442, 1916, 872.5, 817.0, 2560
ys = lambda px: -L / 2 + (px - SX0) / PPM
zs = lambda row: (SZ0 - row) / PPM
xf = lambda px: (px - FXC) / PPM
zf = lambda row: (FZ0 - row) / PPM

def interp(xs, ys_, x):
    if x <= xs[0]: return ys_[0]
    if x >= xs[-1]: return ys_[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i] or 1e-9); return ys_[i] + (ys_[i + 1] - ys_[i]) * t

def fair(v, k=2):
    out = list(v)
    for _ in range(k):
        out = [out[0]] + [(out[i - 1] + 2 * out[i] + out[i + 1]) / 4 for i in range(1, len(out) - 1)] + [out[-1]]
    return out

def gsmooth(xs, vs, sigma, keep_ends=True):
    """Gaussian smoothing of samples vs(xs) with sigma in the same units as xs (removes scan pixel steps)."""
    out = []
    for i, x in enumerate(xs):
        w = [math.exp(-((x2 - x) / sigma) ** 2 / 2) for x2 in xs]
        out.append(sum(a * b for a, b in zip(w, vs)) / sum(w))
    if keep_ends: out[0], out[-1] = vs[0], vs[-1]
    return out

def text_mesh(name, body, size, depth, material, parent):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = depth; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    tmp = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(tmp); bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get())); bpy.data.objects.remove(tmp)
    return kit._obj(name, me, material, parent)

def build():
    root = kit.group('USS Constitution NCC-1700')
    # ---------------- primary hull ----------------
    S = D['saucer']                      # [r, z_top, z_bottom], r descending from the rim to the axis
    S = sorted(S, key=lambda s: s[0])
    rs = [s[0] for s in S]
    zt = gsmooth(rs, [s[1] for s in S], .7); zb = gsmooth(rs, [s[2] for s in S], .7)
    zt[-1] = S[-1][1]; zb[-1] = S[-1][2]
    R = rs[-1]
    yc = D['saucer_axis_y']
    A = sorted(D['saucer_aft_top'], key=lambda s: s[0])
    ar = [a[0] for a in A]; az = gsmooth(ar, [a[1] for a in A], .9)
    # Plan: the B/C-deck dome is an oval 24 m wide; side view: it reaches 11.8 m forward and 18.2 m aft of the saucer axis.
    # Its height profile is the side view's forward half, mapped through that oval; outside it the saucer top is the forward
    # profile continued inward from r = 12 m (the deck the dome sits on).
    DF, DA, DW = 11.8, 18.2, 12.0
    z16, z26 = interp(rs, zt, 16.0), interp(rs, zt, 26.0)
    slope = (z16 - z26) / (16.0 - 26.0)                     # the saucer top's gentle cone, continued in under the dome
    base = lambda r: interp(rs, zt, r) if r >= 16.0 else z16 + slope * (r - 16.0)
    zd = gsmooth(rs, [s[1] for s in S], 1.3); zd[0] = zd[1]
    DE = next(r for r in rs if r > 6 and interp(rs, zd, r) - base(r) < .25)     # dome foot on the forward side
    def dome(rho): return interp(rs, zd, rho * DE)
    def top_xy(x, y):
        dy = y - yc; r = math.hypot(x, dy)
        rho = math.hypot(x / (DW * DE / DF), dy / ((DF if dy < 0 else DA) * DE / DF))
        z = base(r)
        if rho < 1: z = max(z, dome(rho))
        return z
    def top(r, phi): return top_xy(-r * math.sin(phi), yc - r * math.cos(phi))
    rr = [rs[i] for i in range(0, len(rs), 4)] + [R]
    nphi = 144
    bm = bmesh.new()
    ct = bm.verts.new((0, yc, base(0))); cb = bm.verts.new((0, yc, zb[0]))
    T, B = [], []
    for r in rr[1:]:
        T.append([bm.verts.new((-r * math.sin(2 * math.pi * j / nphi), yc - r * math.cos(2 * math.pi * j / nphi), base(r))) for j in range(nphi)])
        B.append([bm.verts.new((-r * math.sin(2 * math.pi * j / nphi), yc - r * math.cos(2 * math.pi * j / nphi), interp(rs, zb, r))) for j in range(nphi)])
    for j in range(nphi):
        k = (j + 1) % nphi
        bm.faces.new((ct, T[0][j], T[0][k])); bm.faces.new((cb, B[0][k], B[0][j]))
        for i in range(len(T) - 1):
            bm.faces.new((T[i][j], T[i + 1][j], T[i + 1][k], T[i][k])); bm.faces.new((B[i][k], B[i + 1][k], B[i + 1][j], B[i][j]))
        bm.faces.new((T[-1][j], B[-1][j], B[-1][k], T[-1][k]))      # rim edge
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('primary hull'); bm.to_mesh(me); bm.free()
    kit.smooth(kit._obj('primary hull', me, 'hull', root), 32)
    # B/C-deck dome: its own mesh in oval polar coordinates (rings follow the oval, so its foot is clean)
    sx, sf, sa = DW * DE / DF, DE, DA * DE / DF
    bm = bmesh.new(); nr, nt = 40, 144
    top_v = bm.verts.new((0, yc, dome(0)))
    rings = []
    for i in range(1, nr + 1):
        rho = i / nr; ring = []
        for j in range(nt):
            t = 2 * math.pi * j / nt; c, s_ = math.cos(t), math.sin(t)
            x = -sx * rho * s_; dy = -(sf if c > 0 else sa) * rho * c
            z = dome(rho) if i < nr else base(math.hypot(x, dy)) - .4
            ring.append(bm.verts.new((x, yc + dy, z)))
        rings.append(ring)
    for j in range(nt):
        k = (j + 1) % nt; bm.faces.new((top_v, rings[0][j], rings[0][k]))
        for i in range(nr - 1): bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('B/C deck dome and bridge'); bm.to_mesh(me); bm.free()
    o = kit._obj('B/C deck dome and bridge', me, 'hull', root); o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
    # deck grid drawn on the plan: rings at 21.8/28.2/35.4/43.0/51.0 m and 24 radials every 15 deg (r 21.8 m -> rim),
    # as fine grey strips laid on the upper surface
    def ribbon(name, pts, w=.32, lift=.06):
        bm = bmesh.new(); prev = None
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0; L_ = math.hypot(dx, dy) or 1e-9; nx, ny = -dy / L_ * w / 2, dx / L_ * w / 2
            def z(x, y):
                r = math.hypot(x, y - yc); ph = math.atan2(-x, -(y - yc)); return top(min(r, R - .05), ph) + lift
            a = [bm.verts.new((x0 + nx, y0 + ny, z(x0, y0))), bm.verts.new((x0 - nx, y0 - ny, z(x0, y0)))]
            b = [bm.verts.new((x1 + nx, y1 + ny, z(x1, y1))), bm.verts.new((x1 - nx, y1 - ny, z(x1, y1)))]
            bm.faces.new((a[0], a[1], b[1], b[0]))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = kit._obj(name, me, 'hullshade', root); o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons)); return o
    for rg in (21.8, 28.2, 35.4, 43.0, 51.0):
        ribbon('deck grid ring', [(-rg * math.sin(2 * math.pi * k / 180), yc - rg * math.cos(2 * math.pi * k / 180)) for k in range(181)])
    for k in range(24):
        t = 2 * math.pi * k / 24
        ribbon('deck grid radial', [(-r_ * math.sin(t), yc - r_ * math.cos(t)) for r_ in [21.8 + (R - 22.3) * j / 30 for j in range(31)]])
    # bridge cap and lower sensor array (the plate's small domes on the axis)
    ztop = zt[0]; zbot = zb[0]
    kit.sphere('lower sensor array', 3.0, (0, yc, zbot + .4), 'dome', scale=(1, 1, .6), parent=root)
    # spine from the dome to the impulse deck (plan rows 862-885 = 3.8 m wide; side: the aft top line above the deck)
    secs = []
    for i in range(30):
        y = yc + 14 + i * (ys(1100) - yc - 14) / 29; r = y - yc
        zt_ = max(interp(ar, az, r), base(r) + .3)
        hwid = 1.9 + 1.4 * max(0, 1 - i / 6)
        secs.append((y, -hwid, hwid, base(r) - .6, zt_))
    kit.loft('dorsal spine', secs, 'hull', p=3.0, seg=40, parent=root)
    # impulse power deck on the saucer's aft upper surface (side px 1090-1222, top row 1569; plan breadth ~ +-13.5 m)
    secs = []
    for i in range(13):
        px = 1090 + i * 11
        hw = 6 + 7.5 * min(1, i / 6)
        secs.append((ys(px), -hw, hw, zs(1612), zs(1569) - (0.0 if i < 11 else (i - 10) * 1.2)))
    kit.loft('impulse power deck', secs, 'hull', p=3.2, seg=48, parent=root)
    for sx in (-1, 1):
        kit.box('impulse power exhaust', (4.2, .4, 2.6), (sx * 4.6, ys(1222) + .1, zs(1584)), 'port', parent=root)
    # ---------------- secondary hull ----------------
    H = [h for h in D['sec_hull'] if h[0] >= ys(1088)]
    yy = [h[0] for h in H]; ht = gsmooth(yy, [h[1] for h in H], 2.2); hb = gsmooth(yy, [h[2] for h in H], 2.2)
    known = [(h[0], h[3]) for h in H if h[3]]
    def half_w(y, top, bot):
        r = (top - bot) / 2
        if y < known[0][0]: return r
        return interp([k[0] for k in known], [k[1] for k in known], y)
    hw = gsmooth(yy, [half_w(y, t, b) for y, t, b in zip(yy, ht, hb)], 2.2)
    secs = [(y, -w, w, b, t) for y, t, b, w in zip(yy, ht, hb, hw)]
    # stern: blunt in the side view (aft face rows 1787-1838 at px 1720), rounded in plan (the clamshell hangar doors).
    # Cut the loft where the hull is still ~full breadth and close it with a plan-rounded cap of the drawn aft height.
    w_ref = interp(yy, hw, ys(1600)); ic = max(i for i, w in enumerate(hw) if w >= .8 * w_ref)
    kit.loft('secondary hull', secs[:ic + 1], 'hull', p=2.15, seg=72, parent=root)
    yc0, w0, b0, t0 = yy[ic], hw[ic], hb[ic], ht[ic]
    ye, be, te = ys(1722), zs(1838), zs(1787)
    cap, door = [], []
    for i in range(17):
        u = i / 16; y = yc0 + (ye - yc0) * u
        w = w0 * math.sqrt(max(1 - u ** 2.2, 1e-4)); b = b0 + (be - b0) * u ** 1.5; t = t0 + (te - t0) * u ** 1.5
        cap.append((y, -w, w, b, t))
        if u >= .55: door.append((y + .3, -(w + .3), w + .3, b + (t - b) * .14, t - (t - b) * .14))   # 0.3 m proud of the cap
    kit.loft('secondary hull stern', cap, 'hull', p=2.15, seg=72, parent=root)
    kit.loft('shuttlecraft hangar doors', door, 'port', p=2.15, seg=72, parent=root)
    # navigational deflector: collar, dish and antenna at the bow of the secondary hull (side px 1000-1090)
    zc = (zs(1785) + zs(1850)) / 2
    kit.cyl('deflector collar', (zs(1765) - zs(1880)) / 2, ys(1090) - ys(1052), (0, (ys(1052) + ys(1090)) / 2, zc), 'hullshade', 'Y', parent=root)
    kit.cyl('navigational deflector dish', (zs(1785) - zs(1852)) / 2, ys(1053) - ys(1028), (0, (ys(1028) + ys(1053)) / 2, zc), 'deflector', 'Y', r2=(zs(1772) - zs(1862)) / 2, parent=root)   # dish seated on the collar
    kit.cyl('deflector antenna', .35, ys(1035) - ys(1002), (0, (ys(1002) + ys(1035)) / 2, zc), 'deflector', 'Y', parent=root)
    # shuttlecraft hangar doors on the aft face
    # ---------------- dorsal (connecting neck) ----------------
    nf = sorted(D['neck_front'], key=lambda p: p[1]); na = sorted(D['neck_aft'], key=lambda p: p[1])
    secs = []
    for i in range(25):
        z = 24 + i * (50.5 - 24) / 24
        y0 = interp([p[1] for p in nf], [p[0] for p in nf], z); y1 = interp([p[1] for p in na], [p[0] for p in na], z)
        secs.append((z, -6.8, 6.8, -y1, -y0))
    neck = kit.loft('dorsal', secs, 'hull', p=3.0, seg=48, parent=root)
    neck.rotation_euler = (math.pi / 2, 0, 0)
    # ---------------- warp nacelles + pylons ----------------
    NPp = D['nacelle_plan']; NSs = D['nacelle_side']
    sy = [s[0] for s in NSs]; st = [s[1] for s in NSs]; sb = [s[2] for s in NSs]
    py_ = [p[0] for p in NPp]; pr = [(p[2] - p[1]) / 2 for p in NPp]; pc = [(p[1] + p[2]) / 2 for p in NPp]
    y_a, y_b = ys(1340), ys(2085)
    mid = lambda v, ys_: sorted(x for y, x in zip(ys_, v) if y_a <= y <= y_b)[len([1 for y in ys_ if y_a <= y <= y_b]) // 2]
    XC = mid(pc, py_); ZC = mid([(a + b) / 2 for a, b in zip(st, sb)], sy)
    # body radius: the plan half-width, smoothed hard (sigma 2.5 m) so the drawn forward fattening and taper stay but the
    # pixel lumps go; the ends keep their measured shape (lighter smoothing)
    prs = gsmooth(py_, pr, 2.5, keep_ends=False); pre = gsmooth(py_, pr, .8)
    def rad(y):
        k = interp(py_, prs, y); e = interp(py_, pre, y)
        w = 1.0 if y_a <= y <= y_b else 0.0
        return w * k + (1 - w) * e
    stS = gsmooth(sy, st, .8); sbS = gsmooth(sy, sb, .8)
    hh = gsmooth(sy, [(a - b) / 2 for a, b in zip(st, sb)], 2.5, keep_ends=False); hhe = gsmooth(sy, [(a - b) / 2 for a, b in zip(st, sb)], .8)
    def radz(y):                                            # vertical half-height from the side view (it draws the unit ~1 m slimmer than plan)
        return interp(sy, hh, y) if y_a <= y <= y_b else interp(sy, hhe, y)
    for side in (-1, 1):
        g = kit.group('space/warp propulsion unit ' + ('starboard' if side < 0 else 'port'), root)
        secs = []
        for i_, y in enumerate(py_):
            if y < sy[0] or y > sy[-1]: continue
            if y_a + 3 < y < y_b - 3 and i_ % 2: continue        # body: every other station is plenty once smoothed
            r_ = rad(y); xc_ = side * abs(XC); rz = radz(y)
            if y <= y_b: z0_, z1_ = ZC - rz, ZC + rz
            else: z0_, z1_ = interp(sy, sbS, y), interp(sy, stS, y)        # raked aft cap as drawn in the side view
            secs.append((y, xc_ - r_, xc_ + r_, z0_, z1_))
        nac = kit.loft('nacelle', secs, 'hull', p=2.0, seg=72, parent=g)
        xc = side * abs(XC); zc = ZC; r = rad((y_a + y_b) / 2)
        # forward band (plan px 1310-1330) and aft end cap ring
        y0 = -L / 2 + (1310 - PX0) / PPM; y1 = -L / 2 + (1332 - PX0) / PPM
        kit.cyl('nacelle forward band', r + .35, y1 - y0, (xc, (y0 + y1) / 2, zc), 'port', 'Y', parent=g)
        ya0 = -L / 2 + (2088 - PX0) / PPM
        kit.cyl('nacelle end cap ring', r * .92, 1.2, (xc, ya0, zc), 'port', 'Y', parent=g)
        secs = []
        for i in range(17):
            px = 1915 + i * 10; y = ys(px); top_ = interp(sy, stS, y); rr_ = rad(y)
            secs.append((y, xc - rr_ * .45, xc + rr_ * .45, zc + rr_ * .6, max(top_, zc + rr_ + .2)))
        kit.loft('intercooler ridge', secs, 'hull', p=3.0, seg=40, parent=g)
        # outboard markings from the side view: emblem + broad bar (px 1425-1625), NCC-1700 (1640-1840), thin bar, grille
        bpy.context.view_layer.update()
        def surf(y, z):                       # outboard nacelle surface at (y, z), found by ray cast (markings sit 0.04 m proud)
            hit, loc, nor, _ = nac.ray_cast(Vector((xc + side * 30, y, z)), Vector((-side, 0, 0)))
            return (loc.x + side * .15) if hit else xc + side * r
        zt_ = zs(1505)
        rot_side = (math.pi / 2, 0, math.pi / 2 if side > 0 else -math.pi / 2)
        o = text_mesh('registry NCC-1700 (nacelle)', 'NCC-1700', 3.9, .05, 'port', g)
        o.location = (surf(ys(1740), zt_), ys(1740), zt_); o.rotation_euler = rot_side
        for a, b_, hgt, nm in ((1475, 1625, 2.6, 'pennant bar'), (1848, 1975, 1.2, 'pennant line')):
            for k in range(6):                 # short segments so each follows the curved flank
                y0_ = ys(a) + (ys(b_) - ys(a)) * k / 6; y1_ = ys(a) + (ys(b_) - ys(a)) * (k + 1) / 6
                kit.box(nm, (.1, y1_ - y0_ + .02, hgt), (surf((y0_ + y1_) / 2, zt_), (y0_ + y1_) / 2, zt_), 'port', parent=g)
        ye = (ys(1425) + ys(1470)) / 2
        kit.box('pennant emblem', (.1, ys(1470) - ys(1425), 2.6), (surf(ye, zt_), ye, zt_), 'port', rot=(math.radians(18) * side, 0, 0), parent=g)
        yg = (ys(1975) + ys(2020)) / 2
        kit.box('nacelle grille', (.1, ys(2020) - ys(1975), 2.8), (surf(yg, zs(1501)), yg, zs(1501)), 'hullshade', parent=g)
        yb_ = (ys(1305) + ys(1355)) / 2; zb_ = zs(1543)
        kit.box('nacelle forward bracket', (.1, ys(1355) - ys(1305), zs(1530) - zs(1555)), (surf(yb_, zb_), yb_, zb_), 'hullshade', parent=g)
        # pylon: front-view strut from the secondary hull (745, 2410) to the nacelle axis, chord from the side view
        # strut line fitted on the front view (outer ink centres (676,2320),(695.5,2340),(715.5,2360): 45 deg), 3.5 m thick
        x0, z0 = side * abs(xf(755)), zf(2400); x1, z1 = side * abs(xf(535)), zf(2178)
        dx, dz = x1 - x0, z1 - z0; ln = math.hypot(dx, dz)
        c0, c1 = ys(1470), ys(1546)
        th = math.atan2(dx, dz)
        kit.box('pylon', (3.5, c1 - c0, ln + 2), (x0 + dx / 2, (c0 + c1) / 2, z0 + dz / 2), 'hull', rot=(0, th, 0), bev=.8, parent=g)
        nx, nz = math.cos(th), -math.sin(th)
        if nz < 0: nx, nz = -nx, -nz
        for row in (668, 696, 724, 752):              # plan: four hatched grilles on the pylon's upper face (rows 655-780, starboard)
            xg = side * abs((row - PYC) / PPM); t = (xg - x0) / dx
            px_, pz_ = x0 + dx * t, z0 + dz * t
            kit.box('pylon grille', (.2, (c1 - c0) * .62, 3.9), (px_ + nx * 1.8, (c0 + c1) / 2, pz_ + nz * 1.8), 'port', rot=(0, th, 0), parent=g)
    # ---------------- markings ----------------
    # NCC-1700 on the primary hull top: along the arc at r = 37 m (plan: letters on the outer ring from row 705 to 1050),
    # letter tops toward the centre, reading starboard -> port; cap height ~6.7 m (40 px)
    Rt = 37.0; zr = interp(rs, zt, Rt) + .25; txt = 'NCC-1700'
    span = [math.radians(-47), math.radians(50)]
    for i, ch in enumerate(txt):
        if ch == ' ': continue
        th = span[0] + (span[1] - span[0]) * (i + .5) / len(txt)
        o = text_mesh('registry NCC-1700 (primary hull)', ch, 9.0, .3, 'port', root)
        o.location = (Rt * math.sin(th), yc - Rt * math.cos(th), zr)
        o.rotation_euler = (0, 0, th)            # glyph +X along the arc (starboard -> port), glyph +Y toward the centre
    # ---------------- weapons, sensors and deck fittings drawn on the plate ----------------
    xp = lambda row: (row - PYC) / PPM; yp = lambda px: -L / 2 + (px - PX0) / PPM
    for row in (668, 1072):                    # phaser bank P/S: dot pairs on the saucer top (plan)
        for px in (805, 830):
            x_, y_ = xp(row), yp(px)
            kit.sphere('phaser bank P/S', 1.1, (x_, y_, top_xy(x_, y_) + .1), 'port', scale=(1, 1, .55), parent=root)
    for row in (658, 1083):                    # small deck hatches near the aft rim (plan squares at px 1053)
        x_, y_ = xp(row), yp(1053)
        kit.box('deck hatch', (2.8, 2.8, .25), (x_, y_, top_xy(x_, y_) + .05), 'hullshade', parent=root)
    zdeck = zs(1569) + .05
    for sgn in (-1, 1):                        # impulse deck: small squares and the L-shaped vents (plan px 1128 / 1150-1185)
        kit.box('impulse deck hatch', (2.2, 2.2, .2), (sgn * abs(xp(800)), yp(1128), zdeck), 'hullshade', parent=root)
        xv = sgn * abs(xp(832)); yv = yp(1167)
        bpy.context.view_layer.update()
        def deck_z(x, y):                     # seat on the impulse deck's real (rounded) top
            h, loc, *_ = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((x, y, 120)), Vector((0, 0, -1)))
            return (loc.z + .08) if h else zdeck
        kit.box('impulse vent', (5.6, 1.0, .25), (xv, yv - 2.6, deck_z(xv, yv - 2.6)), 'port', parent=root)
        kit.box('impulse vent', (1.0, 5.4, .25), (xv + sgn * 2.3, yv, deck_z(xv + sgn * 2.3, yv)), 'port', parent=root)
    bpy.context.view_layer.update()
    dg0 = bpy.context.evaluated_depsgraph_get(); sc0 = bpy.context.scene
    def hit_front(x, z):
        h, loc, nor, *_ = sc0.ray_cast(dg0, Vector((x, -200, z)), Vector((0, 1, 0))); return loc if h else None
    for x_ in (xf(804), xf(826)):              # photon torpedoes P/S: the two dots on the dome's front face (front view)
        loc = hit_front(x_, zf(2194))
        if loc: kit.cyl('photon torpedo tube', .9, .5, (x_, loc.y - .1, zf(2194)), 'port', 'Y', parent=root)
    for x_ in (-4.6, 0.0, 4.6):               # the three forward ports on the rim face below the dome (front view "ooo")
        loc = hit_front(x_, zf(2256))
        if loc: kit.cyl('forward sensor port', 1.6, .3, (x_, loc.y - .05, zf(2256)), 'port', 'Y', parent=root)
    for sgn in (-1, 1):                        # phaser P/S under the saucer (front-view leader; position interpreted)
        x_ = sgn * 7.0; y_ = yc - 9.0
        h, loc, *_ = sc0.ray_cast(dg0, Vector((x_, y_, -50)), Vector((0, 0, 1)))
        if h: kit.sphere('phaser P/S (ventral)', 1.1, (x_, y_, loc.z - .1), 'port', scale=(1, 1, .55), parent=root)
    for side in (1, -1):                       # secondary hull pennant (side px 1135-1170 emblem, 1170-1300 stripe, row ~1820)
        for (a, b_, hgt, nm) in ((1135, 1170, 3.0, 'pennant emblem (secondary hull)'), (1170, 1300, 1.0, 'pennant stripe (secondary hull)')):
            for k in range(5):
                y0_ = ys(a) + (ys(b_) - ys(a)) * k / 5; y1_ = ys(a) + (ys(b_) - ys(a)) * (k + 1) / 5; ym = (y0_ + y1_) / 2
                h, loc, *_ = sc0.ray_cast(dg0, Vector((side * 60, ym, zs(1820))), Vector((-side, 0, 0)))
                if h: kit.box(nm, (.1, y1_ - y0_ + .02, hgt), (loc.x + side * .03, ym, zs(1820)), 'port', parent=root)
    # ---------------- ports and windows (side-view dashes, mirrored port/starboard) ----------------
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    n = 0
    for y, z, w, h in D['windows_side']:
        for side in (1, -1):
            hit, loc, nor, *_ = sc.ray_cast(dg, Vector((side * 120, y, z)), Vector((-side, 0, 0)))
            if not hit or abs(loc.x) < .5: continue
            o = kit.box('port window', (.1, max(w, 1.0), max(h, .6)), (loc.x + side * .02, y, z), 'port', parent=root)
            o.rotation_euler = (0, 0, math.atan2(nor.y, nor.x) - (0 if side > 0 else math.pi)); n += 1
    print('windows placed', n)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export_ship('constitution')
