"""Ray Gun, Type I — PDF 106, TO 01:08:58.  Run: Blender -b -P model-source/blender/ray_gun.py
Printed: length overall 23.5 cm, maximum diameter 8.4 cm, 630 g.
Colours: translucent (diamond emitter tube), antimony SF02UC (collette), gray SF30UC (body housing), black SF32UC (triggers).
The main elevation (plate px 825-1311 x 333-1689, 57.74 px/cm) looks straight at the trigger panel with the emitter up;
the FRONT VIEW (looking down the emitter axis) is a circle with the panel as a bump at the top. So the item is a solid of
revolution about Y (front = -Y) with one raised elliptical trigger panel on the +Z side.
Profile: model-source/blender/profiles/ray-gun-plan.json (extract_profile.py 106 790,300,1350,1720 57.74 --step 1)."""
import sys, os, math, statistics
sys.path.insert(0, os.path.dirname(__file__))
import kit, bmesh, bpy

PPC = 57.74
O = (1067.5, 333)          # profile origin: mid-line x, first silhouette row (emitter tip) in plate px
L = 23.485                 # drawn length (printed 23.5)
Y0 = -L / 2                # tip at -Y
s_of = lambda py: (py - O[1]) / PPC
y_of = lambda py: Y0 + s_of(py)

def radius(prof, s, med=0):
    lo, hi = kit.sample(prof, s, med); return (hi - lo) / 2

def band_radius(prof, py0, py1, trim=3):
    """median drawn radius over the plate rows py0..py1 (trimmed of outline-thickness rows at each end)"""
    vals = [(hi - lo) / 2 for s, lo, hi in prof['rows'] if s_of(py0 + trim) <= s <= s_of(py1 - trim)]
    return statistics.median(vals)

def smoothed(vals, k):
    """two passes of a centred moving average (half-width k rows), window shrinking at the ends"""
    for _ in range(2):
        vals = [sum(vals[max(0, i - min(k, i, len(vals) - 1 - i)):i + min(k, i, len(vals) - 1 - i) + 1]) / (2 * min(k, i, len(vals) - 1 - i) + 1) for i in range(len(vals))]
    return vals

def revolve_rows(name, prof, py0, py1, material, med=2, step=1, smooth_k=0, close_front=True, close_back=True, parent=None):
    rows = [r for r in prof['rows'] if s_of(py0) <= r[0] <= s_of(py1)]
    rad = [radius(prof, r[0], med) for r in rows]
    if smooth_k: rad = smoothed(rad, smooth_k)
    pts = [(rad[i], Y0 + rows[i][0]) for i in list(range(0, len(rows) - 1, step)) + [len(rows) - 1]]
    if close_front: pts.insert(0, (0.0, pts[0][1]))
    if close_back: pts.append((0.0, pts[-1][1]))
    return kit.revolve(name, pts, material, 'Y', parent=parent)

def body_surface_z(prof, x, s):
    r = radius(prof, s, 4); return math.sqrt(max(r * r - x * x, 0.0))

def pad(name, prof, sc, a_len, a_wid, h, material, sink=0.18, rho_max=1.0, s_clip=None, nr=14, nt=72, parent=None):
    """A raised pad following the body surface on +Z: elliptical plan (centre s=sc, semi-axes a_len along the body, a_wid across),
    crowned h above the surface at its middle, falling to the surface at its rim. s_clip=(s0,s1) cuts the pad to a band."""
    bm = bmesh.new()
    def pt(rho, th, top):
        u, v = rho * math.cos(th), rho * math.sin(th)
        x, s = a_wid * u, sc + a_len * v
        if s_clip: s = min(max(s, s_clip[0]), s_clip[1])
        z0 = body_surface_z(prof, x, s)
        z = z0 + (h * (1 - min(rho, 1) ** 6) ** .5 if top else -sink)
        return (x, Y0 + s, z)
    top, bot = [], []
    for k in range(1, nr + 1):
        rho = rho_max * k / nr
        top.append([bm.verts.new(pt(rho, 2 * math.pi * j / nt, True)) for j in range(nt)])
        bot.append([bm.verts.new(pt(rho, 2 * math.pi * j / nt, False)) for j in range(nt)])
    ct = bm.verts.new(pt(0, 0, True)); cb = bm.verts.new(pt(0, 0, False))
    for rings, c in ((top, ct), (bot, cb)):
        for j in range(nt): bm.faces.new((c, rings[0][j], rings[0][(j + 1) % nt]))
        for k in range(nr - 1):
            for j in range(nt):
                bm.faces.new((rings[k][j], rings[k + 1][j], rings[k + 1][(j + 1) % nt], rings[k][(j + 1) % nt]))
    for j in range(nt):
        bm.faces.new((top[-1][j], bot[-1][j], bot[-1][(j + 1) % nt], top[-1][(j + 1) % nt]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), 50)

