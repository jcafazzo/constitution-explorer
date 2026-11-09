"""Measure the Vulcan lyrette's front elevation (PDF 151, TO 03:98:10) into material regions.
Run with system Python from the repo root: python3 model-source/blender/vulcan_lyrette_regions.py [--debug out.png]
Writes model-source/blender/profiles/vulcan-lyrette-regions.json: closed outlines in cm (x right, z up, origin at
the foot tip) for the silhouette and each material, plus the fret-bar line and the measured string fan.

Plate: dist/assets/equipment/page-151.webp (1400 px). The 0-40 cm bar measures 822.5 -> 1288.5 px: 11.65 px/cm.
Materials (the sheet's key): Li'pon = dark fine-grain teak (dark stipple), Sher Skah = mountain luan (light stipple),
Bahun'ahb = mother-of-pearl (white)."""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'accuracy'))
from plate_silhouette import load_gray, silhouette

PPC = 11.65
X0, Y0, X1, Y1 = 570, 310, 1170, 1700                 # front-elevation crop (plate px)
g = load_gray('dist/assets/equipment/page-151.webp')
c = g[Y0:Y1, X0:X1]
H, W = c.shape
P = lambda x, y: (x - X0, y - Y0)                      # plate px -> crop px

# 1. silhouette. Strings in the open air beside the neck get filled by the ink closing, so above the
#    voice box the neck is rebuilt as a band of measured width from its clean outer (left) edge.
sil = silhouette(c, open_=4, holes=[P(800, 800), P(760, 620)])
NECK_W = [(420, 38), (480, 40), (560, 46), (640, 50), (700, 52), (760, 54), (800, 55), (840, 56), (880, 58), (912, 60)]
ny = np.array([a for a, _ in NECK_W]); nw = np.array([b for _, b in NECK_W], float)
for yy in range(420, 913):
    r = yy - Y0; xs = np.where(sil[r])[0]
    if not len(xs): continue
    keep = np.zeros(W, bool); xo = xs.min(); keep[xo:xo + int(round(np.interp(yy, ny, nw)))] = True
    sil[r] &= keep
sil = ndi.binary_opening(sil, np.ones((3, 3))); sil = ndi.binary_fill_holes(sil)
lab, n = ndi.label(sil); sizes = ndi.sum(sil, lab, range(1, n + 1)); sil = lab == (np.argmax(sizes) + 1)

# 2. mother-of-pearl: the white panels enclosed by heavy outlines (seeded flood fill on the inked lines)
ink = ndi.binary_closing(c < 0.8, np.ones((3, 3)), iterations=1)   # stipple counts as ink, so only clean white panels stay free
free, _ = ndi.label(~ink)
def panel(seed, lo=1500, hi=40000):
    # the enclosed white component nearest the seed along its row (the seed itself may sit on a line)
    for d in range(0, 40):
        for x in (seed[0] + d, seed[0] - d):
            k = free[seed[1], x]
            if k and lo < (free == k).sum() < hi: break
        else: continue
        break
    m = free == k
    return ndi.binary_dilation(m, iterations=2) & sil
nacre_back = panel(P(680, 1100))
nacre_ctrl = panel(P(1000, 1060))

# 3. Li'pon (dark teak): the whole neck above the voice box, then the edge strip down the back to the foot.
#    The strip's width is measured row by row on the plate (left silhouette edge to the first clean white or light
#    stipple run), since the dense string fan beside it defeats a tone threshold.
STRIP_W = [(912, 60), (960, 39), (1000, 32), (1040, 31), (1080, 28), (1120, 27), (1200, 25), (1240, 25), (1280, 23), (1320, 23),
           (1360, 20), (1400, 19), (1440, 17), (1480, 15), (1520, 13), (1560, 12), (1640, 12), (1689, 6)]
sy = np.array([a for a, _ in STRIP_W]); sw = np.array([b for _, b in STRIP_W], float)
yy, xx = np.mgrid[0:H, 0:W]
teak = np.zeros_like(sil); teak[:913 - Y0] = sil[:913 - Y0]
for y in range(913, Y1):
    r = y - Y0; xs = np.where(sil[r])[0]
    if len(xs): teak[r, xs.min():xs.min() + int(round(np.interp(y, sy, sw)))] = True
teak &= sil & ~nacre_back
luan = sil & ~teak

