"""Saladin class destroyer, NCC-500 — PDF 77, TO 01:04:12 ("Class I Destroyer").
Run:  /usr/bin/python3 -E model-source/blender/fleet_destroyer_measure.py saladin
      /Applications/Blender.app/Contents/MacOS/Blender -b -P model-source/blender/saladin.py
Printed particulars: L.O.A. 242.5 m, breadth 127.1 m, height 60 m, primary hull dia. 127.1 m, prop. unit L.O.A. 153.6 m, dia. 17.3 m;
main phasers 3 banks / 2 each, photon torpedoes 2 banks.  Scale 6.02 px/m (0-50 m bar 1951 -> 2252 px).
All coordinates below are plate pixels (plan / side / front view) read on p-077.png; fleet_destroyer.py converts them."""
CFG = dict(
    id='saladin', name='Saladin class destroyer NCC-500', registry='NCC-500', printed=(242.5, 127.1, 60.0),
    plate='model-source/fleet/plates/p-077.png', k=6.02,
    crop_plan=[540, 470, 2100, 1300], crop_side=[480, 1440, 2100, 1900], crop_front=[500, 2020, 1400, 2560],
    mask_plan=[[1358, 812, 1390, 838], [1638, 944, 1670, 968]],          # IMPULSE POWER / SPACE-WARP leader tips
    nac_front_side=1108, nac_mid_row=1790, nac_top_row=1743, nac_plan_visible=1362, deck_aft_side=1362,
    nac_hidden_ratio=1.0, nac_hidden_blend=40,   # forward of the deck the nacelle is hidden in plan: round section (front view: ~19 m wide)
    deck_r=15.0, lower_dome_r=8.0,
    lower_dome=(915, 997, 1684, 1700),                                   # side px
    bridge=dict(front=883, rear=1077, top=1517, hw=80, base_f=2150, p=2.6),   # side px edges/top; front-view base half-width px & row
    sensor_array=dict(x=958, hw=12, top=1504),                                              # half-width px, side-view top py
    spine=[(1045, .5), (1052, 7), (1100, 8.5), (1175, 8.5), (1185, 15), (1240, 16), (1300, 15), (1340, 13)],
    impulse_deck=dict(plan=[(1236, 88), (1250, 88), (1325, 88), (1350, 78), (1354, 74)], bottom=1617, top=1577),
    impulse=dict(plan=(840, 870), side=(1325, 1360, 1597, 1615), 
                vents=[[(1281, 836), (1312, 836), (1312, 868), (1268, 868), (1268, 852), (1281, 852)],
                       [(1268, 924), (1312, 924), (1312, 962), (1281, 962), (1281, 946), (1268, 946)]]),
    hatches=[(1262, 826), (1261, 974)], rim_marks=[(722, 690), (1190, 685), (1188, 1110), (726, 1111)], bridge_box=(1012, 1042, 885, 907),
    pylon=dict(outline=[(1091, 1636), (1150, 1600), (1341, 1600), (1341, 1630), (1474, 1748), (1280, 1748)],
               thick=[(1050, 6.4), (1240, 6.0), (1360, 4.2), (1478, 1.0)]),
    nacelle=dict(bands={'nacelle forward band': (1195, 1207), 'nacelle forward ring': (1140, 1146), 'nacelle aft end-cap band': (1958, 1977)},
                 radius=8.65, aft_top=2030, aft_bottom=1998, nose_cap=1140,
                 pods=dict(x=(1772, 1950), top=1731, outer=843),
                 lower_box=dict(side=(1170, 1262, 1815, 1838), front_outer=896),
                 aft_grille=(1880, 1945, 1772, 1800),
                 stripes=[(1345, 1497, 1784, 1799), (1710, 1832, 1784, 1799)],
                 chevron=[[(1300, 1784), (1322, 1784), (1331, 1799), (1297, 1799)], [(1327, 1784), (1345, 1784), (1345, 1799), (1336, 1799)]],
                 lettering=(1525, 1700, 1790, 20)),
    main_sensor=dict(dish_x=(908, 938), dish_cy=1761, dish_r=45, stalk_x=958, stalk_w=9.4, stalk_t=10, ball=(963, 1760, 9), feed_x=896),
    phasers_top=[(937, 703), (957, 703), (937, 1100), (957, 1103)],      # plan px: PHASER BANK P/S
    phasers_lower=[(905, 2262), (1010, 2262)],                            # front px: PHASER P/S
    torpedoes=[(946, 2140), (969, 2140)],                                 # front px: PHOTON TORPEDOS P/S
    bow_ports=[(930, 2203, 9), (955, 2203, 9), (980, 2203, 9)],
    windows=dict(rim=[(0.3, -110, 110, 40)], lower_hull=[(1662, -70, 70, 22), (1672, -55, 55, 14)], dome=[(915, 935, 1533), (955, 967, 1538)],
                 pylon=[(1150, 1170, 1650), (1218, 1232, 1668), (1270, 1290, 1668), (1228, 1242, 1688), (1252, 1266, 1688), (1286, 1300, 1688),
                        (1370, 1390, 1727), (1200, 1214, 1603), (1222, 1236, 1603), (1244, 1258, 1603)]),
    pylon_grilles=[[(1305, 1650), (1378, 1650), (1412, 1686), (1338, 1686)], [(1355, 1700), (1422, 1700), (1452, 1736), (1385, 1736)]],
    deck_grid=dict(rings=[129.5, 169.5, 211.0, 256.0, 303.5], radial_r0=77, radial_step=15),   # plan px from the saucer centre (ink crossings on 6 rays / 2 circles)
    saucer_registry=dict(r=39.6, phi0=-30.0, phi1=38.0, cap=6.2, width=6.0),
)
if __name__ == '__main__':
    import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fleet_destroyer; fleet_destroyer.build(CFG)
