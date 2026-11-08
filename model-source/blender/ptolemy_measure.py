"""Measure the Ptolemy transport/tug (PDF 81, TO 01:04:16) outlines straight from the 300 dpi plate.
Run: /usr/bin/python3 -E model-source/blender/ptolemy_measure.py  → model-source/blender/profiles/ptolemy-*.json
All outputs are in plate pixels (the Blender script converts with its px→world lambdas), smoothed and resampled.

saucer : side view, forward half only, column by column from the saucer axis (side px 1000) to the bow rim (618):
         [[r_px, top_py, bot_py], ...]   (main-sensor strut below r < 7 m replaced by the lower dome's flat bottom)
nacelle: side view top/bottom of the nacelle run per column (1005..1946) and plan width per column (both nacelles averaged,
         visible from 1330 aft; hidden under the saucer before that).  [[px, top_py, bot_py, plan_w_px or null], ...]"""
import sys, os, json
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model-source', 'accuracy'))
from plate_silhouette import load_gray, silhouette

PLATE = os.path.join(ROOT, 'model-source', 'fleet', 'plates', 'p-081.png')
g = load_gray(PLATE)

def sil(x0, y0, x1, y1):
    return silhouette(g[y0:y1, x0:x1], open_=7), x0, y0

def runs(col):
    ys = np.where(col)[0]
    if not len(ys): return []
    out = []; s = p = ys[0]
    for y in ys[1:]:
        if y != p + 1: out.append((s, p)); s = y
        p = y
    out.append((s, p)); return out

def smooth(a, s):
    return ndi.gaussian_filter1d(np.asarray(a, float), s, mode='nearest')

# ---- saucer (side view) ----
m, X0, Y0 = sil(580, 1430, 2000, 1960)
SCX = 1000
cols = list(range(SCX, 617, -1))
top, bot = [], []
for px in cols:
    r = runs(m[:, px - X0])
    t, b = r[0][0] + Y0, r[0][1] + Y0 + 1
    top.append(t); bot.append(b)
top, bot = np.array(top, float), np.array(bot, float)
rr = SCX - np.array(cols, float)
bot[rr < 42] = 1681.0                      # strut of the main sensor hangs below the flat lower-dome pad
# bridge cap: the side top is flat 1484 over the bridge; keep it.  Smooth gently, rim corner untouched.
# dome (r < 110 px): light smoothing keeps its shape; the upper cone and flat band (110-370 px) are straight drawn lines, so
# smooth them hard to stop pixel steps from shading as rings
ts_l, ts_h = smooth(top[:370], 2.0), smooth(top[:370], 9.0)
wgt = np.clip((rr[:370] - 105) / 15, 0, 1)
ts = np.r_[ts_l * (1 - wgt) + ts_h * wgt, top[370:]]
bs = np.r_[smooth(bot[:360], 2.5), bot[360:]]
sauc = [[float(r), round(float(t), 2), round(float(b), 2)] for r, t, b in zip(rr, ts, bs)]
json.dump({'axis_px': SCX, 'rows': sauc, 'note': 'side view, px; r_px from the saucer axis'}, open(os.path.join(HERE, 'profiles', 'ptolemy-saucer.json'), 'w'))

# ---- nacelle (side + plan) ----
nac = []
mp, PX0, PY0 = sil(580, 470, 2000, 1290)
for px in range(1005, 1947):
    rs = [r for r in runs(m[:, px - X0]) if r[1] + Y0 > 1790]
    if not rs: continue
    t, b = rs[-1][0] + Y0, rs[-1][1] + Y0 + 1
    w = None
    if px >= 1330:
        pr = runs(mp[:, px - PX0])
        if len(pr) >= 2:
            a, c = pr[0], pr[-1]
            w = ((a[1] - a[0] + 1) + (c[1] - c[0] + 1)) / 2
    nac.append([px, t, b, w])
nac = np.array([[r[0], r[1], r[2], np.nan if r[3] is None else r[3]] for r in nac], float)
px = nac[:, 0]
# pylon joins the top at 1240..1320 (run continuous to the saucer): the hull top there is the steady 1773
nac[(px >= 1236) & (px <= 1322), 1] = 1773.0
# forward fin hangs below the collar (1040..1165): body bottom mirrors the top about the axis 1822.5
fin = (px >= 1040) & (px <= 1168)
nac[fin, 2] = np.minimum(nac[fin, 2], 2 * 1822.5 - nac[fin, 1])
# leader arrowhead touches the plan inner edges near 1680..1700 and 1745..1765: take the steady neighbours
w = nac[:, 3]
bad = ((px >= 1676) & (px <= 1698)) | ((px >= 1744) & (px <= 1768))
w[bad] = np.nan
ok = ~np.isnan(w)
w_i = np.interp(px, px[ok], w[ok])
w_i[px < px[ok][0]] = np.nan
nac[:, 3] = w_i
out = []
# The drawn unit is a clean tube: rounded nose (to ~1060 px), long body, a raised section 1690-1865 px, aft cap 1865-1943 px.
# Smooth hard inside each run (pixel steps otherwise shade as lumps), lightly across the nose and the cap, keep the steps.
def seg_smooth(a, cuts, sig_body, sig_ends):
    a = np.asarray(a, float).copy(); out = a.copy()
    for lo, hi in zip(cuts[:-1], cuts[1:]):
        m = (px >= lo) & (px < hi)
        if m.sum() > 2: out[m] = smooth(a[m], sig_body)
    light = smooth(a, sig_ends)
    ends = (px < 1060) | (px >= 1900)
    out[ends] = light[ends]
    return out
CUTS = [0, 1060, 1692, 1866, 1900, 9999]
ts, bs = seg_smooth(nac[:, 1], CUTS, 14.0, 2.0), seg_smooth(nac[:, 2], CUTS, 14.0, 2.0)
wf = np.nan_to_num(w_i, nan=w_i[ok][0])
ws = np.where(np.isnan(w_i), np.nan, seg_smooth(wf, CUTS, 14.0, 3.0))
for i in range(0, len(px), 3):
    out.append([float(px[i]), round(float(ts[i]), 2), round(float(bs[i]), 2), None if np.isnan(ws[i]) else round(float(ws[i]), 2)])
if out[-1][0] != px[-1]:
    out.append([float(px[-1]), round(float(ts[-1]), 2), round(float(bs[-1]), 2), None if np.isnan(ws[-1]) else round(float(ws[-1]), 2)])
json.dump({'rows': out, 'note': 'side px column, nacelle top/bottom py (side view), plan width px (avg of both nacelles)'},
          open(os.path.join(HERE, 'profiles', 'ptolemy-nacelle.json'), 'w'))
print('saucer rows', len(sauc), 'rim r', rr.max(), 'nacelle rows', len(out), out[0], out[-1])
