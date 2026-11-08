"""Ptolemy class transport/tug, NCC-3801 — PDF 81, TO 01:04:16.  Run: Blender -b -P model-source/blender/ptolemy.py
Printed: L.O.A. 222 m, B.O.A. 127.1 m, H.O.A. 66 m; primary hull dia. 127.1 m; prop. unit L.O.A. 153.6 m, dia. 17.3 m.
Shown without a cargo container.

Plate at 300 dpi, 6.01 px/m from the 0-50 m bar (300.5 px).  Outlines measured by ptolemy_measure.py
(profiles/ptolemy-saucer.json, profiles/ptolemy-nacelle.json); details placed from plate pixels via the lambdas below.
Frame: metres, Z up, bow = -Y at y = -111, starboard = -X.
  plan  (top of plate): bow image-left, image-up = starboard;  saucer centre at (996.3, 876.6) px, r = 382-385 px.
  side  (middle):       seen from +X (port), bow left;   saucer axis at side px 1000.
  front (bottom):       seen from -Y, image-right = +X;  ship centre-line at px 994.
Callouts on the plate: bridge, sensor array, primary hull, phaser P/S, impulse power, space/warp propulsion 2 units,
tow pad, main sensor.  Windows are the dashes as drawn (projected onto the hull from the view they are drawn in)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
from mathutils import Vector, Matrix

PPM = 6.01
PCX, PCY = 996.3, 876.6              # plan saucer centre (px)
SCX = 1000.0                          # side-view saucer axis (px)
R = 382 / PPM                         # saucer radius (side bow rim 618 px → 63.56 m; plan 385 px incl. outline ink)
YC = -111.0 + R                       # saucer centre y, bow at -111
XN = 45.7                             # nacelle axes ±X (plan 599/1149 px, front 720/1272 px)

yP = lambda px: YC + (px - PCX) / PPM          # plan px → y
xP = lambda py: (py - PCY) / PPM               # plan py → x (image-up = starboard = -X)
yS = lambda px: YC + (px - 997.0) / PPM        # side px → y (side saucer sits 3.7 px aft of plan's; split the difference)
zS = lambda py: (1600.0 - py) / PPM            # side py → z (z = 0 at the rim mid-plane)
xF = lambda px: (px - 994.0) / PPM             # front px → x
zF = lambda py: (2227.5 - py) / PPM            # front py → z (rim band 2206-2250 ≡ side 1578-1623)

HULL, DARK, LINE = 'white', 'black', 'grey'
kit.reset()

# ------------------------------------------------------------------ primary hull (revolved side profile about the plan centre)
sp = json.load(open(os.path.join(kit.PROFILES, 'ptolemy-saucer.json')))['rows']
rows = [(r / PPM, zS(t), zS(b)) for r, t, b in sp]
def interp(tab, r, k):
    if r <= tab[0][0]: return tab[0][k]
    for a, b in zip(tab, tab[1:]):
        if a[0] <= r <= b[0]:
            t = (r - a[0]) / max(b[0] - a[0], 1e-9); return a[k] + (b[k] - a[k]) * t
    return tab[-1][k]
z_top = lambda r: interp(rows, r, 1)
z_bot = lambda r: interp(rows, r, 2)
R_DOME = 104 / PPM                    # upper dome meets the saucer's upper cone at side px 896 (r 104 px)

def rs(a, b, step):
    n = max(1, int(round((b - a) / step))); return [a + (b - a) * i / n for i in range(n + 1)]
# sample: fine on the dome flank, rim and lower dome; coarse on the straight cone
r_top = sorted(set([round(x, 4) for x in rs(R_DOME - .3, 30.0, .45) + rs(30.0, R - 1.2, 1.2) + rs(R - 1.2, R, .15)]))
r_bot = sorted(set([round(x, 4) for x in rs(0, 7.0, 3.5) + rs(7.0, 26.5, .45) + rs(26.5, R - 4.0, 2.0) + rs(R - 4.0, R, .2)]))
# under the dome the upper cone carries on inward (slope of the measured cone 105-285 px), so the narrower-than-round dome
# (see below) always sits on hull
CONE = (z_top(17.5) - z_top(47.4)) / (47.4 - 17.5)
hull_pts = [(0.0, z_top(R_DOME) + CONE * R_DOME - .3), (R_DOME * .5, z_top(R_DOME) + CONE * R_DOME * .5 - .3), (R_DOME - .3, z_top(R_DOME) + CONE * .3 - .3)]
hull_pts += [(r, z_top(r)) for r in r_top if r >= R_DOME - .3]
hull_pts += [(r, z_bot(r)) for r in reversed(r_bot)]
hull = kit.revolve('primary hull', hull_pts, HULL, axis='Z', seg=160, loc=(0, YC, 0))
kit.smooth(hull, 32)

# bridge dome (upper dome with the bridge cap on top) — same measured profile, r < 104 px
r_d = [0.0] + [x / PPM for x in range(2, 104, 2)] + [R_DOME + .4]
dome_pts = [(r, z_top(r)) for r in r_d] + [(R_DOME + .4, z_top(R_DOME) - 1.2), (0.0, z_top(R_DOME) - 1.2)]
dome = kit.revolve('bridge dome', dome_pts, HULL, axis='Z', seg=128, loc=(0, YC, 0))
# The dome is not round: the side view's aft half is the forward profile stretched 1.3x (aft foot at 1130-1140 px against
# 896 px forward), the plan outline is longer fore-and-aft than across, and the front view draws it 0.84x the side width.
# Stretch the revolved (forward-profile) dome by an elliptical factor: 1.0 forward, 1.3 aft, 0.84 across.
DA, DF, DB = 1.3, 1.0, 0.84
for v in dome.data.vertices:
    dx, dy = v.co.x, v.co.y - YC; r = math.hypot(dx, dy)
    if r < 1e-6: continue
    c, s_ = -dy / r, dx / r                                       # c > 0 forward
    a_ = DF if c > 0 else DA
    k = a_ * DB / math.sqrt((DB * c) ** 2 + (a_ * s_) ** 2)
    v.co.x, v.co.y = dx * k, YC + dy * k
kit.smooth(dome, 34)
# bridge: flat cap ring line on the dome crown (plan circle r 31 px) is drawn as a panel line below

# sensor array: small dome aft of the bridge (plan circle at 1028 px, r 10 px; side top 1477 px)
sa_y, sa_r = yP(1028), 10 / PPM
sa_base = z_top(abs(1028 - PCX) / PPM) - .8
kit.cyl('sensor array base', sa_r, (zS(1486) - sa_base), (0, sa_y, (sa_base + zS(1486)) / 2), 'bluegray', axis='Z', seg=40)
kit.sphere('sensor array', sa_r, (0, sa_y, zS(1486)), 'bluegray', scale=(1, 1, (zS(1479) - zS(1486)) / sa_r))   # top at the ink centre of 1477

# ------------------------------------------------------------------ aft deck, keel, impulse power
def side_poly(pts):
    return [(yS(px), zS(py)) for px, py in pts]
deck_w = (964 - 789) / PPM            # plan rectangle 789..964 px
kit.extrude('aft deck', side_poly([(1180, 1562), (1397, 1562), (1397, 1606), (1180, 1606)]), deck_w, HULL, plane='YZ', bev=.5)
# keel: under the deck, 9.4 m wide over its forward part (front view allows <= 9.8 m), and aft the sloping strut that
# runs from the deck's aft edge (1380 px, 1606 px) down to the tow pad (1494 px, 1706 px).  The plan draws that strut's
# ridge as the wedge 1375-1505 px, 857-895 px wide at its root, pointed at the pad: so the strut tapers in plan.
def keel_sec(px):
    if px <= 1272: zb = zS(1627 + (1706 - 1627) * (max(px, 1140) - 1140) / (1272 - 1140))
    else: zb = zS(1706)
    zt = zS(1606) if px <= 1372 else (zS(1606 + 11 * (px - 1372) / 13) if px <= 1385 else zS(1617 + 81 * (px - 1385) / 95))   # slant 1390:1622 .. 1480:1698
    if px <= 1372: hw = 4.7
    elif px <= 1392: hw = 4.7 + (3.15 - 4.7) * (px - 1372) / 20
    else: hw = 3.15 + (.35 - 3.15) * (px - 1392) / (1490 - 1392)
    return (yS(px), -hw, hw, zb, zt)
ks = [keel_sec(px) for px in [1132, 1140, 1160, 1185, 1210, 1235, 1260, 1272, 1300, 1340, 1372, 1385, 1392, 1410, 1430, 1450, 1470, 1484, 1492]]
kit.loft('keel', ks, HULL, p=8.0, seg=48)

# impulse power: pod at the deck's aft face, ending there (side 1372-1403 px, 1574-1603 px; plan 857-895 px wide).
ip = []
for px, hw, z0, z1 in [(1366, 3.0, zS(1604), zS(1576)), (1376, 3.2, zS(1605), zS(1574)), (1398, 3.2, zS(1604), zS(1574)),
                       (1402, 3.05, zS(1602), zS(1576)), (1403.2, 2.7, zS(1599), zS(1579))]:
    ip.append((yS(px), -hw, hw, z0, z1))
kit.loft('impulse power', ip, HULL, p=3.0, seg=48)
kit.box('impulse exhaust', (5.0, .3, 3.0), (0, yS(1403.2) - .05, zS(1589)), 'red', bev=.1)

# ------------------------------------------------------------------ nacelles (space/warp propulsion, 2 units)
# Each unit is a clean surface of revolution: body radius from the printed 17.3 m diameter; nose, raised sleeve and aft cap
# stations from the side/plan views (ptolemy-nacelle.json is kept as the measured reference).
RN = 17.3 / 2
NZ = zS(1825.0)                                          # axis: side top 1773 / bottom 1876 at the body
P_TIP, P_NOSE, P_T0, P_SL0, P_SL1, P_CAP1, P_END = 1020, 1062, 1300, 1692, 1866, 1926, 1952
# Body: full 17.3 m from the nose to 1300 px, then a straight taper to 15.7 m at the sleeve (side: bottom line rises
# 1876 → 1869 px while the top drops 1773 → 1776 px; plan: the outer edge stays put while the inner edge moves out).
# So the tapered part is an oblique cone: its axis moves outboard by the radius lost and up by 0.375 of it (all lines straight).
TAPER, TZ = .8, .375                                    # radius lost by the sleeve; axis rise per metre lost (top drops 3 px)
def shift(px): return TAPER * max(0.0, (px - P_T0) / (P_SL0 - P_T0))
def body_r(px):
    if px <= P_NOSE: d = (P_NOSE - px) / (P_NOSE - P_TIP); return RN * math.sqrt(max(1 - d * d, 0))
    return RN - shift(px)
nose = [P_TIP + (P_NOSE - P_TIP) * (1 - math.cos(math.pi / 2 * i / 14)) for i in range(15)]
body_prof = [(body_r(px), yS(px)) for px in nose] + [(RN, yS(P_T0))] + \
            [(body_r(px), yS(px)) for px in (1400, 1500, 1600, P_SL0, 1780, P_SL1 + 1)] + [(0.0, yS(P_SL1 + 1.5))]
# Raised sleeve 1692-1866 px: plan 653-542 px (outer edge at XN + 10.0 m, inner XN - 8.5 m), side top 1766 px, bottom on the
# body line (1869 px) → a tube r 9.0 m whose axis sits 0.65 m outboard and level with the body's own top + 1.33 m − r.
R_SL, SL_DX, SL_XS = (1870.5 - 1766) / 2 / PPM, .75, 1.075     # tube 1766-1870.5 px tall, 1.075x wider across (plan 111 px)
SL_Z = zS(1766) - R_SL
# Aft cap 1866-1952 px: the side view cuts its underside away (bottom 1869 → 1795 px over 1900-1943 px) and the plan rounds
# it off (86-88 px wide about the outboard axis, closing at 1955 px) — a separate loft from those measured outlines,
# top held level at 1778 px.
R_CAP, CAP_DX = 7.3, .7
# measured side outline: top level 1778 px to ~1930 px, underside rising from 1869 px at ~1895 px to the end at 1943-1945 px
# (end centre ~1795 px); plan: 86-88 px wide to 1925 px, closing at 1952 px.  Quarter-ellipse closures reproduce those
# curves smoothly (the raw columns step several px at the very end).
def qe(px, p0, p1):                                     # 0 before p0, rising to 1 at p1 along a quarter ellipse
    d = min(max((px - p0) / (p1 - p0), 0.0), 1.0); return 1 - math.sqrt(1 - d * d)
cap_secs = []
for i in range(41):
    px = (P_SL1 - 2) + (P_END - (P_SL1 - 2)) * math.sin(math.pi / 2 * i / 40)
    top = 1778 + (1795 - 1778) * qe(px, 1930, P_END)
    bot = 1869.5 - (1869.5 - 1795) * qe(px, 1895, P_END)
    hw = R_CAP * math.sqrt(max(1 - qe(px, 1925, P_END) ** 2 * 0 - max((px - 1925) / (P_END - 1925), 0) ** 2, 0)) if px > 1925 else R_CAP
    cap_secs.append((yS(px), max(hw, .02), zS(bot), zS(top)))
sl_prof = [(R_SL - 1.6, yS(P_SL0 - .5)), (R_SL - 1.25, yS(P_SL0)), (R_SL, yS(P_SL0 + 6)), (R_SL, yS(P_SL1 - 6)), (R_SL - .4, yS(P_SL1 - 1)),
           (R_CAP + .2, yS(P_SL1)), (R_CAP - .5, yS(P_SL1 + .3))]
def nac_hw(y):
    """(outboard half-width, z bottom, z top) of the outer surface at y, for wrapping the markings (axis at XN, NZ)."""
    px = 997.0 + (y - YC) * PPM
    if P_SL0 + 6 <= px <= P_SL1 - 6: return [R_SL * SL_XS + SL_DX, SL_Z - R_SL, SL_Z + R_SL]
    if px > P_SL1: return [R_CAP + CAP_DX, NZ + CAP_DX - R_CAP, NZ + CAP_DX + R_CAP]
    r, sh = body_r(px), shift(px); return [r + sh, NZ + TZ * sh - r, NZ + TZ * sh + r]
for side, nm in ((1, 'port'), (-1, 'starboard')):
    cx = side * XN
    o = kit.revolve(f'space/warp propulsion unit ({nm})', body_prof, HULL, axis='Y', seg=64, loc=(cx, 0, NZ))
    for v in o.data.vertices:
        sh = shift(997.0 + (v.co.y - YC) * PPM); v.co.x += side * sh; v.co.z += TZ * sh
    o = kit.revolve(f'warp unit raised sleeve ({nm})', sl_prof, HULL, axis='Y', seg=64, loc=(0, 0, SL_Z))
    for v in o.data.vertices: v.co.x = cx + side * SL_DX + v.co.x * SL_XS
    cxc = cx + side * CAP_DX
    kit.loft(f'warp unit aft cap ({nm})', [(y, cxc - hw, cxc + hw, z0, z1) for y, hw, z0, z1 in cap_secs], HULL, p=2.0, seg=64)
    # forward collar pads (front view: knobs at the lower sides and a pad below; side view: below to 1888 px over 1088-1160 px)
    y0, y1 = yS(1088), yS(1160)
    # drawn to 1888 px (2.5 m below the hull); held to 0.35 m proud so H.O.A. stays the printed 66 m (top: sensor array)
    kit.box(f'collar keel pad ({nm})', (6.0, y1 - y0, 3.0), (cx, (y0 + y1) / 2, NZ - RN - .35 + 1.5), HULL, bev=.9)
    for s2 in (-1, 1):
        a = math.radians(-38); rr = 8.6
        kit.box(f'collar knob ({nm}, {"outer" if s2 == side else "inner"})', (3.4, y1 - y0, 4.2),
                (cx + s2 * rr * math.cos(a), (y0 + y1) / 2, NZ + rr * math.sin(a)), HULL, rot=(0, -s2 * a, 0), bev=.7)

# pylons: front view straight struts from the saucer underside (x ±21.8 m at 2250 px) to the nacelle axes,
# chord 1245-1312 px in the side view
def strut(name, A, B, chord, thick, mat, n=10):
    A, B = Vector(A), Vector(B); u = (B - A); L = u.length; u.normalize()
    secs = [(L * i / n, -thick / 2, thick / 2, -chord / 2, chord / 2) for i in range(n + 1)]
    o = kit.loft(name, secs, mat, p=3.2, seg=40)
    Z = Vector((0, 1, 0)); X = u.cross(Z)
    o.matrix_world = Matrix.Translation(A) @ Matrix((X, u, Z)).transposed().to_4x4()
    return o
py_c, chord = yS((1245 + 1312) / 2), (1312 - 1245) / PPM
for side, nm in ((1, 'port'), (-1, 'starboard')):
    A0 = Vector((side * 21.8, py_c, zF(2250)))
    B = Vector((side * XN, py_c, NZ)); u = (B - A0).normalized()
    strut(f'pylon ({nm})', A0 - u * 2.2, B, chord, 3.5, HULL)

# ------------------------------------------------------------------ tow pad (side 1225-1532 px, plan 789-964 px wide;
# the front view draws it as a shallow arch: crown 1700 px, tips 1739 px)
def tow_pad():
    hw = deck_w / 2; t = 1.8; sag = (zS(1700) - zS(1739)) - t
    y0, y1 = yS(1225), YC + (1538 - 997) / PPM
    bm = bmesh.new(); N = 28; ring = []
    for i in range(N + 1):
        x = -hw + 2 * hw * i / N; zc = zS(1700) - t / 2 - sag * (x / hw) ** 2
        ring.append((x, zc + t / 2, zc - t / 2))
    top0 = [bm.verts.new((x, y0, zt)) for x, zt, zb in ring]; top1 = [bm.verts.new((x, y1, zt)) for x, zt, zb in ring]
    bot0 = [bm.verts.new((x, y0, zb)) for x, zt, zb in ring]; bot1 = [bm.verts.new((x, y1, zb)) for x, zt, zb in ring]
    for i in range(N):
        bm.faces.new((top0[i], top0[i + 1], top1[i + 1], top1[i])); bm.faces.new((bot0[i], bot1[i], bot1[i + 1], bot0[i + 1]))
        bm.faces.new((top0[i], bot0[i], bot0[i + 1], top0[i + 1])); bm.faces.new((top1[i], top1[i + 1], bot1[i + 1], bot1[i]))
    bm.faces.new((top0[0], top1[0], bot1[0], bot0[0])); bm.faces.new((top0[N], bot0[N], bot1[N], top1[N]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('tow pad'); bm.to_mesh(me); bm.free()
    o = kit._obj('tow pad', me, HULL); kit.bevel(o, .3, 2, 40); return kit.smooth(o, 40)
tow_pad()

# ------------------------------------------------------------------ main sensor (side: strut 980-1005 px from the lower dome,
# pivot (993, 1748), dish rim at 950 px spanning 1702-1795 px, feed to 918 px; front: dish circle 944-1045 px, fork posts)
zp = zS(1748); yp = yS(993)
for s2 in (-1, 1):
    top = z_bot(4.0 / 1) + 1.0
    kit.box(f'main sensor fork ({"port" if s2 > 0 else "starboard"})', (1.9, 3.6, top - zp), (s2 * 3.8, yS(992), (top + zp) / 2), LINE, bev=.3)
kit.cyl('main sensor pivot', 1.05, 9.6, (0, yp, zp), LINE, axis='X', seg=32)
yr = yS(950); DR = 7.9
prof = [(0.0, yr + 2.3)] + [(DR * i / 10, yr + 2.3 * (1 - (i / 10) ** 2)) for i in range(1, 11)]
prof += [(DR + .25, yr + .15), (DR * .98, yr + .7)] + [(DR * (1 - i / 10), yr + .7 + 5.0 * (i / 10) ** 1.3) for i in range(1, 11)]
dish = kit.revolve('main sensor', prof, HULL, axis='Y', seg=72, loc=(0, 0, zp))
kit.smooth(dish, 45)
kit.cyl('main sensor boom', .8, yp - (yr + 5.4), (0, (yp + yr + 5.4) / 2, zp), LINE, axis='Y', seg=24)
kit.cyl('main sensor feed', .42, (yr + 2.4) - yS(918), (0, (yr + 2.4 + yS(918)) / 2, zp), DARK, axis='Y', seg=20)
kit.sphere('main sensor feed horn', .75, (0, yS(918), zp), DARK)

# ------------------------------------------------------------------ surface details by projection from the drawn view
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def hit(origin, d):
    ok, loc, n, *_ = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(d))
    return (loc, n) if ok else (None, None)
def side_world(px, py, s=1): return Vector((s * 400, yS(px), zS(py)))
quads = {}                            # material → list of (centre, tangent, normal, length, height, depth)
def add_plate(mat, loc, n, t, length, height, depth=.26, lift=-.02):   # proud by ~0.1 m
    t = (t - n * t.dot(n)).normalized(); quads.setdefault(mat, []).append((loc + n * lift, t, n, length, height, depth))
def dash_side(x0, x1, py, h=.95, mat=DARK):
    for s in (1, -1):
        loc, n = hit(side_world((x0 + x1) / 2, py, s), (-s, 0, 0))
        if loc is not None: add_plate(mat, loc, n, Vector((0, 1, 0)), (x1 - x0) / PPM, h)
def dash_front(x0, x1, py, h=.95, mat=DARK):
    loc, n = hit((xF((x0 + x1) / 2), -400, zF(py)), (0, 1, 0))
    if loc is not None: add_plate(mat, loc, n, Vector((1, 0, 0)), (x1 - x0) / PPM, h)
def plate_plan(p0, p1, h, mat=DARK, depth=.3, lift=-.02):
    a = Vector((xP(p0[1]), yP(p0[0]), 0)); b = Vector((xP(p1[1]), yP(p1[0]), 0)); c = (a + b) / 2
    loc, n = hit((c.x, c.y, 300), (0, 0, -1))
    if loc is not None: add_plate(mat, loc, n, (b - a).normalized(), (b - a).length, h, depth, lift)

# windows drawn in the side view (seen from port; mirrored to starboard)
for x0, x1, py in [(967, 980, 1525), (983, 994, 1525), (1004, 1015, 1532),               # bridge dome
                   (694, 706, 1595),                                                         # rim
                   (1242, 1260, 1594), (1263, 1276, 1594), (1280, 1292, 1594),               # aft deck
                   (904, 916, 1636), (917, 924, 1636)] + \
                  [(a, b, 1644) for a, b in [(936, 941), (945, 950), (956, 962), (966, 977), (983, 994), (998, 1008), (1012, 1022), (1028, 1034), (1040, 1046), (1050, 1056)]] + \
                  [(a, b, 1655) for a, b in [(952, 956), (962, 968), (973, 983), (988, 1001), (1004, 1012), (1018, 1024), (1027, 1034)]] + \
                  [(1208, 1232, 1636), (1283, 1294, 1636), (1350, 1362, 1636), (1328, 1338, 1653), (1368, 1378, 1654),   # keel, pylon
                   (1283, 1295, 1669), (1332, 1342, 1678), (1344, 1355, 1678), (1376, 1387, 1678), (1390, 1399, 1678), (1282, 1296, 1757)]:
    dash_side(x0, x1, py)
# windows drawn in the front view (as drawn: five to port of the bow on the rim, one to starboard)
for x0, x1, py in [(649, 660, 2223), (699, 714, 2223), (718, 730, 2223), (733, 746, 2223), (749, 761, 2223), (1295, 1307, 2225)] + \
                  [(a, b, 2272) for a, b in [(937, 942), (944, 952), (956, 965), (968, 980), (984, 1000), (1002, 1014), (1015, 1025), (1030, 1039), (1045, 1051)]] + \
                  [(1017, 1026, 2282)]:
    dash_front(x0, x1, py)
# windows drawn on the bridge dome in plan
for p0, p1 in [((971, 823), (984, 814)), ((988, 818), (1001, 811)), ((1002, 812), (1018, 805)),
               ((970, 925), (982, 934)), ((987, 931), (999, 938)), ((1005, 935), (1018, 942))]:
    plate_plan(p0, p1, .7, DARK, .6, -.2)          # on the curved dome flank: seated deep so no corner lifts off
# plan details: sensor hatch aft of the bridge, deck hatches, small fittings round the saucer
plate_plan((1063, 876), (1098, 876), (890 - 862) / PPM, LINE, .9, -.38)      # drawn as an outline: a flush grey panel
for py0, py1 in ((812, 850), (900, 948)):
    plate_plan((1312, (py0 + py1) / 2), (1356, (py0 + py1) / 2), (py1 - py0) / PPM, LINE, .25)
for px, py, s in [(1306, 803, 1.6), (1306, 947, 1.6), (1317, 690, 1.5), (1317, 1060, 1.5)]:
    plate_plan((px - s * PPM / 2, py), (px + s * PPM / 2, py), s, 'dark')
for px, py in [(1233, 663), (1233, 1088)]:         # diamonds
    a = Vector((xP(py), yP(px), 0)); loc, n = hit((a.x, a.y, 300), (0, 0, -1))
    add_plate('dark', loc, n, Vector((1, 1, 0)).normalized(), 2.6, 2.6)

def build_plates(name, items, mat):
    bm = bmesh.new()
    for c, t, n, L, H, D in items:
        b = n.cross(t)
        vs = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    vs.append(bm.verts.new(c + t * (sx * L / 2) + b * (sy * H / 2) + n * (sz * D / 2)))
        f = lambda i, j, k, l: bm.faces.new((vs[i], vs[j], vs[k], vs[l]))
        f(0, 1, 3, 2); f(4, 6, 7, 5); f(0, 4, 5, 1); f(2, 3, 7, 6); f(0, 2, 6, 4); f(1, 5, 7, 3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, mat), 30)

# phasers: dorsal pair at the plan dots (1192, 815/937); ventral pair where the front-view leader ends on the lower dome;
# forward ports: the three circles at the bow rim in the front view.  (All rays cast before any new object is added.)
ph_d = [(hit((xP(py), yP(px), 300), (0, 0, -1)), nm) for px, py, nm in [(1192, 815, 'starboard'), (1192, 937, 'port')]]
ph_v = [(hit((x, -400, zF(2296)), (0, 1, 0)), nm) for x, nm in [(xF(944), 'starboard'), (-xF(944), 'port')]]
ports = [(hit((xF(c), -400, zF(2217.5)), (0, 1, 0)), c) for c in (971.5, 996.5, 1021.0)]
for (loc, n), nm in ph_d:
    kit.sphere(f'phaser P/S dorsal ({nm})', 1.0, tuple(loc), DARK, scale=(1, 1, .55))
    kit.cyl(f'phaser P/S dorsal mount ({nm})', 1.3, .5, tuple(loc), LINE, axis='Z', seg=32)
for (loc, n), nm in ph_v:
    kit.sphere(f'phaser P/S ventral ({nm})', 1.0, tuple(loc + n * .2), DARK, scale=(1, 1, .7))
for (loc, n), c in ports:
    o = kit.cyl(f'forward port {c:.0f}', 1.35, .4, (0, 0, 0), DARK, axis='Z', seg=32)
    o.matrix_world = Matrix.Translation(loc - n * .12) @ n.to_track_quat('Z', 'Y').to_matrix().to_4x4()

# ------------------------------------------------------------------ panel lines on the saucer top (plan: 24 radials every 15°,
# rings at r = 31, 70, 131, 168, 211, 257, 304 px)
def on_deck(x, y): return abs(x) < deck_w / 2 + .4 and y > yS(1180) - .5
def strip(bm, pts, w=.36, up=.08, down=.18):
    rings = []
    for i, p in enumerate(pts):
        q0 = pts[max(i - 1, 0)]; q1 = pts[min(i + 1, len(pts) - 1)]
        tng = Vector((q1[0] - q0[0], q1[1] - q0[1], 0)).normalized(); side = Vector((-tng.y, tng.x, 0)) * (w / 2)
        base = Vector(p)
        rings.append([bm.verts.new(base + side + Vector((0, 0, up))), bm.verts.new(base - side + Vector((0, 0, up))),
                      bm.verts.new(base - side - Vector((0, 0, down))), bm.verts.new(base + side - Vector((0, 0, down)))])
    for a, b in zip(rings, rings[1:]):
        for k in range(4): bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
def dome_k(a):
    c, s_ = math.cos(a), math.sin(a); a_ = DF if c > 0 else DA
    return a_ * DB / math.sqrt((DB * c) ** 2 + (a_ * s_) ** 2)
def surf(r, a):
    """point on the top surface at base radius r, azimuth a (from the bow, + toward port); on the dome the base radius is
    stretched exactly as the dome's vertices were.  None where the dome covers the hull."""
    k = dome_k(a)
    if r < R_DOME: rr = r * k
    elif r < R_DOME * k + .3: return None
    else: rr = r
    return (rr * math.sin(a), YC - rr * math.cos(a), z_top(r))
