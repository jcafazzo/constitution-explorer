"""Measure a drawn view's silhouette row by row, in centimetres, straight from the plate.
usage: python3 extract_profile.py <page> <x0,y0,x1,y1> <pxPerCm> <out.json> [--step 2] [--keep 1] [--open 4] [--mask a,b,c,d ...] [--transpose]
Output: {"rows":[[s, lo, hi], ...], "length": L, "width_max": W, "centre_px": c}
  s  = distance (cm) from the first silhouette row (image top, or image left with --transpose)
  lo/hi = left/right silhouette edges (cm) relative to the silhouette's own mid-line (mean of overall min/max)."""
import sys, json, argparse
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from plate_silhouette import load_gray, silhouette
ap = argparse.ArgumentParser()
ap.add_argument('page'); ap.add_argument('crop'); ap.add_argument('ppc', type=float); ap.add_argument('out')
ap.add_argument('--step', type=float, default=2); ap.add_argument('--keep', type=int, default=1); ap.add_argument('--open', type=int, default=4)
ap.add_argument('--mask', nargs='*', default=[]); ap.add_argument('--transpose', action='store_true'); ap.add_argument('--png', default=None)
a = ap.parse_args()
x0, y0, x1, y1 = map(int, a.crop.split(','))
g = load_gray(a.png or f'dist/assets/equipment/page-{a.page}.webp')[y0:y1, x0:x1]
m = silhouette(g, keep=a.keep, open_=a.open)
for r in a.mask:
    p, q, s_, t = map(int, r.split(',')); m[q:t, p:s_] = False
if a.transpose: m = m.T
rows = np.where(m.any(1))[0]; cols = np.where(m.any(0))[0]
mid = (cols.min() + cols.max()) / 2
out = []
for r in np.arange(rows.min(), rows.max() + 1, a.step):
    r = int(round(r)); c = np.where(m[r])[0]
    if len(c) == 0: continue
    out.append([round((r - rows.min()) / a.ppc, 4), round((c.min() - mid) / a.ppc, 4), round((c.max() + 1 - mid) / a.ppc, 4)])
json.dump({'rows': out, 'length': round((rows.max() + 1 - rows.min()) / a.ppc, 4), 'width_max': round((cols.max() + 1 - cols.min()) / a.ppc, 4),
           'crop': [x0, y0, x1, y1], 'ppc': a.ppc, 'origin_px': ([x0 + float(mid), y0 + int(rows.min())] if not a.transpose else [x0 + int(rows.min()), y0 + float(mid)]), 'page': a.page, 'transpose': a.transpose}, open(a.out, 'w'))
print(a.out, 'L', round((rows.max() + 1 - rows.min()) / a.ppc, 3), 'W', round((cols.max() + 1 - cols.min()) / a.ppc, 3), 'rows', len(out))
