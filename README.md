# Star Fleet Interactive Technical Manual

Buildless Three.js site; `dist/` is both the source and published static directory. Existing Sites identity and private audience are retained in `.openai/hosting.json`.

## Experience

- `#/`: searchable five-vessel index, in the manual's technical-sheet visual language.
- `#/ship/constitution`, `saladin`, `hermes`, `ptolemy`, `federation`: 3D model, source sheet, camera presets, finish, fullscreen, length control and binary STL export.
- `#/compare`: model-derived side projections on a common horizontal length scale; specifications and a 1:2000 fleet collection action.
- `#/bench`: browser-local model selection and length choices. No printer integration or print commands.

Run a static HTTP server from `dist/`. JavaScript syntax check: `node --check dist/app.js`. Vendor Three.js modules are retained locally. Typography uses Google Fonts with local fallbacks.

## Adding an entry

The new vessels are in `dist/assets/fleet/ships.json`; the original Constitution entry remains in `app.js`. A new record needs `id`, `name`, `registry`, `role`, `page`, `plate`, `length`, `width`, `height`, `nacelles`, `crew`, `description`, `status`, and `model`. Dimensions describe the fictional vessel in metres and must be transcribed from a reviewed source.

Provide these assets using the same id:

- `assets/detail/<id>.glb`: detailed display model.
- `assets/fleet/<id>.stl`: original fabrication reference, oriented with fore/aft along Y and up along Z, millimetres at 1:1000.
- `assets/fleet/<id>-100mm.stl`: a validated binary STL with exactly 100 mm length along Y. Export rescales this file in the browser; normals remain unchanged under positive uniform scaling.
- `<id>-plate.webp`: reviewed source page, with its PDF page recorded in the data.
- `<id>-plan.webp`: a plan-view excerpt for browsing.
- `<id>-silhouette.png`: side projection, 1600 × 450 px transparent PNG on the shared length scale (320 m across, front at the left).

Every new model must have a separate geometry report, dimensional checks, and an honest slicing/physical-validation status. Do not label a closed mesh as a completed successful print. Keep source numbers separate from inferred shape and fabrication reinforcement.

## Source and design

Source: user-supplied *Star Trek Star Fleet Technical Manual*, Franz Joseph, scanned 160-page PDF. Selected PDF pages: Constitution 75, Saladin 77, Hermes 79, Ptolemy 81, Federation 88. These are PDF page indices, not invented book pagination. The website follows the book's restrained black technical linework, white sheets, thin borders, expanded headings, drawing codes and red cover accent. Typography is an approximation. It is an unofficial fan companion.

The five complete hulls (`dist/assets/detail/<id>.glb`) are built in Blender from the plates themselves: `model-source/fleet/plates/p-0NN.png` (300 dpi renders of PDF 75/77/79/81/88), measured by `model-source/fleet/constitution_measure.py`, `federation_measure.py`, `model-source/blender/ptolemy_measure.py` and `fleet_destroyer_measure.py`, and built by `model-source/blender/constitution.py`, `federation.py`, `ptolemy.py`, `saladin.py`/`hermes.py` (shared `fleet_destroyer.py`). Each is scored against its plate's plan, side and front silhouettes (`views/<id>.json`, `raw_zup`; `GLB_DIR=dist/assets/detail sh model-source/accuracy/run.sh <id>`). `model-source/blender/fleet_outputs.py -- <ids>` regenerates the Compare silhouettes (drawn at printed length, 5 px/m) and the 100 mm STLs (one voxel-unioned closed body; surface markings dropped, thin parts thickened). Plates' front views disagree with their own plan/side views by 1–2 m, so front is reported as a reference view.

## Verification for this edition

JavaScript syntax, referenced assets, binary STL exports, model dimensions, closed meshes and connected components are checked locally. Blender renderings provide model inspection. Browser interaction and publication checks are recorded separately from model validation in the task artifacts.


## Detailed systems edition

The existing page layout is retained. A compact Explore selector switches between full ship, SW40 main propulsion and IP186 impulse engine. Constitution also includes an open-roof bridge and MK-IX hangar cutaway. The Technical plate tab follows the selected study and offers each relevant source page. Close orbit, zoom, camera presets, finishes, fullscreen and a GLB download apply to the selected display study.

Sources: bridge PDF 94–95; impulse PDF 143; propulsion PDF 144; MK-IX hangar PDF 149–150. Exact component counts and the bridge's 36-degree command-axis offset are grounded in these sheets. Interior depths, fine controls, hidden surfaces, material finishes and door poses are reconstructions. The hangar is explicitly MK-IX and is not assigned to other classes. GLB files use the viewer's Z-up, front-negative-Y coordinates; geometry is in approximate metres. Downloads intended for fabrication remain the original STL files, with their own validation requirements.

Nine display GLBs are validated by parsing them with the same Three.js loader as the website, checking finite coordinates and bounding boxes, and confirming source assets. Materials are batched into 7–14 meshes per study. Blender renders are used to inspect geometry and text placement. Display studies are not claimed watertight or print-ready.

## Equipment Locker edition

`#/equipment` adds thirteen hand-held items from the manual: Hand Phaser Types I and II (PDF 103–105), ray gun (106), sciences tricorder (112–114), medical tricorder (124–126), heartbeat reader (127), spray applicator (128), medical scanner (129), anabolic protoplaser sizes 0 and 2 (130–131), surgical scalpels (132), communicator (137), ear receiver (138) and universal translator (139). Each page has an orbitable GLB study, the source plates, the printed specifications, the values measured from the drawings, and a note on what was interpreted.

- Models are built in Blender from the plates themselves: `model-source/accuracy/extract_profile.py` measures each drawn view's silhouette at the sheet's scale bar, and the scripts in `model-source/blender/` (one per item, sharing `kit.py`) loft, turn or extrude those measured outlines, then place every called-out component at plate-measured positions. Run e.g. `/Applications/Blender.app/Contents/MacOS/Blender -b -P model-source/blender/phaser_1.py` (`run.sh` honours `$BLENDER` for a different binary).
- Accuracy is measured, not asserted: `sh model-source/accuracy/run.sh <id>` renders exact-scale orthographic views in Blender and scores them against the plate silhouettes (IoU and outline distance in mm, with overlay images in `model-source/accuracy/out/`, which is not committed). View definitions live in `model-source/accuracy/views/<id>.json`.
- `Blender -b -P model-source/blender/thumbs.py` renders the catalogue thumbnails and records each model's overall size in `model-source/accuracy/envelopes.json`.
- `model-source/equipment-content.py` writes `dist/assets/equipment/equipment.json`, keeping literal sheet transcriptions (`specs`), measured values (`derived`) and interpretation notes separate.
- The display studies are not print-ready meshes. Source plates are 1400 px WebP renders of single pages; the full PDF is still not bundled.

## Colour plates edition (raster)

The colour plates are the manual's own drawings, colourised, never redrawn as vectors. `model-source/colour/segment.py` turns each plate into a region map (`dist/assets/colours/<id>-map.png`: linework strength, region class, halftone or emblem mask) from seed points and a few traced bands in `model-source/colour/plates.json`. `anchors.py` measures the cuff lines and insignia position, and `braid.py` cuts the rank braid from PDF 65. In the browser, `dist/colour-raster.js` paints these maps on a canvas in the chosen SF palette, adds the division badge and grade braid, and saves a PNG.
