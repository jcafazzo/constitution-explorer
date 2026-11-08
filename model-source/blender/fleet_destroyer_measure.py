"""Measure the Saladin / Hermes plates (PDF 77 / 79) into hull profiles for fleet_destroyer.py.
Run with the system Python (needs numpy/scipy/PIL):  /usr/bin/python3 -E model-source/blender/fleet_destroyer_measure.py saladin
Writes model-source/blender/profiles/<id>-hull.json (metres, ship frame: Z up, bow -Y, starboard -X).

Plate frames (300 dpi):
  plan  : bow image-left, image-up = starboard (-X)      -> y = (px - plan_mid)/k,  x = (py - cy)/k
  side  : bow image-left, top up, seen from +X           -> y = (px - side_mid)/k,  z = -(py - zref)/k
  front : seen from -Y (image-right = +X), up +Z         -> x = (px - fcx)/k,       z = -(py - zref_f)/k
k = px per metre from the printed 0-50 m bar; z = 0 is the saucer rim mid-plane at the bow."""
import sys, os, json, importlib
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model-source', 'accuracy')); sys.path.insert(0, HERE)
from plate_silhouette import load_gray, silhouette


def sil(gray, crop, mask_out=()):
    x0, y0, x1, y1 = crop
    m = silhouette(gray[y0:y1, x0:x1], keep=1, open_=7)
    for a, b, c, d in mask_out: m[b:d, a:c] = False
    full = np.zeros(gray.shape, bool); full[y0:y1, x0:x1] = m
    return full


def runs(v):
    lab, n = ndi.label(v)
    return [(int(np.nonzero(lab == i)[0][0]), int(np.nonzero(lab == i)[0][-1])) for i in range(1, n + 1)]


def smooth(a, k=3):
    a = np.asarray(a, float); out = a.copy()
    for i in range(len(a)):
        out[i] = np.median(a[max(0, i - k):i + k + 1])
    o2 = out.copy()
    for i in range(len(a)):
        o2[i] = out[max(0, i - k):i + k + 1].mean()
    return o2


def spline(a, keep=0, s_px=0.45):
    """Smoothing spline through a pixel-quantised edge (kills the 1-px terraces that band a revolved/lofted surface);
    the first `keep` samples (a sharp rim tip) are blended back in from the light median smooth."""
    from scipy.interpolate import UnivariateSpline
    a = smooth(a, 2); x = np.arange(len(a))
    f = UnivariateSpline(x, a, k=3, s=len(a) * s_px ** 2)(x)
    if keep:
        w = np.clip((x - keep) / max(keep, 1), 0, 1); f = a * (1 - w) + f * w
    return f


def interp_bad(vals, bad):
    vals = np.asarray(vals, float); idx = np.arange(len(vals)); good = ~np.asarray(bad)
    return np.interp(idx, idx[good], vals[good])