# 4. outlines -> cm polygons (x right, z up, origin at the foot tip)
ys, xs = np.where(sil); foot = (float(xs[ys == ys.max()].mean()), float(ys.max()))
def to_cm(x, y): return [round((x - foot[0]) / PPC, 3), round((foot[1] - y) / PPC, 3)]
def polys(mask, tol=0.6, min_area=60):
    mask = ndi.binary_fill_holes(mask); out = []
    for cnt in measure.find_contours(np.pad(mask, 1).astype(float), 0.5):
        cnt = measure.approximate_polygon(cnt - 1, tol)
        if len(cnt) < 4: continue
        a = 0.5 * abs(np.dot(cnt[:, 0], np.roll(cnt[:, 1], 1)) - np.dot(cnt[:, 1], np.roll(cnt[:, 0], 1)))
        if a < min_area: continue
        out.append([to_cm(x, y) for y, x in cnt[:-1]])
    return out

# fret bar: the white line along the inner half of the neck band, found row by row as the brightest
# (smoothed) column in 40-95 % of the band, then smoothed along the neck
bs = ndi.gaussian_filter(c, 1.2); FRET = []
for yy in range(380, 871, 12):
    r = yy - Y0; xs = np.where(sil[r])[0]; xo = xs.min(); w = np.interp(yy, ny, nw)
    a, b2 = int(xo + .4 * w), int(xo + .95 * w)
    FRET.append([float(a + np.argmax(bs[r, a:b2])) + X0, yy])
FRET = np.array(FRET); FRET[:, 0] = np.convolve(np.pad(FRET[:, 0], 2, mode='edge'), np.ones(5) / 5, 'valid')
FRET = [(float(x), float(y)) for x, y in FRET]
STRING_END = (690, 1338); BRIDGE_Y = 1162
fp = lambda p: to_cm(p[0] - X0, p[1] - Y0)
data = {
    'source': 'PDF 151, plate 1400 px, 11.65 px/cm (0-40 cm bar 822.5-1288.5 px); origin = foot tip; x right, z up (cm)',
    'ppc': PPC, 'crop': [X0, Y0, X1, Y1], 'foot_px': [foot[0] + X0, foot[1] + Y0],
    'silhouette': polys(sil), 'silhouette_inset': polys(ndi.binary_erosion(sil)), 'teak': polys(teak), 'luan': polys(luan),
    'nacre_back': polys(nacre_back), 'nacre_control': polys(nacre_ctrl),
    'fret': [fp(p) for p in FRET], 'thickness': round(49 / PPC, 3), 'pins': 30, 'bridge_x': [fp((690, 0))[0], fp((780, 0))[0]], 'string_end': fp(STRING_END), 'bridge_z': fp((0, BRIDGE_Y))[1],
    'rosette': {'centre': fp((793, 1363)), 'r_outer': round(63 / PPC, 3), 'r_inner': round(31 / PPC, 3)},
    'knobs': [{'name': n, 'centre': fp(p), 'r': round(13 / PPC, 3)} for n, p in
              [('Voicer', (840, 972)), ('Decay', (883, 995)), ('Brilliance', (920, 1020)), ('Resonance', (955, 1045))]],
}
os.makedirs('model-source/blender/profiles', exist_ok=True)
json.dump(data, open('model-source/blender/profiles/vulcan-lyrette-regions.json', 'w'))
ext = np.array([p for poly in data['silhouette'] for p in poly])
print('height cm', round(ext[:, 1].max() - ext[:, 1].min(), 2), 'width cm', round(ext[:, 0].max() - ext[:, 0].min(), 2),
      {k: len(data[k]) for k in ('silhouette', 'teak', 'luan', 'nacre_back', 'nacre_control')},
      'nacre px', int(nacre_back.sum()), int(nacre_ctrl.sum()))
if '--debug' in sys.argv:
    rgb = np.stack([c * 255] * 3, -1).astype(np.uint8)
    for m, col in ((luan, (230, 190, 120)), (teak, (120, 60, 30)), (nacre_back, (120, 220, 255)), (nacre_ctrl, (120, 255, 200))):
        rgb[m] = (0.45 * rgb[m] + 0.55 * np.array(col)).astype(np.uint8)
    for x, y in FRET: rgb[int(y) - Y0 - 2:int(y) - Y0 + 3, int(x) - X0 - 2:int(x) - X0 + 3] = (255, 0, 0)
    Image.fromarray(rgb).save(sys.argv[sys.argv.index('--debug') + 1])
