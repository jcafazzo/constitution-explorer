"""Tri-dimensional chess: the regulation tournament board (PDF 152, TO 03:98:30) and playing pieces (PDF 153, TO 03:98:31).
Run: Blender -b -P model-source/blender/tridimensional_chess.py            -> tridimensional-chess.glb and chess-pieces.glb
     CHESS_NO_PIECES=1 CHESS_OUT=<dir> Blender -b -P ...                 -> the board alone, for scoring against the sheet

Everything comes from model-source/blender/tridimensional_chess_regions.py (profiles/tridimensional-chess-regions.json),
measured at each sheet's printed scale bar (PDF 152: 0-20 cm; PDF 153: 0-6 cm).
Frame: x along the boards (Black's end -X), y across, z up from the underside of the base, front view from -Y.
Colours (sheet key): white, natural and red translucent plastic; gold No. SF03UC for the support frame and base."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import kit, bpy, bmesh
from mathutils import Vector, Matrix

kit.PALETTE.update({
    'sq_red': ('b3372c', .25, 0, .82),      # red translucent plastic
    'sq_white': ('f3f1ea', .25, 0, .78),    # white translucent plastic
    'natural': ('e4dcc4', .12, 0, .38),     # transparent natural plastic (posts, pins)
    'ivory': ('ece6d6', .35, 0, 1),         # White's chessmen
    'ebony': ('1d1f22', .3, 0, 1),          # Black's chessmen ("identical ... except for its color")
})
R = json.load(open(os.path.join(kit.PROFILES, 'tridimensional-chess-regions.json')))
P = R['pieces']
NO_PIECES = os.environ.get('CHESS_NO_PIECES') == '1'
OUT = os.environ.get('CHESS_OUT') or None

def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear(); old = o.data; o.data = me; bpy.data.meshes.remove(old)
    return o

def boolean(o, other, op):
    m = o.modifiers.new('bool', 'BOOLEAN'); m.operation = op; m.solver = 'EXACT'; m.object = other
    apply_mods(o); bpy.data.objects.remove(other, do_unlink=True)
    return o

# ---------------- chessmen (one mesh per type and colour, shared by every copy) ----------------
def profile_pts(rows, z_max=None, step=4):
    """[(z, lo, hi)] bottom-first rows -> revolve points (r, z), radius = half the drawn width."""
    pts = [(0.0, 0.0)]
    for z, lo, hi in rows[::step]:
        if z_max is not None and z > z_max: break
        pts.append((max((hi - lo) / 2, 0.0), z))
    pts.append((0.0, pts[-1][1]))
    return pts

def build_piece(kind, material):
    rows = P[kind]['rows']
    name = f'{kind}_{material}'
    if kind == 'king':
        body = kit.revolve(name, profile_pts(rows, 8.2), material, 'Z', seg=48)
        # the cross: flat, its outline is the drawn cross above the crown (the plan shows it as a thin bar along x)
        cr = [(lo, z) for z, lo, hi in rows if z >= 8.12]; cr += [(hi, z) for z, lo, hi in reversed(rows) if z >= 8.12]
        cross = kit.extrude(name + '_c', cr, .42, material, plane='XZ')
        m = body.modifiers.new('u', 'BOOLEAN'); m.operation = 'UNION'; m.solver = 'EXACT'; m.object = cross
        apply_mods(body); bpy.data.objects.remove(cross, do_unlink=True)
        return body
    if kind == 'knight':
        side = P['knight']['side']; H = P['knight']['height']
        head = kit.extrude(name, side, 4.0, material, plane='XZ')
        fw = P['knight']['front_width']   # (fraction of height, width) top first
        half = [(w / 2, f * H) for f, w in fw] + [(-w / 2, f * H) for f, w in reversed(fw)]
        head_front = kit.extrude(name + '_f', [(y, z) for y, z in half], 8.0, material, plane='YZ')
        boolean(head, head_front, 'INTERSECT')
        r = head.modifiers.new('remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = .06
        s = head.modifiers.new('smooth', 'CORRECTIVE_SMOOTH'); s.factor = .6; s.iterations = 8; s.use_only_smooth = True
        apply_mods(head)
        foot = kit.revolve(name + '_b', profile_pts(rows, .95, 1), material, 'Z', seg=48)
        m = head.modifiers.new('u', 'BOOLEAN'); m.operation = 'UNION'; m.solver = 'EXACT'; m.object = foot
        apply_mods(head); bpy.data.objects.remove(foot, do_unlink=True)
        # the eye drawn on the side view (plate 760, 529 -> x -0.68, z 4.39 cm), raised as a small boss on both cheeks
        ex, ez = (760 - P['knight']['axis_px']) / R['ppc_pieces'], (P['knight']['base_px'] - 529) / R['ppc_pieces']
        wf = min(fw, key=lambda r: abs(r[0] * H - ez))[1] / 2
        for e in (-1, 1):
            eye = kit.sphere(name + f'_e{e}', .2, (ex, e * (wf - .06), ez), material, scale=(1, .55, 1))
            m = head.modifiers.new('u', 'BOOLEAN'); m.operation = 'UNION'; m.solver = 'EXACT'; m.object = eye
            apply_mods(head); bpy.data.objects.remove(eye, do_unlink=True)
        d = head.modifiers.new('dec', 'DECIMATE'); d.ratio = .3; apply_mods(head)
        return kit.smooth(head, 50)
    body = kit.revolve(name, profile_pts(rows), material, 'Z', seg=48)
    top = rows[-1][0]
    if kind == 'rook':   # eight crenels round the turret (front view shows the notches, plan shows eight)
        for i in range(4):
            c = kit.box(name + f'_n{i}', (3.0, .3, .5), (0, 0, top), material, rot=(0, 0, i * math.pi / 4))
            boolean(body, c, 'DIFFERENCE')
    if kind == 'bishop':  # the mitre's slit, seen face-on in the elevation and as a bar across the plan
        c = kit.box(name + '_s', (.13, 3.0, 1.75), (0, 0, top - .02), material)
        boolean(body, c, 'DIFFERENCE')
    return body

_cache = {}
def piece(kind, colour, loc, rot_z=0.0):
    material = 'ivory' if colour == 'w' else 'ebony'
    key = (kind, material)
    if key not in _cache:
        src = build_piece(kind, material); src.name = f'_{kind}_{material}_src'
        _cache[key] = src
        src.hide_render = True
    src = _cache[key]
    o = bpy.data.objects.new(f'{"White" if colour == "w" else "Black"}_{kind.capitalize()}', src.data)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o

def drop_sources():
    for o in list(_cache.values()): bpy.data.objects.remove(o, do_unlink=True)
    _cache.clear()

# ---------------- board assembly ----------------
def build_board():
    kit.reset(); kit._mats.clear()
    lz = R['level_z']; T = .6                          # board thickness (drawn ≈ 0.6-0.8 cm)
    s = R['plan']['square_x']                          # 5.6 cm squares (the plan's 8 files over 44.9 cm)
    sa = R['plan']['attack_size'] / 2                  # attack-board squares, 5.5 cm
    inset = R['plan']['pin_inset']
    cx = {k: (a + b) / 2 for k, (a, b) in R['board_x_cm'].items()}
    cx['B'], cx['W'] = cx['N'] - 2 * s, cx['N'] + 2 * s          # keep the files aligned through all three levels
    half = 2 * s

    # main boards: B (files 0-3), N (2-5), W (4-7); square colour alternates with (row + file) as the plan shows
    x0 = cx['B'] - half
    for k, f0 in (('B', 0), ('N', 2), ('W', 4)):
        for i in range(4):
            for j in range(4):
                f = f0 + i
                x = x0 + (f + .5) * s; y = half - (j + .5) * s
                kit.box(f'Board_{k}_{f}{j}', (s, s, T), (x, y, lz[k] - T / 2), 'sq_red' if (f + j) % 2 == 0 else 'sq_white')
        for sx in (-1, 1):
            for sy in (-1, 1):
                px, py = cx[k] + sx * (half - inset), sy * (half - inset)
                kit.cyl(f'Pin_{k}_{sx}{sy}', .38, 2.6, (px, py, lz[k] - T / 2), 'natural', axis='Z', seg=24)
                for e in (-1, 1): kit.sphere(f'PinEnd_{k}_{sx}{sy}_{e}', .38, (px, py, lz[k] - T / 2 + e * 1.3), 'natural')
    # attack boards in the normal starting position: Black's on B's outer pins, White's on W's outer pins
    attack = {}
    for side, k, sx, level in (('b', 'B', -1, lz['A_black']), ('w', 'W', 1, lz['A_white'])):
        for sy in (1, -1):
            px, py = cx[k] + sx * (half - inset), sy * (half - inset)
            kit.cyl(f'Post_{side}{sy}', .55, level - T - lz[k], (px, py, (level - T + lz[k]) / 2), 'natural', axis='Z', seg=32)
            for a in (-1, 1):
                for b in (-1, 1):
                    x, y = px + a * sa / 2, py + b * sa / 2
                    kit.box(f'Attack_{side}{sy}_{a}{b}', (sa, sa, T), (x, y, level - T / 2), 'sq_red' if a != b else 'sq_white')
            attack[(side, sy)] = (px, py, level)

    # support frame (gold): the elevation outline extruded through the strip width seen in the plan
    for i, poly in enumerate(R['frame']):
        kit.smooth(kit.extrude(f'SupportFrame_{i}', poly, R['frame_depth'], 'gold', plane='XZ', bev=.18), 35)
    pts = [(0.0, R['base'][0][1])] + [tuple(p) for p in R['base']] + [(0.0, 0.0)]
    kit.revolve('Base', pts, 'gold', 'Z', seg=96)

    if NO_PIECES: return None
    # starting arrangement (PDF 153): back rank KT B B KT on the main board, pawns ahead; R K / Q R and their pawns on the attack boards
    for colour, k, fb, fp, face in (('b', 'B', 0, 1, -math.pi), ('w', 'W', 7, 6, 0.0)):
        for j, kind in enumerate(('knight', 'bishop', 'bishop', 'knight')):
            y = half - (j + .5) * s
            piece(kind, colour, (x0 + (fb + .5) * s, y, lz[k]), face if kind == 'knight' else 0.0)
            piece('pawn', colour, (x0 + (fp + .5) * s, y, lz[k]))
        out = -1 if colour == 'b' else 1
        for sy, (upper, lower) in ((1, ('rook', 'king')), (-1, ('queen', 'rook'))):
            px, py, level = attack[(colour, sy)]
            for yy, kind in ((py + sa / 2, upper), (py - sa / 2, lower)):
                piece(kind, colour, (px + out * sa / 2, yy, level), face if kind == 'knight' else 0.0)
                piece('pawn', colour, (px - out * sa / 2, yy, level))
    return None

# ---------------- the six chessmen as drawn on PDF 153 ----------------
def build_pieces_sheet():
    kit.reset(); kit._mats.clear(); _cache.clear()
    ref = sum(P[k]['axis_px'] for k in P) / len(P)
    for kind in ('king', 'queen', 'bishop', 'knight', 'rook', 'pawn'):
        o = piece(kind, 'w', ((P[kind]['axis_px'] - ref) / R['ppc_pieces'], 0, 0))
        o.name = kind.capitalize()
    drop_sources()
    return kit.export('chess-pieces', OUT)

if __name__ == '__main__':
    build_board(); drop_sources(); kit.export('tridimensional-chess', OUT)
    if not NO_PIECES: build_pieces_sheet()
