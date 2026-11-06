"""Surgical Scalpels SFAF/SG-MK10-000, -00, -0 — PDF 132, TO 02:11:14.  Run: Blender -b -P model-source/blender/surgical_scalpels.py
No dimensions are printed; everything is measured at the sheet's 0-4 cm bar (67.95 px/cm on the 1400 px plate).
Housing: rodinium, colour antimony SF02UC (all three). Upright: Z up, prime-focus cone on top (base down on the ribbed body),
trigger / intensity scale / range scale lock facing the front (-Y). Three models side by side along X: 000 (−X), 00, 0 (+X).
Turned outline of each: revolved from its elevation silhouette (profiles/surgical-scalpels-<n>-elev.json).
Front details: x / y read on the elevation, x converted to an angle on the grip (asin of offset / drawn radius)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bmesh, bpy

PPC = 67.95
# per model: axis x, top / bottom rows, scale ring, grip and skirt rows, trigger oval, slider strip, lock box (px on PDF 132)
MODELS = {
    '000': dict(axis=1072.5, top=311, ring=(486, 500), grip=(500, 655), skirt=(655, 692.5), trig=(968, 1033, 503, 578),
                slide=(1035, 1105, 500, 583), lock=(1037, 1107, 583, 655), ticks=((950, 985), (1083, 1190)), maxmark=970, tenmark=1150, flat=0),
    '00': dict(axis=1076.5, top=776, ring=(978, 990), grip=(990, 1145), skirt=(1145, 1172), trig=(972, 1036, 993, 1063),
               slide=(1040, 1108, 990, 1075), lock=(1042, 1112, 1075, 1145), ticks=((962, 995), (1090, 1190)), maxmark=980, tenmark=1155, flat=1),
    '0': dict(axis=1081.0, top=1261, ring=(1545, 1558), grip=(1558, 1717), skirt=(1717, 1745), trig=(973, 1035, 1563, 1635),
              slide=(1043, 1112, 1558, 1650), lock=(1043, 1112, 1650, 1717), ticks=((978, 1005), (1095, 1185)), maxmark=992, tenmark=1158, flat=1),
}
SPACING = 4.4
# The end views draw every grip 2-3 % smaller in diameter than the elevations do (whose knurled end rings are drawn in heavy
# line); the grip radius is taken 1.5 % inside the elevation outline to split that difference.
GRIP_K = 0.985

def curved_pad(name, R, t, a0, a1, z0, z1, material, ellipse=False, parent=None, n=40):
    """A pad lying on the cylinder of radius R (axis Z), proud by t; spans angles a0..a1 (rad, from +X) and heights z0..z1."""
    ac, zc, ha, hz = (a0 + a1) / 2, (z0 + z1) / 2, (a1 - a0) / 2, (z1 - z0) / 2
    if ellipse:
        outline = [(ac + ha * math.cos(2 * math.pi * i / n), zc + hz * math.sin(2 * math.pi * i / n)) for i in range(n)]
    else:
        k = 10; outline = ([(a0 + (a1 - a0) * i / k, z0) for i in range(k)] + [(a1, z0 + (z1 - z0) * i / 4) for i in range(4)] +
                           [(a1 - (a1 - a0) * i / k, z1) for i in range(k)] + [(a0, z1 - (z1 - z0) * i / 4) for i in range(4)])
    bm = bmesh.new()
    P = lambda a, zz, r: bm.verts.new((r * math.cos(a), r * math.sin(a), zz))
    m, K = len(outline), 6
    ring = lambda k, r: [P(ac + (a - ac) * k / K, zc + (zz - zc) * k / K, r) for a, zz in outline]
    for r, flip in ((R + t, False), (R - .02, True)):        # concentric rings on the curved face, so it follows the cylinder
        c = P(ac, zc, r); rs = [ring(k, r) for k in range(1, K + 1)]
        for i in range(m):
            j = (i + 1) % m
            f = (c, rs[0][i], rs[0][j]); bm.faces.new(f[::-1] if flip else f)
            for k in range(K - 1):
                f = (rs[k][i], rs[k + 1][i], rs[k + 1][j], rs[k][j]); bm.faces.new(f[::-1] if flip else f)
        if not flip: outer = rs[-1]
        else: inner = rs[-1]
    for i in range(m):
        j = (i + 1) % m; bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), 20 if not ellipse else 35)

def rdp(pts, tol):
    """Ramer-Douglas-Peucker: drop profile rows that lie within tol (cm) of the straight line between kept rows."""
    if len(pts) < 3: return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]; L = math.hypot(x1 - x0, y1 - y0) or 1e-9
    d = [abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0)) / L for x, y in pts[1:-1]]
    i = max(range(len(d)), key=d.__getitem__)
    if d[i] <= tol: return [pts[0], pts[-1]]
    return rdp(pts[:i + 2], tol)[:-1] + rdp(pts[i + 1:], tol)

def build_one(key, parent=None, x0=0.0):
    p = MODELS[key]
    prof = kit.load_profile(f'surgical-scalpels-{key}-elev')
    bot = p['top'] + prof['length'] * PPC                       # silhouette foot row
    z = lambda py: (bot - py) / PPC
    g = kit.group(f'Scalpel SFAF/SG-MK10-{key}', parent); g.location = (x0, 0, 0)
    # housing outline: revolve the measured elevation (radius = half the drawn width each row), split at the drawn joints
    def piece(name, y0, y1, mat='antimony', k=1.0):
        rad = lambda py: (lambda lo_hi: max((lo_hi[1] - lo_hi[0]) / 2, 0.0))(kit.sample(prof, (py - p['top']) / PPC, 1))
        ys = [y0] + [p['top'] + r[0] * PPC for r in prof['rows'] if y0 < p['top'] + r[0] * PPC < y1] + [y1]
        pts = [(0.0, z(y0))] + rdp([(k * rad(py), z(py)) for py in ys], .003) + [(0.0, z(y1))]
        return kit.revolve(name, pts[::-1], mat, axis='Z', parent=g)
    piece('prime focus cone' if not p['flat'] else 'prime focus cone (cutting tip flat)', p['top'], p['ring'][0])
    piece('intensity scale ring', p['ring'][0], p['ring'][1])
    piece("surgeon's grip", p['ring'][1], p['skirt'][0], k=GRIP_K)
    piece('body', p['skirt'][0], bot)
    RG = lambda py: GRIP_K * (lambda lo_hi: (lo_hi[1] - lo_hi[0]) / 2)(kit.sample(prof, (py - p['top']) / PPC, 2))
    ang = lambda px, R: -math.pi / 2 + math.asin(max(-.99, min(.99, (px - p['axis']) / PPC / R)))  # front = -Y; image right = +X
    # grip ribs: fine horizontal rings every ~7 px between the knurled end rings
    g0, g1 = p['grip']; Rg = RG((g0 + g1) / 2)
    n = int((g1 - g0 - 14) / 7)
    for i in range(n + 1):
        py = g0 + 7 + i * (g1 - g0 - 14) / n
        kit.torus('grip rib', RG(py) - .004, .012, (0, 0, z(py)), 'antimony', 'Z', parent=g, seg=48)
    # cutting tip (flat top of 00 / 0) — the small circle of the end view
    if p['flat']:
        rt = (lambda lo_hi: (lo_hi[1] - lo_hi[0]) / 2)(kit.sample(prof, 0.02, 0))
        kit.torus('cutting tip edge', rt - .015, .008, (0, 0, z(p['top']) - .004), 'dark', 'Z', parent=g)
    # intensity scale: graduations on the ring, index "0" at the front, max reading at left, "10" at right
    r0, r1 = p['ring']; Rr = RG((r0 + r1) / 2)
    for lo, hi in p['ticks']:
        k = int((hi - lo) / 8)
        for i in range(k + 1):
            px = lo + i * (hi - lo) / max(k, 1); a = ang(px, Rr)
            kit.box('scale graduation', (.012, .02, (r1 - r0) / PPC * .45), (Rr * math.cos(a), Rr * math.sin(a), z(r1) + (r1 - r0) / PPC * .25),
                    'black', rot=(0, 0, a + math.pi / 2), parent=g)
    for px in (p['maxmark'], p['tenmark']):
        a = ang(px, Rr); kit.box('scale figure', (.18, .02, (r1 - r0) / PPC * .5), (Rr * math.cos(a), Rr * math.sin(a), z((r0 + r1) / 2) + .02), 'black', rot=(0, 0, a + math.pi / 2), parent=g)
    a = ang(p['axis'], Rr); kit.torus('scale index 0', .04, .008, ((Rr + .004) * math.cos(a), (Rr + .004) * math.sin(a), z((r0 + r1) / 2) + .02), 'black', 'Y', parent=g)
    # trigger: oval pad at the left of the grip front
    x0t, x1t, y0t, y1t = p['trig']
    curved_pad('trigger', Rg, .025, ang(x0t, Rg), ang(x1t, Rg), z(y1t), z(y0t), 'antimony', ellipse=True, parent=g)
    curved_pad('trigger outline', Rg, .012, ang(x0t - 2, Rg), ang(x1t + 2, Rg), z(y1t + 2), z(y0t - 2), 'black', ellipse=True, parent=g)
    # range scale slider strip (vertically ribbed) with the up-pointing index triangle under the scale's 0
    sx0, sx1, sy0, sy1 = p['slide']
    curved_pad('range scale slider', Rg, .02, ang(sx0, Rg), ang(sx1, Rg), z(sy1), z(sy0), 'antimony', parent=g)
    for i in range(1, 9):
        px = sx0 + i * (sx1 - sx0) / 9; a = ang(px, Rg)
        kit.box('slider rib', (.02, .03, (sy1 - sy0) / PPC * .96), ((Rg + .032) * math.cos(a), (Rg + .032) * math.sin(a), z((sy0 + sy1) / 2)), 'antimony', rot=(0, 0, a + math.pi / 2), parent=g)
    a = ang((sx0 + sx1) / 2, Rg)
    tri = lambda name, zc, up: kit.extrude(name, [(-.1, -.11 * up), (.1, -.11 * up), (0, .11 * up)], .02, 'black', plane='XZ',
                                           loc=((Rg + .035) * math.cos(a), (Rg + .035) * math.sin(a), zc), rot=(0, 0, a + math.pi / 2), parent=g)
    tri('index triangle (up)', z(sy0 + 14), 1)
    # range scale lock: square block with the down-pointing triangle
    lx0, lx1, ly0, ly1 = p['lock']
    curved_pad('range scale lock', Rg, .04, ang(lx0, Rg), ang(lx1, Rg), z(ly1), z(ly0), 'antimony', parent=g)
    curved_pad('lock outline', Rg, .03, ang(lx0 - 2, Rg), ang(lx1 + 2, Rg), z(ly1 + 1), z(ly0 - 1), 'black', parent=g)
    tri('lock triangle (down)', z((ly0 + ly1) / 2 - 2), -1)
    return g

def build(parent=None, name='Surgical Scalpels'):
    root = kit.group(name, parent)
    for i, k in enumerate(('000', '00', '0')):
        build_one(k, root, (i - 1) * SPACING)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('surgical-scalpels')
    if '--units' in sys.argv:          # each scalpel alone, for scoring against its own drawing
        out = sys.argv[sys.argv.index('--units') + 1]
        for k in MODELS:
            kit.reset(); kit._mats.clear(); build_one(k); kit.export(f'surgical-scalpels-{k}', out)
