"""Measure the tri-dimensional chess sheets (PDF 152 board, PDF 153 pieces) into profiles/tridimensional-chess-regions.json.
Run: /usr/bin/python3 -E model-source/blender/tridimensional_chess_regions.py

Plates are the 1400 px renders in dist/assets/equipment (page-152.webp, page-153.webp), uniform scale in x and y.
PDF 152: 0-20 cm bar from x 178 to 470 px  -> 14.6 px/cm.   PDF 153: 0-6 cm bar from x 932 to 1196 px -> 44.0 px/cm.
Frame (PDF 152 elevation): z up from the underside of the base, x across the sheet from the base's centre line (plate x 820).
"""
import os, sys, json
import numpy as np
from scipy import ndimage as ndi
from skimage import measure
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'model-source', 'accuracy'))
from plate_silhouette import load_gray, silhouette

OUT = os.path.join(ROOT, 'model-source', 'blender', 'profiles', 'tridimensional-chess-regions.json')
PPC_B, PPC_P = (470 - 178) / 20, (1196 - 932) / 6

# ---------------- PDF 152: board assembly ----------------
g = load_gray(os.path.join(ROOT, 'dist/assets/equipment/page-152.webp'))
X0, Y0, X1, Y1 = 440, 940, 1260, 1800
m = g[Y0:Y1, X0:X1] < 0.6
m = ndi.binary_closing(m, np.ones((3, 3)), iterations=2)
m = ndi.binary_fill_holes(m)
m = ndi.binary_opening(m, np.ones((6, 6)))
lab, n = ndi.label(m); sizes = ndi.sum(m, lab, range(1, n + 1))
elev = lab == (np.argmax(sizes) + 1)
rows = np.where(elev.any(1))[0]
YB = Y0 + rows.max() + 1                   # underside of the base (plate px)

# centre line: the base is turned, so its mid-line over the foot rows
foot = [np.where(elev[r])[0] for r in range(rows.max() - 40, rows.max() - 5)]
XC = X0 + float(np.mean([(c.min() + c.max() + 1) / 2 for c in foot]))
cm_x = lambda px: (px - XC) / PPC_B
cm_z = lambda py: (YB - py) / PPC_B

# board levels (top face, plate y) and pin/post positions read off the elevation
levels = {'B': 953, 'N': 1244, 'W': 1535, 'A_black': 809, 'A_white': 1387}
level_z = {k: round(cm_z(v), 3) for k, v in levels.items()}
board_x = {'B': (530, 852), 'N': (700, 1020), 'W': (865, 1185)}
pins_x = {'B': (548, 830), 'N': (717, 1000), 'W': (883, 1163)}

# frame: erase the boards (and their pins/posts) from the elevation; what is left above the stem top is the frame
STEM_Y = 1616
fr = elev.copy()
for k, (a, b) in board_x.items():
    y = levels[k] - Y0; fr[max(y - 3, 0):y + 10, a - 25 - X0:b + 25 - X0] = False
for k, xs in pins_x.items():
    y = levels[k] - Y0
    for x in xs: fr[max(y - 30, 0):y + 35, x - 12 - X0:x + 12 - X0] = False
fr[1380 - Y0:1405 - Y0, 1080 - X0:1260 - X0] = False   # white attack board
fr[1380 - Y0:1560 - Y0, 1150 - X0:1185 - X0] = False   # its post
fr[STEM_Y - Y0:, :] = False
fr = ndi.binary_opening(fr, np.ones((3, 3)))
lab, n = ndi.label(fr); sizes = ndi.sum(fr, lab, range(1, n + 1))
frame = lab == (np.argmax(sizes) + 1)
polys = []
for c in measure.find_contours(np.pad(frame, 1).astype(float), 0.5):
    c = measure.approximate_polygon(c, 0.7)
    if len(c) < 8: continue
    polys.append([(round(cm_x(X0 + p[1] - 1), 3), round(cm_z(Y0 + p[0] - 1), 3)) for p in c[:-1]])
polys.sort(key=len, reverse=True)

# base: radius per row below the stem top (turned)
base = []
for r in range(STEM_Y - Y0 - 6, rows.max() + 1, 2):
    c = np.where(elev[r])[0]
    c = c[np.abs(X0 + c - XC) < 200]
    if len(c): base.append((round(max(XC - (X0 + c.min()), X0 + c.max() + 1 - XC) / PPC_B, 3), round(cm_z(Y0 + r), 3)))

