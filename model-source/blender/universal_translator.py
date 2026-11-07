"""Universal Translator SFAF/CC-MK-01, Type I — PDF 139, TO 03:02:04.  Run: Blender -b -P model-source/blender/universal_translator.py
Printed: length overall 28 cm, maximum diameter 4.8 cm, 500 g; activating switch at 45 deg. Colours: antimony SF02UC, black SF32UC.
Plate 43.80 px/cm. TOP PLAN (x 1117-1283, centre 1200, tip row 325) looks at the display D / speaker F (+Z);
SIDE PROFILE (x 735-902, centre 818.5, tip row 328) is seen from +X so the display strip is edge-on at its right (+Z).
The activating switch shows in both (plan left = +X, side right = +Z), i.e. 45 deg between the display and the +X side.
All stations below are TOP PLAN rows (side rows are 3 px lower); diameters agree on both views to 0.05 cm.
Surface details (review fixes): A is a fully packed light honeycomb in a black frame (FRONT ELEVATION); the B grilles and the
operator's speaker F are light panels carrying a dark cross-hatch / maze; the transparent cover J is clear and colourless so D's
white and stippled ('grey') cells in the black grid read as drawn; the "ON" legend under G follows the TOP PLAN.
Profiles: profiles/universal-translator-plan.json, -side.json (extract_profile.py 139 <crop> 43.80 --step 1)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh, random
from mathutils import Matrix, Vector

PPC = 43.80
TIP = 325                   # plan row of the tip (sensor cap's forward edge)
L = (1556 - 325) / PPC      # drawn length 28.1 cm (printed 28)
Y0 = -L / 2
y = lambda py: Y0 + (py - TIP) / PPC                # plan row -> y (front = -Y)
xp = lambda px: -(px - 1200) / PPC                   # plan column -> x (image left = +X)
zs = lambda px: (px - 818.5) / PPC                   # side column -> z (image right = +Z)
ys = lambda py: y(py - 3)                            # side row -> y
R = 3.79 / 2                                         # housing radius

def lathe(name, stations, material, parent=None):
    """stations: [(plan_row, diameter_cm), ...] front to back; closed at both ends."""
    pts = [(0.0, y(stations[0][0]))] + [(d / 2, y(py)) for py, d in stations] + [(0.0, y(stations[-1][0]))]
    return kit.revolve(name, pts, material, 'Y', seg=96, parent=parent)

def knurl(name, r_core, r_out, py0, py1, n, core_mat, rib_mat, parent=None):
    g = kit.group(name, parent)
    lathe(name + ' core', [(py0, 2 * r_core), (py1, 2 * r_core)], core_mat, g)
    w = 2 * math.pi * r_out / n * .5
    for i in range(n):
        a = 2 * math.pi * i / n; rm = (r_core + r_out) / 2
        kit.box(name + ' rib', (w, (py1 - py0) / PPC - .04, r_out - r_core), (rm * math.sin(a), (y(py0) + y(py1)) / 2, rm * math.cos(a)), rib_mat, rot=(0, a, 0), parent=g)
    return g

def arc_slab(name, r0, r1, half_w, py0, py1, material, parent=None, n=24):
    """Curved slab on +Z between radii r0..r1, spanning |x| <= half_w (measured at r1), rows py0..py1."""
    th = math.asin(min(half_w / r1, 1)); bm = bmesh.new(); rings = []
    for yy in (y(py0), y(py1)):
        ring = []
        for r in (r0, r1):
            ring.append([bm.verts.new((r * math.sin(-th + 2 * th * i / n), yy, r * math.cos(-th + 2 * th * i / n))) for i in range(n + 1)])
        rings.append(ring)
    (a0, a1), (b0, b1) = rings
    for i in range(n):
        bm.faces.new((a1[i], a1[i + 1], b1[i + 1], b1[i])); bm.faces.new((a0[i], b0[i], b0[i + 1], a0[i + 1]))
        bm.faces.new((a0[i], a0[i + 1], a1[i + 1], a1[i])); bm.faces.new((b0[i], b1[i], b1[i + 1], b0[i + 1]))
    for k in (0, n):
        bm.faces.new((a0[k], a1[k], b1[k], b0[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), 30)

def cut(obj, cutter):
    m = obj.modifiers.new('cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_move_to_index(modifier='cut', index=0)
    bpy.ops.object.modifier_apply(modifier='cut')
    bpy.data.objects.remove(cutter, do_unlink=True)

def bm_box(bm, centre, size, roty=0.0):
    """Add a closed box to a bmesh (centre, size in cm; rotated about the Y axis by roty)."""
    m = Matrix.Translation(centre) @ Matrix.Rotation(roty, 4, 'Y') @ Matrix.Diagonal((*size, 1))
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)

def mesh_obj(name, bm, material, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit._obj(name, me, material, parent)

def intersect(obj, keeper):
    """Keep only the part of obj inside keeper (exact Boolean, applied); keeper is deleted."""
    m = obj.modifiers.new('clip', 'BOOLEAN'); m.operation = 'INTERSECT'; m.object = keeper; m.solver = 'EXACT'; m.use_self = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='clip')
    bpy.data.objects.remove(keeper, do_unlink=True)

def maze_walls(nc, nr, seed):
    """Interior walls of a perfect maze on an nc x nr grid (randomised depth-first search), as
    ('v', i, j) = wall on the line x = i between rows j..j+1, ('h', i, j) = wall on the line y = j between columns i..i+1."""
    rnd = random.Random(seed); seen = {(0, 0)}; stack = [(0, 0)]; opened = set()
    while stack:
        i, j = stack[-1]
        nb = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i + di < nc and 0 <= j + dj < nr and (i + di, j + dj) not in seen]
        if not nb: stack.pop(); continue
        a = rnd.choice(nb); opened.add(frozenset(((i, j), a))); seen.add(a); stack.append(a)
    walls = [('v', i, j) for i in range(1, nc) for j in range(nr) if frozenset(((i - 1, j), (i, j))) not in opened]
    walls += [('h', i, j) for i in range(nc) for j in range(1, nr) if frozenset(((i, j - 1), (i, j))) not in opened]
    return walls

def build():
    # ---- head: upper cap, collars, decoding/encoding ring C, step collar (diameters from both views) ----
    lathe('Upper cap', [(410, 3.56), (412, 3.70), (415, 3.79), (472.5, 3.79), (472.5, 4.60), (474.5, 4.63), (496, 4.63)], 'antimony')
    knurl('Decoding/encoding section (C)', 2.37, 2.43, 495, 549, 120, 'dark', 'antimony')
    for py0, py1 in ((495, 497.5), (546.5, 549)):   # rounded ring edges
        lathe('ring edge', [(py0, 4.80), (py1, 4.80)], 'antimony')
    lathe('Lower collar', [(548, 4.65), (569, 4.65), (569, 4.27), (588, 4.25), (591, 4.08), (593.5, 3.79)], 'antimony')
    # ---- housing L: primary computer section E, mid joint (grooves 996-1004 & 1028-1033), data storage banks H ----
    E = lathe('Housing (L): primary computer section (E)', [(593, 3.79), (996.5, 3.79)], 'antimony')
    lathe('Mid joint', [(996, 3.72), (997.5, 3.47), (1003, 3.47), (1004.5, 3.81), (1027.5, 3.81), (1028.5, 3.74), (1032.5, 3.74), (1033.5, 3.79)], 'antimony')
    H = lathe('Housing (L): data storage banks section (H)', [(1033, 3.79), (1531.5, 3.79)], 'antimony')
    knurl('Rear cover (K)', 1.96, 2.02, 1531, 1550, 90, 'black', 'black')
    lathe('rear cover end', [(1549, 3.97), (1552, 3.88), (1555.5, 3.40)], 'black')

    # ---- (A) speech characteristics sensors: block with an 18 deg slanted face capped by a black honeycomb slab ----
    zl, zr = zs(749), zs(885)                        # side view extent of the block (-Z .. +Z)
    A = kit.group('Speech characteristics sensors (A)')
    kit.extrude('sensor block', [(ys(345), zl), (ys(390), zr), (y(411), zr), (y(411), zl)], xp(1168) - xp(1232), 'antimony', plane='YZ', parent=A)
    kit.extrude('sensor cap', [(ys(328), zl), (ys(372), zr), (ys(390), zr), (ys(345), zl)], xp(1165) - xp(1236), 'black', plane='YZ', parent=A)
    p1, p2 = (ys(328), zl), (ys(372), zr); dy, dz = p2[0] - p1[0], p2[1] - p1[1]; ln = math.hypot(dy, dz)
    n = (-dz / ln, dy / ln)                          # outward normal of the slanted face (towards -Y, +Z)
    # fully packed honeycomb as drawn (FRONT ELEVATION: ~12 rows of 4-5 light cells in a thin black web inside a black frame
    # 0.11 cm wide): light hex cells on the black cap, clipped to the frame opening so the edge cells are cut, as on the plate
    vy, vz = dy / ln, dz / ln
    M = Matrix(((1, 0, 0, 0), (0, vy, n[0], p1[0]), (0, vz, n[1], p1[1]), (0, 0, 0, 1)))   # local (u, v, w) -> world
    pitch, web = .30, .035; ap = pitch / 2 - web / 2; rh = ap / math.cos(math.pi / 6); rp = pitch * math.sqrt(3) / 2
    bm = bmesh.new(); hu = (xp(1165) - xp(1236)) / 2 - .11
    for j in range(-1, int(ln / rp) + 2):
        for i in range(-4, 5):
            cu, cv = (i + (.5 if j % 2 else 0)) * pitch, .11 + j * rp
            ring0 = [bm.verts.new((cu + rh * math.cos(math.radians(90 + 60 * k)), cv + rh * math.sin(math.radians(90 + 60 * k)), 0)) for k in range(6)]
            ring1 = [bm.verts.new((v.co.x, v.co.y, .03)) for v in ring0]
            bm.faces.new(ring0[::-1]); bm.faces.new(ring1)
            for k in range(6): bm.faces.new((ring0[k], ring0[(k + 1) % 6], ring1[(k + 1) % 6], ring1[k]))
    cells = mesh_obj('sensor honeycomb', bm, 'white')
    keep = kit.box('honeycomb opening', (2 * hu, ln - .22, .2), (0, ln / 2, 0), 'white')
    intersect(cells, keep)
    cells.parent = A; cells.matrix_world = M
    # ---- (B) other party speaker/microphone: two half-round grilles on the cap's forward face beside A ----
    for sgn in (1, -1):
        th0 = math.acos(.92 / 1.62); arc = [(sgn * 1.62 * math.cos(a), 1.62 * math.sin(a)) for a in [-th0 + 2 * th0 * k / 24 for k in range(25)]]
        outline = [(sgn * .92, -1.33)] + arc + [(sgn * .92, 1.33)]
        g = kit.extrude('Other party speaker/microphone (B)', outline, .05, 'antimony', plane='XZ', loc=(0, y(410) - .02, 0))
        # light grille with a dark cross-hatch (plate: fine dark lattice on white, ~0.11 cm cells)
        bm = bmesh.new(); yf = y(410) - .045; t, w = .02, .022; ri, xi, zi = 1.58, .95, 1.29   # bars clipped to the inset outline
        for k in range(9, 15):
            xc = sgn * k * .11; ze = min(zi, math.sqrt(max(ri * ri - xc * xc, 0)))
            if ze > .05: bm_box(bm, (xc, yf - t / 2 + .008, 0), (w, t, 2 * ze))
        for k in range(-11, 12):
            zc = k * .11; xe = math.sqrt(max(ri * ri - zc * zc, 0))
            if xe > xi + .05: bm_box(bm, (sgn * (xi + xe) / 2, yf - t / 2 + .008, zc), (xe - xi, t, w))
        mesh_obj('B grille cross-hatch', bm, 'dark')

    # ---- (D) computer functions display + (F) operator's speaker/microphone in a recess on +Z; (J) transparent cover over D ----
    cutter = kit.box('recess cutter', (2 * 1.18, y(963) - y(649), 3), (0, (y(649) + y(963)) / 2, 1.05 + 1.5), 'black')
    cut(E, cutter)
    D = kit.group('Computer functions display panel (D)')
    arc_slab('display base', 1.40, 1.66, 1.18, 651, 814, 'black', D)
    rows = ['xxx.....', '......x.', '.xx.....', '..x.....', '....x...', 'xxxxxxxx', 'xxxxx.x.', '...xx...', '..x.x...', '..xx....', '......x.', 'xx......']
    cx = [1157.5, 1170.5, 1183, 1195.5, 1208.5, 1222, 1235, 1246]; cy = [672, 684.5, 697.5, 710, 723.5, 737, 749, 761.5, 774.5, 787, 800, 810]
    for j, row in enumerate(rows):          # cell pattern sampled from the plate: x = stippled, . = white
        for i, ch in enumerate(row):
            xx = xp(cx[i]); a = math.asin(xx / 1.68)
            kit.box('display cell', (.19, .19, .03), (1.665 * math.sin(a), y(cy[j]), 1.665 * math.cos(a)), 'dark' if ch == 'x' else 'white', rot=(0, a, 0), parent=D)  # inset in a heavy black grid
    # (J) clear, colourless cover so D reads as on the plate (white and stippled cells in a black grid)
    kit.PALETTE.setdefault('clear', ('f4f4f2', .05, 0, .04))
    J = kit.group('Transparent cover (J)')
    kit.box('cover top', (2.14, y(816) - y(649), .06), (0, (y(649) + y(816)) / 2, 1.915), 'clear', parent=J)
    for sgn in (1, -1):
        kit.box('cover side', (.06, y(816) - y(649), .5), (sgn * 1.07, (y(649) + y(816)) / 2, 1.67), 'clear', parent=J)
    # (F) light panel with a dark maze pattern (plate: labyrinth of short dark strokes on white, ~0.11 cm cells, 22 x 30)
    F = arc_slab("Operator's speaker/microphone (F)", 1.62, 1.82, 1.17, 817, 962, 'antimony')
    nc, nr = 22, 30; th = math.asin(1.17 / 1.82); ya, yb_ = y(817), y(962); ch, cw = (yb_ - ya) / nr, 2 * th / nc
    bm = bmesh.new(); rw, hw, wt = 1.83, .022, .03
    for kind, i, j in maze_walls(nc, nr, 139):
        if kind == 'v':     # axial stroke at angle -th + i*cw, rows j..j+1
            a = -th + i * cw; bm_box(bm, (rw * math.sin(a), ya + (j + .5) * ch, rw * math.cos(a)), (hw, ch + hw, wt), a)
        else:               # circumferential stroke on row line j, columns i..i+1
            a = -th + (i + .5) * cw; bm_box(bm, (rw * math.sin(a), ya + j * ch, rw * math.cos(a)), (2 * rw * math.sin(cw / 2) + hw, hw, wt), a)
    mesh_obj('F speaker maze', bm, 'dark', F)
    arc_slab("speaker backing", 1.40, 1.62, 1.18, 816, 963, 'antimony')
    # frame round the recess (plan x 1141-1259, rows 645-967): two side rails and two end rails following the surface
    th0, th1 = math.asin(1.18 / 1.915), math.asin(1.35 / 1.915)
    for sgn in (1, -1):
        o = arc_slab('display frame', 1.86, 1.915, 1.915 * math.sin((th1 - th0) / 2), 645, 967, 'antimony'); o.rotation_euler = (0, sgn * (th0 + th1) / 2, 0)
    for py0, py1 in ((645, 650), (962, 967)):
        arc_slab('display frame', 1.86, 1.915, 1.35, py0, py1, 'antimony')

    # ---- (G) activating switch on a chord flat at 45 deg between +Z (display) and +X ----
    a45 = math.radians(45); d = 1.40; u = (math.sin(a45), 0, math.cos(a45))
    py0, py1 = 1042, 1077
    cutter = kit.box('flat cutter', (3, y(py1) - y(py0) + .1, 2), (u[0] * (d + 1), (y(py0) + y(py1)) / 2, u[2] * (d + 1)), 'black', rot=(0, a45, 0))
    cut(H, cutter)
    G = kit.group('Activating switch (G)')
    at = lambda h: (u[0] * (d + h), (y(py0) + y(py1)) / 2, u[2] * (d + h))
    kit.box('switch frame', (2.3, y(py1) - y(py0), .06), at(.03), 'antimony', rot=(0, a45, 0), bev=.01, parent=G)
    kit.box('switch plate', (2.1, y(py1) - y(py0) - .14, .06), at(.07), 'black', rot=(0, a45, 0), parent=G)
    for sx in (-.82, .82):
        o = kit.cyl('switch lamp', .1, .03, (0, 0, 0), 'white', 'Z', parent=G); o.scale = (.8, 1.3, 1)
        p = at(.1); o.location = (p[0] + sx * math.cos(a45), p[1], p[2] - sx * math.sin(a45)); o.rotation_euler = (0, a45, 0)
    kit.box('switch slider', (.6, .26, .05), at(.12), 'dark', rot=(0, a45, 0), parent=G)
    # legend: TOP PLAN (where G is called out) prints "ON" centred under the switch, 8 px (1.8 mm) cap height at row ~1084.
    # The SIDE PROFILE prints "OFF" at the same place - the two views conflict; the plan is followed.
    cu = bpy.data.curves.new('legend', 'FONT'); cu.body = 'ON'; cu.size = .25; cu.extrude = .02; cu.offset = .004
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    to = bpy.data.objects.new('legend', cu); bpy.context.scene.collection.objects.link(to)
    me = bpy.data.meshes.new_from_object(to.evaluated_get(bpy.context.evaluated_depsgraph_get())); bpy.data.objects.remove(to); bpy.data.curves.remove(cu)
    lo = kit._obj('switch legend "ON"', me, 'black', G)
    tx, ty = Vector((-math.cos(a45), 0, math.sin(a45))), Vector((0, -1, 0)); tn = tx.cross(ty); rl = R + .002
    lo.matrix_world = Matrix((( tx.x, ty.x, tn.x, rl * u[0]), (tx.y, ty.y, tn.y, y(1084)), (tx.z, ty.z, tn.z, rl * u[2]), (0, 0, 0, 1)))

if __name__ == '__main__':
    kit.reset(); build(); kit.export('universal-translator')