bm = bmesh.new()
for k in range(24):
    a = math.radians(k * 15 + .5)            # plan radials at 15° steps, ~0.5° off the centre-line
    run = []
    for r in rs(70 / PPM, 20.0, .5) + rs(20.0, R - .35, 2.0)[1:]:
        p = surf(r, a)
        if p is None or on_deck(p[0], p[1]):
            if len(run) > 1: strip(bm, run)
            run = []; continue
        run.append(p)
    if len(run) > 1: strip(bm, run)
for rp in (31, 70, 131, 168, 211, 257, 304):
    r = rp / PPM; run = []
    n = max(48, int(2 * math.pi * r / 1.3))
    pts = [surf(r, 2 * math.pi * i / n) for i in range(n + 1)]
    for p in pts:
        if p is None or on_deck(p[0], p[1]):
            if len(run) > 1: strip(bm, run)
            run = []; continue
        run.append(p)
    if len(run) > 1: strip(bm, run)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('panel lines'); bm.to_mesh(me); bm.free()
kit.smooth(kit._obj('panel lines', me, LINE), 30)

# ------------------------------------------------------------------ registry lettering
def text_mesh(body, extrude=.1):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body; cu.extrude = extrude; cu.align_x = 'LEFT'
    ob = bpy.data.objects.new('t', cu); bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    return bm
