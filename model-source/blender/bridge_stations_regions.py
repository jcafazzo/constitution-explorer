"""Measure the three main-bridge wall stations into profiles/bridge-stations.json.
Run: /usr/bin/python3 -E model-source/blender/bridge_stations_regions.py <plate-dir>
<plate-dir> holds 1400 px renders plate-<page>.png (pdftoppm -scale-to-x 1400 -scale-to-y -1); the published
dist/assets/equipment/page-<page>.webp files are the same renders.

Each station has three views on two sheets:
  front elevation + View A-A (a section through the centre line), at the sheet's 0-80 cm bar;
  View B-B, the controls console seen square-on to its sloping top, at the 0-50 cm bar on the next sheet.
Hand-read key points (plate px) are listed in STATIONS; the console's panels and buttons are traced automatically from B-B.
Model frame: x across the station (+x to the operator's right), y = depth with the back wall at 0 and the operator at -y,
z up from the bridge deck. All lengths in cm."""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model-source', 'accuracy'))
from plate_silhouette import silhouette
PLATES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'assets', 'equipment')
OUT = os.path.join(ROOT, 'model-source', 'blender', 'profiles', 'bridge-stations.json')

def gray(p):
    f = os.path.join(PLATES, f'plate-{p}.png')
    if not os.path.exists(f): f = os.path.join(PLATES, f'page-{p}.webp')
    return np.asarray(Image.open(f).convert('L'), dtype=np.float32) / 255.0

