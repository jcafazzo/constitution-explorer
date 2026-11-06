"""Hand Phaser Type I — PDF 103, TO 01:08:50.  Run: Blender -b -P model-source/blender/phaser_1.py
Printed: L.O.A. 107.20 mm, W.O.A. 49.40 mm, D.O.A. 27.00 mm. Colours: br. antimony SF02UC, gloss black SF32UC.
Body: lofted from the top-view (plan) and side-view silhouettes measured on the plate (68.37 px/cm).
Details: positions read on the plate in px and converted with the profiles' origins."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import kit

PPC = 68.37
TOP_O = (393.0, 522)   # plan-view origin (mid-line x, first silhouette row y) in plate px
SIDE_O = (732.0, 522)  # side-view origin
L_DRAWN = 10.575       # plan silhouette length incl. emitter cap (printed L.O.A. 10.72)
SCALE_L = 10.72 / L_DRAWN

def build(parent=None, origin=(0, 0, 0), name='Hand Phaser Type I'):
    """Returns the root empty. origin = position of the body's geometric centre; front is −Y."""
    root = kit.group(name, parent); root.location = origin; root.scale = (1, SCALE_L, 1)
    plan = kit.load_profile('phaser-1-top'); side = kit.load_profile('phaser-1-side')
    y0 = -L_DRAWN / 2
    # Side-view silhouette is measured about its own mid-line; the body's z centre sits there too.
    body = kit.loft_from_profiles('body shell', plan, side, 0.24, L_DRAWN - .01, 'black', n=110, p=2.8, side_flip=True, y0=y0, median=6, parent=root)
    y = lambda py: y0 + (py - TOP_O[1]) / PPC          # plan px → y (cm)
    x = lambda px: -(px - TOP_O[0]) / PPC               # plan px → x (cm); image-left is +X
    zs = lambda px: -(px - SIDE_O[0]) / PPC             # side px → z (left of side view = top)
    ztop = lambda py: -kit.sample(side, (py - SIDE_O[1]) / PPC, 6)[0]
    # Emitter cap and 1.02 MeV photon emitter at the front.
    kit.box('emitter housing', (1.38, .32, 1.0), (x(411), y(529), zs(735)), 'antimony', bev=.06, parent=root)
    kit.box('face plate', (1.9, .06, 1.3), (0, y(537), -.02), 'antimony', bev=.03, parent=root)
    kit.cyl('1.02 MeV photon emitter', .38, .1, (0, y(522) - .02, -.02), 'antimony', 'Y', parent=root)
    kit.cyl('emitter lens', .24, .05, (0, y(522) - .08, -.02), 'glass', 'Y', parent=root)
    kit.box('sight', (.5, .3, .25), (x(458), y(525), zs(716)), 'antimony', bev=.03, parent=root)
    # Top surface: electron aspirator pile, trigger, force wheel, operational light, force indicator dial.
    zt = ztop(700)
    kit.box('electron aspirator pile', (x(482) - x(308), y(800) - y(590), .12), (x(395), y(695), ztop(695) - .02), 'antimony', bev=.03, parent=root)
    for i in range(8):
        kit.box('pile lattice', (x(478) - x(312), .05, .05), (x(395), y(600 + i * 26), ztop(600 + i * 26) + .05), 'dark', parent=root)
    kit.box('trigger', (x(482) - x(307), y(850) - y(803), .16), (x(395), y(826), ztop(826) - .03), 'black', bev=.05, parent=root)
    kit.box('trigger frame', (x(486) - x(303), y(855) - y(798), .08), (x(395), y(826), ztop(826) - .06), 'antimony', bev=.04, parent=root)
    for i in range(10):
        kit.box('force setting wheel', (x(325) - x(297), .08, .34), (x(311), y(912 + i * 12.5), ztop(970) + .02), 'dark', parent=root)
    kit.cyl('operational light (blue)', .14, .14, (x(367), y(970), ztop(970)), 'blue', 'Z', parent=root)
    kit.torus('light bezel', .18, .03, (x(367), y(970), ztop(970) + .05), 'antimony', 'Z', parent=root)
    kit.box('force indicator dial', (x(478) - x(410), y(1050) - y(893), .08), (x(444), y(972), ztop(972) - .01), 'white', parent=root)
    for i in range(6):
        kit.box('dial graduation', (.36, .03, .03), (x(444), y(905 + i * 26), ztop(905 + i * 26) + .04), 'black', parent=root)
    # Sides: deflector shield slot (antimony strip) running most of the length.
    half = lambda py: kit.sample(plan, (py - TOP_O[1]) / PPC, 6)
    for s in (-1, 1):
        for i in range(0, 64):
            py = 572 + i * 10
            lo, hi = half(py); xx = (-lo if s > 0 else -hi) - s * .005
            kit.box('deflector shield', (.06, .16, .14), (xx, y(py), zs(718)), 'antimony', parent=root)
    # Bottom: magnatomic adhesion area, access plate and screw.
    zb = lambda py: -kit.sample(side, (py - SIDE_O[1]) / PPC, 6)[1]
    kit.box('magnatomic adhesion area', (x(1170) - x(995) , y(1025) - y(850), .06), (0, y(938), zb(938) + .01), 'dark', bev=.15, parent=root)
    kit.cyl('access plate screw', .17, .06, (0, y(1148), zb(1148)), 'antimony', 'Z', parent=root)
    return root

if __name__ == '__main__':
    kit.reset(); build(); kit.export('phaser-1')