# frame width in plan: the strip at plate y 537-553
plan_frame_w = round((553 - 537) / PPC_B, 3)

# plan: board grid. B starts at x 530 and W ends at 1185 (8 files), the boards are 4 squares deep from y 385 to 700
plan = dict(x_start=round(cm_x(530), 3), x_end=round(cm_x(1185), 3), y_top=385, y_bottom=700,
            square_x=round((1185 - 530) / 8 / PPC_B, 3), square_y=round((700 - 385) / 4 / PPC_B, 3),
            pin_inset=round(np.mean([548 - 530, 1185 - 1163, 408 - 385, 700 - 686]) / PPC_B, 3),
            attack_size=round((632 - 472) / PPC_B, 3))

# ---------------- PDF 153: pieces ----------------
gp = load_gray(os.path.join(ROOT, 'dist/assets/equipment/page-153.webp'))
crops = {'king': (95, 315, 312, 727), 'queen': (318, 315, 522, 727), 'bishop': (524, 315, 697, 727),
         'knight': (703, 315, 878, 727), 'rook': (882, 315, 1052, 727), 'pawn': (1058, 315, 1208, 727)}
pieces = {}
for name, (a, b, c_, d) in crops.items():
    s = silhouette(gp[b:d, a:c_], keep=1, open_=3)
    rr = np.where(s.any(1))[0]; base_rows = [np.where(s[r])[0] for r in range(rr.max() - 12, rr.max() - 2)]
    ax = float(np.mean([(q.min() + q.max() + 1) / 2 for q in base_rows]))
    yb = rr.max() + 1
    prof = []
    for r in range(rr.min(), rr.max() + 1):
        q = np.where(s[r])[0]
        if len(q): prof.append((round((yb - r) / PPC_P, 4), round((q.min() - ax) / PPC_P, 4), round((q.max() + 1 - ax) / PPC_P, 4)))
    entry = dict(axis_px=round(a + ax, 2), base_px=b + int(yb), height=round((yb - rr.min()) / PPC_P, 3), rows=prof[::-1])
    if name == 'knight':
        cs = measure.find_contours(np.pad(s, 1).astype(float), 0.5)
        cc = measure.approximate_polygon(max(cs, key=len), 0.6)
        entry['side'] = [(round((p[1] - 1 - ax) / PPC_P, 3), round((yb - (p[0] - 1)) / PPC_P, 3)) for p in cc[:-1]]
    pieces[name] = entry

# knight front view (head seen face-on): width per row, heights scaled to the side view's height
fa, fb, fc, fd = 735, 980, 850, 1250
fs = silhouette(gp[fb:fd, fa:fc], keep=1, open_=3)
fr_ = np.where(fs.any(1))[0]; H = (fr_.max() + 1 - fr_.min())
front = []
for r in range(fr_.min(), fr_.max() + 1, 2):
    q = np.where(fs[r])[0]
    front.append((round((fr_.max() + 1 - r) / H, 4), round((q.max() + 1 - q.min()) / PPC_P, 4)))
pieces['knight']['front_width'] = front[::-1]   # (fraction of height, full width cm), top first

json.dump(dict(ppc_board=PPC_B, ppc_pieces=PPC_P, xc_px=XC, base_px=YB, levels_px=levels, level_z=level_z,
               board_x_cm={k: [round(cm_x(a), 3), round(cm_x(b), 3)] for k, (a, b) in board_x.items()},
               pins_x_cm={k: [round(cm_x(a), 3), round(cm_x(b), 3)] for k, (a, b) in pins_x.items()},
               frame=polys, base=base, frame_depth=plan_frame_w, plan=plan, pieces=pieces),
          open(OUT, "w"), indent=0, default=float)
print('wrote', OUT)
print('XC', round(XC, 1), 'YB', YB, 'levels', level_z, 'frame polys', [len(p) for p in polys], 'base rows', len(base))
print('plan', plan)
for k, v in pieces.items(): print(k, 'axis', v['axis_px'], 'h', v['height'], 'w', round(max(r[2] - r[1] for r in v['rows']), 3))
