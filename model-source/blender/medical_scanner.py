"""Medical Scanner — PDF 129, TO 02:11:07.  Run: Blender -b -P model-source/blender/medical_scanner.py
Printed: length overall 6.05 cm, maximum diameter 3.5 cm. Colours: antimony SF02UC, gray SF30UC, black SF32UC.
Upright: Z up, computer housing A on top, activating switch B facing the front (-Y). z = 0 at the scanner end (flange).
Read on the plate (68.52 px/cm): elevation axis x 794, rows y 323 (top) .. 737.5 (flange foot) — profile medical-scanner-elev.json;
dial view ("ROT 180° CW") centre (1094, 447); bottom view centre (791, 993)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy

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
    housing = kit.revolve('(A) computer housing', pts, 'grey', axis='Z', parent=root)
    # eight vertical flutes (rounded upper ends at y ~336) milled through the grey finish, antimony floor;
    # their tops break the rounded rim, giving the scallops seen in the dial view. Front flute at -8.4° (stripe x 761-791).
    cutters = []
    for k in range(8):
        a = math.radians(-90 - 8.4 + 45 * k)          # angle from +X; -90° = front (-Y)
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
    kit.box('(B) activating switch (press on-off)', (cm(830 - 793), .05, cm(546 - 480)), (xs, yS - .005, z((480 + 546) / 2)), 'antimony',
            rot=(0, 0, a), bev=.02, parent=root)
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
    # (C) scanner housing: 48-mesh screen, a slight taper from dia 2.55 (y 584) to 2.47 (y 723)
    r0, r1 = cm(880 - 707) / 2, cm(2.47 * PPC) / 2
    kit.revolve('(C) scanner housing (48 mesh screen)', [(0, z(723)), (r1, z(723)), (r0, z(584)), (0, z(584))], 'mesh', axis='Z', parent=root)
    for k in range(5):                                    # the drawn horizontal screen hoops
        t = k / 4; kit.torus('screen hoop', r0 + (r1 - r0) * (.1 + .8 * t) + .002, .008, (0, 0, z(584) - (z(584) - z(723)) * (.1 + .8 * t)), 'dark', 'Z', parent=root)
    # (D) rotating scanner inside the screen: drum with a domed lens (drawn at x 725-765, y 635-680)
    kit.cyl('(D) rotating scanner drum', .62, z(590) - z(718), (0, 0, (z(590) + z(718)) / 2), 'antimony', 'Z', parent=root)
    kit.sphere('(D) rotating scanner lens', cm(22), (cm(745 - AX) * .55, -.55, z(656)), 'glass', scale=(1, .9, 1), parent=root)
    kit.cyl('(D) lens collar', cm(24), .12, (cm(745 - AX) * .55, -.5, z(656)), 'antimony', 'Y', parent=root)
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
    X = lambda px: cm(px - 1094); Y = lambda py: -cm(py - 447)          # dial view: image right = +X, image up = +Y
    readings = {'A': (1041, 431, 447, -1), 'B': (1062, 436, 455, -1), 'Γ': (1081, 436, 457, -1), 'K': (1104, 412, 445, 1),
                'Θ': (1124, 423, 440, 1), 'Ξ': (1143.5, 425, 460, 1)}
    for g, (px, y0, y1, side) in readings.items():
        kit.box(f'gauge slot {g}', (cm(8), cm(500 - 385), .01), (X(px), Y(442.5), zt0 + .006), 'dark', parent=root)
        kit.box(f'gauge slot {g} bore', (cm(4), cm(500 - 389), .012), (X(px), Y(442.5), zt0 + .007), 'white', parent=root)
        kit.box(f'reading {g}', (cm(4), cm(y1 - y0), .012), (X(px) + side * cm(6), Y((y0 + y1) / 2), zt0 + .008), 'black', parent=root)
    # (H) NT normal Terran range marks, on the horizontal centre line at left and right of the gauges
    kit.box('(H) NT mark', (cm(10), cm(2.5), .01), (X(1027), Y(447), zt0 + .008), 'black', parent=root)
    kit.box('(H) NT mark', (cm(10), cm(2.5), .01), (X(1160), Y(447), zt0 + .008), 'black', parent=root)
    kit.box('NT range line', (cm(140), cm(1.2), .008), (X(1094), Y(447), zt0 + .007), 'dark', parent=root)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('medical-scanner')
