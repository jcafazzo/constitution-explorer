"""Anabolic Protoplaser — size 0 (PDF 130, TO 02:11:13) and size 2 (PDF 131, TO 02:11:12).
Run: Blender -b -P model-source/blender/anabolic_protoplaser.py [-- --units <dir>]
Printed: size 0 SFAF/SG-MK08-0  25 x 3.8 x 4.2 cm;  size 2 SFAF/SG-MK08-2  35 x 5.6 x 6.95 cm.
Colours: antimony SF02UC, gray SF30UC, red SF10UC, black SF32UC.
Each size is built from its own sheet (size 0 at 43.48 px/cm, size 2 at 33.98 px/cm): housing lofted from the TOP PLAN width
(profiles/anabolic-protoplaser-size*-plan.json, made symmetric about the drawn centre line) and the SIDE PROFILE's top and
bottom lines (housing top read under the D hump; bottom from profiles/*-side.json). Sheet callout letters differ:
size 0: C spec plate, D activating switch + intensity control, J force light; size 2: C activating switch, D intensity control,
J spec plate, K force light.
Axes per unit: front (ray duct) = -Y, Z up, +X = the unit's left (seen as image-right in the top plan, which is drawn rear-up);
the side profiles are drawn from +X. Unit origin: y = 0 at the housing's front face, z = 0 on the duct axis.
Display: size 0 at -X, size 2 at +X, rear ends level, bottoms on z = 0."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy

def lerp_pts(pts, v):
    """piecewise-linear interpolation through [(key, value), ...] (keys ascending)"""
    if v <= pts[0][0]: return pts[0][1]
    for (a, fa), (b, fb) in zip(pts, pts[1:]):
        if v <= b: return fa + (fb - fa) * (v - a) / (b - a)
    return pts[-1][1]

class Sheet:
    """Plate → unit coordinates for one sheet."""
    def __init__(self, ppc, py_front, axis_plan, axis_side, plan, side):
        self.P, self.F, self.AP, self.AS = ppc, py_front, axis_plan, axis_side
        self.plan, self.side = kit.load_profile(plan), kit.load_profile(side)
    def y(self, py): return -(py - self.F) / self.P                # plan / side row → y
    def x(self, px): return (px - self.AP) / self.P                # plan column → x (image right = +X)
    def z(self, px): return -(px - self.AS) / self.P               # side column → z (image left = top)
    def half_w(self, py):
        lo, hi = kit.sample(self.plan, (py - self.plan['origin_px'][1]) / self.P, 4); return (hi - lo) / 2
    def bottom(self, py):
        lo, hi = kit.sample(self.side, (py - self.side['origin_px'][1]) / self.P, 4)
        return self.z(self.side['origin_px'][0] + hi * self.P)
    def side_top(self, py):
        lo, hi = kit.sample(self.side, (py - self.side['origin_px'][1]) / self.P, 4)
        return self.z(self.side['origin_px'][0] + lo * self.P)

def conform_plate(name, secs, half_w, parent, material='antimony', p=2.6, z_min=None):
    """A plate that hugs the rounded top: the housing-top sections grown slightly, cut to |x| <= half_w (boolean intersect)
    and, with z_min, to z >= z_min (so a plate on the top surface does not wrap round the sides and bottom)."""
    shell = kit.loft(name, secs, material, p=p, parent=parent)
    ys = [s_[0] for s_ in secs]; zs = [v for s_ in secs for v in s_[3:]]
    z0 = min(zs) - .5 if z_min is None else z_min; z1 = max(zs) + .5
    cut = kit.box(name + ' cutter', (2 * half_w, max(ys) - min(ys) + 1, z1 - z0), (0, (max(ys) + min(ys)) / 2, (z0 + z1) / 2), 'antimony', parent=parent)
    m = shell.modifiers.new('clip', 'BOOLEAN'); m.operation = 'INTERSECT'; m.object = cut; m.solver = 'EXACT'
    bpy.context.view_layer.update(); bpy.context.view_layer.objects.active = shell; bpy.ops.object.modifier_apply(modifier='clip')
    bpy.data.objects.remove(cut)
    return shell

def rows(a, b, n):
    return [a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * i / n)) for i in range(n + 1)]

# ------------------------------------------------------------------ size 0 (PDF 130)
def size0(parent=None, name='Anabolic Protoplaser size 0 (SFAF/SG-MK08-0)'):
    S = Sheet(43.48, 1137.0, 821.5, 1230.0, 'anabolic-protoplaser-size0-plan', 'anabolic-protoplaser-size0-side')
    g = kit.group(name, parent)
    R0, F0 = 318.0, 1137.0                                   # rear end / housing front rows
    ztop = lambda py: S.z(lerp_pts([(325, 1170), (1135, 1152)], py))      # housing top line, under D
    zgw = lambda py: S.z(lerp_pts([(325, 1194), (1135, 1201)], py))       # grey top / antimony band boundary
    zwb = lambda py: S.z(lerp_pts([(325, 1250), (1135, 1257)], py))       # antimony band / black panel boundary
    grey, band, black = [], [], []
    for py in rows(R0, F0, 90):
        w, zb, zt, z1, z2 = S.half_w(py), S.bottom(py), ztop(py), zgw(py), zwb(py)
        k = min(1.0, (py - R0) / 4 + .25)                     # the drawn rear corners
        grey.append((S.y(py), -.86 * w, .86 * w, z2, zt))
        band.append((S.y(py), -w * k, w * k, z2 - .01, z1 + .01))
        black.append((S.y(py), -.96 * w, .96 * w, zb, z2 + (z2 - zb)))
    kit.loft('(A) housing (grey)', grey, 'grey', p=2.6, parent=g)
    kit.loft('housing side band (antimony)', band, 'antimony', p=7, parent=g)
    kit.loft('(B) removable bottom panel', black, 'black', p=2.6, parent=g)
    # (D) activating switch and intensity control: antimony wedge on the top centre line, rising from the rear end to a 0.77 cm
    # step at row 960 (side-profile outer line), 1.31 cm wide (plan strip x 788-845); seam across it at row 785
    zD = lambda py: S.z(lerp_pts([(318, 1170), (325, 1167), (400, 1158), (500, 1147), (600, 1138), (700, 1130), (785, 1125), (800, 1124), (900, 1121), (960, 1120)], py))
    hw = (845 - 788) / 2 / S.P
    secs = [(S.y(py), -hw, hw, ztop(py) - .25, max(zD(py), ztop(py) + .02)) for py in rows(R0 + 1, 960, 60)]
    kit.loft('(D) activating switch and intensity control', secs, 'antimony', p=8, parent=g)
    kit.box('switch seam', (2 * hw + .02, .03, .04), (0, S.y(785), zD(785) - .01), 'dark', parent=g)
    # (J) intensity force light: square window on D (plan x 795-838, y 800-845)
    kit.box('(J) intensity force light', (S.x(838) - S.x(795), S.y(800) - S.y(845), .04), (S.x(816.5) + 5 / S.P, S.y(822.5), zD(822) + .005), 'white', bev=.01, parent=g)
    kit.box('J frame', (S.x(840) - S.x(793), S.y(798) - S.y(847), .03), (S.x(816.5) + 5 / S.P, S.y(822.5), zD(822) - .002), 'black', parent=g)
    # (E) effectivity sensor: red disc on the front face of the D step (front elevation: dia 0.58, 0.46 cm above the housing top)
    kit.cyl('(E) effectivity sensor', .29, .05, (0, S.y(960) - .02, ztop(960) + .46), 'red', 'Y', parent=g)
    # (C) specifications plate on the top near the front (plan x 758-884, y 1020-1080; 0.09 proud in the side profile)
    conform_plate('(C) specifications plate', [(S.y(py), -.86 * S.half_w(py) - .03, .86 * S.half_w(py) + .03, zwb(py) - .03, ztop(py) + .03)
                                               for py in rows(1020, 1080, 8)], (884 - 758) / 2 / S.P, g)
    # (H) recharging chamber: circle dia 1.43 on the rear end face (ROT 90 CCW view), with its top-strip tab above
    yr = S.y(R0)
    kit.cyl('(H) recharging chamber', .715, .04, (0, yr + .005, (ztop(330) + S.bottom(330)) / 2 + .1), 'grey', 'Y', parent=g)
    kit.torus('H rim', .715, .025, (0, yr + .02, (ztop(330) + S.bottom(330)) / 2 + .1), 'dark', 'Y', parent=g)
    # (F) DNA match synthesization unit: cylinder dia 2.62 (rows 1137-1275), then the cone to a 0.53 cm flat tip at row 1408
    rF = (879 - 764) / 2 / S.P
    kit.cyl('(F) DNA match synthesization unit', rF, S.y(F0) - S.y(1275), (0, (S.y(F0) + S.y(1275)) / 2, 0), 'antimony', 'Y', parent=g)
    kit.revolve('(F) emitter cone', [(0, S.y(1275)), (rF, S.y(1275)), (.265, S.y(1408)), (0, S.y(1408))], 'antimony', axis='Y', parent=g)
    # (G) ray emission duct: the dashed bore along the axis, opening at the tip (front elevation: dia 0.28 ring)
    kit.cyl('(G) ray emission duct', .14, .04, (0, S.y(1408) - .005, 0), 'black', 'Y', parent=g)
    kit.cyl('(G) duct bore (hidden)', .14, S.y(F0) - S.y(1408), (0, (S.y(F0) + S.y(1408)) / 2, 0), 'dark', 'Y', parent=g)
    return g, S.bottom(1110), yr

# ------------------------------------------------------------------ size 2 (PDF 131)
def size2(parent=None, name='Anabolic Protoplaser size 2 (SFAF/SG-MK08-2)'):
    S = Sheet(33.98, 1205.0, 684.0, 1085.5, 'anabolic-protoplaser-size2-plan', 'anabolic-protoplaser-size2-side')
    g = kit.group(name, parent)
    R0, F0 = 312.0, 1205.0
    ztop = lambda py: S.z(lerp_pts([(320, 1025), (1195, 990)], py))
    housing = []
    for py in rows(R0, F0, 90):
        w = S.half_w(py) if not 860 < py < 990 else (S.half_w(860) + (S.half_w(990) - S.half_w(860)) * (py - 860) / 130)  # switch C masked out
        k = min(1.0, (py - R0) / 4 + .25)
        housing.append((S.y(py), -w * k, w * k, S.bottom(py) - .03, ztop(py)))   # bottom panel line drawn heavy: 0.3 mm below its centre
    kit.loft('(A) housing', housing, 'grey', p=4.2, parent=g)
    # (B) removable bottom panel (grey on this sheet): the seam line along the lower side faces
    # one continuous swept strip per side following the tapered face, trimmed short of the end radii
    for sg in (-1, 1):
        secs = []
        for i in range(0, 41):
            py = R0 + 28 + i * (F0 - R0 - 56) / 40; w = S.half_w(py); zs = S.bottom(py) + .45
            xc = sg * (w - .005)
            secs.append((S.y(py), xc - .012, xc + .012, zs - .012, zs + .012))
        kit.loft('(B) bottom panel seam', secs, 'dark', p=2.0, seg=12, parent=g)
    # (D) intensity control: wedge on the top centre line — grey base 2.1 wide and antimony top 1.8 wide (front elevation tiers),
    # rising from the rear end to a 1.35 cm step at row 1030 (side-profile outer line)
    zD = lambda py: S.z(lerp_pts([(312, 1025), (320, 1020), (400, 1008), (500, 994), (600, 980), (700, 968), (800, 957), (900, 950), (1000, 945), (1030, 944)], py))
    zT = lambda py: ztop(py) + (zD(py) - ztop(py)) * .22
    base = [(S.y(py), -1.05, 1.05, ztop(py) - .3, max(zT(py), ztop(py) + .01)) for py in rows(R0 + 1, 1030, 60)]
    top = [(S.y(py), -.9, .9, ztop(py) - .1, max(zD(py), ztop(py) + .02)) for py in rows(R0 + 1, 1030, 60)]
    kit.loft('(D) intensity control base', base, 'grey', p=8, parent=g)
    kit.loft('(D) intensity control (depress to increase intensity)', top, 'antimony', p=5, parent=g)
    # (K) intensity force light: a white square light (plan x 665-700, y 873-902) in a black square frame (x 659-706, y 867-908),
    # both standing proud of D's top and tilted to its slope (D rises 0.07 cm toward the front over the light)
    tilt = math.atan2(-(zD(905) - zD(870)), S.y(870) - S.y(905))
    zK = zD(887.5); xc = S.x(682.5); yc = S.y(887.5)
    fo, fi = (706 - 659) / S.P, (700 - 665) / S.P; bw = (fo - fi) / 2; hk = .14
    for dx, dy, sx, sy in ((0, (fi + bw) / 2, fo, bw), (0, -(fi + bw) / 2, fo, bw), ((fi + bw) / 2, 0, bw, fi), (-(fi + bw) / 2, 0, bw, fi)):
        kit.box('(K) force light frame', (sx, sy, hk), (xc + dx, yc + dy * math.cos(tilt), zK + .045 - hk / 2 + dy * math.sin(tilt)), 'black', rot=(tilt, 0, 0), parent=g)
    kit.box('(K) intensity force light', (fi, fi, hk), (xc, yc, zK + .03 - hk / 2), 'white', rot=(tilt, 0, 0), parent=g)
    # (E) effectivity sensor on the front face of the D step (front elevation: dia 0.82, 0.59 above the housing top)
    kit.cyl('(E) effectivity sensor', .41, .05, (0, S.y(1030) - .02, ztop(1030) + .59), 'red', 'Y', parent=g)
    # (C) activating switch, black-off / red-on, push forward: on the +X side face (plan x 773-784, side window rows 868-975, z ±0.43)
    xw = S.half_w(920) - .02
    kit.box('(C) activating switch housing', (.3, S.y(868) - S.y(975), .86), (xw + .15, S.y(921.5), 0), 'grey', bev=.04, parent=g)
    kit.box('(C) switch window', (.02, S.y(872) - S.y(971), .5), (xw + .305, S.y(921.5), 0), 'antimony', parent=g)
    kit.box('(C) switch slider (black = off)', (.04, S.y(905) - S.y(950), .36), (xw + .31, S.y(927.5), 0), 'black', parent=g)
    for i in range(6):
        kit.box('switch grip rib', (.03, .03, .36), (xw + .33, S.y(878 + i * 4.5), 0), 'black', parent=g)
    # (J) specifications plate on the top near the front (plan x 603-765, y 1078-1150)
    # (the side profile draws J only on the top edge: the plate is clipped 0.6 cm below the housing top, so it stays on the top face)
    conform_plate('(J) specifications plate', [(S.y(py), -S.half_w(py) - .03, S.half_w(py) + .03, S.bottom(py) - .03, ztop(py) + .05)
                                               for py in rows(1078, 1150, 8)], (765 - 603) / 2 / S.P, g, p=4.2, z_min=ztop(1150) - .6)
    # (H) recharging chamber: dia 2.15 circle on the rear end face
    yr = S.y(R0)
    zc = (ztop(330) + S.bottom(330)) / 2
    kit.cyl('(H) recharging chamber', 1.07, .04, (0, yr + .005, zc), 'grey', 'Y', parent=g)
    kit.torus('H rim', 1.07, .03, (0, yr + .02, zc), 'dark', 'Y', parent=g)
    # (F) DNA match synthesization unit: collar (rows 1205-1218, 3.77 wide), neck dia 1.62 (1218-1250), cone flaring to the
    # blunt cylinder dia 3.88 (1362-1510) whose front holds the recessed conical duct (G). F is drawn unshaded: antimony.
    # The front elevation draws three concentric circles: F rim (dia 3.72), cone mouth (dia 3.15) and bore (dia 1.16, the dashed
    # duct running back through the unit in the side profile); cone 1.18 deep.
    kit.cyl('collar', 3.77 / 2, S.y(1205) - S.y(1219), (0, S.y(1212), 0), 'antimony', 'Y', bev=.05, parent=g)
    rN, rF = (710 - 655) / 2 / S.P, (750 - 618) / 2 / S.P
    yF = S.y(1510); rM, rB = 3.15 / 2, 1.16 / 2
    pts = [(0, S.y(1217)), (rN, S.y(1217)), (rN, S.y(1250)), (rF, S.y(1362)), (rF, yF), (rM, yF), (rB, yF + 1.18), (0, yF + 1.18)]
    kit.revolve('(F) DNA match synthesization unit', pts, 'antimony', axis='Y', parent=g)
    kit.revolve('(G) ray emission duct (recessed cone)', [(rM - .02, yF + .002), (rB, yF + 1.17), (rB - .01, yF + 1.17)], 'grey', axis='Y', parent=g)
    kit.cyl('(G) ray emission duct bore', rB, .02, (0, yF + 1.165, 0), 'black', 'Y', parent=g)
    return g, S.bottom(1190), yr

def build(parent=None):
    root = kit.group('Anabolic Protoplaser', parent)
    a, zb0, yr0 = size0(root); b, zb2, yr2 = size2(root)
    # side by side: size 0 at -X, size 2 at +X (2.1 cm gap), rear ends level, bottoms on z = 0
    a.location = (-(3.83 / 2 + 1.05), -yr0, -zb0)
    b.location = ((5.74 / 2 + 1.05), -yr2, -zb2)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('anabolic-protoplaser')
    if '--units' in sys.argv:          # each size alone, for scoring against its own sheet
        out = sys.argv[sys.argv.index('--units') + 1]
        kit.reset(); kit._mats.clear(); size0(); kit.export('anabolic-protoplaser-size0', out)
        kit.reset(); kit._mats.clear(); size2(); kit.export('anabolic-protoplaser-size2', out)