def band(name, s0, s1, halfw, ztop, zbot, material, parent=None, ns=24, nx=16):
    """closed surface patch between s0..s1, x within ±halfw(s), top ztop(x,s), bottom zbot(x,s)"""
    bm = bmesh.new(); T, B = [], []
    for i in range(ns + 1):
        s = s0 + (s1 - s0) * i / ns; w = halfw(s); rt, rb = [], []
        for j in range(nx + 1):
            x = -w + 2 * w * j / nx
            rt.append(bm.verts.new((x, Y0 + s, ztop(x, s)))); rb.append(bm.verts.new((x, Y0 + s, zbot(x, s))))
        T.append(rt); B.append(rb)
    for i in range(ns):
        for j in range(nx):
            bm.faces.new((T[i][j], T[i][j + 1], T[i + 1][j + 1], T[i + 1][j])); bm.faces.new((B[i][j], B[i + 1][j], B[i + 1][j + 1], B[i][j + 1]))
    for i in range(ns):
        bm.faces.new((T[i][0], T[i + 1][0], B[i + 1][0], B[i][0])); bm.faces.new((T[i][nx], B[i][nx], B[i + 1][nx], T[i + 1][nx]))
    for j in range(nx):
        bm.faces.new((T[0][j], B[0][j], B[0][j + 1], T[0][j + 1])); bm.faces.new((T[ns][j], T[ns][j + 1], B[ns][j + 1], B[ns][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), 35)

def build():
    prof = kit.load_profile('ray-gun-plan')
    # Diamond emitter tube: six coaxial steps; edges at plate rows 333 (tip) 410 488 564 641 716 790 (collette).
    edges = [334, 410, 488, 564, 641, 716, 791]
    tube = kit.group('Diamond emitter tube')
    for i in range(6):
        r = band_radius(prof, edges[i], edges[i + 1])
        kit.cyl(f'emitter tube step {i + 1}', r, (edges[i + 1] - edges[i]) / PPC, (0, (y_of(edges[i]) + y_of(edges[i + 1])) / 2, 0), 'topaz', 'Y', seg=72, parent=tube)
    # constant-bore core (dashed on the plate, x 1040-1095 = 0.95 cm) seen through the tube; black aperture at the tip (FRONT VIEW)
    kit.cyl('emitter bore', .475, (791 - 336) / PPC, (0, (y_of(336) + y_of(791)) / 2, 0), 'black', 'Y', parent=tube)
    kit.cyl('emitter aperture', .475, .03, (0, y_of(334) - .005, 0), 'black', 'Y', parent=tube)
    # Collette: stepped antimony cone (plate rows 791-872), revolved straight from the measured silhouette.
    revolve_rows('Collette', prof, 790.5, 874.5, 'antimony', med=1)
    # Body housing: gray egg/ogive (rows 872-1689), revolved from the silhouette.
    revolve_rows('Body housing', prof, 872, 1689, 'grey', med=2, step=2, smooth_k=6)
    # Trigger panel on +Z: ellipse y 930-1452, x 1013-1124 on the plan; stands 0.26 cm proud (FRONT VIEW bump 1050 vs circle 1065).
    sc, al, aw = s_of((930 + 1452) / 2), (1452 - 930) / 2 / PPC, (1124 - 1013) / 2 / PPC
    panel = kit.group('Triggers')
    pad('trigger panel', prof, sc, al, aw, .26, 'black', parent=panel)
    # Trigger pads (offensive forward, rows 990-1190; defensive aft, rows 1192-1392) set in the panel, divided by seams.
    crown = lambda x, s: body_surface_z(prof, x, s) + .26 * max(1 - min((x / aw) ** 2 + ((s - sc) / al) ** 2, 1) ** 3, 0) ** .5
    halfw = lambda s, m: max(aw * math.sqrt(max(1 - ((s - sc) / al) ** 2, 0)) - m, .05)
    for nm, a, b, mtl, lift, m in (('offensive trigger', 993, 1188, 'black', .02, .06), ('defensive trigger', 1195, 1389, 'black', .02, .06),
                                   ('trigger seam', 987, 993, 'dark', .012, .03), ('trigger seam', 1188, 1195, 'dark', .012, .03), ('trigger seam', 1389, 1395, 'dark', .012, .03)):
        band(nm, s_of(a), s_of(b), lambda s, m=m: halfw(s, m), lambda x, s, lift=lift: crown(x, s) + lift, lambda x, s: body_surface_z(prof, x, s) - .1, mtl, panel)

if __name__ == '__main__':
    kit.reset(); build(); kit.export('ray-gun')