def lettering(name, body, mapper, mat=DARK, size=(30.0, 4.0)):
    bm = text_mesh(body)
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]
    u0, u1, v0, v1 = min(xs), max(xs), min(ys), max(ys)
    W, H = size                                   # lay out flat at true size, cut long edges so the glyphs follow the curve
    for v in bm.verts:
        v.co = Vector(((v.co.x - u0) / (u1 - u0) * W, (v.co.y - v0) / (v1 - v0) * H, v.co.z))
    for _ in range(3):
        long_e = [e for e in bm.edges if e.calc_length() > .45]
        if not long_e: break
        bmesh.ops.subdivide_edges(bm, edges=long_e, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=bm.faces)
    for v in bm.verts:
        v.co = Vector(mapper(v.co.x / W, v.co.y / H, v.co.z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, mat), 30)
# saucer: along the arc between the 211 and 257 px rings, letter tops toward the centre, reading starboard → port
r_base, r_cap = 253 / PPM, 217 / PPM
ph0, ph1 = math.asin((728 - PCY) / (235 / 1)), math.asin((1043 - PCY) / 235)
def saucer_map(u, v, w):
    ph = ph0 + (ph1 - ph0) * u; rad = r_base - (r_base - r_cap) * v
    return (rad * math.sin(ph), YC - rad * math.cos(ph), z_top(rad) + .07 + w)