STATIONS = {
 'command-intelligence': dict(
  front=110, console=111, bar=(1048, 1275, 80), bar_bb=(1030, 1246, 50),
  back=214, deck=1743,
  section=dict(  # plate px, View A-A
   housing=[(214, 1087), (548, 1087), (541, 1118), (531, 1123), (480, 1348), (458, 1350), (214, 1350)],
   band=[(214, 1350), (458, 1350), (491, 1459), (214, 1459)],
   console=[(214, 1459), (491, 1459), (658, 1517), (658, 1528), (538, 1528), (538, 1540), (214, 1540)],
   lip=[(538, 1528), (658, 1528), (658, 1540), (538, 1540)],
   pedestal=[(214, 1540), (538, 1540), (494, 1743), (214, 1743)]),
  face=((531, 1123), (480, 1348)), band_face=((458, 1350), (491, 1459)), slope=((658, 1517), (491, 1459)), ped_face=((538, 1540), (494, 1743)),
  chair_crop=(560, 1400, 760, 1750),
  f_deck=990, f_top=345, xc=743.5,
  f_outline=[(308, 345), (1184, 345), (1201, 598), (1208, 601), (1208, 703), (1150, 769), (1150, 783), (1184, 784), (1197, 990),
             (289, 990), (303, 784), (332, 783), (332, 769), (279, 703), (279, 601), (290, 598)],
  vi_panel=(372, 1117, 378, 612), displays=[(505, 700, 413, 553), (790, 988, 413, 553)],
  cds=[(312, 392), (417, 499), (525, 712, 618, 652), (545, 700, 664, 700), (774, 859), (883, 964), (989, 1070), (1094, 1179)],
  vents=[(415, 630, 850, 920), (860, 1072, 850, 920)],
  bb_front=((914, 423), (820, 1026), (836, 1139), (908, 1639)), bb_back=((633, 334), (536, 997), (579, 1355), (629, 1722)),
  bb_crop=(470, 310, 940, 1745), line_th=.3, button_th=.78, band_rows=(601, 703), scanner=dict(bb=(700, 1600), base=(28, 25), top=(15.5, 14), h=31)),
 'communications': dict(
  front=135, console=136, bar=(1022, 1253, 80), bar_bb=(987, 1202, 50),
  back=206, deck=1730,
  section=dict(
   housing=[(206, 1070), (558, 1070), (492, 1329), (467, 1332), (206, 1332)],
   band=[(206, 1332), (467, 1332), (499, 1446), (206, 1446)],
   console=[(206, 1446), (499, 1446), (670, 1501), (670, 1510), (546, 1510), (546, 1521), (206, 1521)],
   lip=[(546, 1510), (670, 1510), (670, 1521), (546, 1521)],
   pedestal=[(206, 1521), (546, 1521), (504, 1730), (206, 1730)]),
  face=((558, 1070), (492, 1329)), band_face=((467, 1332), (499, 1446)), slope=((670, 1501), (499, 1446)), ped_face=((546, 1521), (504, 1730)),
  chair_crop=(575, 1390, 775, 1735),
  f_deck=970, f_top=321, xc=734,
  f_outline=[(298, 321), (1177, 321), (1193, 576), (1199, 579), (1199, 688), (1143, 750), (1143, 764), (1177, 766), (1186, 970),
             (275, 970), (290, 766), (325, 764), (325, 750), (269, 688), (269, 579), (279, 576)],
  vi_panel=(362, 1122, 352, 585), displays=[(497, 692, 390, 528), (780, 977, 390, 528)],
  cds=[(298, 384), (405, 490), (511, 598), (620, 704), (764, 851), (871, 957), (977, 1064), (1084, 1172)],
  vents=[(400, 618, 828, 898), (848, 1065, 828, 898)],
  bb_front=((843, 413), (767, 912), (766, 1135), (837, 1638)), bb_back=((567, 330), (464, 1021), (464, 1021), (560, 1724)),
  bb_crop=(420, 300, 900, 1740), line_th=.4, button_th=.88, band_rows=(579, 688), scanner=None),
 'engineering': dict(
  front=140, console=141, bar=(1062, 1301, 80), bar_bb=(1022, 1242, 50),
  back=218, deck=1770,
  section=dict(
   housing=[(218, 1093), (518, 1092), (514, 1120), (501, 1132), (451, 1361), (425, 1364), (218, 1364)],
   band=[(218, 1364), (425, 1364), (456, 1475), (218, 1475)],
   console=[(218, 1475), (456, 1475), (633, 1536), (633, 1546), (510, 1546), (510, 1560), (218, 1560)],
   lip=[(510, 1546), (633, 1546), (633, 1560), (510, 1560)],
   pedestal=[(218, 1560), (510, 1560), (468, 1770), (218, 1770)]),
  face=((501, 1132), (451, 1361)), band_face=((425, 1364), (456, 1475)), slope=((633, 1536), (456, 1475)), ped_face=((510, 1560), (468, 1770)),
  chair_crop=(540, 1430, 730, 1775),
  f_deck=990, f_top=327, xc=759.5,
  f_outline=[(312, 327), (1212, 327), (1230, 585), (1237, 590), (1237, 700), (1171, 767), (1171, 778), (1212, 780), (1223, 990),
             (293, 990), (306, 780), (348, 778), (348, 767), (282, 700), (282, 590), (292, 585)],
  vi_panel=(380, 1155, 360, 573), displays=[(514, 717, 398, 542), (807, 1012, 398, 542)],
  cds=[(315, 399), (423, 508), (533, 617), (644, 727), (791, 877), (902, 986), (1012, 1095), (1120, 1205)],
  vents=[(420, 640, 845, 918), (878, 1098, 845, 918)],
  bb_front=((882, 418), (802, 933), (801, 1152), (872, 1667)), bb_back=((601, 335), (493, 1038), (493, 1038), (590, 1751)),
  bb_crop=(440, 300, 990, 1770), line_th=.42, button_th=.85, band_rows=(590, 700), scanner=dict(bb=(660, 1545), base=(27, 25), top=(15, 14), h=30)),
}

# operator's chair, seen from the front (shared by all three sheets; half-widths in cm at heights above the deck)
CHAIR_FRONT = [(0, 17.6), (1.5, 16.0), (4, 8.0), (6, 4.2), (8, 3.6), (35, 3.6), (37, 5.0), (40, 12.0), (45, 18.0), (52, 21.5),
               (60, 22.4), (66, 21.5), (71, 20.5), (85, 17.5), (100, 14.0), (114, 11.5)]

def intersect(p1, p2, p3, p4):
    p1, p2, p3, p4 = map(np.asarray, (p1, p2, p3, p4)); d1, d2 = p2 - p1, p4 - p3
    t = np.cross(p3 - p1, d2) / np.cross(d1, d2)
    return p1 + t * d1

