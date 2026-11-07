"""Ear Receiver — PDF 138, TO 03:02:02 (SFAF/CC-MK05-0, size 0).  Run: Blender -b -P model-source/blender/ear_receiver.py [-- --pose profile --out DIR]
Printed: length overall 6.55 cm, width overall 3.15 cm, maximum diameter 2.6 cm, 57 gm. Colours: antimony SF02UC, black SF32UC,
transparent half-hard plastic ear-piece.  Fins, rails, stem, flange, plate B and housing C use the 'antimony' material (colour key);
the energy cell housing, core, cone and root lobes are black; the ear-piece is transparent ('glass').
END view (below the PLAN, seen from the base): outer circle 180-181 px = fin OD, inner circle 128-130 px (ratio 0.71-0.72) = base
flange edge (PLAN 134/184 = 0.73; the plan is kept, 0.4 mm apart); the two strips across the annulus are the axial rails' feet.
Upright: Z = length (base at z = 0). PLAN seen from -Y (image-right = +X, ear-piece to -X); PROFILE seen from -X.
The drawing is followed, not the print: it measures 6.75 cm long (+3%) and 2.67 cm across the fins (printed 2.6).
Body: revolved from the PLAN silhouette (profiles/ear-receiver-plan.json); the two axial rails that close the fin grooves at
+-Y come from the PROFILE silhouette (ear-receiver-profile.json), whose outline is straight with a chamfered foot (F).
Head: retention plate B (drawn edge-on in PLAN from (812,415) to (887,325) px, face-on in PROFILE 1103-1265 x 318-433 px),
earphone housing C behind it, ear-piece A traced from the PLAN (profiles/ear-receiver-earpiece.json,
model-source/accuracy/helpers/ear_receiver_earpiece.py). The housing axis is drawn 39.8 deg below horizontal (marked 40 deg).
--pose profile: the PROFILE draws plate B face-on, i.e. the head swivelled level to face the viewer; that pose is exported
only to score the PROFILE view (views/ear-receiver-profile.json)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import kit

PPC = 68.59
AX = 878.0              # PLAN centre-line (px)
BOT = 775.0             # base (flange) bottom row (px)
x = lambda px: (px - AX) / PPC
z = lambda py: (BOT - py) / PPC

def prof_rows(name):
    p = kit.load_profile(name); oy = p['origin_px'][1]
    return [(oy + s * PPC, (hi - lo) / 2) for s, lo, hi in p['rows']]

def build(pose='plan'):
    root = kit.group('Ear Receiver')
    plan = prof_rows('ear-receiver-plan'); side = prof_rows('ear-receiver-profile')
    # ---- (E) energy cell housing (black) and base flange (antimony), from the PLAN ----
    rf = sum(r for py, r in plan if 765 <= py <= 772) / sum(1 for py, r in plan if 765 <= py <= 772)
    rc_ = sum(r for py, r in plan if 750 <= py <= 760) / sum(1 for py, r in plan if 750 <= py <= 760)
    kit.revolve('base flange', [(0, z(775)), (rf - .03, z(775)), (rf, z(774)), (rf, z(763)), (0, z(763))], 'antimony', axis='Z', parent=root)
    kit.revolve('(E) energy cell housing', [(0, z(764)), (rc_, z(764)), (rc_, z(747)), (0, z(747))], 'black', axis='Z', parent=root)
    # ---- (D) receiver housing: black core with eight antimony fins (PLAN: fins 183 px OD, core 144 px) ----
    fins = []; inside = False
    for py, r in plan:
        if 566 <= py <= 748:
            wide = r * 2 * PPC > 165
            if wide and not inside: fins.append([py, py])
            if wide: fins[-1][1] = py
            inside = wide
    core_r = 144 / 2 / PPC
    # core stops 0.1 mm short of the lowest fin's underside so that fin, not the black core, is seen from below: the END view
    # draws a plain annulus from the fin OD (outer circle) to the base flange edge (inner circle, 0.71-0.72 of the outer)
    kit.revolve('(D) receiver housing core', [(0, z(748) + .01), (core_r, z(748) + .01), (core_r, z(566)), (0, z(566))], 'black', axis='Z', parent=root)
    fin_r = sum(r for py, r in plan if any(a <= py <= b for a, b in fins)) / sum(1 for py, r in plan if any(a <= py <= b for a, b in fins))
    for a, b in fins:
        kit.cyl('(D) receiver housing fin', fin_r, (b - a + 1) / PPC, (0, 0, z((a + b + 1) / 2)), 'antimony', 'Z', seg=96, bev=.015, parent=root)
    # black cone above the fins (PLAN y 528..566)
    cone = [(r, z(py)) for py, r in plan if 528 <= py <= 566][::2]
    kit.revolve('receiver cone', [(0, z(566))] + sorted(cone, key=lambda p: p[1]) + [(0, z(527))], 'black', axis='Z', parent=root)
    # axial rails at +-Y: 10 px wide (PLAN centre strip), flush with the fin OD, foot chamfered as drawn in PROFILE (F)
    R = max(r for py, r in side if 575 <= py <= 745)
    foot = [(py, r) for py, r in side if 745 <= py <= 776]
    for sgn in (1, -1):
        pts = [(.76, z(566))] + [(R, z(568))] + [(r, z(py)) for py, r in foot[::3]] + [(.76, z(776))]
        prof = [(sgn * r_, zz) for r_, zz in pts]
        kit.extrude('(F) high gain antenna grid / heat sink rail', [(p[0], p[1]) for p in prof], 10 / PPC, 'antimony', plane='YZ', parent=root)
    # ---- stem (PLAN x 857-897, PROFILE 1167-1205) with four black root lobes (drawn as a pair in both views) ----
    rs = 19.5 / PPC
    kit.cyl('stem', rs, z(440) - z(530), (0, 0, (z(440) + z(530)) / 2), 'antimony', 'Z', parent=root)
    for k in range(4):
        a = math.radians(45 + 90 * k); d = 12 / PPC
        kit.sphere('stem root lobe', 8 / PPC, (d * math.cos(a), d * math.sin(a), z(540)), 'black', scale=(1, 1, 3.0), parent=root)
    # ---- head: plate B, housing C, ear-piece A (head-local: X' = housing axis a, Y = across, Z' = along plate u) ----
    ep = kit.load_profile('ear-receiver-earpiece')
    pcx, pcy = ep['plate_centre_px']
    tilt = math.radians(ep['housing_axis_below_horizontal_deg'])
    head = kit.group('earphone head (swivels stiffly at G)', root)
    if pose == 'plan':
        head.location = (x(pcx), 0, z(pcy)); head.rotation_euler = (0, tilt, 0)
    else:  # PROFILE: plate centre at y 375.5, head level, ear-piece toward the -X viewer
        head.location = (x(pcx), (1184 - 1188.5) / PPC, z(375.5)); head.rotation_euler = (0, 0, 0)
    W, H, T, rc = (1265 - 1103) / PPC, 1.66, 12 / PPC, 16 / PPC
    pts = []
    for cy, cz, a0 in ((W / 2 - rc, H / 2 - rc, 0), (-W / 2 + rc, H / 2 - rc, 90), (-W / 2 + rc, -H / 2 + rc, 180), (W / 2 - rc, -H / 2 + rc, 270)):
        for k in range(7):
            a = math.radians(a0 + k * 15); pts.append((cy + rc * math.cos(a), cz + rc * math.sin(a)))
    kit.extrude('(B) ear-piece retention plate', pts, T, 'antimony', plane='YZ', bev=.02, parent=head)
    kit.sphere('(B) retention plate dome', 27 / PPC, (0, 0, H / 2 - .02), 'antimony', scale=(.32, 1, .7), parent=head)  # PROFILE knob 55 px wide, 18 px proud
    # housing C: PLAN square a 0.12..1.05 cm, u -0.71..+0.46 cm
    kit.cyl('(C) earphone housing', .58, .98, (.12 + .98 / 2, 0, -.13), 'antimony', 'X', parent=head)
    kit.torus('(G) swivel', .5, .035, (.08, 0, -.13), 'antimony', axis='X', parent=head)
    # ear-piece A: PLAN outline extruded across (end-on in PROFILE it is the 80 px circle -> 1.17 cm)
    poly = ep['poly']
    if sum((poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]) for i in range(len(poly))) < 0: poly = poly[::-1]
    # (the PROFILE draws only plate B and two circles for the head; the PLAN ear-piece outline, whose lip reaches below the
    # plate, cannot hide behind B in any swivel position - accepted as a drawing inconsistency, not posed away)
    # Moulded, not slab-sided: lofted along u, each section a rounded superellipse spanning the PLAN outline's a-range at that
    # u (so the PLAN silhouette is kept) and, across, tapering from the PROFILE's 1.17 cm circle to rounded ends.
    kit.PALETTE.setdefault('clear', ('dde4e6', .06, 0, .3))          # "transparent" half-hard plastic: near-colourless
    us = [q[1] for q in poly]; u0, u1 = min(us) + .005, max(us) - .005; secs = []
    for i in range(41):
        uu = u0 + (u1 - u0) * i / 40; hits = []
        for (a1, v1), (a2, v2) in zip(poly, poly[1:] + poly[:1]):
            if (v1 - uu) * (v2 - uu) <= 0 and v1 != v2: hits.append(a1 + (a2 - a1) * (uu - v1) / (v2 - v1))
        if len(hits) < 2: continue
        lo, hi = min(hits), max(hits); t = 2 * (uu - u0) / (u1 - u0) - 1
        hw = min(80 / PPC / 2 * max(1 - abs(t) ** 4, 0) ** .25, max((hi - lo) * .8, .12))
        secs.append((uu, lo, hi, -max(hw, .03), max(hw, .03)))
    ear = kit.loft('(A) molded plastic ear-piece', secs, 'clear', p=2.4, seg=48, parent=head)
    ear.rotation_euler = (math.pi / 2, 0, 0)                          # loft Y (= u) -> head Z', loft Z (across) -> head Y
    return root

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    pose = argv[argv.index('--pose') + 1] if '--pose' in argv else 'plan'
    out = argv[argv.index('--out') + 1] if '--out' in argv else None
    kit.reset(); build(pose)
    kit.export('ear-receiver' if pose == 'plan' else 'ear-receiver-' + pose, out)
