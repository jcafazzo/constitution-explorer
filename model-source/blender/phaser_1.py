"""Hand Phaser Type I — PDF 103, TO 01:08:50.  Run: Blender -b -P model-source/blender/phaser_1.py
Printed: L.O.A. 107.20 mm, W.O.A. 49.40 mm, D.O.A. 27.00 mm. Colours: br. antimony SF02UC, gloss black SF32UC.
Body: lofted from the top-view (plan) and side-view silhouettes measured on the plate (68.37 px/cm).
Details: positions read on the plate in px and converted with the profiles' origins."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit

PPC = 68.37
TOP_O = (393.0, 522)   # plan-view origin (mid-line x, first silhouette row y) in plate px
SIDE_O = (732.0, 522)  # side-view origin
L_DRAWN = 10.575       # plan silhouette length incl. emitter cap (printed L.O.A. 10.72)
SCALE_L = 10.72 / L_DRAWN

def build(parent=None, origin=(0, 0, 0), name='Hand Phaser Type I'):
    """Returns the root empty. origin = position of the body's geometric centre; front is −Y."""
    root = kit.group(name, parent); root.location = origin; root.scale = (1, SCALE_L, 1)
    plan = kit.load_profile('phaser-1-top'); side = kit.load_profile('phaser-1-side')
    y0 = -L_DRAWN / 2
    # Side-view silhouette is measured about its own mid-line; the body's z centre sits there too.
    body = kit.loft_from_profiles('body shell', plan, side, 0.24, L_DRAWN - .01, 'black', n=110, p=2.8, side_flip=True, y0=y0, median=6, parent=root)
    y = lambda py: y0 + (py - TOP_O[1]) / PPC          # plan px → y (cm)
    x = lambda px: -(px - TOP_O[0]) / PPC               # plan px → x (cm); image-left is +X
    zs = lambda px: -(px - SIDE_O[0]) / PPC             # side px → z (left of side view = top)
    ztop = lambda py: -kit.sample(side, (py - SIDE_O[1]) / PPC, 6)[0]
    # Emitter cap and 1.02 MeV photon emitter at the front.
    kit.box('emitter housing', (1.38, .32, 1.0), (x(411), y(529), zs(735)), 'antimony', bev=.06, parent=root)
    kit.box('face plate', (1.9, .06, 1.3), (0, y(537), -.02), 'antimony', bev=.03, parent=root)
    kit.cyl('1.02 MeV photon emitter', .38, .1, (0, y(522) - .02, -.02), 'antimony', 'Y', parent=root)
    kit.cyl('emitter lens', .24, .05, (0, y(522) - .08, -.02), 'glass', 'Y', parent=root)
    kit.box('sight', (.5, .3, .25), (x(458), y(525), zs(716)), 'antimony', bev=.03, parent=root)
    # Top surface: electron aspirator pile (white field with a zig-zag lattice), trigger, force wheel, light, dial.
    px0, px1, py0, py1 = 308, 482, 590, 800
    # The pile is a thin plate that follows the crowned top (ray-cast onto the shell), so the shell never shows through it.
    import bpy, bmesh
    from mathutils import Vector
    bpy.context.view_layer.update()
    def top_at(xx, yy):
        hit, loc, *_ = body.ray_cast(Vector((xx, yy, 10.0)), Vector((0, 0, -1)))
        return loc.z if hit else ztop((yy - y0) * PPC + TOP_O[1])
    nx, ny = 14, 18; X0, X1, Y0, Y1 = x(px1), x(px0), y(py0), y(py1)
    grid = [[(X0 + (X1 - X0) * i / nx, Y0 + (Y1 - Y0) * j / ny) for i in range(nx + 1)] for j in range(ny + 1)]
    H = [[top_at(*g) for g in row] for row in grid]
    bm = bmesh.new()
    top = [[bm.verts.new((g[0], g[1], H[j][i] + .05)) for i, g in enumerate(row)] for j, row in enumerate(grid)]
    bot = [[bm.verts.new((g[0], g[1], H[j][i] - .02)) for i, g in enumerate(row)] for j, row in enumerate(grid)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
    rim = [top[0][i] for i in range(nx + 1)] + [top[j][nx] for j in range(1, ny + 1)] + [top[ny][i] for i in range(nx - 1, -1, -1)] + [top[j][0] for j in range(ny - 1, 0, -1)]
    rimb = [bot[0][i] for i in range(nx + 1)] + [bot[j][nx] for j in range(1, ny + 1)] + [bot[ny][i] for i in range(nx - 1, -1, -1)] + [bot[j][0] for j in range(ny - 1, 0, -1)]
    for k in range(len(rim)):
        bm.faces.new((rim[k], rimb[k], rimb[(k + 1) % len(rim)], rim[(k + 1) % len(rim)]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('electron aspirator pile'); bm.to_mesh(me); bm.free()
    kit.smooth(kit._obj('electron aspirator pile', me, 'antimony', root), 40)
    # lattice: the drawn X / zig-zag hatch over the whole field, each bar seated on the pile's own top surface
    cx_n, cy_n = 6, 8; dx = (X1 - X0) / cx_n; dy = (Y1 - Y0) / cy_n
    for r_ in range(cy_n):
        for c_ in range(cx_n):
            cx = X0 + dx * (c_ + .5); cy = Y0 + dy * (r_ + .5); zz = top_at(cx, cy) + .065
            for k in (-1, 1):
                kit.box('pile lattice', (math.hypot(dx, dy) * .9, .03, .03), (cx, cy, zz), 'dark', rot=(0, 0, k * math.atan2(dy, dx)), parent=root)
    kit.box('trigger', (x(482) - x(307), y(850) - y(803), .14), (x(395), y(826), ztop(826) + .02), 'antimony', bev=.05, parent=root)
    kit.box('trigger frame', (x(486) - x(303), y(855) - y(798), .06), (x(395), y(826), ztop(826) - .01), 'dark', bev=.03, parent=root)
    # Force setting wheel: a ribbed thumbwheel across X whose rim rises above the top as the side view's semicircle.
    wr = (1025 - 915) / PPC / 2; wy = y(970); wz = ztop(970) + (655 - 630) / PPC - wr
    kit.cyl('force setting wheel', wr, x(297) - x(325), (x(311), wy, wz), 'dark', 'X', seg=48, parent=root)
    for i in range(36):
        a = 2 * math.pi * i / 36
        kit.box('wheel rib', (x(297) - x(325) - .02, .05, .06), (x(311), wy + math.sin(a) * wr, wz + math.cos(a) * wr), 'black', rot=(-a, 0, 0), parent=root)
    kit.cyl('operational light (blue)', .14, .1, (x(367), y(970), ztop(970) + .02), 'blue', 'Z', parent=root)
    kit.torus('light bezel', .18, .03, (x(367), y(970), ztop(970) + .04), 'antimony', 'Z', parent=root)
    dz = ztop(972)
    kit.box('force indicator dial', (x(410) - x(478), y(1050) - y(893), .06), (x(444), y(972), dz + .01), 'antimony', parent=root)
    for i, py in enumerate((903, 925, 948, 972, 996, 1019, 1041)):
        kit.box('dial graduation', (.3 if i != 3 else .4, .03, .02), (x(450), y(py), dz + .05), 'black', parent=root)
    # Sides: deflector shield — one continuous antimony rail standing proud of the body (front view), z from the side view.
    half = lambda py: kit.sample(plan, (py - TOP_O[1]) / PPC, 6)
    zr = zs(718)
    for sgn in (-1, 1):
        secs = []
        for py in range(545, 1212, 8):
            lo, hi = half(py); xe = (-lo if sgn > 0 else -hi)
            secs.append((y(py), xe - .07 if sgn > 0 else xe - .04, xe + .04 if sgn > 0 else xe + .07, zr - .09, zr + .09))
        kit.loft('deflector shield', secs, 'antimony', p=2.2, seg=20, parent=root)
    # Bottom: access plate seam (rear panel from row ~728), magnatomic adhesion area following the curved bottom, Phillips screw.
    zb = lambda py: -kit.sample(side, (py - SIDE_O[1]) / PPC, 6)[1]
    lo, hi = half(728)
    kit.box('access plate seam', ((hi - lo) * .5, .05, .03), (0, y(728), zb(728) + .012), 'dark', parent=root)
    secs = []
    for i in range(25):
        u = -1 + 2 * i / 24; py = 938 + u * 87.5
        hw = 1.28 * max(1 - abs(u) ** 6, 1e-3) ** (1 / 6)
        secs.append((y(py), -hw, hw, zb(py) - .02, zb(py) + .03))
    kit.loft('magnatomic adhesion area', secs, 'dark', p=6, seg=32, parent=root)
    kit.cyl('access plate screw', .17, .05, (0, y(1148), zb(1148) - .01), 'antimony', 'Z', parent=root)
    for r in (0, math.pi / 2):
        kit.box('screw slot', (.24, .04, .03), (0, y(1148), zb(1148) - .03), 'dark', rot=(0, 0, r), parent=root)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('phaser-1')
