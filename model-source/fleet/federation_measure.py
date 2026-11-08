"""Measure the Federation-class dreadnought (PDF 88) silhouettes on the 300 dpi plate, in plate pixels.
Run: /usr/bin/python3 -E model-source/fleet/federation_measure.py  ->  model-source/blender/profiles/federation.json
Each profile is a list of [px_along, edge_a, edge_b] read column by column from the filled view silhouette
(model-source/accuracy/plate_silhouette.py, same settings as the scoring views), taking the run that contains a
reference row on the part's own axis. Columns where another part (pylon, leader arrow, bracket) merges into the run
are dropped and bridged by linear interpolation; the Blender script converts px to metres."""
import json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model-source', 'accuracy'))
from plate_silhouette import load_gray, silhouette

g = load_gray(os.path.join(ROOT, 'model-source', 'fleet', 'plates', 'p-088.png'))
spec = json.load(open(os.path.join(ROOT, 'model-source', 'accuracy', 'views', 'federation.json')))
M = {}
for v in spec['views']:
    x0, y0, x1, y1 = v['crop']
    M[v['name']] = (silhouette(g[y0:y1, x0:x1], open_=v['open'], holes=[tuple(h) for h in v.get('holes', [])]), x0, y0)

def run_at(view, col, ref):
    """(start, end) plate rows of the silhouette run in column `col` containing row `ref`."""
    m, x0, y0 = M[view]
    line = m[:, col - x0]; r = ref - y0
    if not line[r]: return None
    a = r
    while a > 0 and line[a - 1]: a -= 1
    b = r
    while b < len(line) - 1 and line[b + 1]: b += 1
    return a + y0, b + 1 + y0

def profile(view, c0, c1, ref, bad_lo=(), bad_hi=(), step=2):
    """[[col, lo, hi], ...]; bad_* = column ranges where that edge is merged with another part (interpolated)."""
    cols = list(range(c0, c1 + 1, step)); lo = []; hi = []
    for c in cols:
        r = run_at(view, c, ref)
        a, b = (np.nan, np.nan) if r is None else r
        if any(p <= c <= q for p, q in bad_lo): a = np.nan
        if any(p <= c <= q for p, q in bad_hi): b = np.nan
        lo.append(a); hi.append(b)
    def fill(arr):
        arr = np.array(arr, float); ok = ~np.isnan(arr)
        return np.interp(cols, np.array(cols)[ok], arr[ok])
    lo, hi = fill(lo), fill(hi)
    return [[c, round(float(a), 2), round(float(b), 2)] for c, a, b in zip(cols, lo, hi)]

out = {}
# Saucer, side view: top/bottom edges of the run through the rim (row 1763), bow edge 359 to the centre column 781.
# Bridge dome / lower sensor dome (cols >= 738) are separate parts: the body there is the flat deck at the measured level.
sau = profile('side', 359, 781, 1763, step=1)
for r in sau:
    if r[0] >= 738: r[1] = max(r[1], 1668.0); r[2] = min(r[2], 1851.0)
out['saucer_side'] = sau
# Plan circle: bounding columns/rows of the saucer outline.
out['saucer_plan'] = {'x_min': 355, 'y_min': 500, 'y_max': 1347}
# Side nacelles: plan (starboard about row 613, port about row 1232) and side (port, about row 1808).
out['nac_stbd_plan'] = profile('plan', 1346, 2271, 613, bad_hi=[(1498, 1645)])
out['nac_port_plan'] = profile('plan', 1346, 2271, 1232, bad_lo=[(1498, 1645)])
out['nac_side_side'] = profile('side', 1351, 2282, 1808, bad_hi=[(1395, 1650)])
# Dorsal nacelle, side view (about row 1612); the dorsal pylon merges below between 1105 and 1270.
out['nac_dorsal_side'] = profile('side', 961, 1890, 1612, bad_hi=[(1105, 1272)])
# Secondary hull, side view (about row 1990): bottom edge; top is the flat drawn deck line (1892).
out['sec_side'] = profile('side', 1108, 1815, 1990, bad_hi=[(1135, 1216), (1740, 1800)])
for r in out['sec_side']: r[1] = 1892.0
# Secondary hull, plan: outer edges of the body around the dorsal nacelle (pylons merge 1498-1645, saucer before 1196).
sp = profile('plan', 1196, 1800, 923, bad_lo=[(1270, 1290), (1498, 1650)], bad_hi=[(1498, 1650)])
out['sec_plan'] = sp
json.dump(out, open(os.path.join(ROOT, 'model-source', 'blender', 'profiles', 'federation.json'), 'w'))
for k, v in out.items():
    if isinstance(v, list): print(k, len(v), v[0], v[len(v) // 2], v[-1])
