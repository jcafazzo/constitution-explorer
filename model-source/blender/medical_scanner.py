"""Medical Scanner — PDF 129, TO 02:11:07.  Run: Blender -b -P model-source/blender/medical_scanner.py
Printed: length overall 6.05 cm, maximum diameter 3.5 cm. Colours: antimony SF02UC, gray SF30UC, black SF32UC.
Upright: Z up, computer housing A on top, activating switch B facing the front (-Y). z = 0 at the scanner end (flange).
Read on the plate (68.52 px/cm): elevation axis x 794, rows y 323 (top) .. 737.5 (flange foot) — profile medical-scanner-elev.json;
dial view ("ROT 180° CW") centre (1094, 447); bottom view centre (791, 993).
The dial view is drawn turned 180° from the direct view down on the top (front at the bottom), so the dial face is placed
rotated 180° from the drawing (gauge letters toward the rear). Ten flutes, 36° apart: the dial view draws ten rim scallops at
image angles 9° + 36k, and the elevation's flute centres sit at -9°, 27°, 63° (asin of offset / radius) — the same phase.
Housing finish grey SF30UC is drawn as a light stipple, so its paint is a light grey (not the kit's darker 'grey').
(C) is a dark 48-mesh screen through which (D), a pair of twisted white vanes with the domed lens, shows white."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
kit.PALETTE.setdefault('grey30', ('a7abac', .55, .1, 1))         # gray SF30UC as drawn: light stipple
kit.PALETTE.setdefault('screen48', ('141516', .85, 0, .55))    # 48-mesh screen: dark, see-through (vanes read white)

PPC = 68.52
AX = 794.0                                 # elevation axis x
z = lambda py: (737.5 - py) / PPC          # elevation row → height
cm = lambda px: px / PPC

def capsule(name, r, z0, z1, loc_xy, material):
    """Vertical cylinder from z0 to z1 with a hemispherical top (flute cutter)."""
    pts = [(0, z0), (r, z0)] + [(r * math.cos(a), z1 - r + r * math.sin(a)) for a in [i * math.pi / 2 / 8 for i in range(9)]]
    return kit.revolve(name, pts, material, axis='Z', seg=32, loc=(loc_xy[0], loc_xy[1], 0))

def build(parent=None, name='Medical Scanner'):
    root = kit.group(name, parent)
    RH = (916 - 672) / 2 / PPC - .005      # housing / collar radius 1.775 (drawn 3.56 incl. line; printed 3.5)
    # (A) computer housing: grey turned cylinder y 323-546, top edge rounded r 0.17
    zt, zb, rc = z(323), z(546), .17
    pts = [(0, zb), (RH, zb)] + [(RH - rc + rc * math.cos(a), zt - rc + rc * math.sin(a)) for a in [i * math.pi / 2 / 10 for i in range(11)]] + [(0, zt)]
    housing = kit.revolve('(A) computer housing', pts, 'grey30', axis='Z', parent=root)
    # ten vertical flutes (rounded upper ends at y ~336) milled through the grey finish, antimony floor;
    # their tops break the rounded rim, giving the ten scallops of the dial view. Front flute at -9.2° (stripe x 757-792).
    cutters = []
    for k in range(10):
        a = math.radians(-90 - 9.2 + 36 * k)          # angle from +X; -90° = front (-Y)
        rr = RH + .12
        cutters.append(capsule('flute cutter', .26, zb - .5, zt + .3, (rr * math.cos(a), rr * math.sin(a)), 'antimony'))
    bpy.ops.object.select_all(action='DESELECT')
    for c in cutters: c.select_set(True)
    bpy.context.view_layer.objects.active = cutters[0]; bpy.ops.object.join(); cut = cutters[0]
    m = housing.modifiers.new('flutes', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cut; m.solver = 'EXACT'
    try: m.material_mode = 'TRANSFER'
    except Exception: pass
    bpy.context.view_layer.objects.active = housing; bpy.ops.object.modifier_apply(modifier='flutes')
    bpy.data.objects.remove(cut)
    # (B) activating switch: flat push pad 0.54 x 0.99 cm, x 793-830, y 480-548 (on the housing just above the collar)
    xs = cm((793 + 830) / 2 - AX); yS = -math.sqrt(RH ** 2 - xs ** 2)
    a = math.atan2(xs, -yS)
    kit.box('(B) activating switch (press on-off)', (cm(830 - 793), .05, cm(546 - 480)), (xs, yS - .005, z((480 + 546) / 2)), 'grey',
            rot=(0, 0, a), bev=.02, parent=root)
    for i in range(7):                       # fine vertical ribbing, as on the housing finish
        u = (i - 3) * cm(830 - 793) / 8
        kit.box('(B) switch rib', (.015, .02, cm(546 - 480) - .08), (xs + u * math.cos(a), yS - .035 + u * math.sin(a), z((480 + 546) / 2)), 'dark',
                rot=(0, 0, a), parent=root)
    # collar (antimony, y 546-567) and step ring (y 567-584, dia 2.98)
    kit.cyl('collar', RH, z(546) - z(567), (0, 0, (z(546) + z(567)) / 2), 'antimony', 'Z', bev=.01, parent=root)
    RS = (896 - 692) / 2 / PPC
    kit.cyl('step ring', RS, z(567) - z(584) + .01, (0, 0, (z(567) + z(584)) / 2), 'antimony', 'Z', parent=root)
    # (F) life form type selection scale: ticks round the step's underside between r 1.29-1.46 (bottom view, 250° of arc)
    for i in range(0, 64):
        phi = math.radians(95 - i * 250 / 63)             # bottom-view image angle; image right = +X, image up = -Y
        L = .16 if i % 5 == 0 else .08
        rm = RS - .02 - L / 2
        kit.box('(F) scale tick', (L, .012, .01), (rm * math.cos(phi), -rm * math.sin(phi), z(584) - .004), 'black', rot=(0, 0, -phi), parent=root)
    # (C) scanner housing: 48-mesh screen, a slight taper from dia 2.55 (y 584) to 2.47 (y 723); drawn black, with the
    # rotating scanner showing white through it. Light rims at both ends (y 584-590, 717-723).
    r0, r1 = cm(880 - 707) / 2, cm(2.47 * PPC) / 2
    kit.revolve('(C) scanner housing (48 mesh screen)', [(r1, z(723)), (r0, z(584))], 'screen48', axis='Z', parent=root)
    kit.revolve('(C) screen rim (upper)', [(r0 - .06, z(590)), (r0 + .005, z(590)), (r0 + .005, z(584)), (r0 - .06, z(584))], 'antimony', axis='Z', parent=root)
    kit.revolve('(C) screen rim (lower)', [(r1 - .06, z(723)), (r1 + .005, z(723)), (r1 + .005, z(717)), (r1 - .06, z(717))], 'antimony', axis='Z', parent=root)
    kit.cyl('scanner cavity floor', r0 - .04, .02, (0, 0, z(590) - .01), 'black', 'Z', parent=root)
    # (D) rotating scanner inside the screen: a dark hub carrying two twisted white vanes (a 100° twist over the height;
    # drawn as the broad white band twisting across the centre and the narrower one at the left) and the domed lens
    zd0, zd1 = z(717), z(590)
    kit.cyl('(D) rotating scanner hub', .3, zd1 - zd0, (0, 0, (zd0 + zd1) / 2), 'white', 'Z', parent=root)   # plate: white down the centre
    def vane(name, th0, twist, ri, ro, t=.035, nz=24, nr=4):
        bm = bmesh.new(); grid = []
        for i in range(nz + 1):
            zz = zd0 + (zd1 - zd0) * i / nz; th = th0 + twist * (zz - zd0) / (zd1 - zd0)
            c, s_ = math.cos(th), math.sin(th); n = (-s_, c)
            row = []
            for j in range(nr + 1):
                rr = ri + (ro - ri) * j / nr
                row.append([bm.verts.new((rr * c + sg * t / 2 * n[0], rr * s_ + sg * t / 2 * n[1], zz)) for sg in (-1, 1)])
            grid.append(row)
        for i in range(nz):
            for j in range(nr):
                for sg in (0, 1):
                    q = (grid[i][j][sg], grid[i][j + 1][sg], grid[i + 1][j + 1][sg], grid[i + 1][j][sg])
                    bm.faces.new(q if sg else q[::-1])
            for j in (0, nr):                      # inner / outer edges
                q = (grid[i][j][0], grid[i][j][1], grid[i + 1][j][1], grid[i + 1][j][0]); bm.faces.new(q if j else q[::-1])
        for i in (0, nz):                          # top / bottom edges
            for j in range(nr):
                bm.faces.new((grid[i][j][0], grid[i][j + 1][0], grid[i][j + 1][1], grid[i][j][1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        return kit.smooth(kit._obj(name, me, 'white', root), 50)
    for k in range(2):
        vane('(D) rotating scanner vane', math.radians(-55 + 180 * k), math.radians(100), .28, r1 - .1)
    lx = cm(752 - AX); ly = -math.sqrt(max((r1 - .25) ** 2 - lx ** 2, 0))
    # domed lens drawn in profile: a "D" whose flat back sits on a black collar and whose dome bulges toward +X
    rl = cm(22); n = 12
    dome = [(rl * math.cos(math.pi / 2 * i / n), lx + rl * math.sin(math.pi / 2 * i / n)) for i in range(n + 1)]
    kit.revolve('(D) rotating scanner lens', [(0.0, lx)] + dome, 'white', axis='X', seg=48, parent=root, loc=(0, ly, z(656)))
    kit.cyl('(D) lens collar', cm(24), .08, (lx - .04, ly, z(656)), 'black', 'X', parent=root)
    kit.box('(D) lens arm', (.12, abs(ly) - .15, .3), (lx / 2, ly / 2, z(656)), 'black', rot=(0, 0, math.atan2(lx, -ly)), parent=root)
    # flange at the scanner end (y 723-737.5, dia 2.57)
    RF = cm(882 - 706) / 2
    kit.cyl('flange', RF, z(723), (0, 0, z(723) / 2), 'antimony', 'Z', bev=.01, parent=root)
    # (G) ground plane screen, 48 mesh (bottom view: dia 2.10, hub dia 0.41)
    kit.cyl('(G) ground plane screen (48 mesh)', cm(72), .02, (0, 0, .006), 'black', 'Z', parent=root)
    kit.cyl('screen hub', cm(14), .03, (0, 0, .0), 'antimony', 'Z', parent=root)
    kit.torus('screen rim', cm(72), .012, (0, 0, .0), 'black', 'Z', parent=root)
    # (E) readings dial on the top face (view centre 1094,447): bezel dia 2.73, window dia 2.54, six bar gauges
    zt0 = zt
    kit.cyl('(E) dial bezel', cm(94), .04, (0, 0, zt0 - .01), 'antimony', 'Z', parent=root)
    kit.cyl('(E) readings dial face', cm(87), .05, (0, 0, zt0 - .02), 'white', 'Z', parent=root)
    X = lambda px: -cm(px - 1094); Y = lambda py: cm(py - 447)          # dial view turned back 180° (ROT 180° CW)
    readings = {'A': (1041, 431, 447, -1), 'B': (1062, 436, 455, -1), 'Γ': (1081, 436, 457, -1), 'K': (1104, 412, 445, 1),
                'Θ': (1124, 423, 440, 1), 'Ξ': (1143.5, 425, 460, 1)}
    for g, (px, y0, y1, side) in readings.items():
        kit.box(f'gauge slot {g}', (cm(8), cm(500 - 385), .01), (X(px), Y(442.5), zt0 + .006), 'dark', parent=root)
        kit.box(f'gauge slot {g} bore', (cm(4), cm(500 - 389), .012), (X(px), Y(442.5), zt0 + .007), 'white', parent=root)
        kit.box(f'reading {g}', (cm(4), cm(y1 - y0), .012), (X(px + side * 6), Y((y0 + y1) / 2), zt0 + .008), 'black', parent=root)
    # (H) NT normal Terran range marks, on the horizontal centre line at left and right of the gauges
    kit.box('(H) NT mark', (cm(10), cm(2.5), .01), (X(1027), Y(447), zt0 + .008), 'black', parent=root)
    kit.box('(H) NT mark', (cm(10), cm(2.5), .01), (X(1160), Y(447), zt0 + .008), 'black', parent=root)
    kit.box('NT range line', (cm(140), cm(1.2), .008), (X(1094), Y(447), zt0 + .007), 'dark', parent=root)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('medical-scanner')
