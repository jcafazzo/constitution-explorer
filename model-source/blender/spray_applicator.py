"""Spray Applicator SFAF/SG-MK01-70 — PDF 128, TO 02:11:06.  Run: Blender -b -P model-source/blender/spray_applicator.py
Printed: length overall loaded 6.5 cm, maximum diameter 1.9 cm. Colour: antimony SF02UC; vial transparent (colour follows contents).
Upright: Z up, vial C on top, spray trigger B facing the front (-Y). z = 0 at the nozzle end.
Every radius and height below is read on the plate (68.60 px/cm): the assembled elevation (x 799-930, y 324-771, axis x 864.5),
the vial drawn alone (x 1145-1278, y 322-600), the nozzle end view (centre 865,907) and the vial end view (centre 1211,703).
Silhouettes: profiles/spray-applicator-elev.json and -vial.json (extract_profile.py)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bmesh, bpy

PPC = 68.60
TOP_PY, BOT_PY = 324.0, 771.0            # assembled elevation: vial top / nozzle end
L = (BOT_PY - TOP_PY) / PPC              # 6.516 cm (printed 6.5)
z = lambda py: (BOT_PY - py) / PPC       # elevation row → height above the nozzle end
r = lambda px: px / PPC / 2              # drawn diameter in px → radius (cm)

def fluted(name, pts, material, n=40, depth=.02, seg_per=6, parent=None, zr=(None, None)):
    """Revolve (radius, z) points about Z with n rounded flutes cut `depth` deep wherever zr[0] <= z <= zr[1]."""
    bm = bmesh.new(); rings = []; seg = n * seg_per
    for rad, t in pts:
        ring = []
        on = (zr[0] is None or t >= zr[0]) and (zr[1] is None or t <= zr[1])
        for i in range(seg):
            a = 2 * math.pi * i / seg
            cut = depth * (0.5 - 0.5 * math.cos(n * a)) ** 0.6 if on and rad > depth * 2 else 0
            rr = max(rad - cut, 0)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), t)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            a, b = rings[k][i], rings[k][(i + 1) % seg]; c, d = rings[k + 1][(i + 1) % seg], rings[k + 1][i]
            bm.faces.new((a, b, c, d))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return kit.smooth(kit._obj(name, me, material, parent), 30)

def rounded_pts(r0, z0, z1, rc_top=0.0, rc_bot=0.0, n=8):
    """Radius profile of a cylinder r0 from z0 to z1 with quarter-round edges (bottom → top)."""
    pts = []
    for i in range(n + 1):
        a = math.pi / 2 * (1 - i / n); pts.append((r0 - rc_bot + rc_bot * math.cos(a), z0 + rc_bot - rc_bot * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 * i / n; pts.append((r0 - rc_top + rc_top * math.cos(a), z1 - rc_top + rc_top * math.sin(a)))
    return pts

def vial(parent=None, base_z=0.0):
    """Interchangeable vial C, drawn alone at right: fluted barrel 322-555 px, bayonet neck 555-590, teat D to 600.
    base_z = height of the barrel's lower end (where it meets the upper collar band)."""
    g = kit.group('(C) Interchangeable vial', parent)
    zb = lambda py: base_z + (555.0 - py) / PPC           # vial-alone rows, barrel foot at y 555
    R = r(1278 - 1145) - .004                             # 0.966 drawn (crest of the flutes; body is 0.955)
    fluted('vial barrel (fluted, transparent)', rounded_pts(R, zb(555), zb(322.5), rc_top=.11, rc_bot=.03), 'glass', n=40, depth=.025, parent=g,
           zr=(zb(548), zb(332)))
    # bayonet neck (inside the applicator body when assembled) with its two L-shaped lock slots
    kit.revolve('vial neck (bayonet)', rounded_pts(r(1271 - 1153), zb(590), zb(555), rc_bot=.06), 'glass', axis='Z', parent=g)
    for s in (-1, 1):
        x = s * (r(1271 - 1153) + .002)
        kit.box('bayonet slot', (.02, .05, .24), (x, 0, zb(573)), 'dark', parent=g)
        kit.box('bayonet slot', (.02, .22, .05), (x, -s * .09 + 0, zb(584)), 'dark', parent=g)
    # dispensing teat D: small dome on the axis, 0.47 cm dia, ~0.15 cm proud (y 590-600)
    pts = [(r(1220 - 1188) * math.cos(a), zb(590) - (600 - 590) / PPC * math.sin(a)) for a in [i * math.pi / 2 / 10 for i in range(11)]]
    kit.revolve('(D) dispensing teat', [(r(1220 - 1188), zb(590) + .01)] + pts, 'grey', axis='Z', parent=g)
    return g

