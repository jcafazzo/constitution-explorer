"""Extract a filled silhouette of one drawn view from a manual plate crop.
Ink → close small gaps (halftone, line breaks) → fill holes → drop thin leader lines/text by opening → largest blobs."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

def load_gray(path):
    return np.asarray(Image.open(path).convert('L'), dtype=np.float32) / 255.0

def silhouette(gray, ink=0.55, close=3, open_=4, keep=1, min_frac=0.02):
    m = gray < ink
    m = ndi.binary_closing(m, structure=np.ones((close, close)), iterations=2)
    m = ndi.binary_fill_holes(m)
    if open_:
        m = ndi.binary_opening(m, structure=np.ones((open_, open_)))
    lab, n = ndi.label(m)
    if n == 0:
        return m
    sizes = ndi.sum(m, lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1]
    out = np.zeros_like(m)
    for i in order[:keep]:
        if sizes[i] >= min_frac * m.size or i == order[0]:
            out |= lab == (i + 1)
    return ndi.binary_fill_holes(out)

def ink_mask(gray, ink=0.55):
    return gray < ink
