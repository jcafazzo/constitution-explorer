"""Hermes class scout, NCC-585 — PDF 79, TO 01:04:14 ("Class I Scout").
Run:  /usr/bin/python3 -E model-source/blender/fleet_destroyer_measure.py hermes
      /Applications/Blender.app/Contents/MacOS/Blender -b -P model-source/blender/hermes.py
Printed particulars: L.O.A. 242.5 m, breadth 127.1 m, height 60 m, primary hull dia. 127.1 m, prop. unit L.O.A. 153.6 m, dia. 17.3 m;
main phasers 1 bank / 2 each (lower hull, "PHASER P/S" in the front view); no photon torpedoes (none listed or drawn).
Scale 6.00 px/m (0-50 m bar 1900 -> 2200 px).  Same hull drawing as the Saladin (PDF 77), redrawn ~55 px left / ~30 px up;
every coordinate below is plate pixels read on p-079.png (plan / side / front view) and checked against the overlays."""
CFG = dict(
    id='hermes', name='Hermes class scout NCC-585', registry='NCC-585', printed=(242.5, 127.1, 60.0),
    plate='model-source/fleet/plates/p-079.png', k=6.00,
    crop_plan=[470, 420, 2060, 1260], crop_side=[440, 1400, 2060, 1880], crop_front=[470, 1990, 1320, 2540],
    mask_plan=[[1305, 785, 1332, 806], [1585, 914, 1612, 936]],          # IMPULSE POWER / SPACE-WARP leader tips
    nac_front_side=1062, nac_mid_row=1769, nac_top_row=1711, nac_plan_visible=1306, deck_aft_side=1306,
    nac_hidden_ratio=1.0, nac_hidden_blend=40,
    deck_r=15.0, lower_dome_r=8.0,
    lower_dome=(860, 942, 1654, 1670),
    bridge=dict(front=828, rear=1022, top=1487, hw=80, base_f=2121, p=2.6),
    sensor_array=dict(x=903, hw=12, top=1474),
    spine=[(990, .5), (997, 7), (1045, 8.5), (1120, 8.5), (1130, 15), (1185, 16), (1245, 15), (1285, 13)],
    impulse_deck=dict(plan=[(1181, 87), (1195, 87), (1270, 87), (1295, 77), (1299, 73)], bottom=1587, top=1545),
    impulse=dict(plan=(809, 839), side=(1270, 1305, 1567, 1585), 
                vents=[[(1226, 803), (1256, 803), (1256, 839), (1213, 839), (1213, 823), (1226, 823)],
                       [(1213, 895), (1256, 895), (1256, 931), (1226, 931), (1226, 915), (1213, 915)]]),
    hatches=[(1205, 794), (1205, 939)], rim_marks=[(668, 660), (1134, 654), (1130, 1078), (674, 1080)], bridge_box=(962, 998, 852, 876),
    pylon=dict(outline=[(1033, 1606), (1095, 1570), (1286, 1570), (1286, 1600), (1419, 1718), (1222, 1718)],
               thick=[(995, 6.4), (1185, 6.0), (1305, 4.2), (1419, 1.0)]),
    nacelle=dict(bands={'nacelle forward band': (1140, 1152), 'nacelle forward ring': (1085, 1091), 'nacelle aft end-cap band': (1903, 1922)},
                 radius=8.65, aft_top=1975, aft_bottom=1943, nose_cap=1085,
                 pods=dict(x=(1717, 1895), top=1701, outer=811),
                 lower_box=dict(side=(1115, 1207, 1785, 1808), front_outer=840),
                 aft_grille=(1825, 1890, 1742, 1770),
                 stripes=[(1290, 1442, 1754, 1769), (1655, 1777, 1754, 1769)],
                 chevron=[[(1245, 1754), (1267, 1754), (1276, 1769), (1242, 1769)], [(1272, 1754), (1290, 1754), (1290, 1769), (1281, 1769)]],
                 lettering=(1468, 1645, 1760, 20)),
    main_sensor=dict(dish_x=(853, 883), dish_cy=1731, dish_r=45, stalk_x=901, stalk_w=9.4, stalk_t=10, ball=(903, 1730, 9), feed_x=841),
    phasers_top=[],
    phasers_lower=[(849, 2233), (954, 2233)],                             # front px: PHASER P/S
    torpedoes=[],
    bow_ports=[(877, 2172, 9), (900, 2172, 9), (922, 2172, 9)],
    windows=dict(rim=[(0.3, -110, 110, 40)], lower_hull=[(1632, -70, 70, 22), (1642, -55, 55, 14)], dome=[(860, 880, 1503), (900, 912, 1508)],
                 pylon=[(1095, 1115, 1620), (1163, 1177, 1638), (1215, 1235, 1638), (1173, 1187, 1658), (1197, 1211, 1658), (1231, 1245, 1658),
                        (1315, 1335, 1697), (1145, 1159, 1573), (1167, 1181, 1573), (1189, 1203, 1573)]),
    pylon_grilles=[[(1240, 1620), (1290, 1620), (1340, 1656), (1285, 1656)], [(1290, 1668), (1340, 1668), (1380, 1703), (1328, 1703)]],
    deck_grid=dict(rings=[127.5, 167.0, 209.8, 255.5, 302.2], radial_r0=77, radial_step=15),   # plan px from the saucer centre (ink crossings on 6 rays / 2 circles)
    saucer_registry=dict(r=39.6, phi0=-30.0, phi1=38.0, cap=6.2, width=6.0),
)
if __name__ == '__main__':
    import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fleet_destroyer; fleet_destroyer.build(CFG)
