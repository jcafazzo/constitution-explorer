"""Cleaned END VIEW plate for heartbeat-reader (PDF 127): the drawn circle + tabs are outline-only and cut by
centre lines, so the plain silhouette() keeps only one tab. Fill the closed outline (ink closed 5x5), drop the
centre lines by opening, write a full-page black-on-white image used as 'plate' in views/heartbeat-reader-base.json.
usage: /usr/bin/python3 -E model-source/accuracy/helpers/heartbeat_reader_base_plate.py"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
g = np.asarray(Image.open('dist/assets/equipment/page-127.webp').convert('L'), dtype=np.float32) / 255
x0, y0, x1, y1 = 940, 1200, 1330, 1400
m = g[y0:y1, x0:x1] < 0.6
m = ndi.binary_closing(m, np.ones((5, 5)), iterations=1)
m = ndi.binary_fill_holes(m)
m = ndi.binary_opening(m, np.ones((6, 6)))
lab, n = ndi.label(m); s = ndi.sum(m, lab, range(1, n + 1)); m = lab == (np.argmax(s) + 1)
out = np.full(g.shape, 255, np.uint8); out[y0:y1, x0:x1][m] = 0
Image.fromarray(out).save('model-source/accuracy/helpers/plates/heartbeat-reader-base-end.png')
r = np.where(m.any(1))[0]; c = np.where(m.any(0))[0]
print('end view silhouette x', x0 + c.min(), x0 + c.max() + 1, 'y', y0 + r.min(), y0 + r.max() + 1)
