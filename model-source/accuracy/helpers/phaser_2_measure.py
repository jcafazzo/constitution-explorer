"""Measure the Hand Phaser Type II silhouettes on plate PDF 104 (67.61 px/cm) and write the profiles used by
model-source/blender/phaser_2.py.  Run from the repo root: /usr/bin/python3 -E model-source/accuracy/helpers/phaser_2_measure.py

Rows are [s, lo, hi] in cm; s = (plate row - 236) / ppc from the beam-shield tip.
  phaser-2-side.json : side view (right drawing, seen from +X, image right = +Z); lo/hi = z of the body's -Z/+Z edges about the
                       barrel axis (plate x 1020). Body only: the grip is masked (its hidden root edge is the straight line
                       (875,760)-(920,1080) that continues the body's visible -Z edge), the force setting dial and the +Z spine on the aft
                       section are clipped (aft +Z edge = silhouette - 8 px; under the dial interpolated).
  phaser-2-top.json  : top view (middle drawing, seen from +Z, image left = +X); lo/hi = image offsets from the axis (plate x 632);
                       x = -offset. The lock release tab (rows 1388-1436, left) is clipped.
  phaser-2-barrel.json: beam emitter + photon accelerator radius per row (mean of top and side half-widths), rows 236-546.
Each body edge is smoothed with a cubic smoothing spline (residual ~0.5 px) between breakpoints where it jumps by more than 2 px
from one row to the next, so the lofted surface has no pixel staircase but keeps its steps (head, lockplates, aft section)."""
import sys, json, os
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model-source', 'accuracy'))
from plate_silhouette import load_gray, silhouette
PPC = 67.61; TIP = 236; AX_S = 1020; AX_T = 632
g = load_gray(os.path.join(ROOT, 'dist/assets/equipment/page-104.webp'))
side = silhouette(g[225:1760, 760:1300]); top = silhouette(g[225:1760, 470:800])
def ext(m, x0, y0, py):
    c = np.where(m[py - y0])[0]
    return (c.min() + x0, c.max() + x0 + 1) if len(c) else None
out = os.path.join(ROOT, 'model-source', 'blender', 'profiles')
S, T, B = [], [], []
lerp = lambda a, b, t: a + (b - a) * t
for py in range(236, 1746):
    s = round((py - TIP) / PPC, 4)
    es, et = ext(side, 760, 225, py), ext(top, 470, 225, py)
    if py <= 546 and es and et:
        B.append([s, round(((es[1] - es[0]) + (et[1] - et[0])) / 4 / PPC, 4)])
    if 548 <= py <= 1733 and es:
        lo, hi = es
        if 755 <= py <= 1080: lo = lerp(875, 920, (py - 760) / 320)                 # grip root hidden: straight body edge
        if 548 <= py <= 652: hi = min(hi, 1196)                                      # forward lockplate face plate added separately
        if 1336 <= py <= 1347: hi = 1093 + (py - 1336) / 11 * (1182 - 1093)         # rear lockplate ledge (separate part)
        if py >= 1348:
            hi = hi - 8                                                              # +Z spine on the aft section (separate part)
            if 1415 <= py <= 1556: hi = lerp(1181, 1173, (py - 1415) / 141)          # under the force setting dial
        S.append([s, round((lo - AX_S) / PPC, 4), round((hi - AX_S) / PPC, 4)])
    if 548 <= py <= 1745 and et:
        lo, hi = et
        if 1386 <= py <= 1438: lo = 550                                              # lock release tab (separate part)
        T.append([s, round((lo - AX_T) / PPC, 4), round((hi - AX_T) / PPC, 4)])
from scipy.interpolate import UnivariateSpline
def smooth_edges(rows):
    a = np.array(rows, dtype=float)
    for col in (1, 2):
        v = a[:, col] * PPC; cuts = [0] + [i + 1 for i in range(len(v) - 1) if abs(v[i + 1] - v[i]) > 2.0] + [len(v)]
        for i0, i1 in zip(cuts, cuts[1:]):
            if i1 - i0 >= 8:
                x = np.arange(i1 - i0, dtype=float)
                v[i0:i1] = UnivariateSpline(x, v[i0:i1], k=3, s=(i1 - i0) * 0.5 ** 2)(x)
        a[:, col] = np.round(v / PPC, 4)
    return a.tolist()
S, T = smooth_edges(S), smooth_edges(T)
meta = dict(page=104, ppc=PPC, tip_row=TIP)
json.dump(dict(rows=S, axis_px=AX_S, **meta), open(os.path.join(out, 'phaser-2-side.json'), 'w'))
json.dump(dict(rows=T, axis_px=AX_T, **meta), open(os.path.join(out, 'phaser-2-top.json'), 'w'))
json.dump(dict(rows=B, **meta), open(os.path.join(out, 'phaser-2-barrel.json'), 'w'))
print('side', len(S), 'top', len(T), 'barrel', len(B))
