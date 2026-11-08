"""Shared builder for the Class I destroyer / scout hull (Saladin PDF 77, Hermes PDF 79): saucer, one warp nacelle
under it on a single swept pylon, no secondary hull.  Run through saladin.py / hermes.py inside Blender.

Measured outlines come from profiles/<id>-hull.json (fleet_destroyer_measure.py, system Python):
  saucer  — side-view half-profile (front half, bow to centre), revolved about the saucer centre found in plan
  nacelle — side-view top/bottom + plan width per station, lofted
Everything else is placed from plate pixel coordinates in the ship's CFG (plan / side / front px) through the
converters below. Frame: metres, Z up, bow -Y, starboard -X; z = 0 on the saucer rim mid-plane."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import kit

HERE = os.path.dirname(os.path.abspath(__file__))


class Plate:
    def __init__(self, M):
        self.M = M; k = M['k']; self.k = k
        self.Yp = lambda px: (px - M['plan_mid']) / k       # plan px -> y
        self.Xp = lambda py: (py - M['cy']) / k             # plan py -> x (image-up = starboard = -X)
        self.Ys = lambda px: (px - M['side_mid']) / k       # side px -> y
        self.Zs = lambda py: -(py - M['zref']) / k          # side py -> z
        self.Xf = lambda px: (px - M['fcx']) / k            # front px -> x (seen from the bow, image-right = +X)
        self.Zf = lambda py: -(py - M['zref_f']) / k        # front py -> z
        self.L = lambda px: px / k                          # px length -> m


def interp(table, col, x):
    xs = [r[0] for r in table]; vs = [r[col] for r in table]
    if xs[0] > xs[-1]: xs, vs = xs[::-1], vs[::-1]
    return float(np.interp(x, xs, vs))


# ---------- mesh helpers ----------
def obj_from_bm(name, bm, material, parent=None, angle=40):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), angle)


def fin(name, outline, thick, material, parent=None):
    """Thin plate whose side outline is outline [(y, z)...] (closed, any winding) and whose thickness is thick(y)."""
    bm = bmesh.new()
    L = [bm.verts.new((-thick(y) / 2, y, z)) for y, z in outline]
    R = [bm.verts.new((thick(y) / 2, y, z)) for y, z in outline]
    n = len(outline)
    fl = bm.faces.new(L); fr = bm.faces.new(R[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((L[i], L[j], R[j], R[i]))
    bmesh.ops.triangulate(bm, faces=[fl, fr])
    return obj_from_bm(name, bm, material, parent, 35)


def orient(n, along):
    n = Vector(n).normalized(); a = Vector(along); a = (a - a.dot(n) * n)
    if a.length < 1e-6: a = n.orthogonal()
    a.normalize(); b = n.cross(a)
    return Matrix((a, b, n)).transposed()


def plaque(name, loc, n, along, size, material, parent=None, lift=0.0):
    """Box lying on a surface: size = (along, across, thickness); its underside sits `lift` below the hit point."""
    m = orient(n, along)
    o = kit.box(name, size, Vector(loc) + Vector(n).normalized() * (size[2] / 2 - lift), material, parent=parent)
    o.rotation_euler = m.to_euler(); return o


def cast(objs, origin, direction):
    """Nearest hit on any of objs (all built at identity transforms): (location, normal) or None."""
    best = None
    d = Vector(direction).normalized()
    for o in objs:
        ok, loc, nor, _ = o.ray_cast(Vector(origin), d)
        if ok:
            dist = (loc - Vector(origin)).length
            if best is None or dist < best[0]: best = (dist, loc, nor)
    return (best[1], best[2]) if best else None


def glyph_mesh(name, ch, cap, depth, material, parent=None, width=None):
    """One character as a mesh (Blender's built-in font), centred on its cell, reading +X, up +Y, facing +Z."""
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = ch; cu.size = cap / 0.72; cu.extrude = depth / 2
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.resolution_u = 6
    tmp = bpy.data.objects.new(name + '_tmp', cu); bpy.context.scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); me.name = name
    # re-centre on the actual glyph box so the letter sits where the plate draws it
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    if xs:
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        sx = (width / max(max(xs) - min(xs), 1e-6)) if (width and ch not in '-.') else 1.0
        sy = cap / max(max(ys) - min(ys), 1e-6) if ch not in '-.' else 1.0
        for v in me.vertices: v.co.x = (v.co.x - cx) * sx; v.co.y = (v.co.y - cy) * sy
    o = kit._obj(name, me, material, parent)
    return kit.smooth(o, 30)


