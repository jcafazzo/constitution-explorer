"""Zoom a plate region with a labelled grid (plate px) for picking seed points: python3 zoom.py <page> x0 y0 x1 y1 [step] [out]"""
import sys
from PIL import Image, ImageDraw
p, x0, y0, x1, y1 = sys.argv[1], *map(int, sys.argv[2:6]); step = int(sys.argv[6]) if len(sys.argv) > 6 else 20
src = sys.argv[8] if len(sys.argv) > 8 else f'dist/assets/colours/page-{p}.webp'
im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1)); k = 3; im = im.resize((im.width * k, im.height * k), Image.NEAREST)
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    d.line([((x - x0) * k, 0), ((x - x0) * k, im.height)], fill=(255, 0, 0) if x % 100 == 0 else (255, 170, 170)); d.text(((x - x0) * k + 2, 2), str(x), fill=(200, 0, 0))
for y in range((y0 // step + 1) * step, y1, step):
    d.line([(0, (y - y0) * k), (im.width, (y - y0) * k)], fill=(0, 0, 255) if y % 100 == 0 else (170, 170, 255)); d.text((2, (y - y0) * k + 2), str(y), fill=(0, 0, 200))
im.save(sys.argv[7] if len(sys.argv) > 7 else '/tmp/zoom.png')