def build(parent=None, name='Spray Applicator'):
    root = kit.group(name, parent)
    RB = r(930 - 799)                                    # 0.955 body / band radius
    # (A) applicator body: plain antimony cylinder, nozzle end flat with a small edge round (y 629-771)
    kit.revolve('(A) applicator body', rounded_pts(RB, 0, z(629), rc_bot=.06), 'antimony', axis='Z', parent=root)
    # two collar bands with grooves between (y 558.5-590, 593.5-625.5; grooves 590-593.5, 625.5-629)
    kit.revolve('collar band (upper)', rounded_pts(RB, z(590), z(558.5), rc_top=.015, rc_bot=.015), 'antimony', axis='Z', parent=root)
    kit.revolve('collar band (lower)', rounded_pts(RB, z(625.5), z(593.5), rc_top=.015, rc_bot=.015), 'antimony', axis='Z', parent=root)
    kit.cyl('band groove', RB - .03, z(590) - z(593.5) + .02, (0, 0, (z(590) + z(593.5)) / 2), 'antimony', 'Z', parent=root)
    kit.cyl('band groove', RB - .03, z(625.5) - z(629) + .02, (0, 0, (z(625.5) + z(629)) / 2), 'antimony', 'Z', parent=root)
    # (C) vial: its barrel foot sits on the upper band; neck + teat hidden inside the bands
    vial(root, base_z=z(558.5))
    # (B) spray trigger: round push button facing front, outer ring dia 0.70 / inner 0.58, centre at y 726
    zt = z(726)
    kit.cyl('(B) spray trigger bezel', r(48), .06, (0, -RB - .005, zt), 'antimony', 'Y', parent=root)
    kit.cyl('(B) spray trigger (press to spray)', r(40), .1, (0, -RB - .03, zt), 'antimony', 'Y', bev=.015, parent=root)
    kit.torus('trigger ring line', r(44), .006, (0, -RB - .035, zt), 'dark', 'Y', parent=root)
    # (E) interchangeable nozzle on the end face (end view centre 865,907): ring dia 0.99 with four notches, orifice ring, orifice
    kit.cyl('(E) interchangeable nozzle', r(68), .04, (0, 0, -.01), 'antimony', 'Z', parent=root)
    kit.torus('nozzle ring line', r(68), .008, (0, 0, -.03), 'dark', 'Z', parent=root)
    for k in range(4):
        a = k * math.pi / 2
        kit.cyl('nozzle notch', .045, .02, (r(68) * math.cos(a), r(68) * math.sin(a), -.03), 'dark', 'Z', parent=root)
    kit.torus('orifice ring', r(20), .008, (0, 0, -.03), 'dark', 'Z', parent=root)
    kit.cyl('nozzle orifice', .03, .02, (0, 0, -.035), 'black', 'Z', parent=root)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('spray-applicator')
    if '--vial' in sys.argv:   # vial alone, for scoring against the plate's separate vial drawing
        out = sys.argv[sys.argv.index('--vial') + 1]
        kit.reset(); kit._mats.clear(); vial(); kit.export('spray-applicator-vial', out)