def text_on(objs, s, name, centre, along, up, cap, material, parent=None, depth=0.12, spacing=0.82, out=None):
    """Lay string s on the surface of objs: letters centred along `along` around `centre`, letter tops toward `up`;
    each letter is ray-cast onto the surface from outside along -normal guess `out`."""
    along = Vector(along).normalized(); out = Vector(out).normalized()
    adv = cap * spacing; n = len(s); parts = []
    for i, ch in enumerate(s):
        if ch == ' ': continue
        p = Vector(centre) + along * ((i - (n - 1) / 2) * adv)
        hit = cast(objs, p + out * 30, -out)
        if not hit: continue
        loc, nor = hit
        g = glyph_mesh(f'{name} {ch}', ch, cap, depth, material, parent, width=adv * .78)
        upv = Vector(up); upv = (upv - upv.dot(nor) * nor).normalized(); rd = upv.cross(nor)  # reading dir = up x normal
        g.matrix_world = Matrix.Translation(loc + nor * (depth / 2 - 0.03)) @ Matrix((rd, upv, nor)).transposed().to_4x4()
        parts.append((g, loc.copy(), nor.copy()))
    return parts


def merge_repeats(root):
    """Join same-named, same-material small parts (window dashes, letters of one word, paired fittings) into one mesh each."""
    groups = {}
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH': continue
        base = o.name.split('.')[0]
        if base.startswith(('saucer registry', 'nacelle registry')) and base != 'nacelle registry chevron':
            base = base.rsplit(' ', 1)[0] if base.split(' ')[-1] in 'NC-0123456789' else base
        key = (base, o.data.materials[0].name if o.data.materials else '')
        groups.setdefault(key, []).append(o)
    for (base, _), objs in groups.items():
        if len(objs) < 2: continue
        bm = bmesh.new()
        for o in objs:
            me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new(base); bm.to_mesh(me); bm.free()
        for m in objs[0].data.materials: me.materials.append(m)
        for o in objs: bpy.data.objects.remove(o)
        kit._obj(base, me, None, root)


NAC_INFO = {}


