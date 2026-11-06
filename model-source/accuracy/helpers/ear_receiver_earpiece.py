"""Trace the ear-piece (A) outline on the PLAN of PDF 138 into head-local coordinates.
Head frame (cm): origin at the retention plate (B) centre, a = earphone-housing axis (plate -> housing, image down-right),
u = along the plate (image up-right). Plate B is drawn edge-on from (812,415) to (887,325) px.
Writes model-source/blender/profiles/ear-receiver-earpiece.json  {"poly": [[a, u], ...]} (the part on the -a side of the plate).
usage: /usr/bin/python3 -E model-source/accuracy/helpers/ear_receiver_earpiece.py"""
import sys, json, math
sys.path.insert(0, 'model-source/accuracy')
import numpy as np
from skimage import measure
from plate_silhouette import load_gray, silhouette
PPC = 68.59
X0, Y0 = 700, 290
m = silhouette(load_gray('dist/assets/equipment/page-138.webp')[Y0:790, X0:990], open_=4)
P1, P2 = np.array([812., 415.]), np.array([887., 325.])
pc = (P1 + P2) / 2
u = np.array([P2[0] - P1[0], -(P2[1] - P1[1])]); u /= np.linalg.norm(u)      # model (X right, Z up)
a = np.array([u[1], -u[0]])                                                     # perpendicular, toward the housing
yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
dX = (xx + X0 - pc[0]); dZ = -(yy + Y0 - pc[1])
A = (dX * a[0] + dZ * a[1]) / PPC; U = (dX * u[0] + dZ * u[1]) / PPC
ear = m & (A < -0.06) & (yy + Y0 < 450)
c = max(measure.find_contours(ear.astype(float), .5), key=len)
c = measure.approximate_polygon(c, 0.8)
poly = []
for r, q in c[:-1]:
    dx = q + X0 - pc[0]; dz = -(r + Y0 - pc[1])
    poly.append([round((dx * a[0] + dz * a[1]) / PPC, 4), round((dx * u[0] + dz * u[1]) / PPC, 4)])
ang = math.degrees(math.atan2(-a[1], a[0]))
json.dump({'poly': poly, 'plate_centre_px': pc.tolist(), 'housing_axis_below_horizontal_deg': round(ang, 2),
           'plate_len_cm': round(float(np.linalg.norm(P2 - P1)) / PPC, 3)}, open('model-source/blender/profiles/ear-receiver-earpiece.json', 'w'))
print(len(poly), 'pts; housing axis %.1f deg below horizontal; plate %.2f cm' % (ang, np.linalg.norm(P2 - P1) / PPC))