lettering('registry NCC-3801 (primary hull)', 'NCC-3801', saucer_map, size=(60.0, 6.0))
# nacelles: side view, outer faces, 1415-1610 px along, 1812-1835 px high; read bow→aft to port, aft→bow to starboard
def nac_map(side, ya, yb, za, zb):
    def m(u, v, w):
        y = ya + (yb - ya) * u if side > 0 else yb - (yb - ya) * u
        z = za + (zb - za) * v
        hw, z0, z1 = nac_hw(y); zc, b = (z0 + z1) / 2, (z1 - z0) / 2
        x = hw * math.sqrt(max(1 - ((z - zc) / b) ** 2, 0)) + .07 + w
        return (side * (XN + x), y, z)
    return m
def rect_bm(nu=24, nv=4):
    """unit rectangle (u, v in 0..1) as a closed slab, w = ±0.1"""
    bm = bmesh.new(); top = []; bot = []
    for j in range(nv + 1):
        top.append([bm.verts.new((i / nu, j / nv, .1)) for i in range(nu + 1)])
        bot.append([bm.verts.new((i / nu, j / nv, -.1)) for i in range(nu + 1)])
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
    edge = [(0, i) for i in range(nu)] + [(j, nu) for j in range(nv)] + [(nv, i) for i in range(nu, 0, -1)] + [(j, 0) for j in range(nv, 0, -1)]
    for k in range(len(edge)):
        (j0, i0), (j1, i1) = edge[k], edge[(k + 1) % len(edge)]
        bm.faces.new((top[j0][i0], bot[j0][i0], bot[j1][i1], top[j1][i1]))
    return bm
def decal(name, x0, x1, y0, y1, mat, side):
    bm = rect_bm(); f = nac_map(side, yS(x0), yS(x1), zS(y1), zS(y0))
    for v in bm.verts: v.co = Vector(f(v.co.x, v.co.y, v.co.z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, mat), 30)
for side, nm in ((1, 'port'), (-1, 'starboard')):
    lettering(f'registry NCC-3801 ({nm} nacelle)', 'NCC-3801', nac_map(side, yS(1415), yS(1610), zS(1835), zS(1812)), size=(32.4, 3.8))
    decal(f'nacelle band fwd ({nm})', 1175, 1196, 1813, 1838, DARK, side)
    decal(f'nacelle band ({nm})', 1205, 1408, 1813, 1838, DARK, side)
    decal(f'nacelle stripe ({nm})', 1625, 1745, 1816, 1835, DARK, side)
    decal(f'nacelle grille ({nm})', 1795, 1860, 1808, 1840, 'dark', side)

for mat, items in quads.items():
    build_plates(f'windows and fittings ({mat})', items, mat)

size = kit.export_ship('ptolemy')
print('NACELLE AXIS z', round(NZ, 2), 'saucer R', round(R, 2), 'YC', round(YC, 2))
