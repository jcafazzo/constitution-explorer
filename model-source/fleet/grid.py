"""Grid-annotated view of a plate region for locating crops: python3 grid.py <png> x0,y0,x1,y1 <scale> <out> [step]"""
import sys
from PIL import Image, ImageDraw
p, crop, sc, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]; step = int(sys.argv[5]) if len(sys.argv) > 5 else 100
x0, y0, x1, y1 = map(int, crop.split(','))
im = Image.open(p).convert('RGB').crop((x0, y0, x1, y1)); im = im.resize((int(im.width * sc), int(im.height * sc)))
d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * sc; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0) if x % (step * 5) == 0 else (255, 170, 170)); d.text((X + 2, 2), str(x), fill=(200, 0, 0))
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * sc; d.line([(0, Y), (im.width, Y)], fill=(0, 0, 255) if y % (step * 5) == 0 else (170, 170, 255)); d.text((2, Y + 2), str(y), fill=(0, 0, 200))
im.save(out)
