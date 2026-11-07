#!/usr/bin/env python3
"""Render the owner's scanned Star Fleet Technical Manual PDF into cleaned page
images for the virtual book (#/book).

The output folder, dist/book/pages/, is gitignored. Those page images are the
owner's private archival copy of a copyrighted book. Do not commit or publish
them. The public site works without them and shows only the binder and a note.

Usage:
  python3 model-source/book/render-pages.py "/path/to/Star Trek Star Fleet Technical Manual.pdf"

Needs poppler (pdftoppm, pdfimages), cwebp, Pillow and numpy.

Steps for each page:
  1. Render at the scan's native resolution (150 dpi; pdfimages shows 150 ppi
     for nearly every page), so no detail is invented.
  2. Normalise every page to one trim size (aspect 0.7712, the median of the
     scanned page boxes). The page is scaled to cover the trim and centred,
     which loses at most about 2% at the margins.
  3. Clean monochrome pages: take the paper and ink levels from that page's own
     histogram, map paper to white and ink to near-black, apply a slight gamma
     to firm up thin linework, and clamp near-white specks to paper. The
     browser then lays a paper tone and fibre over the clean ink, so pages
     read as print on stock, not as a grey scan.
  4. Colour pages (1, 2, 49, 158, 160): white-balance from the paper or border
     where there is one, and apply gentle contrast. The cover photographs are
     left nearly as scanned.
  5. Unsharp mask, then write two sizes as WebP: sm (1024 px tall, used as the
     page textures) and lg (2048 px tall, used by the zoom loupe).
"""
import json, os, subprocess, sys, tempfile, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dist' / 'book' / 'pages'
ASPECT = 0.7712
SM_H, LG_H = 1024, 2048
COLOUR = {1, 2, 49, 158, 160}
# Pages where the paper is not white, so the levels pass must not whiten them.
DARK = {1, 160}


def run(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def fit(img, w, h, fill):
    s = max(w / img.width, h / img.height)
    r = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


def clean_mono(img):
    a = np.asarray(img.convert('L'), dtype=np.float32)
    paper = np.percentile(a, 75)          # most of every sheet is paper
    ink = min(np.percentile(a, 0.4), paper - 60)
    lo, hi = ink + 4, paper - 10
    v = np.clip((a - lo) / max(hi - lo, 1), 0, 1)
    v = v ** 1.18                          # firm up hairlines and type
    v[v > 0.93] = 1.0                      # remove paper grain and specks
    return Image.fromarray((v * 255 + 0.5).astype(np.uint8))


def clean_colour(img, n):
    a = np.asarray(img.convert('RGB'), dtype=np.float32)
    if n not in DARK:
        # White-balance only on bright, low-saturation pixels (paper or margin).
        lum = a.mean(axis=2)
        sat = a.max(axis=2) - a.min(axis=2)
        m = (lum > np.percentile(lum, 90)) & (sat < 40)
        if m.sum() > 500:
            ref = a[m].mean(axis=0)
            a = a * (245.0 / np.maximum(ref, 1))
    lo = np.percentile(a, 0.3)
    hi = np.percentile(a, 99.7)
    a = (a - lo) * (255.0 / max(hi - lo, 1))
    a = 128 + (a - 128) * 1.04
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def webp(img, path, q):
    tmp = path.with_suffix('.png')
    img.save(tmp, optimize=False, compress_level=1)
    run('cwebp', '-quiet', '-q', str(q), '-m', '6', '-sharp_yuv', str(tmp), '-o', str(path))
    tmp.unlink()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pdf = sys.argv[1]
    info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True, check=True).stdout
    count = int(next(l.split()[-1] for l in info.splitlines() if l.startswith('Pages:')))
    only = {int(x) for x in sys.argv[2].split(',')} if len(sys.argv) > 2 else None
    (OUT / 'sm').mkdir(parents=True, exist_ok=True)
    (OUT / 'lg').mkdir(parents=True, exist_ok=True)
    tmpd = Path(tempfile.mkdtemp())
    pages = []
    try:
        for n in range(1, count + 1):
            colour = n in COLOUR
            pages.append({'n': n, 'colour': colour})
            if only and n not in only:
                continue
            base = tmpd / f'p{n}'
            run('pdftoppm', '-r', '150', '-f', str(n), '-l', str(n), '-singlefile',
                *([] if colour else ['-gray']), '-png', pdf, str(base))
            img = Image.open(f'{base}.png')
            img = clean_colour(img, n) if colour else clean_mono(img)
            fill = (0, 0, 0) if n in DARK else (255, 255, 255) if colour else 255
            for size, h, q, amt in (('lg', LG_H, 84, 90), ('sm', SM_H, 80, 70)):
                w = round(h * ASPECT)
                out = fit(img, w, h, fill)
                out = out.filter(ImageFilter.UnsharpMask(radius=1.1 if size == 'sm' else 1.6, percent=amt, threshold=2))
                webp(out, OUT / size / f'p{n:03d}.webp', q)
            print(f'page {n}/{count}', flush=True)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    (OUT / 'manifest.json').write_text(json.dumps({
        'source': 'Owner-supplied scan of Star Fleet Technical Manual (Franz Joseph, Ballantine). Private archival copy; not for publication.',
        'count': count, 'aspect': ASPECT,
        'sm': [round(SM_H * ASPECT), SM_H], 'lg': [round(LG_H * ASPECT), LG_H],
        'pages': pages}, indent=1))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