def measure(cfg):
    g = load_gray(os.path.join(ROOT, cfg['plate']))
    k = cfg['k']
    P = sil(g, cfg['crop_plan'], [(a - cfg['crop_plan'][0], b - cfg['crop_plan'][1], c - cfg['crop_plan'][0], d - cfg['crop_plan'][1]) for a, b, c, d in cfg.get('mask_plan', [])])
    S = sil(g, cfg['crop_side'], [(a - cfg['crop_side'][0], b - cfg['crop_side'][1], c - cfg['crop_side'][0], d - cfg['crop_side'][1]) for a, b, c, d in cfg.get('mask_side', [])])
    F = sil(g, cfg['crop_front'])
    ys, xs = np.nonzero(P); pxmin, pxmax = xs.min(), xs.max()
    # saucer: vertical extent of the plan disc, front edge = leftmost ink
    sau = P[:, pxmin:pxmin + int(0.9 * (pxmax - pxmin) * 0.5)]
    sy = np.nonzero(sau.any(1))[0]; cy = (sy.min() + sy.max()) / 2; R_px = (sy.max() - sy.min()) / 2
    cx = pxmin + R_px
    plan_mid = (pxmin + pxmax) / 2
    ys, xs = np.nonzero(S); sxmin, sxmax = xs.min(), xs.max(); side_mid = (sxmin + sxmax) / 2
    # rim mid-plane at the bow (side view)
    c = sxmin + 25; r = runs(S[:, c]); zref = (r[0][0] + r[0][1]) / 2
    # side saucer centre: symmetry of the lower hull (level halfway between rim bottom and the lower-hull bottom)
    def mainrun(x):  # the run through the rim mid-plane (skips leader arrow tips and ticks above/below)
        rr = [q for q in runs(S[:, x]) if q[0] <= zref <= q[1]]
        if rr: return rr[0]
        rr = runs(S[:, x])
        return max(rr, key=lambda q: q[1] - q[0]) if rr else None
    bot = {x: mainrun(x)[1] for x in range(sxmin, sxmin + int(2 * R_px)) if mainrun(x)}
    rimb = bot[sxmin + 40]; deep = max(bot[x] for x in range(int(cx - 60), int(cx - 20)))
    lvl = (rimb + deep) / 2
    xf = next(x for x in sorted(bot) if bot[x] > lvl)
    xr = xf
    while bot.get(xr + 1, 0) > lvl: xr += 1
    cxs = (xf + xr) / 2
    ys, xs = np.nonzero(F); fxmin, fxmax = xs.min(), xs.max()
    c = fxmin + 15; r = runs(F[:, c]); zref_f = (r[0][0] + r[0][1]) / 2
    fcx = cfg.get('front_cx', (fxmin + fxmax) / 2)
    Y = lambda px: (px - plan_mid) / k
    Ys = lambda px: (px - side_mid) / k
    Z = lambda py: -(py - zref) / k
    out = dict(k=k, plan_mid=float(plan_mid), cy=float(cy), side_mid=float(side_mid), zref=float(zref), fcx=float(fcx), zref_f=float(zref_f),
               saucer_cx_plan=float(cx), saucer_cx_side=float(cxs), R=float(R_px / k), saucer_y=float(Y(cx)),
               length_drawn=float((pxmax - pxmin) / k), breadth_drawn=float(2 * R_px / k))
    # ---- saucer half-profile (front half of the side view) ----
    cols = list(range(sxmin, int(cxs) + 1))
    top = [mainrun(x)[0] for x in cols]; bt = [mainrun(x)[1] for x in cols]
    top = spline(top, 20); bt = spline(bt, 20)
    out['saucer'] = [[round((cxs - x) / k, 3), round(Z(t), 3), round(Z(b), 3)] for x, t, b in zip(cols, top, bt)]
    # saucer top behind the centre (rises to the impulse deck) at the centre-line
    cols = list(range(int(cxs), cfg['deck_aft_side'] + 1))
    tr = spline([mainrun(x)[0] for x in cols], 0, .6)
    out['top_rear'] = [[round(Ys(x), 3), round(Z(t), 3)] for x, t in zip(cols, tr)]
    # ---- nacelle (warp propulsion unit) ----
    nf, ne, nm = cfg['nac_front_side'], sxmax, cfg['nac_mid_row']
    while not any(q[0] <= nm <= q[1] for q in runs(S[:, nf])): nf += 1
    cols = list(range(nf, ne + 1)); T, B = [], []
    for x in cols:
        rr = [q for q in runs(S[:, x]) if q[0] <= nm <= q[1]]
        if not rr: rr = [min(runs(S[:, x]), key=lambda q: abs((q[0] + q[1]) / 2 - nm))]
        T.append(rr[0][0]); B.append(rr[0][1])
    T = np.array(T, float); B = np.array(B, float)
    ntop = cfg['nac_top_row']
    badT = (T < ntop - 3) & (np.array(cols) > nf + 60)          # pylon root / grille pods rising above the body
    T = spline(interp_bad(T, badT), 12, .5); B = spline(B, 12, .5)
    # plan width where the nacelle is visible (aft of the impulse deck)
    pv0 = cfg['nac_plan_visible']; W = {}
    for x in range(pv0, pxmax + 1):
        rr = [q for q in runs(P[:, x]) if q[0] <= cy <= q[1]]
        if rr: W[x] = rr[0]
    wx = np.array(sorted(W)); wlo = np.array([W[x][0] for x in wx], float); whi = np.array([W[x][1] for x in wx], float)
    wd = whi - wlo; med = np.median(wd[: len(wd) // 2])
    bad = (wd > med + 3) & (wx < pxmax - 45)                         # grille pods
    wlo = spline(interp_bad(wlo, bad), 0, .5); whi = spline(interp_bad(whi, bad), 0, .5)
    # side px -> plan px for the same station
    shift = plan_mid - side_mid
    secs = []
    h_vis = None
    for i, x in enumerate(cols):
        xp = x + shift
        zc, h = (T[i] + B[i]) / 2, (B[i] - T[i]) / 2
        if xp >= wx[0]:
            j = min(int(round(xp - wx[0])), len(wx) - 1)
            xc, w = (wlo[j] + whi[j]) / 2, (whi[j] - wlo[j]) / 2
            if h_vis is None: h_vis = None
        else:
            xc, w = cy, None
        secs.append([x, xc, w, zc, h])
    j0 = next(i for i, s in enumerate(secs) if s[2] is not None)
    ratio = secs[j0][2] / secs[j0][4]
    # forward of the plan's visible part the nacelle is hidden under the saucer: keep the measured width/height ratio,
    # but never narrower than the visible width (the side view shows the body deepening forward)
    rh = cfg.get('nac_hidden_ratio', ratio); nb = cfg.get('nac_hidden_blend', 30)
    for i, s in enumerate(secs[:j0]):
        f = min(1.0, (j0 - i) / nb)
        s[2] = s[4] * (ratio + (rh - ratio) * f)
    out['nacelle'] = [[round(Ys(x), 3), round((xc - cy) / k, 3), round(w / k, 3), round(Z(zc), 3), round(h / k, 3)] for x, xc, w, zc, h in secs[::2]]
    out['nacelle_top_z'] = float(Z(ntop)); out['nacelle_axis_z'] = float(Z(np.median((T + B) / 2)))
    # plan extents of the deck
    out['plan_extent'] = [float(Y(pxmin)), float(Y(pxmax))]
    ys_, xs_ = np.nonzero(S); out['side_z_extent'] = [float(Z(ys_.max())), float(Z(ys_.min()))]
    ys_, xs_ = np.nonzero(F); out['front_x_extent'] = [float((xs_.min() - fcx) / k), float((xs_.max() - fcx) / k)]
    return out


if __name__ == '__main__':
    ship = sys.argv[1]
    cfg = importlib.import_module(ship).CFG
    out = measure(cfg)
    os.makedirs(os.path.join(HERE, 'profiles'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'profiles', ship + '-hull.json'), 'w'), indent=0)
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list) or len(v) < 4}, indent=1))