out = {}
for sid, S in STATIONS.items():
    ppc = (S['bar'][1] - S['bar'][0]) / S['bar'][2]
    ppb = (S['bar_bb'][1] - S['bar_bb'][0]) / S['bar_bb'][2]
    deck, back = S['deck'], S['back']
    sec = lambda p: (round(-(p[0] - back) / ppc, 3), round((deck - p[1]) / ppc, 3))
    H = (deck - S['section']['housing'][0][1]) / ppc
    fz = H / (S['f_deck'] - S['f_top'])                      # front elevation heights scaled to the section's
    fr = lambda p: (round((p[0] - S['xc']) / ppc, 3), round((S['f_deck'] - p[1]) * fz, 3))
    st = dict(ppc=ppc, ppc_bb=ppb, height=round(H, 2),
              section={k: [sec(p) for p in v] for k, v in S['section'].items()},
              face=[sec(p) for p in S['face']], band_face=[sec(p) for p in S['band_face']],
              slope=[sec(p) for p in S['slope']], ped_face=[sec(p) for p in S['ped_face']],
              front=[fr(p) for p in S['f_outline']])
    # rectangles on the front elevation -> (x0, x1, z0, z1) cm
    rect = lambda r: (round((r[0] - S['xc']) / ppc, 2), round((r[1] - S['xc']) / ppc, 2), round((S['f_deck'] - r[3]) * fz, 2), round((S['f_deck'] - r[2]) * fz, 2))
    g = gray(S['front'])
    cds = []; found = []
    for c in S['cds']:
        if len(c) == 2:   # find the screen's rows: light (stippled) pixels in the band at the screen's middle column
            r0, r1 = S['band_rows']; xm = (c[0] + c[1]) // 2; col = g[r0 + 3:r1 - 3, xm - 3:xm + 4].mean(1) > .45
            rows = np.where(col)[0] + r0 + 3; runs = np.split(rows, np.where(np.diff(rows) > 2)[0] + 1); r = max(runs, key=len)
            c = (c[0], c[1], int(r[0]), int(r[-1])); found.append(c)
        cds.append(c)
    r0m, r1m = int(np.median([c[2] for c in found])), int(np.median([c[3] for c in found]))   # one row height for the plain screens
    cds = [rect(c if (len(S['cds'][i]) == 4) else (c[0], c[1], r0m, r1m)) for i, c in enumerate(cds)]
    st.update(vi_panel=rect(S['vi_panel']), displays=[rect(r) for r in S['displays']], cds=cds, vents=[rect(r) for r in S['vents']])
    # chair: side silhouette from View A-A
    a, b, c_, d = S['chair_crop']
    m = silhouette(g[b:d, a:c_], keep=1, open_=3)
    cs = measure.approximate_polygon(max(measure.find_contours(np.pad(m, 1).astype(float), .5), key=len), 1.0)
    st['chair_side'] = [sec((a + p[1] - 1, b + p[0] - 1)) for p in cs[:-1]]
    st['chair_front'] = CHAIR_FRONT
    # ---- View B-B: console frame per half, panels and buttons ----
    gb = gray(S['console'])
    f_top, f_kup, f_klo, f_bot = map(np.asarray, S['bb_front']); b_top, b_kup, b_klo, b_bot = map(np.asarray, S['bb_back'])
    K = intersect(f_top, f_kup, f_klo, f_bot); KB = intersect(b_top, b_kup, b_klo, b_bot)
    halves = {}
    for name, end, bend in (('right', f_top, b_top), ('left', f_bot, b_bot)):
        u = (end - K) / np.linalg.norm(end - K)
        n = np.array([-u[1], u[0]]) if name == 'left' else np.array([u[1], -u[0]])
        if np.dot(KB - K, n) < 0: n = -n                      # n points from the front edge toward the back
        halves[name] = dict(u=u, n=n, front_len=round(float(np.linalg.norm(end - K)) / ppb, 2),
                            back_len=round(float(np.dot(bend - K, u)) / ppb, 2), depth=round(float(np.dot(bend - K, n)) / ppb, 2),
                            angle_deg=round(float(np.degrees(np.arctan2(abs(u[0]), abs(u[1])))), 2))
    def to_console(P):
        P = np.asarray(P, float); side = 'right' if P[1] < K[1] else 'left'; h = halves[side]
        a_ = float(np.dot(P - K, h['u'])) / ppb; d_ = float(np.dot(P - K, h['n'])) / ppb
        return side, (round(a_ if side == 'right' else -a_, 3), round(d_, 3))
    x0, y0, x1, y1 = S['bb_crop']
    sub = gb[y0:y1, x0:x1]
    lines = ndi.binary_closing(ndi.binary_opening(sub < S['line_th'], np.ones((2, 2))), np.ones((3, 3)))
    con = ndi.binary_fill_holes(ndi.binary_closing(sub < .8, np.ones((5, 5)), iterations=2))
    cl, cn = ndi.label(con); con = cl == (np.argmax(ndi.sum(con, cl, range(1, cn + 1))) + 1)
    con_in = ndi.binary_erosion(con, iterations=7)          # panels lie wholly inside the console; background pieces reach its edge
    lab, n = ndi.label(~lines); sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    panels = []; pmask = np.zeros_like(lines)
    for i, s in enumerate(sizes):
        if not (1500 < s < 80000): continue
        r = lab == (i + 1)
        if r[0].any() or r[-1].any() or r[:, 0].any() or r[:, -1].any(): continue
        ys, xs = np.where(r); tone = sub[r].mean()
        if tone > .8 or (r & ~con_in).any(): continue                                    # white areas (the scanner hood, the seat) are not panels
        pmask |= r
        poly = measure.approximate_polygon(max(measure.find_contours(np.pad(r, 1).astype(float), .5), key=len), 1.5)
        pts = [(x0 + p[1] - 1, y0 + p[0] - 1) for p in poly[:-1]]
        side, _ = to_console((x0 + xs.mean(), y0 + ys.mean()))
        mapped = [to_console(p)[1] for p in pts]
        if side == 'left': mapped = mapped[::-1]
        panels.append(dict(side=side, area_cm2=round(float(s) / ppb ** 2, 1), pts=mapped))
    # buttons and lamps: small closed outlines inside a panel, i.e. the small regions of the same line labelling, lighter than the panel
    buttons = []; bdbg = []
    inner = ndi.binary_dilation(pmask, iterations=3)
    from skimage.feature import blob_log
    sm = ndi.gaussian_filter(sub, 1.0)
    core = ndi.binary_erosion(pmask, iterations=3)
    pane_tone = float(np.median(sm[core])) if core.any() else .7
    hi = float(np.percentile(sm[core], 99.5)) if core.any() else .95
    thr = (pane_tone + hi) / 2
    for y, x, sg in blob_log(sm, min_sigma=2.2, max_sigma=5, num_sigma=6, threshold=.06):
        y, x = int(y), int(x)
        if not core[y, x] or sm[y, x] < thr: continue
        ext = []
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            k = 0
            while k < 16 and 0 <= y + dy * (k + 1) < sm.shape[0] and 0 <= x + dx * (k + 1) < sm.shape[1] and sm[y + dy * (k + 1), x + dx * (k + 1)] > thr - .06: k += 1
            ext.append(k)
        w_, h_ = ext[0] + ext[1] + 3, ext[2] + ext[3] + 3
        cx, cy = x + (ext[0] - ext[1]) / 2, y + (ext[2] - ext[3]) / 2
        side, (a_, d_) = to_console((x0 + cx, y0 + cy)); bdbg.append((int(cy), int(cx)))
        buttons.append(dict(side=side, a=a_, d=d_, w=round(w_ / ppb, 2), h=round(h_ / ppb, 2), round=bool(abs(w_ - h_) <= 2)))
    dbg = np.stack([sub * 255] * 3, -1); dbg[pmask] = dbg[pmask] * .5 + np.array([40, 90, 255]) * .5
    for c_ in bdbg: dbg[c_[0]-1:c_[0]+2, c_[1]-1:c_[1]+2] = [255, 40, 40]
    if os.environ.get('DEBUG_DIR'): Image.fromarray(dbg.astype(np.uint8)).save(os.path.join(os.environ['DEBUG_DIR'], f'bb-{sid}.png'))
    st['console'] = dict(halves={k: {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()} for k, v in halves.items()},
                         panels=panels, buttons=buttons)
    if S['scanner']:
        side, (a_, d_) = to_console(S['scanner']['bb']); st['scanner'] = dict(side=side, a=a_, d=d_, **{k: v for k, v in S['scanner'].items() if k != 'bb'})
    out[sid] = st
    print(sid, 'ppc', round(ppc, 3), 'bb', round(ppb, 3), 'H', round(H, 1), 'halves', {k: (v['front_len'], v['back_len'], v['depth'], v['angle_deg']) for k, v in halves.items()},
          'panels', len(panels), 'buttons', len(buttons), 'cds', [c[2:] for c in cds][:2])
json.dump(out, open(OUT, 'w'), indent=0, default=float)
print('wrote', OUT)
