"""Segment a manual colour-plate drawing into colourable regions (raster; no vector redraw).
usage: python3 segment.py <config.json> <id>
Config per id: page, crop [x0,y0,x1,y1] (plate px), seeds [[x, y, class], ...] in plate px, optional
"solid_black": true to treat solid ink fields as class 'black', and "scale" (output downscale).
Output dist/assets/colours/<id>-map.png: R = linework strength (0–255, halftone dot texture removed
inside halftone regions), G = class index (see CLASSES), B = 255 where the pixel is halftone in the source."""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
CLASSES = ['paper', 'tunic', 'black', 'hose', 'badge', 'field', 'metal', 'device', 'braid']
cfg = json.load(open(sys.argv[1]))[sys.argv[2]]; out_id = sys.argv[2]
g = np.asarray(Image.open(f"dist/assets/colours/page-{cfg['page']}.webp").convert('L'), dtype=np.float32) / 255
x0, y0, x1, y1 = cfg['crop']; g = g[y0:y1, x0:x1].copy()
for a, b, c, d in cfg.get('erase', []):          # labels that would contradict a chosen grade, stray frame lines
    g[max(b - y0, 0):d - y0, max(a - x0, 0):c - x0] = 1.0
ink = g < cfg.get('ink', .55)
if cfg.get('mode') == 'flag':
    # "B/W as shown" sheets: inside the emblem's own outline, paper = field colour and ink = metal/device colour.
    fieldc, inkc = CLASSES.index(cfg.get('field', 'field')), CLASSES.index(cfg.get('inkclass', 'metal'))
    solid = ndi.binary_fill_holes(ndi.binary_closing(ink, np.ones((3, 3))))
    lab, _ = ndi.label(solid); keep = np.zeros(g.shape, bool)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    lab_ink, _ = ndi.label(ink)
    for sd in cfg['seeds']:
        x, y = sd[0], sd[1]
        if len(sd) > 2 and sd[2] == 'ink':          # lettering etc.: the ink shape only, so enclosed counters stay open
            k = lab_ink[y - y0, x - x0]
            if k: keep |= lab_ink == k
            else: print('ink seed not on ink, ignored:', x, y)
            continue
        k = lab[y - y0, x - x0]
        if k and k not in border: keep |= lab == k
        else: print('flag seed outside the emblem, ignored:', x, y)
    li, ni = ndi.label(ink & keep)                 # scan dust: tiny isolated ink specks inside the field
    if ni:
        sz = ndi.sum(ink & keep, li, range(1, ni + 1)); speck = np.zeros(ni + 1, bool); speck[1:] = sz < cfg.get('speck', 40)
        ink = ink & ~speck[li]
    keep = ndi.binary_opening(keep, np.ones((3, 3)))
    cls = np.zeros(g.shape, np.uint8); cls[keep & ~ink] = fieldc; cls[keep & ink] = inkc
    edge = (np.clip((.75 - g) / .5, 0, 1) * 255).astype(np.uint8) * (keep & ink)   # antialias weight for metal
    a = keep.astype(np.uint8) * 255
    img = np.stack([edge.astype(np.uint8), cls * 20, a], -1)
    im = Image.fromarray(img); sc = cfg.get('scale', 1)
    if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.NEAREST)
    im.save(f'dist/assets/colours/{out_id}-map.png', optimize=True)
    pal = {fieldc: cfg.get('preview_field', [200, 35, 41]), inkc: cfg.get('preview_ink', [205, 208, 214]), 0: [251, 250, 245]}
    prev = np.zeros(g.shape + (3,), np.uint8)
    for k, v in pal.items(): prev[cls == k] = v
    Image.fromarray(prev).save(f'/tmp/{out_id}-preview.png'); print(out_id, 'flag', im.size, int(keep.sum())); sys.exit()
