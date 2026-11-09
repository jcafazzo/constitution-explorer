"""Vulcan Lyrette, orchestral model — PDF 151, TO 03:98:10.  Run: Blender -b -P model-source/blender/vulcan_lyrette.py
Printed: pitch range 60-3180 cps; materials Bahun'ahb (mother-of-pearl), Sher Skah (mountain-grown luan),
Li'pon (dark fine-grain teak). No dimensions are printed; everything is measured at the sheet's 0-40 cm bar (11.65 px/cm).

Views on the sheet: a front elevation and a side elevation (the front face is on the side view's left).
The side view is a constant-thickness board, 49 px = 4.2 cm, from the scroll to the foot, so the body is the measured
front outline extruded 4.2 cm. On the front face: the eridanite pins stand 1.0 cm proud, the control knobs 1.9 cm,
the tension boss rises 2.4 cm and the glide disc reaches 4.2 cm (all read off the side view).

Outlines come from model-source/blender/vulcan_lyrette_regions.py (profiles/vulcan-lyrette-regions.json).
Frame: x across the face (plate right = +X), z up from the foot tip, front face toward -Y."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
from mathutils import Vector

kit.PALETTE.update({
    'teak': ('3d2518', .5, 0, 1),        # Li'pon: dark fine-grain teak
    'luan': ('b8875a', .55, 0, 1),       # Sher Skah: mountain-grown luan
    'nacre': ('ece6da', .22, .12, 1),    # Bahun'ahb: mother-of-pearl
    'pin': ('a7b0b6', .25, .8, 1),       # eridanite pins
    'string': ('d8d3c4', .3, .7, 1),
})
kit.reset()
R = json.load(open(os.path.join(kit.PROFILES, 'vulcan-lyrette-regions.json')))
T = R['thickness']; F = -T / 2           # front face plane (y)

def slab(name, poly, y0, y1, material):
    """Extrude a front-view outline [(x, z), ...] between depths y0 < y1."""
    o = kit.extrude(name, poly, y1 - y0, material, plane='XZ', loc=(0, (y0 + y1) / 2, 0))
    return kit.smooth(o, 30)

# body: luan board (outline inset one plate pixel), teak proud by 0.03 cm on both faces, nacre inlays on the front
for i, p in enumerate(R['silhouette_inset']): slab(f'VoiceBox_{i}', p, F + .03, -F - .03, 'luan')
for i, p in enumerate(R['teak']): slab(f'Neck_Back_Teak_{i}', p, F, -F, 'teak')
for i, p in enumerate(R['nacre_back']): slab(f'Back_Nacre_{i}', p, F - .06, F + .2, 'nacre')
for i, p in enumerate(R['nacre_control']): slab(f'ControlBox_{i}', p, F - .1, F + .2, 'nacre')

def rod(name, a, b, r, material, seg=10):
    a, b = Vector(a), Vector(b); d = b - a
    o = kit.cyl(name, r, d.length, (a + b) / 2, material, seg=seg)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return o

# fret bar along the inner neck, eridanite pins on it
fret = [Vector((x, 0, z)) for x, z in R['fret']]
seglen = [(fret[i + 1] - fret[i]).length for i in range(len(fret) - 1)]; total = sum(seglen)
def along(t):
    s = t * total
    for i, l in enumerate(seglen):
        if s <= l or i == len(seglen) - 1: return fret[i] + (fret[i + 1] - fret[i]) * min(s / l, 1)
        s -= l
for i in range(len(fret) - 1):
    rod(f'FretBar_{i}', (fret[i].x, F - .12, fret[i].z), (fret[i + 1].x, F - .12, fret[i + 1].z), .22, 'nacre', 12)
N = R['pins']; pins = []
for k in range(N):
    p = along(.02 + .96 * k / (N - 1)); pins.append(p)
    kit.cyl(f'Pin_{k:02d}', .2, 1.0, (p.x, F - .5, p.z), 'pin', axis='Y', seg=16)
    kit.sphere(f'PinHead_{k:02d}', .3, (p.x, F - 1.0, p.z), 'pin')

# bridge: a rounded bar across the string fan, standing 1.3 cm off the face
bx0, bx1 = R['bridge_x']; bz = R['bridge_z']
bridge = kit.box('Bridge', (bx1 - bx0 + 1.2, 1.2, 1.3), ((bx0 + bx1) / 2, F - .6, bz), 'nacre', bev=.35)

# strings: pin -> over the bridge -> converge on the anchor above the tension boss (top pins land at the bridge's right)
ex, ez = R['string_end']
for k, p in enumerate(pins):
    bxk = bx1 - (bx1 - bx0) * k / (N - 1)
    rod(f'String_{k:02d}a', (p.x, F - .95, p.z), (bxk, F - 1.28, bz), .055, 'string', 6)
    rod(f'String_{k:02d}b', (bxk, F - 1.28, bz), (ex, F - .25, ez), .055, 'string', 6)
kit.sphere('StringAnchor', .55, (ex, F - .2, ez), 'pin', scale=(1, .6, 1))

# control box knobs: Voicer, Decay, Brilliance, Resonance (1.9 cm proud on the side view)
for kn in R['knobs']:
    x, z = kn['centre']; r = kn['r']
    kit.revolve(f"Knob_{kn['name']}", [(0, F), (r, F), (r, F - 1.55), (r * .8, F - 1.85), (0, F - 1.9)], 'nacre', 'Y', seg=40)
    bpy.context.scene.objects[f"Knob_{kn['name']}"].location = (x, 0, z)

# tension boss (luan, revolved from the side view) and the glide disc (teak) with its cross index
cx, cz = R['rosette']['centre']; ro, ri = R['rosette']['r_outer'], R['rosette']['r_inner']
boss = [(0, F + .1), (ro, F + .1), (ro, F), (ro * .95, F - .6), (ro * .82, F - 1.5), (ro * .68, F - 1.95), (ro * .52, F - 2.25), (ro * .4, F - 2.4), (0, F - 2.4)]
kit.revolve('TensionBoss', boss, 'luan', 'Y').location = (cx, 0, cz)
kit.revolve('GlideStem', [(0, F - 2.3), (.9, F - 2.3), (.9, F - 3.1), (0, F - 3.1)], 'teak', 'Y', seg=32).location = (cx, 0, cz)
kit.revolve('Glide', [(0, F - 3.05), (ri, F - 3.05), (ri, F - 4.0), (ri * .92, F - 4.2), (0, F - 4.2)], 'teak', 'Y', seg=64).location = (cx, 0, cz)
for i, (sx, sz) in enumerate(((ri * 1.5, .1), (.1, ri * 1.5))):
    kit.box(f'GlideIndex_{i}', (sx, .06, sz), (cx, F - 4.22, cz), 'nacre')

size = kit.export('vulcan-lyrette')
