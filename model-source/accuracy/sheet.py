"""Contact sheet of overlays (+ shaded renders) for one item: python3 sheet.py <id> [out.png]"""
import sys, glob, os
from PIL import Image
item = sys.argv[1]; d = f'model-source/accuracy/out/{item}'
ims = [Image.open(f) for k in ('overlay', 'shaded') for f in sorted(glob.glob(f'{d}/*-{k}.png'))]
H = 520; ims = [i.resize((max(1, int(i.width * H / i.height)), H)) for i in ims]
rows, row, w = [], [], 0
for i in ims:
    if w + i.width > 2000 and row: rows.append(row); row, w = [], 0
    row.append(i); w += i.width + 8
rows.append(row)
W = max(sum(i.width + 8 for i in r) for r in rows); c = Image.new('RGB', (W, H * len(rows) + 8 * len(rows)), 'white')
for k, r in enumerate(rows):
    x = 0
    for i in r: c.paste(i.convert('RGB'), (x, k * (H + 8))); x += i.width + 8
out = sys.argv[2] if len(sys.argv) > 2 else f'{d}/sheet.png'; c.save(out); print(out, c.size)
