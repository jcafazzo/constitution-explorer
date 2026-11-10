"""Star Trek Maps (Bantam, 1980): build the book pages from the owner's scan.
Run: python3 model-source/book/render-maps.py <Star-Trek-Maps.pdf>      -> dist/library/maps/pages/ (private; git-ignored)

The scan is 37 sheets: front cover, the four wall maps (one image each, about 12,300 x 8,700 px), the 31 scanned pages of the
manual "Introduction to Navigation", and the back cover. The book engine wants facing pages, so each map becomes a left and a
right half, and the manual comes first so that its own rectos fall on the right:
  p1 front cover | p2-p32 manual pages 1-31 | p33-p40 maps A-D as halves | p41 blank | p42 back cover
The large images are 3072 px tall, not the usual 2048, because the map lettering is small."""
import json, subprocess, sys, tempfile
from pathlib import Path
import importlib.util
import numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rp', HERE / 'render-pages.py'); rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
OUT = rp.ROOT / 'dist' / 'library' / 'maps' / 'pages'
ASPECT, SM_H, LG_H = 0.70, 1024, 3072
SIZES = (('lg', (round(LG_H * ASPECT), LG_H), 82), ('sm', (round(SM_H * ASPECT), SM_H), 80))
FOLDER = (12, 18, 24)                      # the dark ground of the maps, for the blank sheet

def main():
    pdf = sys.argv[1]
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(['pdfimages', '-all', pdf, str(tmp / 'i')], check=True)
    src = sorted(tmp.glob('i-*.jpg'))
    assert len(src) == 37, len(src)
    for s in ('sm', 'lg'): (OUT / s).mkdir(parents=True, exist_ok=True)
    pages = []
    def put(img, colour, how, **meta):
        n = len(pages) + 1
        for size, (w, h), q in SIZES:
            r = rp.contain(img, w, h) if how == 'contain' else rp.fit(img, w, h, None)
            if size == 'sm' or not colour: r = r.filter(ImageFilter.UnsharpMask(1.0, 40, 2))
            rp.webp(r.convert('RGB'), OUT / size / f'p{n:03d}.webp', q)
        pages.append({'n': n, 'colour': colour, **meta}); print(n, meta, flush=True)

    put(Image.open(src[0]).convert('RGB'), True, 'contain', **{'from': 1})
    put(Image.open(src[5]).convert('RGB'), False, 'fit', **{'from': 6})                       # manual cover: a halftone, left as scanned
    for i in range(6, 36): put(rp.clean_mono(Image.open(src[i])), False, 'fit', **{'from': i + 1})
    for i in range(1, 5):
        m = Image.open(src[i]).convert('RGB'); c = m.width // 2
        put(m.crop((0, 0, c, m.height)), True, 'fit', **{'from': i + 1, 'half': 'L'})
        put(m.crop((c, 0, m.width, m.height)), True, 'fit', **{'from': i + 1, 'half': 'R'})
    put(Image.new('RGB', (700, 1000), FOLDER), True, 'fit', blank=True)
    put(Image.open(src[36]).convert('RGB'), True, 'contain', **{'from': 37})
    json.dump({'source': 'Owner-supplied scan of Star Trek Maps (Bantam Books, 1980). Private copy; not for publication.',
               'count': len(pages), 'aspect': ASPECT, 'sm': list(SIZES[1][1]), 'lg': list(SIZES[0][1]), 'pages': pages},
              open(OUT / 'manifest.json', 'w'), indent=1)

main()
