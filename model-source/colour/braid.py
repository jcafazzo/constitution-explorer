"""Cut one rank-braid stripe from PDF 65 (Lieutenant swatch), rotate it level and save as a map:
R = stroke weight, G = class (8 = braid), A = inside the braid. Used to stamp cuff stripes on the uniforms."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
im = Image.open('dist/assets/colours/page-65.webp').convert('L').crop((230, 1080, 500, 1340)).rotate(45, expand=True, fillcolor=255, resample=Image.BICUBIC)
g = np.asarray(im, np.float32) / 255; ink = g < .55
inside = ndi.binary_fill_holes(ndi.binary_closing(ink, np.ones((3, 3))))
# the braid is the long horizontal component through the middle; the swatch background (halftone) is excluded by its texture
lab, n = ndi.label(inside & ~ndi.binary_opening(ndi.uniform_filter(ink.astype(np.float32), 9) > .3, np.ones((7, 7))))
h, w = g.shape; best = max(range(1, n + 1), key=lambda k: ((lab == k) & (np.abs(np.arange(h)[:, None] - h // 2) < 25)).sum())
m = ndi.binary_dilation(lab == best, np.ones((3, 3)), iterations=2) & inside
ys, xs = np.where(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
m = m[y0:y1, x0:x1]; gg = g[y0:y1, x0:x1]
edge = (np.clip((.75 - gg) / .5, 0, 1) * 255 * m).astype(np.uint8)
out = np.stack([edge, (m * 160).astype(np.uint8), (m * 255).astype(np.uint8), (m * 255).astype(np.uint8)], -1)
Image.fromarray(out, 'RGBA').save('dist/assets/colours/braid-map.png', optimize=True)
prev = np.where(m[..., None], np.array([196, 154, 66]) * (1 - edge[..., None] / 255 * .75), 255).astype(np.uint8)
Image.fromarray(prev).resize((prev.shape[1] * 2, prev.shape[0] * 2)).save('/tmp/braid.png'); print('braid', m.shape)
