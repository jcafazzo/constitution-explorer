"""Transporter controls console (PDF 145, TO 03:16:32): top plan and side profile.
Run: Blender -b -P model-source/blender/transporter_console.py          -> transporter-console.glb
     CONSOLE_NO_BASE=1 CONSOLE_OUT=<dir> Blender -b -P ...             -> the console body alone, for scoring against the side profile

Measured on the 1400 px plate. Scale: the plan's width (325-1195 px) is the printed L.O.A. 197.5 cm -> 4.405 px/cm
(the 0-50 cm bar reads 4.38-4.44). Plan: P(x, y) px; side profile: Q(x, y) px, front at x = 742, body's lowest point at y = 1565.
Frame: x across (operator's left -X), y front (0) to back, z up from the floor.

HEIGHT. The sheet prints H.O.A. 181.3 cm, but the profile draws the pedestal with a break line, so its length is not drawn. The body
alone is 70 cm tall; at 181.3 cm the control surface would stand about 149 cm off the floor. This build takes the figure as a
transposition of 118.3 cm (control surface 86-95 cm). CONSOLE_HOA=181.3 builds it as printed.
ASSUMED: the pedestal's width (drawn only in profile, 46 cm deep) is taken as the centre block's 77 cm; which printed colour goes where."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy

kit.PALETTE.update({
    'platinum': ('d3d4d0', .35, .3, 1),   # Platinum No. SF29UC
    'skyblue': ('8fb4d6', .6, 0, 1),      # Sky blue No. SF16UC (the stippled deck)
    'lamp_w': ('f2efe2', .3, 0, 1), 'lamp_y': ('e3c443', .35, 0, 1),
})
S = 4.405
HOA = float(os.environ.get('CONSOLE_HOA', 118.3))
NO_BASE = os.environ.get('CONSOLE_NO_BASE') == '1'
OUT = os.environ.get('CONSOLE_OUT') or None
Z0 = HOA - (1565 - 1250) / S            # floor to the body's lowest point; 1250 = top of the intercom
CX = 760.0                              # plan centre line
K = (1180 - 742) / (1070 - 637)         # plan depth -> profile depth (433 px vs 438 px)

def Y(qx): return (qx - 742) / S
def Z(qy): return Z0 + (1565 - qy) / S
def q(pts): return [(Y(a), Z(b)) for a, b in pts]
def X(px): return (px - CX) / S
def py2q(py): return 742 + (1070 - py) * K      # plan y -> profile x

kit.reset()
W = (1195 - 325) / S                    # 197.5
WC = (927 - 587) / S                    # centre block, 77.2

# ---- body: the profile's outer line (wing surface), extruded across the full width
body = kit.extrude('body', q([(742, 1402), (755, 1405), (1035, 1347), (1040, 1340), (1105, 1295), (1160, 1295), (1180, 1565),
                              (803, 1508), (755, 1450), (742, 1450)]), W, 'platinum', plane='YZ', bev=.4)
# ---- centre block: raised black slab under the selector grid, hood B and shelf A
kit.extrude('centre', q([(738, 1400), (903, 1360), (1010, 1335), (1045, 1335), (1040, 1345), (742, 1410)]), WC, 'black', plane='YZ', bev=.2)
hood = kit.extrude('hood', q([(903, 1362), (909, 1338), (912, 1300), (910, 1275), (907, 1258), (1010, 1335)]), WC, 'platinum', plane='YZ', bev=.3)
kit.box('hood_view', (WC - 8, .5, 14), (0, Y(911) - .1, Z(1312)), 'screen')

# ---- decks: groups lying on each sloped surface; children placed at (x, v along the slope from the group's origin, w above it)
def deck(name, q0, q1):
    a = math.atan2(q0[1] - q1[1], q1[0] - q0[0])
    g = kit.group(name); g.location = (0, Y(q0[0]), Z(q0[1])); g.rotation_euler = (a, 0, 0)
    c = math.cos(a)
    def v(py): return (Y(py2q(py)) - Y(q0[0])) / c
    return g, v
wing, wv = deck('wing', (755, 1405), (1035, 1347))
ctr, cv = deck('ctr', (738, 1400), (903, 1360))
face, fv = deck('face', (1040, 1340), (1105, 1295))

def plate(name, g, v, x0, y0, x1, y1, material, h=.3, bev=0.0):
    """Plan rectangle (px) laid on a deck."""
    a, b = v(y1), v(y0)
    return kit.box(name, ((x1 - x0) / S, b - a, h), (X((x0 + x1) / 2), (a + b) / 2, h / 2), material, bev=bev, parent=g)
def dot(name, g, v, px, py, r, material, h=.5):
    return kit.cyl(name, r / S, h, (X(px), v(py), h / 2 + .2), material, axis='Z', seg=20, parent=g)

# stippled (sky blue) deck inlays
plate('deck_l', wing, wv, 332, 783, 584, 1062, 'skyblue', .12)
plate('deck_r', wing, wv, 930, 783, 1188, 1062, 'skyblue', .12)
plate('deck_c', face, fv, 587, 716, 927, 757, 'skyblue', .12)

# left wing: computer readout board, energizing controls (C), main power panel
plate('readout', wing, wv, 351, 803, 490, 937, 'screen', .5, .1)
plate('energizing', wing, wv, 505, 815, 570, 962, 'lamp_w', .35, .08)
for i, px in enumerate((522, 538, 553)):       # photon ionization, neural paralyzer, magnetic field
    plate(f'slot{i}', wing, wv, px - 1.5, 842, px + 1.5, 947, 'black', .45)
    plate(f'slider{i}', wing, wv, px - 6, 820, px + 6, 842, 'brushed', 1.6, .1)
plate('power', wing, wv, 351, 965, 490, 1045, 'black', .5, .1)
for i in range(8):
    plate(f'pbar{i}', wing, wv, 367 + i * 9.6, 978, 374 + i * 9.6, 998, 'lamp_w', .8)
    dot(f'plamp{i}', wing, wv, 360 + i * 12.6, 1017, 4.5, ('lamp_w', 'amber', 'red', 'blue')[i % 4], .7)
for i, py in enumerate((976, 1000, 1023)):
    plate(f'pbtn{i}', wing, wv, 463, py - 5, 485, py + 5, 'lamp_w', .8)

# right wing: power beam level indicator, channel selector controls
plate('level_frame', wing, wv, 1022, 800, 1163, 932, 'black', .5, .1)
plate('level_face', wing, wv, 1035, 810, 1150, 885, 'lamp_w', .62)
for r_px in (62, 40):                          # the two arcs of the meter scale, centre below the face
    n = 14; pts = []
    for k in range(n + 1):
        t = math.radians(40 + 100 * k / n); pts.append(((1092 + r_px * math.cos(t) - CX) / S, wv(905 - r_px * math.sin(t) * .78)))
    for k in range(n):
        (xa, va), (xb, vb) = pts[k], pts[k + 1]
        kit.box(f'arc{r_px}_{k}', (math.hypot(xb - xa, vb - va) + .1, .28, .1), ((xa + xb) / 2, (va + vb) / 2, .68), 'black',
                rot=(0, 0, math.atan2(vb - va, xb - xa)), parent=wing)
plate('channel', wing, wv, 1022, 960, 1163, 1045, 'black', .5, .1)
for i, (px, py, w, h) in enumerate(((1042, 975, 22, 10), (1042, 998, 18, 6), (1042, 1022, 22, 10), (1108, 975, 16, 20), (1108, 1016, 16, 20),
                                    (1145, 975, 22, 10), (1145, 998, 22, 10), (1145, 1021, 22, 10))):
    plate(f'cbtn{i}', wing, wv, px - w / 2, py - h / 2, px + w / 2, py + h / 2, 'lamp_w', .8)
dot('cdot0', wing, wv, 1070, 997, 6, 'red', .8); dot('cdot1', wing, wv, 1070, 1020, 6, 'lamp_w', .8)
dot('key', wing, wv, 970, 1012, 6, 'brushed', .6)

# tilted rear face: carrier beam (left) and power beam (right) systems status displays
LAMPS = ('lamp_w', 'blue', 'red', 'amber')
for i, (x0, x1) in enumerate(((338, 405), (422, 493), (505, 577), (935, 1010), (1020, 1095), (1105, 1180))):
    plate(f'status{i}', face, fv, x0, 718, x1, 774, 'lamp_w', .3, .08)
    for c in range(4):
        for r in range(4):
            if (c * 3 + r * 5 + i * 7) % 5 < 3:      # the sheet scatters the lamps; this is a stand-in pattern
                dot(f'st{i}_{c}{r}', face, fv, x0 + 10 + c * (x1 - x0 - 20) / 3, 726 + r * 13.5, 4.5, LAMPS[(c + r + i) % 4], .35)

# centre block: the coordinate selector grid, a half disc with its flat edge at the hood
def arc_strip(name, r0, r1, material, h, zc):
    n = 36; pts = [(r1 * math.cos(math.pi + math.pi * k / n), r1 * math.sin(math.pi + math.pi * k / n)) for k in range(n + 1)]
    if r0 > 0: pts += [(r0 * math.cos(2 * math.pi - math.pi * k / n), r0 * math.sin(2 * math.pi - math.pi * k / n)) for k in range(n + 1)]
    return kit.extrude(name, pts, h, material, plane='XY', loc=(X(757), cv(902), zc), parent=ctr)
arc_strip('selector', 0, 120 / S, 'lamp_w', .3, .15)
for i, r in enumerate((15, 33, 50, 66, 83)):
    arc_strip(f'ring{i}', (r - 1.2) / S, (r + 1.2) / S, 'black', .08, .34)
for i in range(1, 6):
    t = math.pi + i * math.pi / 6; r0, r1 = 15 / S, 83 / S
    kit.box(f'spoke{i}', (r1 - r0, .5, .08), (X(757) + (r0 + r1) / 2 * math.cos(t), cv(902) + (r0 + r1) / 2 * math.sin(t), .34), 'black',
            rot=(0, 0, t), parent=ctr)

# rear ledge: transport warning lights (red, yellow) either side of the intercom
zt = Z(1295)
for name, x0, x1, material in (('warn_red', 625, 675, 'red'), ('warn_yellow', 838, 887, 'lamp_y')):
    kit.box(name + '_base', ((x1 - x0) / S, 33 / S, 3.4), (X((x0 + x1) / 2), Y(py2q(688)), zt + 1.7), 'dark', bev=.15)
    kit.box(name, ((x1 - x0) / S - 1, 33 / S - 1, 3.4), (X((x0 + x1) / 2), Y(py2q(688)), zt + 5.1), material, bev=.3)
kit.box('intercom', ((812 - 701) / S, 20 / S, 45 / S), (X(756), Y(1147), zt + 22.5 / S), 'dark', bev=.2)
kit.box('intercom_grille', ((790 - 705) / S, .4, 6), (X(718), Y(1147) - 10 / S - .1, zt + 5.5), 'mesh')
kit.cyl('intercom_btn', 1.4, .6, (X(800), Y(1147) - 10 / S - .2, zt + 5.5), 'lamp_w', axis='Y', seg=24)

# ---- pedestal (drawn in profile only, with a break line)
if not NO_BASE:
    zf = 0.0
    kit.extrude('pedestal', [(Y(968), Z(1533)), (Y(1150), Z(1561)), (Y(1157), zf), (Y(950), zf)], WC, 'platinum', plane='YZ', bev=.4)
    kit.box('foot', (WC + 6, Y(1157) - Y(950) + 6, 2.5), (0, (Y(1157) + Y(950)) / 2, 1.25), 'dark', bev=.3)

for o in bpy.data.objects:
    if o.type == 'MESH' and o.name in ('body', 'centre', 'hood'): kit.smooth(o, 30)
kit.export('transporter-console', OUT)
