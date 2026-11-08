"""Measure the Constitution (PDF 75, TO 01:04:10) from the 300 dpi plate into world-space profiles for the Blender build.
usage: /usr/bin/python3 -E model-source/fleet/constitution_measure.py  ->  model-source/blender/profiles/constitution.json
World frame (metres): Z up, bow at y = -L/2 (front = -Y), starboard = -X.  Plate px -> world:
  side  (bow left, seen from +X):  y = -L/2 + (px - SX0)/PPM,  z = (SZ0 - row)/PPM   (z = 0 at the lowest drawn point)
  plan  (bow left, image-up = starboard): y = -L/2 + (px - PX0)/PPM,  x = (row - PYC)/PPM
  front (seen from -Y):           x = (px - FXC)/PPM,  z = (FZ0 - row)/PPM
Scale: drawn overall length 1733 px (plan and side agree) = printed L.O.A. 288.6 m; the 0-50 m bar gives 6.02 px/m."""
import sys, json, os
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'accuracy'))
from plate_silhouette import load_gray, silhouette

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
G = load_gray(os.path.join(ROOT, 'model-source/fleet/plates/p-075.png'))
L = 288.6; PPM = 1733 / L
def mask(x0, y0, x1, y1, o=7, holes=()):
    m = np.zeros(G.shape, bool); m[y0:y1, x0:x1] = silhouette(G[y0:y1, x0:x1], open_=o, holes=[(x - x0, y - y0) for x, y in holes]); return m
PLAN = mask(420, 470, 2215, 1265); SIDE = mask(380, 1440, 2200, 1945)
SX0, PX0 = 434, 442
SZ0 = 1916; PYC = 872.5
FXC = 817.0; FZ0 = 2560
ys = lambda px: -L / 2 + (px - SX0) / PPM
yp = lambda px: -L / 2 + (px - PX0) / PPM
zs = lambda row: (SZ0 - row) / PPM

def runs(col, r0, r1):
    out, s = [], None
    for i in range(r0, r1 + 1):
        v = col[i] if i < len(col) else False
        if v and s is None: s = i
        if (not v) and s is not None: out.append((s, i - 1)); s = None
    return out

def smooth(vals, k=9):
    v = np.array(vals, float); return list(ndi.median_filter(v, size=k, mode='nearest'))

out = {'ppm': PPM, 'L': L, 'notes': __doc__}

# ---- primary hull: revolve the side view's forward half (bow rim -> saucer axis); axis column from the plan circle fit ----
SAX = 815.6                                  # side-view saucer axis column (bow rim 434 + plan radius 381.6)
rows = []
for c in range(SX0, int(SAX) + 1):
    rr = runs(SIDE[:, c], 1440, 1760)
    if not rr: continue
    t, b = rr[0]
    rows.append((c, t, b))
cs = [r[0] for r in rows]; ts = smooth([r[1] for r in rows], 7); bs = smooth([r[2] for r in rows], 7)
out['saucer'] = [[round((SAX - c) / PPM, 3), round(zs(t), 3), round(zs(b + 1), 3)] for c, t, b in zip(cs, ts, bs)]
out['saucer_axis_y'] = round(ys(SAX), 3)
aft = []                                         # aft half of the upper surface (dome is drawn longer aft); stop before the impulse deck
for c in range(int(SAX) + 1, 1086):
    rr = runs(SIDE[:, c], 1440, 1760)
    if rr: aft.append((c, rr[0][0]))
at = smooth([a[1] for a in aft], 7)
out['saucer_aft_top'] = [[round((c - SAX) / PPM, 3), round(zs(t), 3)] for (c, _), t in zip(aft, at)]

# ---- secondary hull: side top/bottom (neck 1100-1345 and pylon 1455-1555 bridged), plan width where it is visible ----
def side_hull(c):
    rr = [r for r in runs(SIDE[:, c], 1700, 1944) if r[1] > 1740]
    return rr[-1] if rr else None
H = []
for c in range(1040, 1738, 3):
    r = side_hull(c)
    if r: H.append([c, r[0], r[1]])