# ---------- the build ----------
def build(cfg):
    kit.reset()
    M = json.load(open(os.path.join(HERE, 'profiles', cfg['id'] + '-hull.json')))
    pl = Plate(M); Yp, Xp, Ys, Zs, Xf, Zf, L = pl.Yp, pl.Xp, pl.Ys, pl.Zs, pl.Xf, pl.Zf, pl.L
    Yc = M['saucer_y']; Rp = M['R']
    root = kit.group(cfg['name'])
    W, D = 'white', 'dark'

    # ---- primary hull: revolve the measured side half-profile about the saucer centre ----
    prof = sorted(M['saucer'])                     # [r, top, bottom] ascending r
    r_dk, r_ld = cfg['deck_r'], cfg['lower_dome_r']
    top = lambda r: interp(prof, 1, max(r, r_dk))
    bot = lambda r: interp(prof, 2, max(r, r_ld))
    # the plan disc fixes the diameter (side-view rim tips carry the ink line): scale the half-profile radially so the
    # rim lands on the plan radius less half an ink line
    rs_scale = (Rp - 0.25) / (prof[-1][0] + 0.15)
    prof = [[r * rs_scale, t, b] for r, t, b in prof]
    rmax = prof[-1][0]
    rs = list(np.arange(0, rmax - 1.2, 0.5)) + list(np.linspace(rmax - 1.2, rmax, 9))
    # rim: the drawn bow tip is rounded; close the profile through the measured tip
    pts = [(r, top(r)) for r in rs] + [(rmax + 0.15 * rs_scale, (top(rmax) + bot(rmax)) / 2)] + [(r, bot(r)) for r in rs[::-1]]
    saucer = kit.revolve('primary hull', pts, W, axis='Z', seg=128, parent=root, loc=(0, Yc, 0))
    # deck grid drawn on the plan saucer: concentric rings + radials every 15 deg, as thin 'hullshade' ribbons laid on
    # the measured top surface (house style shared with constitution.py: 0.32 m wide, lifted 0.06 m)
    kit.PALETTE.setdefault('hullshade', ('c4c6c2', .5, .08, 1))
    def ribbon(name, pts, w=.32, lift=.06):
        bm = bmesh.new()
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0; l_ = math.hypot(dx, dy) or 1e-9; nx, ny = -dy / l_ * w / 2, dx / l_ * w / 2
            zf = lambda x, y: top(math.hypot(x, y - Yc)) + lift
            a = [bm.verts.new((x0 + nx, y0 + ny, zf(x0, y0))), bm.verts.new((x0 - nx, y0 - ny, zf(x0, y0)))]
            b = [bm.verts.new((x1 + nx, y1 + ny, zf(x1, y1))), bm.verts.new((x1 - nx, y1 - ny, zf(x1, y1)))]
            bm.faces.new((a[0], a[1], b[1], b[0]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for f in me.polygons: f.use_smooth = True
        if any(f.normal.z < 0 for f in me.polygons):
            me.flip_normals()
        return kit._obj(name, me, 'hullshade', root)
    dg = cfg['deck_grid']                          # plan px: ring radii, radial start radius, radial step (deg)
    for rp in dg['rings']:
        rg = L(rp)
        ribbon('deck grid ring', [(rg * math.sin(2 * math.pi * k / 180), Yc - rg * math.cos(2 * math.pi * k / 180)) for k in range(181)])
    r0, r1 = L(dg['radial_r0']), rmax - .35
    for k in range(int(round(360 / dg['radial_step']))):
        t = math.radians(k * dg['radial_step'])
        ribbon('deck grid radial', [(r_ * math.sin(t), Yc - r_ * math.cos(t)) for r_ in np.linspace(r0, r1, 40)])
    # lower sensor dome: the rounded disc the drawn lower hull ends in
    ld = cfg['lower_dome']                         # side px: x0, x1, y_top, y_bottom
    rr = L(ld[1] - ld[0]) / 2; zt, zb = Zs(ld[2]), Zs(ld[3]); e = (zt - zb) * .45
    pts = [(0, zb)] + [(rr - e + e * math.sin(a), zb + e - e * math.cos(a)) for a in np.linspace(0, math.pi / 2, 8)] + [(rr, zt), (0, zt)]
    ldome = kit.revolve('lower sensor dome', pts, 'antimony', axis='Z', seg=96, parent=root, loc=(0, Yc, 0))

    # ---- bridge: one smooth dome, revolved from a single profile ----
    # Profile r(z) from the front view (base half-width at the saucer, superellipse fitted to the drawn rows: p ~ 2.2
    # reproduces them within ~3 px), top height from the side view; the side and plan show it ~1.2x longer fore-aft
    # than wide, so the revolved surface is stretched along Y about its own centre (side-view front/rear edges).
    bd = cfg['bridge']
    r0 = L(bd['hw']); zb0 = Zf(bd['base_f']); ztop = Zs(bd['top']); pb = bd['p']
    yb_c = Ys((bd['front'] + bd['rear']) / 2); sy = L(bd['rear'] - bd['front']) / 2 / r0
    pts = [(0, zb0 - 1.2), (r0, zb0 - 1.2)]
    for t in np.linspace(0, 1, 28)[:-1]:
        pts.append((r0 * (1 - t ** pb) ** (1 / pb), zb0 + (ztop - zb0) * t))
    pts.append((0, ztop))
    dome = kit.revolve('bridge dome', pts, W, axis='Z', seg=96, parent=root)
    dome.data.transform(Matrix.Translation((0, yb_c, 0)) @ Matrix.Diagonal((1, sy, 1, 1)))
    sa = cfg['sensor_array']                       # side px centre x, front half-width px, side top py
    ra, za = L(sa['hw']), Zs(sa['top']); zs_b = ztop - 0.25
    pts = [(0, za)] + [(ra * math.sin(a) ** .8, zs_b + (za - zs_b) * math.cos(a) ** 1.4) for a in np.linspace(0.12, math.pi / 2, 10)] + [(ra, zs_b - .3), (0, zs_b - .3)]
    kit.revolve('sensor array', pts, 'grey', axis='Z', seg=64, parent=root, loc=(0, Ys(sa['x']), 0))

    # ---- dorsal spine, impulse deck and pylon ----
    tr = M['top_rear']                             # [y, z] side-view top behind the saucer centre
    ztr = lambda y: interp(tr, 1, y)
    sp = cfg['spine']                              # plan px stations [(px, half-width px)]
    secs = [(Yp(px), -L(hw), L(hw), top(abs(Yp(px) - Yc)) - 1.5, ztr(Yp(px)) - 0.1) for px, hw in sp]
    spine = kit.loft('dorsal spine', secs, W, p=2.4, seg=48, parent=root)
    dk = cfg['impulse_deck']                       # plan px stations [(px, half-width px)], aft-face bottom side py
    zbot = Zs(dk['bottom'])
    secs = []
    for px, hw in dk['plan']:
        y = Yp(px); secs.append((y, -L(hw), L(hw), zbot, Zs(dk['top'])))
    deck = kit.loft('impulse deck', secs, W, p=5, seg=72, parent=root)
    ya = Yp(dk['plan'][-1][0])
    for side in (-1, 1):
        ip = cfg['impulse']                        # side px rect x0,x1,y0,y1; plan py rows of one unit
        x0, x1 = sorted((Xp(ip['plan'][0]), Xp(ip['plan'][1])))
        xc, wx = side * abs((x0 + x1) / 2), abs(x1 - x0)
        z0, z1 = Zs(ip['side'][3]), Zs(ip['side'][2]); y0 = Ys(ip['side'][0])
        kit.box('impulse power housing', (wx, ya - y0 + .5, z1 - z0), (xc, (y0 + ya + .5) / 2, (z0 + z1) / 2), W, bev=.5, parent=root)
        kit.box('impulse power exhaust', (wx * .8, .3, (z1 - z0) * .7), (xc, ya + .62, (z0 + z1) / 2), 'red', bev=.1, parent=root)
    # the L-shaped impulse vents drawn on the deck top (plate outlines), raised mid-grey panels
    zdeck = Zs(dk['top'])
    for poly in cfg['impulse']['vents']:
        pts = [(Xp(py), Yp(px)) for px, py in poly]
        if sum((a[0] * b[1] - b[0] * a[1]) for a, b in zip(pts, pts[1:] + pts[:1])) < 0: pts = pts[::-1]
        kit.extrude('impulse power vent', pts, .5, 'grey', plane='XY', loc=(0, 0, zdeck + .1), parent=root)
    def mark(name, px, py, sz_px, objs, h=.3, material='grey'):
        x, y = Xp(py), Yp(px); hit = cast(objs, (x, y, 60), (0, 0, -1))
        if hit:
            along = Vector((x, y - Yc, 0)).normalized()
            plaque(name, hit[0], hit[1], along, (L(sz_px), L(sz_px), h), material, root, .1)
    for px, py in cfg['hatches']:                  # small squares at the deck's forward-outboard corners
        mark('impulse deck hatch', px, py, 8, [deck, saucer])
    for px, py in cfg['rim_marks']:                # the four small rectangles near the saucer rim (plan)
        mark('saucer rim hatch', px, py, 8, [saucer])
    bx = cfg['bridge_box']                         # plan px x0,x1,y0,y1: the box aft of the bridge
    hit = cast([spine, saucer], (Xp((bx[2] + bx[3]) / 2), Yp((bx[0] + bx[1]) / 2), 60), (0, 0, -1))
    if hit:
        plaque('bridge aft housing', hit[0], Vector((0, 0, 1)), (0, 1, 0), (L(bx[1] - bx[0]), L(bx[3] - bx[2]), 1.4), W, root, .5)
    py_ = cfg['pylon']                             # side px outline, thickness stations [(y px, thickness m)]
    th = [(Ys(px), t) for px, t in py_['thick']]
    thick = lambda y: float(np.interp(y, [a for a, b in th], [b for a, b in th]))
    outline = [(Ys(px), Zs(py)) for px, py in py_['outline']]
    pylon = fin('pylon', outline, thick, W, root)

    # ---- warp nacelle (space/warp propulsion unit): a true surface of revolution, tapering as drawn ----
    # Circular stations whose radius is a straight-line fit to the drawn side-view half-height along the body (plate
    # draws it tapering ~19 m -> ~15 m), with the axis tilted so the drawn top line stays flat; hemispherical nose from
    # the drawn nose; aft end raked as drawn (top edge ~5 m aft of the bottom edge) with a flared collar lip and an
    # elliptical cap set in the cut face.  Mirrored exactly (stations are circles about x = 0).
    nc = cfg['nacelle']; N = M['nacelle']
    ztop = Zs(cfg['nac_top_row'])
    y_n = Ys(cfg['nac_front_side']); yT, yB = Ys(nc['aft_top']), Ys(nc['aft_bottom'])
    fit = [(y, h) for y, xc, w, zc, h in N if y_n + 25 < y < yB - 6]     # behind the nose/keel region (that is the ventral strip)
    bslope, a0 = np.polyfit([f[0] for f in fit], [f[1] for f in fit], 1)
    # nose dome radius = the drawn half-height just behind the nose; the body then tapers straight from there to the
    # fitted aft radius (the drawn taper), so the station radius never jumps
    r0 = float(np.median([h for y, xc, w, zc, h in N if y_n + 8 < y < y_n + 16]))
    y_j = y_n + r0; r_aft = a0 + bslope * yB
    rb = lambda y: r0 + (r_aft - r0) * (y - y_j) / (yB - y_j)
    def R(y):
        if y < y_n: return 0.0
        if y < y_j: return r0 * math.sqrt(max(0.0, 1 - ((y_j - y) / r0) ** 2))
        return rb(y)
    ZC = lambda y: ztop - (r0 if y < y_j else rb(y))
    NAC_INFO['nacelle'] = dict(r_front=round(rb(y_j), 2), r_aft=round(rb(yB), 2), mean_dia=round(rb(y_j) + rb(yB), 2))
    zbot_B = ztop - 2 * rb(yB)
    pn = Vector((0, ztop - zbot_B, -(yT - yB))).normalized()   # raked-face normal, pointing aft
    p0 = Vector((0, yT, ztop))
    def rev_y(name, prof, material, cuts=(), seg=96):
        """Circular stations [(r, y)] centred on the tilted axis; cuts = [(plane point, normal)]: drop the + side, cap."""
        bm = bmesh.new(); rings = []
        for r, t in prof:
            zc = ZC(t)
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / seg), t, zc + r * math.sin(2 * math.pi * i / seg))) for i in range(seg)])
        for k in range(len(rings) - 1):
            for i in range(seg):
                a, b = rings[k][i], rings[k][(i + 1) % seg]; c, d = rings[k + 1][(i + 1) % seg], rings[k + 1][i]
                bm.faces.new((a, b, c, d))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        for co, no in cuts:
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=True)
        if cuts:
            bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        return kit.smooth(kit._obj(name, me, material, root), 40)
    body_ys = list(np.linspace(y_n, y_j, 26)) + list(np.linspace(y_j, yT + 1.0, 30))[1:]
    nac = rev_y('space/warp propulsion unit', [(R(y), y) for y in body_ys], W, cuts=[(p0, pn)])
    # flared collar lip around the raked end (band ~1.3 m wide, flaring 0.12 -> 0.45 m proud)
    lys = np.linspace(yB - 3.0, yT + 1.0, 8)
    lip = [(R(lys[0]) - .25, lys[0])] + [(R(y) + .12 + .33 * i / 7, y) for i, y in enumerate(lys)] + [(R(lys[-1]) - .25, lys[-1]), (R(lys[0]) - .25, lys[0])]
    rev_y('nacelle aft collar', lip, 'antimony', cuts=[(p0, pn), (p0 - pn * 1.3, -pn)])
    # elliptical cap inside the cut face
    pt_top, pt_bot = Vector((0, yT, ztop)), Vector((0, yB, zbot_B))
    dvec = pt_top - pt_bot; fc = (pt_top + pt_bot) / 2
    cap = kit.sphere('nacelle aft end cap', 1.0, (0, 0, 0), 'antimony', parent=root)
    cap.matrix_world = Matrix.Translation(fc) @ Matrix((Vector((1, 0, 0)) * rb(fc.y) * .62, dvec.normalized() * dvec.length / 2 * .62, pn * 1.1)).transposed().to_4x4()
    # nose end cap and bands (thin shells following the hull)
    def shell(name, y0, y1, grow, material):
        ys_ = np.linspace(y0, y1, 12 if y0 < y_j else 3)
        pr = [(max(R(y0), .05) - .3, y0)] + [(R(y) + grow, y) for y in ys_] + [(max(R(y1), .05) - .3, y1), (max(R(y0), .05) - .3, y0)]
        return rev_y(name, pr, material)
    ncap = Ys(nc['nose_cap'])
    rev_y('nacelle forward end cap', [(R(y) + .05, y) for y in np.linspace(y_n - .05, ncap, 18)] + [(R(ncap) - .3, ncap), (0, ncap)], 'antimony')
    for nm, (a, b) in nc['bands'].items():
        shell(nm, Ys(a), Ys(b), .12, D)
    # ventral strip: where the plate draws the underside deeper than the fitted body (forward keel), as a fairing
    zbc = lambda y: ZC(y) - R(y)
    deep = [(y, zc - h) for y, xc, w, zc, h in N if zc - h < zbc(y) - .15 and y_j < y < yB - 10]   # behind the nose dome only
    if deep:
        ya_, yb_ = deep[0][0], deep[-1][0]
        y_s = max(ya_ - 4, y_n + r0 * .6)
        ss = [(y_s, -1.0, 1.0, zbc(y_s) + .6, zbc(y_s) + 2.5)]
        for y in np.linspace(ya_, yb_, 30):
            zz = min(float(np.interp(y, [d[0] for d in deep], [d[1] for d in deep])), zbc(y))
            ss.append((y, -2.8, 2.8, zz, zbc(y) + 2.5))
        ss.append((yb_ + 6, -1.0, 1.0, zbc(yb_ + 6) + .6, zbc(yb_ + 6) + 2.5))
        kit.loft('nacelle ventral strip', ss, W, p=2.6, seg=48, parent=root)
    # grille pod fairings on the upper flanks (plan bulges + side-view top rail), embedded in the body
    gp = nc['pods']
    y0, y1 = Ys(gp['x'][0]), Ys(gp['x'][1]); zt = Zs(gp['top']); xo = abs(Xp(gp['outer'])); rp = nc.get('pod_r', 3.0)
    for side in (-1, 1):
        xc = side * (xo - rp); zc = zt - rp; ss = []
        for t in np.linspace(0, 1, 30):
            y = y0 + (y1 - y0) * t; f = min(1, min(t, 1 - t) / .1) ** .55
            ss.append((y, xc - rp * f, xc + rp * f, zc - rp * f, zc + rp * f))
        kit.loft('nacelle grille pod', ss, W, p=2.2, seg=40, parent=root)
        kit.box('nacelle pod grille', (rp * .55, (y1 - y0) * .78, .3), (xc, (y0 + y1) / 2, zc + rp * .93), D, parent=root)   # top of the pod (centre 0.93 r, top just proud)
    # lower forward grille housings (front view "ears", side-view rounded box)
    lb = nc['lower_box']
    y0, y1 = Ys(lb['side'][0]), Ys(lb['side'][1]); z1, z0 = Zs(lb['side'][2]), Zs(lb['side'][3])
    ym = (y0 + y1) / 2; xo = abs(Xf(lb['front_outer'])); xin = math.sqrt(max(R(ym) ** 2 - ((z0 + z1) / 2 - ZC(ym)) ** 2, 1)) - .6
    for side in (-1, 1):
        kit.box('nacelle lower grille housing', (xo - xin, y1 - y0, z1 - z0), (side * (xo + xin) / 2, (y0 + y1) / 2, (z0 + z1) / 2), W, bev=.8, parent=root)
        kit.box('nacelle lower grille', (.2, (y1 - y0) * .8, (z1 - z0) * .5), (side * (xo + .02), (y0 + y1) / 2, (z0 + z1) / 2), D, parent=root)
    # decals seated on the true surface (r + 0.05 m), both flanks
    def decal(name, poly, material, side):
        bm = bmesh.new()
        f = bm.faces.new([bm.verts.new((y, z, 0)) for y, z in poly])
        bmesh.ops.triangulate(bm, faces=[f])
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=5, use_grid_fill=True)
        for vv in bm.verts:
            y, z = vv.co.x, vv.co.y
            vv.co = Vector((side * math.sqrt(max((R(y) + .05) ** 2 - (z - ZC(y)) ** 2, 0)), y, z))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        if sum(p_.normal.x for p_ in me.polygons) * side < 0: me.flip_normals()
        for p_ in me.polygons: p_.use_smooth = True
        return kit._obj(name, me, material, root)
    rect = lambda a, b, c, d_: [(Ys(a), Zs(d_)), (Ys(b), Zs(d_)), (Ys(b), Zs(c)), (Ys(a), Zs(c))]
    for side in (-1, 1):
        g = nc['aft_grille']; decal('nacelle aft grille', rect(*g), 'grey', side)
        for st in nc['stripes']: decal('registry stripe', rect(*st), 'black', side)
        for blk in nc['chevron']: decal('registry chevron', [(Ys(a), Zs(b)) for a, b in blk][::-1], 'black', side)
        t = nc['lettering']
        yc = Ys((t[0] + t[1]) / 2); cap = L(t[3])
        rd = Vector((0, 1, 0)) if side > 0 else Vector((0, -1, 0))
        for gl, loc, nor in text_on([nac], cfg['registry'], 'nacelle registry', (0, yc, Zs(t[2])), rd, (0, 0, 1), cap, 'black', root,
                                    spacing=L(t[1] - t[0]) / len(cfg['registry']) / cap, out=(side, 0, 0)):
            me = gl.data; me.transform(gl.matrix_world); gl.matrix_world = Matrix.Identity(4)
            for vv in me.vertices:      # wrap the flat glyph onto the cylinder: height above its tangent plane kept
                h = (vv.co - loc).dot(nor); zc_ = ZC(vv.co.y); dr = Vector((vv.co.x, 0, vv.co.z - zc_)).normalized()
                vv.co = Vector((0, vv.co.y, zc_)) + dr * (R(vv.co.y) + .04 + max(h + .03, 0))

    # ---- main sensor / deflector: dish on a stalk under the lower sensor dome ----
    ms = cfg['main_sensor']                        # side px
    yd0, yd1 = Ys(ms['dish_x'][0]), Ys(ms['dish_x'][1]); zd = Zs(ms['dish_cy']); rd_ = L(ms['dish_r'])
    pts = [(0, yd1 - .2), (rd_ * .35, yd1 - .35), (rd_ * .75, yd1 - (yd1 - yd0) * .6), (rd_, yd0), (rd_ - .35, yd0 + .05),
           (rd_ * .72, yd1 - (yd1 - yd0) * .5), (rd_ * .3, yd1 - .7), (0, yd1 - .55)]
    kit.revolve('main sensor dish', pts, 'antimony', axis='Y', seg=96, parent=root, loc=(0, 0, zd))
    ys_ = Ys(ms['stalk_x']); zs0 = Zs(ld[3]) + .3; zs1 = Zs(ms['ball'][1])
    kit.box('main sensor stalk', (ms['stalk_w'], L(ms['stalk_t']), zs0 - zs1), (0, ys_, (zs0 + zs1) / 2), W, bev=.3, parent=root)
    kit.sphere('main sensor hub', L(ms['ball'][2]), (0, Ys(ms['ball'][0]), zd), W, parent=root)
    yb = Ys(ms['ball'][0])
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        p0 = Vector((rd_ * .8 * math.cos(a), yd0 + (yd1 - yd0) * .25, zd + rd_ * .8 * math.sin(a))); p1 = Vector((0, yb, zd))
        v = p1 - p0
        c = kit.cyl('main sensor strut', .15, v.length, (p0 + p1) / 2, D, parent=root)
        c.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    yf = Ys(ms['feed_x'])
    kit.cyl('main sensor feed', .35, yd1 - yf, (0, (yf + yd1) / 2, zd), 'antimony', 'Y', r2=.6, parent=root)
    kit.sphere('main sensor feed tip', .5, (0, yf, zd), 'antimony', parent=root)

    # ---- armament ----
    for px, py in cfg.get('phasers_top', []):      # plan px, ray-cast down onto the saucer
        hit = cast([saucer], (Xp(py), Yp(px), 40), (0, 0, -1))
        if hit:
            kit.sphere('phaser bank', .75, hit[0] + hit[1] * .1, D, scale=(1, 1, .6), parent=root)
    for px, py in cfg.get('phasers_lower', []):    # front px/py: x and z on the lower hull
        x = Xf(px); hit = cast([saucer], (x, Yc - 2, -40), (0, 0, 1))
        if hit:
            kit.sphere('phaser bank (lower)', .75, hit[0] + hit[1] * .1, D, scale=(1, 1, .6), parent=root)
    for px, py in cfg.get('torpedoes', []):        # front px/py on the superstructure face
        hit = cast([dome], (Xf(px), Yc - 60, Zf(py)), (0, 1, 0))
        if hit:
            c = kit.cyl('photon torpedo launcher', .55, .4, hit[0], 'black', parent=root)
            c.rotation_euler = hit[1].to_track_quat('Z', 'Y').to_euler()

    # ---- forward ports (the three circles drawn on the bow rim) ----
    for px, py, rp in cfg['bow_ports']:
        hit = cast([saucer], (Xf(px), Yc - 90, Zf(py)), (0, 1, 0))
        if hit:
            c = kit.cyl('forward sensor port', L(rp), .3, hit[0], D, parent=root)
            c.rotation_euler = hit[1].to_track_quat('Z', 'Y').to_euler()

    # ---- windows: dashes drawn on rim, superstructure, lower hull, pylon and deck ----
    def ring(name, z, ang0, ang1, n, ln, ht, objs, centre=(0, Yc)):
        for a in np.linspace(math.radians(ang0), math.radians(ang1), n):
            d = Vector((math.sin(a), -math.cos(a), 0))
            o = Vector((centre[0], centre[1], z)) + d * 120
            hit = cast(objs, o, -d)
            if hit: plaque(name, hit[0], hit[1], (math.cos(a), math.sin(a), 0), (ln, ht, .12), 'black', root, .04)
    for z, a0, a1, n in cfg['windows']['rim']:
        ring('rim windows', z, a0, a1, n, 1.4, .45, [saucer])
    for z, a0, a1, n in cfg['windows']['lower_hull']:
        ring('lower hull windows', Zs(z), a0, a1, n, 1.2, .4, [saucer])
    for side in (-1, 1):
        for (x0, x1, py) in cfg['windows']['dome']:   # the few dashes drawn on the bridge dome
            hit = cast([dome], (side * 40, Ys((x0 + x1) / 2), Zs(py)), (-side, 0, 0))
            if hit: plaque('bridge dome windows', hit[0], hit[1], (0, 1, 0), (L(x1 - x0), .45, .12), 'black', root, .04)
        for (x0, x1, py) in cfg['windows']['pylon']:
            y = Ys((x0 + x1) / 2); z = Zs(py)
            hit = cast([pylon, deck, saucer], (side * 40, y, z), (-side, 0, 0))
            if hit: plaque('pylon windows', hit[0], hit[1], (0, 1, 0), (max(L(x1 - x0), 1.0), .45, .12), 'black', root, .04)
        for quad in cfg['pylon_grilles']:          # dotted panels on the pylon, side px corners
            pts = [(Ys(a), Zs(b)) for a, b in quad]
            if side > 0: fin('pylon grille', pts, lambda y: thick(y) + .16, 'grey', root)   # slab through the tapered pylon, both faces

    # ---- registry on the saucer top (as drawn: an arc on the forward quarter) ----
    rg = cfg['saucer_registry']                    # radius m, first/last letter azimuth (deg, + toward port), cap m
    n = len(cfg['registry'])
    for i, ch in enumerate(cfg['registry']):
        if ch == ' ': continue
        phi = math.radians(rg['phi0'] + (rg['phi1'] - rg['phi0']) * i / (n - 1))
        p = Vector((rg['r'] * math.sin(phi), Yc - rg['r'] * math.cos(phi), 60))
        hit = cast([saucer], p, (0, 0, -1))
        if not hit: continue
        g = glyph_mesh(f'saucer registry {ch}', ch, rg['cap'], .12, 'black', root, width=rg.get('width'))
        nor = hit[1]; inward = Vector((-math.sin(phi), math.cos(phi), 0))
        up = (inward - inward.dot(nor) * nor).normalized(); rd = up.cross(nor)
        g.matrix_world = Matrix.Translation(hit[0] + nor * .03) @ Matrix((rd, up, nor)).transposed().to_4x4()

    bpy.context.view_layer.update()
    merge_repeats(root)
    size = kit.export_ship(cfg['id'])
    print('PRINTED L/B/H', cfg['printed'], 'MODEL', size, 'NACELLE', NAC_INFO.get('nacelle'))
    return size
