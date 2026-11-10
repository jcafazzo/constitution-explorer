#!/usr/bin/env python3
"""Render an owner's scanned PDF of a Technical Library volume into cleaned page
images for the virtual book (#/book, #/library/<slug>).

With no options it renders the Star Fleet Technical Manual, exactly as before:
into dist/book/pages/, with the manual's colour and dark pages. Other volumes
name their slug (see dist/library/volumes.js) and go to
dist/library/<slug>/pages/.

Both output folders are gitignored. The page images are the owner's private
archival copy of a copyrighted book. Do not commit or publish them. The public
site works without them: the manual shows its binder and a note, and the other
volumes stay on the shelf.

Usage:
  python3 model-source/book/render-pages.py "/path/to/Star Trek Star Fleet Technical Manual.pdf"
  python3 model-source/book/render-pages.py scan.pdf 12,13            # re-render two pages
  python3 model-source/book/render-pages.py scan.pdf --slug mr-scotts-guide --colour 1,2,128 --dark 1,128

Options:
  --slug SLUG     volume to render (default: manual)
  --out DIR       output folder, overriding the one the slug implies
  --colour LIST   pages kept in colour, e.g. 1,2,49 or 1-4,128 (default for the manual: 1,2,49,158,160)
  --dark LIST     colour pages whose paper is not white (default for the manual: 1,160)
  --aspect X      trim, width / height (default for the manual: 0.7712; otherwise the
                  median of the PDF's page boxes)
  --title TEXT    name of the book, recorded in the manifest's `source` line

TODO (not built): deep-zoom tiles for very large sheets. The Blueprints and the
wall maps of Star Trek Maps need a tile pyramid (see model-source/library/PLAN.md,
step 2), but the plan chest and map table that would read the tiles do not exist
yet, so there is no tile layout to write to. Add a --tiles option here when the
first of those presenters is built.

Needs poppler (pdftoppm, pdfimages), cwebp, Pillow and numpy.

Steps for each page:
  1. Render at the scan's native resolution (150 dpi; pdfimages shows 150 ppi
     for nearly every page), so no detail is invented.
  2. Normalise every page to one trim size (for the manual, aspect 0.7712, the
     median of the scanned page boxes). The page is scaled to cover the trim and centred,
     which loses at most about 2% at the margins.
  3. Clean monochrome pages: take the paper and ink levels from that page's own
     histogram, map paper to white and ink to near-black, apply a slight gamma
     to firm up thin linework, and clamp near-white specks to paper. The
     browser then lays a paper tone and fibre over the clean ink, so pages
     read as print on stock, not as a grey scan.
  4. Colour pages (for the manual: 1, 2, 49, 158, 160): white-balance from the paper or border
     where there is one, and apply gentle contrast. The cover photographs are
     left nearly as scanned.
  5. Unsharp mask, then write two sizes as WebP: sm (1024 px tall, used as the
     page textures) and lg (2048 px tall, used by the zoom loupe).
"""
import argparse, json, os, statistics, subprocess, sys, tempfile, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SM_H, LG_H = 1024, 2048
# The manual is the default volume. Its pages stay in dist/book/pages/ (the private build reads
# them from there); every other volume goes to dist/library/<slug>/pages/.
MANUAL = {
    'out': ROOT / 'dist' / 'book' / 'pages',
    'aspect': 0.7712,
    'colour': {1, 2, 49, 158, 160},
    # Pages where the paper is not white, so the levels pass must not whiten them.
    'dark': {1, 160},
    'title': 'Star Fleet Technical Manual (Franz Joseph, Ballantine)',
}
DARK = set(MANUAL['dark'])               # set from the arguments in main()


def page_list(text):
    """'1,2,49' or '1-4,128' -> {1, 2, 49} / {1, 2, 3, 4, 128}. An empty string is no pages."""
    out = set()
    for part in filter(None, (p.strip() for p in text.split(','))):
        a, _, b = part.partition('-')
        out.update(range(int(a), int(b or a) + 1))
    return out


def median_aspect(pdf, count):
    """Width / height of the PDF's page boxes: the median, so one odd sheet does not set the trim."""
    info = subprocess.run(['pdfinfo', '-f', '1', '-l', str(count), pdf], capture_output=True, text=True, check=True).stdout
    r = []
    for line in info.splitlines():
        if line.startswith('Page') and 'size:' in line:
            w, _, h = line.split('size:')[1].split()[:3]
            r.append(float(w) / float(h))
    if not r:
        sys.exit('Could not read the page sizes; pass --aspect.')
    return round(statistics.median(r), 4)


def run(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def fit(img, w, h, fill):
    s = max(w / img.width, h / img.height)
    r = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


def clean_mono(img):
    a = np.asarray(img.convert('L'), dtype=np.float32)
    paper = np.percentile(a, 75)          # most sheets are mostly paper...
    if paper < 200:                       # ...but charts and dividers can be mostly ink
        paper = max(paper, np.percentile(a, 97))
    ink = min(np.percentile(a, 0.4), paper - 60)
    lo, hi = ink + 4, paper - 10
    v = np.clip((a - lo) / max(hi - lo, 1), 0, 1)
    v = v ** 1.18                          # firm up hairlines and type
    v[v > 0.95] = 1.0                      # remove paper grain and specks (keep light halftone)
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
    global DARK
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ap = argparse.ArgumentParser(usage=__doc__, add_help=True)
    ap.add_argument('pdf')
    ap.add_argument('only', nargs='?', type=page_list, default=None)
    ap.add_argument('--slug', default='manual')
    ap.add_argument('--out', type=Path)
    ap.add_argument('--colour', '--color', type=page_list)
    ap.add_argument('--dark', type=page_list)
    ap.add_argument('--aspect', type=float)
    ap.add_argument('--title')
    args = ap.parse_args()
    manual = args.slug == 'manual'
    if not manual and not all(c.isalnum() or c == '-' for c in args.slug):
        sys.exit('The slug is a route segment: letters, digits and hyphens only.')
    pdf = args.pdf
    info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True, check=True).stdout
    count = int(next(l.split()[-1] for l in info.splitlines() if l.startswith('Pages:')))
    only = args.only or None
    OUT = (args.out.resolve() if args.out else MANUAL['out'] if manual else ROOT / 'dist' / 'library' / args.slug / 'pages')
    COLOUR = args.colour if args.colour is not None else MANUAL['colour'] if manual else set()
    DARK = args.dark if args.dark is not None else MANUAL['dark'] if manual else set()
    COLOUR = COLOUR | DARK               # a dark page is always a colour page
    ASPECT = args.aspect or (MANUAL['aspect'] if manual else median_aspect(pdf, count))
    title = args.title or (MANUAL['title'] if manual else args.slug)
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
        'source': f'Owner-supplied scan of {title}. Private archival copy; not for publication.',
        'count': count, 'aspect': ASPECT,
        'sm': [round(SM_H * ASPECT), SM_H], 'lg': [round(LG_H * ASPECT), LG_H],
        'pages': pages}, indent=1))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