H = np.array(H, float)
bridge = (H[:, 0] > 1095) & (H[:, 0] < 1350) | (H[:, 0] > 1450) & (H[:, 0] < 1560)
top = H[:, 1].copy(); good = ~bridge
top[bridge] = np.interp(H[bridge, 0], H[good, 0], H[good, 1])
pw = []
for c in H[:, 0].astype(int):
    pc = c + (PX0 - SX0)
    if pc < 1215 or 1455 < pc < 1555: pw.append(np.nan); continue
    rr = [r for r in runs(PLAN[:, pc], 700, 1050) if r[0] < PYC < r[1]]
    pw.append((rr[0][1] + 1 - rr[0][0]) / 2 / PPM if rr else np.nan)
pw = np.array(pw)
out['sec_hull'] = [[round(ys(c), 3), round(zs(t), 3), round(zs(b + 1), 3), (None if np.isnan(w) else round(float(w), 3))]
                   for c, t, b, w in zip(H[:, 0], smooth(top, 5), smooth(H[:, 2], 5), pw)]

# ---- dorsal (neck): front edge and aft edge lines in the side view ----
nf, na = [], []
for c in range(965, 1150, 4):      # front/lower edge: bottom of the saucer+neck run above the gap
    rr = runs(SIDE[:, c], 1560, 1760)
    if len(rr) and rr[0][1] > 1625: nf.append([round(ys(c), 3), round(zs(rr[0][1] + 1), 3)])
for c in range(1205, 1345, 4):     # aft/upper edge: top of the run that reaches the secondary hull
    rr = [r for r in runs(SIDE[:, c], 1595, 1944) if r[1] > 1880]
    if rr: na.append([round(ys(c), 3), round(zs(rr[0][0]), 3)])
out['neck_front'] = nf; out['neck_aft'] = na

# ---- warp nacelle: plan (starboard unit, pylon box bridged) and side profiles ----
NP, NS = [], []
for c in range(1240, 2185, 3):
    rr = [r for r in runs(PLAN[:, c], 500, 700) if r[1] - r[0] > 10]
    if rr: NP.append([c, rr[0][0], rr[0][1]])
    rs = [r for r in runs(SIDE[:, c], 1440, 1600) if r[1] - r[0] > 10]
    if rs: NS.append([c, rs[0][0], min(rs[0][1], 1575)])
NP = np.array(NP, float); NS = np.array(NS, float)
b = (NP[:, 0] > 1455) & (NP[:, 0] < 1555)
NP[b, 2] = np.interp(NP[b, 0], NP[~b, 0], NP[~b, 2])
b = (NS[:, 0] > 1455) & (NS[:, 0] < 1555)
NS[b, 2] = np.interp(NS[b, 0], NS[~b, 0], NS[~b, 2])
out['nacelle_plan'] = [[round(yp(c), 3), round((r0 - PYC) / PPM, 3), round((r1 + 1 - PYC) / PPM, 3)] for c, r0, r1 in NP]
out['nacelle_side'] = [[round(ys(c), 3), round(zs(r0), 3), round(zs(r1 + 1), 3)] for c, r0, r1 in NS]

# ---- windows / ports: short ink dashes inside the side silhouette (both sides of the ship) ----
ink = G < .5
lab, n = ndi.label(ink)
win = []
for i, sl in enumerate(ndi.find_objects(lab)):
    h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
    cy, cx = (sl[0].start + sl[0].stop) / 2, (sl[1].start + sl[1].stop) / 2
    if not (1440 < cy < 1945 and 380 < cx < 2200): continue
    if 2 <= h <= 9 and 6 <= w <= 30 and w > 1.6 * h and SIDE[int(cy), int(cx)]:
        win.append([round(ys(cx), 2), round(zs(cy), 2), round(w / PPM, 2), round(h / PPM, 2)])
out['windows_side'] = win

os.makedirs(os.path.join(ROOT, 'model-source/blender/profiles'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'model-source/blender/profiles/constitution.json'), 'w'))
print('saucer', len(out['saucer']), 'r_max', out['saucer'][0][0], 'sec_hull', len(out['sec_hull']), 'neck', len(nf), len(na),
      'nacelle', len(NP), len(NS), 'windows', len(win))
print('nacelle plan centre x', round(float(np.mean([(a + b) / 2 for _, a, b in out['nacelle_plan']])), 2),
      'side centre z', round(float(np.mean([(a + b) / 2 for _, a, b in out['nacelle_side']])), 2))
