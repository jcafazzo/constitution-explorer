"""Heartbeat Reader — PDF 127, TO 02:11:04 (SFAF/SG-MK06 Type M).  Run: Blender -b -P model-source/blender/heartbeat_reader.py [-- --variant base --out DIR]
Printed: length overall 17.75 cm, maximum diameter 5.2 cm, 230 gm. Colours: antimony SF02UC, black SF32UC, blue + red L.E.D.s.
Upright: Z = length (base at z = 0), front elevation seen from -Y, image-right = +X.
Turned parts are revolved from the front-elevation silhouette (profiles/heartbeat-reader-front.json, 67.88 px/cm);
details are placed from plate pixel coordinates. The drawing measures 17.96 cm overall (printed 17.75, +1.2%) and the
clamp band 5.27 cm (printed 5.2); the model follows the drawing.
--variant base exports only the base (drum + side tabs) for scoring the END VIEW, which the sheet draws as a partial view."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit

PPC = 67.88
MID_X = 810.5           # centre-line of the front elevation (px)
BOTTOM_Y = 1551         # base bottom (px)
x = lambda px: (px - MID_X) / PPC
z = lambda py: (BOTTOM_Y - py) / PPC

def rows_r(prof, py0, py1):
    """[(radius, z)] from the measured silhouette between plate rows py0..py1 (half the drawn width)."""
    oy = prof['origin_px'][1]; out = []
    for s, lo, hi in prof['rows']:
        py = oy + s * PPC
        if py0 <= py <= py1: out.append(((hi - lo) / 2, z(py)))
    return out

def body_r(prof, py):
    return BODY_R(z(py))
BODY_R = None

def build(variant='full'):
    prof = kit.load_profile('heartbeat-reader-front')
    root = kit.group('Heartbeat Reader')
    # ---- base: centre drum carrying the solo/multiple reading selector and volume control; flat side tabs ----
    kit.revolve('base drum (reading selector / volume control)', [(0, z(1548)), (1.04, z(1548)), (1.085, z(1545)), (1.085, z(1450)), (0.99, z(1446)), (0, z(1446))], 'white', axis='Z', parent=root)
    # side tabs: 4.22 cm tip to tip x 1.18 cm (front elevation, x 662-950 outside the lines), 0.57 cm thick (END VIEW, y 1296-1335),
    # rounded corners. The base is drawn about x 806 (drum 734-878, tabs 662-950), so the tabs are centred on the axis.
    tw, th, tt, rc = (950 - 662) / PPC - .02, z(1457) - z(1537), 39 / PPC, 10 / PPC
    pts = []
    for cx, cz, a0 in ((tw / 2 - rc, th / 2 - rc, 0), (-tw / 2 + rc, th / 2 - rc, 90), (-tw / 2 + rc, -th / 2 + rc, 180), (tw / 2 - rc, -th / 2 + rc, 270)):
        for k in range(7):
            a = math.radians(a0 + k * 15); pts.append((cx + rc * math.cos(a), cz + rc * math.sin(a)))
    kit.extrude('side tabs', pts, tt, 'white', plane='XZ', loc=(0, 0, (z(1457) + z(1537)) / 2), parent=root)
    if variant == 'base':
        return root
    # scales on the drum front: SAMPLE (S..M, upper, index pointer above) and VOL (0..10, lower, pointer below)
    R = 1.09
    def on_drum(name, px, py, size, mat):
        a = math.asin(max(-1, min(1, x(px) / R)))
        kit.box(name, size, (R * math.sin(a), -R * math.cos(a), z(py)), mat, rot=(0, 0, a), parent=root)
    for i in range(11):
        px = 772 + i * 6.7; on_drum('SAMPLE scale tick', px, 1465, (.025, .03, .12 if i % 5 == 0 else .07), 'black')
        on_drum('VOL scale tick', px, 1537, (.025, .03, .12 if i % 5 == 0 else .07), 'black')
    on_drum('selector index (S..M)', 768, 1458, (.1, .03, .08), 'black')
    on_drum('volume index (0..10)', 768, 1541, (.1, .03, .08), 'black')
    for py in (1491, 1505): on_drum('legend line', 800, py, (.5, .02, .05), 'black')
    # ---- body shell: tapering tube revolved from the silhouette (y 638..1447) ----
    # rebuild cleanly: bottom centre, outline bottom->top, top centre
    # the shell is drawn with straight sides: least-squares line through the measured half-widths (removes pixel jitter)
    meas = rows_r(prof, 650, 1440); n_ = len(meas)
    mz = sum(p[1] for p in meas) / n_; mr = sum(p[0] for p in meas) / n_
    b_ = sum((p[1] - mz) * (p[0] - mr) for p in meas) / sum((p[1] - mz) ** 2 for p in meas)
    rz = lambda zz: mr + b_ * (zz - mz)
    global BODY_R; BODY_R = rz
    print('body shell diameter top %.3f bottom %.3f cm' % (2 * rz(z(641)), 2 * rz(z(1446))))
    pts = [(0, z(1446)), (rz(z(1446)), z(1446))] + [(rz(z(641)), z(641)), (1.17, z(638)), (0, z(638))]
    kit.revolve('body shell', pts, 'white', axis='Z', parent=root)
    kit.torus('body collar line', 1.175, .025, (0, 0, z(648)), 'grey', axis='Z', parent=root)
    # ---- head: spherical guard (upper) and ground-plane (lower) screens, clamp band, omnidirectional sensor ----
    head = rows_r(prof, 333, 637)
    # under the clamp band the sphere outline is hidden: fit the sphere from rows just outside the band
    cz = (z(474) + z(516)) / 2; rr = sum(r for r, zz in head if abs(zz - z(470)) < .05 or abs(zz - z(520)) < .05) / max(1, sum(1 for r, zz in head if abs(zz - z(470)) < .05 or abs(zz - z(520)) < .05))
    rr = math.sqrt(rr ** 2 + ((z(470) - z(520)) / 2) ** 2)
    sph = [(r, zz) for r, zz in head if not (z(516) < zz < z(474))]
    sph += [(math.sqrt(max(rr ** 2 - (zz - cz) ** 2, 0)), zz) for zz in [z(516) + k * (z(474) - z(516)) / 10 for k in range(1, 10)]]
    sph = sorted(sph, key=lambda p: p[1])[::3]
    top = max(zz for r, zz in sph)
    outline = [(0, sph[0][1])] + sph + [(0, top + .001)]
    # Screens: a light antimony sphere under a fine woven wire mesh (the plate stipples ~1.5 mm cells over the whole head).
    # The mesh is a geodesic (icosphere, 4 subdivisions: ~1.6 mm cells, no poles) wire grid; every vertex is pushed out
    # radially from the sphere centre onto the measured silhouette, so the head follows the drawn outline.
    import bpy, bmesh
    pol = sorted((math.atan2(zz - cz, r), math.hypot(r, zz - cz)) for r, zz in sph if r > .02)
    def rho(phi):              # silhouette distance from the head centre at elevation angle phi
        if phi <= pol[0][0]: return rr
        if phi >= pol[-1][0]: return pol[-1][1]
        for (a0, r0), (a1, r1) in zip(pol, pol[1:]):
            if a0 <= phi <= a1: return r0 + (r1 - r0) * (phi - a0) / max(a1 - a0, 1e-9)
    def geo(name, inset, material):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
        for v in bm.verts:
            d = v.co.normalized(); phi = math.asin(max(-1, min(1, d.z)))
            v.co = d * (rho(phi) - inset); v.co.z += cz
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        return kit._obj(name, me, material, root)
    kit.smooth(geo('omnidirectional sensor screens (antimony)', .03, 'antimony'), 60)
    wire = geo('screen wire mesh (woven)', .006, 'grey')
    m = wire.modifiers.new('wire', 'WIREFRAME'); m.thickness = .022; m.offset = 0; m.use_even_offset = True; m.use_replace = True
    bpy.context.view_layer.objects.active = wire; bpy.ops.object.modifier_apply(modifier='wire')
    for f in wire.data.polygons: f.use_smooth = True
    # clamp band (y 476..513, 5.27 cm across): a flat, square-edged band
    Rb = 357 / 2 / PPC
    kit.revolve('clamp band', [(0, z(513)), (Rb, z(513)), (Rb, z(476)), (0, z(476))], 'white', axis='Z', parent=root)
    kit.sphere('omnidirectional sensor', .32, (0, 0, cz), 'grey', parent=root)
    # ---- front face (-Y): indicators, readout, slide switches ----
    def front(py, px=MID_X): return -math.sqrt(max(body_r(prof, py) ** 2 - x(px) ** 2, 0))
    # multiple reading cancel indicator (light stipple = blue in the key), unit go indicator (dense stipple = red)
    for py, mat, n in ((722, 'blue', 'multiple reading cancel indicator (L.E.D.)'), (800, 'red', 'unit go indicator (L.E.D.)')):
        kit.cyl(n, 8 / PPC, .1, (x(783), front(py, 783) - .01, z(py)), mat, 'Y', parent=root)
        kit.torus(n + ' bezel', 9 / PPC, .018, (x(783), front(py, 783) - .03, z(py)), 'black', axis='Y', parent=root)
    # digital readout with floating decimal: outlined surround x 798-840, y 715-810; window x 805-830, y 722-800 holding four
    # seven-segment figures drawn as outlined 8s, turned to read along the body (each cell ~20 x 19 px)
    yb = front(762, 820)
    kit.box('digital readout surround', (x(840) - x(798), .12, z(715) - z(810)), (x(819), yb - .02, z(762.5)), 'white', parent=root)
    kit.box('digital readout surround outline', (x(841) - x(797), .1, z(714) - z(811)), (x(819), yb - .005, z(762.5)), 'black', parent=root)
    kit.box('digital readout window', (x(830) - x(805), .04, z(722) - z(800)), (x(817.5), yb - .09, z(761)), 'screen', parent=root)
    U, V, T = (x(827) - x(809)) / 2, (z(0) - z(15)) / 2, .02          # half length (across the window), half height, bar
    yd = yb - .112
    for i in range(4):
        uc, zc = x(818), z(731.5 + i * 19.5)
        for du in (-U, 0, U):                                          # the three bars across the figure
            kit.box('readout segment', (T, .02, 2 * V), (uc + du, yd, zc), 'red', parent=root)
        for du in (-U / 2, U / 2):                                     # the four bars along it
            for dv in (-V, V):
                kit.box('readout segment', (U - T, .02, T), (uc + du, yd, zc + dv), 'red', parent=root)
    for i in range(3):  # "BPM" legend, printed vertically left of the window
        kit.box('BPM legend', (.1, .01, .08), (x(795), front(748 + i * 13, 795) - .005, z(748 + i * 13)), 'black', parent=root)
    # slide switches ACTIVATE (y 830-866) and AUDIBLE (y 885-920): ribbed black boss 0.28 cm proud (SECTION), OFF end at right
    for (py0, py1), n in (((830, 866), 'activate'), ((885, 920), 'audible')):
        pc = (py0 + py1) / 2; yb = front(pc, 809)
        kit.box(f'slide switch boss ({n})', (x(848) - x(770), .3, z(py0) - z(py1)), (x(809), yb - .1, z(pc)), 'black', bev=.02, parent=root)
        for i in range(10):
            kit.box(f'slide switch rib ({n})', (.025, .05, z(py0) - z(py1) - .1), (x(773 + i * 6), yb - .27, z(pc)), 'dark', parent=root)
        kit.box(f'slide switch OFF plate ({n})', (x(847) - x(832), .04, z(py0) - z(py1) - .08), (x(839.5), yb - .26, z(pc)), 'white', parent=root)
        kit.box(f'slide switch legend ({n})', (x(848) - x(770), .01, .07), (x(809), front(py1 + 10, 809) - .005, z(py1 + 10)), 'black', parent=root)
    return root

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    variant = argv[argv.index('--variant') + 1] if '--variant' in argv else 'full'
    out = argv[argv.index('--out') + 1] if '--out' in argv else None
    kit.reset(); build(variant)
    kit.export('heartbeat-reader' if variant == 'full' else 'heartbeat-reader-' + variant, out)
