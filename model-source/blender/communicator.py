"""Communicator Type I — PDF 137, TO 03:02:00.  Run: Blender -b -P model-source/blender/communicator.py [-- --pose closed --out DIR]
Printed: L.O.A. 113.5 mm, W.O.A. 63.5 mm, H.O.A. 28 mm, 200 gm, range 12 000 km. Colours: gold SF03UC, antimony SF02UC, black SF32UC.
Axes: Y = length with the hinge / tuned-ferrite-loop end at -Y (front), X = width (+X = image top of the TOP view), Z up.
Plate views (67.63 px/cm): TOP from +Z (up = +X, hinge at image right), SIDE from -X, BOTTOM from -Z (up = -X), END from -Y.
Body: three horizontal-slice lofts (lower shell, gold band, upper shell). At each height the section is a plan superellipse
(exponent 9, fitted to the TOP-view corners) whose length and centre come from that row of the SIDE silhouette
(profiles/communicator-side.json) and whose width comes from the same row of the END silhouette (communicator-end.json),
widened 1.1 % so the band meets the printed 63.5 mm (END/BOTTOM views draw 62.8 mm, TOP view 64.2 mm).
Details: plate pixel positions. Hidden internals drawn dashed (006P energy unit, speaker/microphone) are not modelled.
--pose closed: grille shut (used to score against the plates, which draw it shut); default pose = antenna open 110 deg."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bmesh, bpy

PPC = 67.63
SX = 6.35 / (425 / PPC)            # width correction: END-view band 425 px -> printed 63.5 mm
SIDE_MID, BOT_PY = 740.5, 1136     # SIDE view: Y centre px, bottom row
TOP_MID = (743.0, 661.5)           # TOP view centre (px)
BOTV_MID = (742.0, 1415.5)         # BOTTOM view centre (px)
END_DY = 724                       # END-view row + 724 = SIDE-view row (bottoms 412/1136, band centres 325/1049)
P_PLAN = 9.0
zs = lambda py: (BOT_PY - py) / PPC                  # SIDE row -> z
ys = lambda px: -(px - SIDE_MID) / PPC               # SIDE column -> y
yt = lambda px: -(px - TOP_MID[0]) / PPC             # TOP column -> y
xt = lambda py: -(py - TOP_MID[1]) / PPC * SX        # TOP row -> x
yb = lambda px: -(px - BOTV_MID[0]) / PPC            # BOTTOM column -> y
xb = lambda py: (py - BOTV_MID[1]) / PPC * SX        # BOTTOM row -> x

def se_ring(bm, cy, hx, hy, z, seg=160, p=P_PLAN):
    ring = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; c, s = math.cos(a), math.sin(a)
        ring.append(bm.verts.new((hx * math.copysign(abs(c) ** (2 / p), c), cy + hy * math.copysign(abs(s) ** (2 / p), s), z)))
    return ring

def slice_loft(name, secs, material, parent, cap_lo=True, cap_hi=True):
    """secs: [(z, y_lo, y_hi, half_x), ...] bottom -> top; plan superellipse sections."""
    bm = bmesh.new(); rings = [se_ring(bm, (a + b) / 2, hx, (b - a) / 2, z) for z, a, b, hx in secs]
    n = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
    if cap_lo: bm.faces.new(list(reversed(rings[0])))
    if cap_hi: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), 35)

def section(side, end, py):
    lo, hi = kit.sample(side, (py - side['origin_px'][1]) / PPC, 3)
    elo, ehi = kit.sample(end, (py - END_DY - end['origin_px'][1]) / PPC, 3)
    return (zs(py), -hi, -lo, (ehi - elo) / 2 * SX)

def build(pose='open'):
    root = kit.group('Communicator')
    side = kit.load_profile('communicator-side'); end = kit.load_profile('communicator-end')
    rows = lambda a, b, st=2: sorted([section(side, end, py) for py in list(range(a, b, st)) + [b]], key=lambda q: q[0])
    # ---- body: removable bottom (lower shell), gold equatorial band, upper body shell ----
    slice_loft('removable bottom (lower body shell)', rows(1059, 1135), 'black', root)
    slice_loft('gold equatorial band', rows(1037, 1059, 1), 'gold', root)
    slice_loft('upper body shell', rows(963, 1037), 'black', root)
    ztop = zs(963)
    # ---- control deck on the upper shell top (exposed when the antenna is open), TOP-view positions ----
    for px, py, mat, n in ((650, 622, 'red', 'red (ON) L.E.D.'), (690, 530, 'amber', 'yellow (T) L.E.D.'), (720, 787, 'blue', 'blue (R) L.E.D.')):
        kit.sphere(n, .11, (xt(py), yt(px), ztop), mat, scale=(1, 1, .35), parent=root)
        kit.torus(n + ' bezel', .13, .025, (xt(py), yt(px), ztop + .01), 'antimony', axis='Z', parent=root)
    kit.cyl('channel switch (SW2)', .27, .06, (xt(782), yt(568), ztop + .01), 'antimony', 'Z', parent=root)
    kit.box('channel switch slot', (.4, .05, .02), (xt(782), yt(568), ztop + .04), 'black', rot=(0, 0, .6), parent=root)
    kit.box('vent', (xt(553) - xt(622), yt(528) - yt(602), .02), (xt(587), yt(565), ztop + .005), 'dark', parent=root)
    for i in range(4):
        kit.box('vent slot', (xt(553) - xt(622) - .12, .05, .03), (xt(587), yt(535 + i * 20), ztop + .02), 'black', parent=root)
    # transmit/receive switch SW1: semicircular tab at the grille's free end (TOP view centre (500, 670), r 30 px)
    r1 = 30 / PPC; pts = [(r1 * math.cos(math.radians(a)) * SX, r1 * math.sin(math.radians(a))) for a in range(0, 181, 10)]
    kit.extrude('transmit/receive switch (SW1)', [(x_, y_) for x_, y_ in pts], .1, 'dark', plane='XY', loc=(xt(670), yt(500), ztop + .03), parent=root, rot=(0, 0, 0))
    # ---- tuned ferrite loop (antimony barrel across the hinge end) between two gold hinge posts ----
    yb_, zb_ = ys(1077), zs(993); rb = 42 / PPC
    kit.cyl('tuned ferrite loop', rb, (1202 - 945) / PPC * SX, (0, yb_, zb_), 'antimony', 'X', seg=64, parent=root)
    # gold hinge posts at the loop ends (END view x 920-945 / 1202-1228); round in the SIDE view, where the barrel outline shows
    for pxe in (932.5, 1215):
        kit.cyl('hinge post', rb + .03, 25 / PPC * SX, ((pxe - 1075) / PPC * SX, yb_, zb_), 'gold', 'X', seg=64, bev=.03, parent=root)
    # ---- antenna: gold perforated grille (TOP view x 500-1088, y 508-800, 17 px thick in SIDE view), hinged on the loop ----
    hinge = kit.group('antenna hinge', root); hinge.location = (0, yb_, zb_)
    if pose == 'open': hinge.rotation_euler = (math.radians(110), 0, 0)
    g0, g1, gx0, gx1, gt = yt(1088), yt(500), xt(800), xt(508), 17 / PPC
    rc = 12 / PPC; pts = []
    for cx_, cy_, a0 in ((gx1 - rc, g1 - rc, 0), (gx0 + rc, g1 - rc, 90), (gx0 + rc, g0 + rc, 180), (gx1 - rc, g0 + rc, 270)):
        for k in range(7):
            a = math.radians(a0 + k * 15); pts.append((cx_ + rc * math.cos(a), cy_ + rc * math.sin(a) - yb_))
    zg = ztop + gt / 2 - zb_        # lies on the shell top (SIDE view); the low deck controls sit under it
    kit.extrude('antenna (perforated grille)', pts, gt, 'gold', plane='XY', loc=(0, 0, zg), bev=.02, parent=hinge)
    # hex-packed perforations: 21.7 px pitch, 17 px holes, staggered rows 18.8 px apart (drawn on both faces)
    bm = bmesh.new(); hr = 8.5 / PPC; nh = 0
    yy = 508 + 12; row = 0
    while yy <= 800 - 10:
        xx = 500 + 12 + (10.85 if row % 2 else 0)
        while xx <= 1088 - 10:
            for zf in (zg + gt / 2 + .003, zg - gt / 2 - .003):
                bmesh.ops.create_circle(bm, cap_ends=True, segments=12, radius=hr, matrix=__import__('mathutils').Matrix.Translation((xt(yy), yt(xx) - yb_, zf)))
            nh += 1; xx += 21.7
        yy += 18.8; row += 1
    me = bpy.data.meshes.new('grille perforations'); bm.to_mesh(me); bm.free()
    kit._obj('grille perforations', me, 'black', hinge)
    kit.box('grille hinge knuckle', ((gx1 - gx0) - .3, .5, .3), ((gx0 + gx1) / 2, .0, zg - .08), 'gold', bev=.08, parent=hinge)
    # ---- bottom (BOTTOM view): magnatomic adhesion surface, two attach screws, on/off switch (SW, drawn dashed) ----
    zbot = zs(1135)
    rc = 12 / PPC; mx0, mx1, my0, my1 = xb(1325), xb(1517), yb(880), yb(604); pts = []
    for cx_, cy_, a0 in ((mx1 - rc, my1 - rc, 0), (mx0 + rc, my1 - rc, 90), (mx0 + rc, my0 + rc, 180), (mx1 - rc, my0 + rc, 270)):
        for k in range(7):
            a = math.radians(a0 + k * 15); pts.append((cx_ + rc * math.cos(a), cy_ + rc * math.sin(a)))
    kit.extrude('magnatomic adhesion surface', pts, .04, 'dark', plane='XY', loc=(0, 0, zbot + .01), parent=root)
    for py in (1293, 1547):
        kit.cyl('attach screw', 15 / PPC, .04, (xb(py), yb(740), zbot + .01), 'antimony', 'Z', parent=root)
        for r in (0.6, -0.6):
            kit.box('attach screw cross-head', (.22, .05, .02), (xb(py), yb(740), zbot - .005), 'black', rot=(0, 0, math.pi / 4 + (r > 0) * math.pi / 2), parent=root)
    kit.box('on/off switch (SW)', (xb(1595) - xb(1548), yb(970) - yb(1040), .02), (xb(1571), yb(1005), zbot + .005), 'dark', parent=root)
    return root

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    pose = argv[argv.index('--pose') + 1] if '--pose' in argv else 'open'
    out = argv[argv.index('--out') + 1] if '--out' in argv else None
    kit.reset(); build(pose)
    kit.export('communicator', out)
