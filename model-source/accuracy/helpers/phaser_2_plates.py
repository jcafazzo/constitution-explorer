"""Build the cleaned plate image used to score the Type II side view (PDF 104, right drawing).
Run from the repo root: /usr/bin/python3 -E model-source/accuracy/helpers/phaser_2_plates.py

On the sheet the side view's grip runs left behind the top view (middle drawing) and in front of the end view (left drawing),
so a plain crop would merge three drawings and lose the grip's middle. This keeps only:
  * the right drawing (x >= 845) minus the callout texts, SECT. A-A and the label of the lower deflector shield;
  * the grip's visible pixels inside the band between its two straight edges, measured left of the top view (x 220-500):
        front edge  y = 1000.5 - 0.396 (x - 300)      rear edge  y = 1263.0 - 0.396 (x - 300)
    (these same lines meet the grip's visible right-hand part at x 760-880 within 3 px, so the grip is straight);
  * behind the top view (x 506-759) the grip is not drawn; there the band between the two edges is filled solid.
The filled band is the only synthesized area (2.3 cm along the grip); everything else is the plate's own ink.
Output: model-source/accuracy/helpers/plates/phaser-2-104-side.png (same size as the page, so the view's crop box is unchanged)."""
import os
import numpy as np
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
im = np.asarray(Image.open(os.path.join(ROOT, 'dist/assets/equipment/page-104.webp')).convert('L')).copy()
H, W = im.shape
yy, xx = np.mgrid[0:H, 0:W]
front = 1000.5 - 0.396 * (xx - 300); rear = 1263.0 - 0.396 * (xx - 300)
band = (yy >= front - 3) & (yy <= rear + 3) & (xx >= 180) & (xx <= 885)
keep = (xx >= 845) | band
out = np.where(keep, im, 255).astype(np.uint8)
# behind the top view: fill the grip band solid (no ink is visible there)
hidden = (xx >= 506) & (xx <= 759) & (yy >= front) & (yy <= rear)
out[hidden] = 60
# callouts and other drawings that touch the right drawing (x0, y0, x1, y1 in plate px)
for x0, y0, x1, y1 in [(1040, 228, 1310, 262), (1072, 268, 1310, 305), (1136, 312, 1310, 376), (1124, 376, 1310, 398), (1150, 488, 1310, 540),
                       (1100, 700, 1250, 760), (1080, 840, 1230, 975), (1125, 1240, 1290, 1300), (1190, 1590, 1310, 1700),
                       (760, 1255, 938, 1665), (760, 1690, 995, 1736), (760, 1110, 912, 1200), (760, 455, 890, 540)]:
    out[y0:y1, x0:x1] = 255
Image.fromarray(out).save(os.path.join(os.path.dirname(__file__), 'plate-104-side.png'))
print('wrote plate-104-side.png')