lab_i, n = ndi.label(ink); sizes = ndi.sum(ink, lab_i, range(1, n + 1))
big = np.zeros(n + 1, bool); big[1:] = sizes > cfg.get('min_line', 45)
dotsz = np.zeros(n + 1, bool); dotsz[1:] = sizes < cfg.get('dot_max', 28)
small = ink & dotsz[lab_i]                  # halftone dots are tiny; single-stroke letters (I, l) are larger
dens = ndi.uniform_filter(small.astype(np.float32), 15)
half = ndi.binary_closing(dens > .05, np.ones((9, 9)))   # halftone fields: many small dots close together
lines = ink & ~(small & half)               # keep strokes and all lettering (i-dots, decimal points); drop only halftone dots
solid = ndi.binary_opening(ink, np.ones((7, 7)))
barrier = ndi.binary_dilation(lines, np.ones((3, 3)), iterations=cfg.get('close', 1))
lab_r, _ = ndi.label(~barrier)
dense = ndi.binary_closing(ndi.uniform_filter(ink.astype(np.float32), 9) > .3, np.ones((5, 5)))
lab_d, _ = ndi.label(dense)
cls = np.zeros(g.shape, np.uint8)
for x, y, c in cfg['seeds']:
    x -= x0; y -= y0; k = CLASSES.index(c)
    if solid[y, x] and c in ('black', 'device'):
        ls, _ = ndi.label(solid); cls[ls == ls[y, x]] = k
    elif lab_r[y, x]: cls[(lab_r == lab_r[y, x]) & (cls == 0)] = k
    elif ink[y, x] and c in ('black', 'device'): cls[lab_i == lab_i[y, x]] = k   # a thin solid band drawn as one stroke
    else: print('seed on a line, ignored:', x + x0, y + y0, c)
from PIL import ImageDraw
bgl = set(np.unique(np.concatenate([lab_r[0], lab_r[-1], lab_r[:, 0], lab_r[:, -1]]))) - {0}
bg = np.isin(lab_r, list(bgl))
for c, poly in cfg.get('polys', []):          # traced bands too densely hatched to flood (neckbands, cuffs)
    pm = Image.new('L', (g.shape[1], g.shape[0]), 0); ImageDraw.Draw(pm).polygon([(x - x0, y - y0) for x, y in poly], fill=1)
    cls[np.asarray(pm, bool) & ~bg] = CLASSES.index(c)
for k in range(1, len(CLASSES)):           # absorb lettering/islands enclosed by one region
    m = cls == k
    if m.any():
        holes = ndi.binary_fill_holes(m) & ~m & (cls == 0)
        lh, nh = ndi.label(holes)
        if nh:
            hs = ndi.sum(holes, lh, range(1, nh + 1)); small = np.zeros(nh + 1, bool); small[1:] = hs < cfg.get('max_hole', 3000)
            cls[small[lh]] = k
for _ in range(3):                          # colour reaches under its boundary stroke's halo (not the stroke)
    grown = ndi.grey_dilation(cls, size=(3, 3)); cls = np.where((cls == 0) & barrier & ~lines & (grown > 0), grown, cls)
bm = cls == CLASSES.index('badge')
if bm.any():
    cls[ndi.binary_dilation(bm, np.ones((3, 3)), iterations=4) & (lines | (cls == 0))] = CLASSES.index('badge')
R = (np.clip((cfg.get('ink', .55) + .2 - g) / (cfg.get('ink', .55) + .2), 0, 1) * 255 * lines).astype(np.uint8)
# in black garments the drawing's information is light-on-dark: strokes in halftone fields, paper highlights in solid fields
solidf = ndi.binary_dilation(ndi.binary_opening(ink, np.ones((5, 5))), np.ones((3, 3)))
blk = cls == CLASSES.index('black')
hl = (np.clip((g - .35) / .4, 0, 1) * 255).astype(np.uint8)
big2 = np.zeros(n + 1, bool); big2[1:] = sizes > cfg.get('min_line_black', 160)
R = np.where(blk & ~big2[lab_i] & ~solidf, 0, R)       # inside black garments keep only real seams/folds, not dot fragments
R = np.where(blk & solidf, hl, R).astype(np.uint8)

img = np.stack([R, cls * 20, half.astype(np.uint8) * 255], -1)
sc = cfg.get('scale', 1)
im = Image.fromarray(img)
if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.NEAREST)
im.save(f'dist/assets/colours/{out_id}-map.png', optimize=True)
# preview with a neutral palette for checking
pal = np.array([[251, 250, 245], [186, 100, 31], [35, 36, 38], [197, 165, 137], [196, 154, 66], [200, 35, 41], [200, 205, 213], [32, 33, 36], [196, 154, 66]], np.float32)
base = pal[cls]; L = (R / 255.0)[..., None]
inkc = np.where((cls == 2)[..., None], np.array([150, 150, 150], np.float32), np.array([29, 29, 27], np.float32))
prev = base * (1 - L) + inkc * L
Image.fromarray(prev.astype(np.uint8)).save(f'/tmp/{out_id}-preview.png')
print(out_id, 'classes', {CLASSES[k]: int((cls == k).sum()) for k in np.unique(cls)}, 'size', im.size)
