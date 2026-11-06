"""Measure cuff lines (for rank braid) and the insignia box from a uniform's segmented map.
usage: python3 anchors.py <id> ; sleeve search boxes (plate px) are in plates.json "sleeves"."""
import sys, json
import numpy as np
from PIL import Image
cfg = json.load(open('model-source/colour/plates.json'))[sys.argv[1]]
x0, y0 = cfg['crop'][:2]
G = np.asarray(Image.open(f"dist/assets/colours/{sys.argv[1]}-map.png"))[..., 1] // 20
tunic = G == 1; out = {'cuffs': [], 'badge': None}
for ax, ay, bx, by in cfg.get('cuffs', []):     # traced cuff lines (plate px): a→b across the sleeve end
    p1, p2 = np.array([ax - x0, ay - y0], float), np.array([bx - x0, by - y0], float); t = p2 - p1
    n = np.array([t[1], -t[0]]) / np.linalg.norm(t)
    if n[1] > 0: n = -n
    out['cuffs'].append({'a': p1.tolist(), 'b': p2.tolist(), 'up': n.round(4).tolist()})
for (a, b, c, d) in ([] if cfg.get('cuffs') else cfg['sleeves']):
    a, b, c, d = a - x0, b - y0, c - x0, d - y0
    pts = [(x, b + np.where(tunic[b:d, x])[0].max()) for x in range(a, c) if tunic[b:d, x].any()]
    xs = np.array([p[0] for p in pts]); ys = np.array([p[1] for p in pts])
    k = np.polyfit(xs, ys, 1); xl, xr = xs.min() + 2, xs.max() - 2
    p1, p2 = [float(xl), float(np.polyval(k, xl))], [float(xr), float(np.polyval(k, xr))]
    t = np.array(p2) - np.array(p1); n = np.array([t[1], -t[0]]) / np.linalg.norm(t)
    if n[1] > 0: n = -n                     # toward the shoulder (up the sleeve)
    out['cuffs'].append({'a': p1, 'b': p2, 'up': n.round(4).tolist()})
ys, xs = np.where(G == 4)
if len(xs): out['badge'] = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
out['pxPerCm'] = cfg.get('pxPerCm')
out['views'] = {k: [v[0] - x0, v[1] - x0] for k, v in cfg.get('views', {}).items()}
json.dump(out, open(f"dist/assets/colours/{sys.argv[1]}-meta.json", 'w'))
print(sys.argv[1], json.dumps(out)[:400])
