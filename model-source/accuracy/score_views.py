"""Score rendered model silhouettes against plate silhouettes.
usage: python3 score_views.py <views.json> <item-id> <render-dir> [--out report.json]
For each view: register by translation (+ optional mirror) with FFT correlation, then report
IoU, mean/95th-percentile outline distance (mm), and write an overlay PNG
(plate in grey, plate outline blue, model outline red, model-only fill red tint, plate-only fill blue tint)."""
import sys, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
sys.path.insert(0, os.path.dirname(__file__))
from plate_silhouette import load_gray, silhouette

def outline(m):
    return m & ~ndi.binary_erosion(m)

def register(model, plate):
    a = model.astype(np.float32); b = plate.astype(np.float32)
    corr = fftconvolve(b, a[::-1, ::-1], mode='same')
    iy, ix = np.unravel_index(np.argmax(corr), corr.shape)
    dy, dx = iy - b.shape[0] // 2, ix - b.shape[1] // 2
    return ndi.shift(model.astype(np.float32), (dy, dx), order=0) > .5, (int(dx), int(dy))

def score(views_path, item, rdir):
    spec = json.load(open(views_path)); res = []
    for v in spec['views']:
        x0, y0, x1, y1 = v['crop']
        gray = load_gray(v.get('plate', f"dist/assets/equipment/page-{v['page']}.webp"))[y0:y1, x0:x1]
        plate = silhouette(gray, keep=v.get('keep', 1), open_=v.get('open', 4))
        if 'mask_out' in v:  # rectangles (crop coords) to exclude, e.g. overlapping labels
            for a, b, c, d in v['mask_out']: plate[b:d, a:c] = False
        m = np.asarray(Image.open(os.path.join(rdir, f"{v['name']}-mask.png")).convert('L')) > 127
        best = None
        for mirror in ([False, True] if v.get('try_mirror', False) else [False]):
            mm = m[:, ::-1] if mirror else m
            reg, off = register(mm, plate)
            inter = (reg & plate).sum(); uni = (reg | plate).sum()
            iou = inter / max(uni, 1)
            if best is None or iou > best[0]: best = (iou, reg, off, mirror)
        iou, reg, off, mirror = best
        po, mo = outline(plate), outline(reg)
        dp = ndi.distance_transform_edt(~po); dm = ndi.distance_transform_edt(~mo)
        d = np.concatenate([dp[mo], dm[po]]) / v['pxPerCm'] * 10  # mm
        r = dict(view=v['name'], iou=round(float(iou), 3), mean_mm=round(float(d.mean()), 2), p95_mm=round(float(np.percentile(d, 95)), 2),
                 plate_area_cm2=round(float(plate.sum()) / v['pxPerCm'] ** 2, 2), model_area_cm2=round(float(reg.sum()) / v['pxPerCm'] ** 2, 2),
                 offset_px=off, mirrored=mirror)
        img = np.stack([gray * 255] * 3, -1)
        img[plate & ~reg] = img[plate & ~reg] * .55 + np.array([60, 110, 255]) * .45
        img[reg & ~plate] = img[reg & ~plate] * .55 + np.array([255, 70, 60]) * .45
        img[ndi.binary_dilation(po)] = [30, 80, 230]; img[ndi.binary_dilation(mo)] = [230, 30, 30]
        Image.fromarray(img.astype(np.uint8)).save(os.path.join(rdir, f"{v['name']}-overlay.png"))
        res.append(r)
    return res

if __name__ == '__main__':
    views, item, rdir = sys.argv[1:4]
    r = score(views, item, rdir)
    for x in r: print(item, x)
    json.dump(r, open(os.path.join(rdir, 'score.json'), 'w'), indent=1)
