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

- `assets/fleet/<id>.stl`: viewer model, oriented with fore/aft along Y and up along Z, millimetres at 1:1000.
- `assets/fleet/<id>-100mm.stl`: a validated binary STL with exactly 100 mm length along Y. Export rescales this file in the browser; normals remain unchanged under positive uniform scaling.
- `<id>-plate.webp`: reviewed source page, with its PDF page recorded in the data.
- `<id>-plan.webp`: a plan-view excerpt for browsing.
- `<id>-silhouette.svg`: side projection using a shared 320-by-100 view box, front at X=0.

Every new model must have a separate geometry report, dimensional checks, and an honest slicing/physical-validation status. Do not label a closed mesh as a completed successful print. Keep source numbers separate from inferred shape and fabrication reinforcement.

## Source and design

Source: user-supplied *Star Trek Star Fleet Technical Manual*, Franz Joseph, scanned 160-page PDF. Selected PDF pages: Constitution 75, Saladin 77, Hermes 79, Ptolemy 81, Federation 88. These are PDF page indices, not invented book pagination. The website follows the book's restrained black technical linework, white sheets, thin borders, expanded headings, drawing codes and red cover accent. Typography is an approximation. It is an unofficial fan companion.

The four new vessels are simplified dimension-led interpretations. The original Constitution is the previous detailed reconstruction. New models and their generator, Blender studies, renderings and checks are in the task's `outputs/manual-fleet/` directory. The full PDF is not bundled with the site.

## Verification for this edition

JavaScript syntax, referenced assets, binary STL exports, model dimensions, closed meshes and connected components are checked locally. Blender renderings provide model inspection. Browser UI automation was blocked by the browser tool's URL policy; desktop/mobile layout and end-to-end browser interactions remain unverified for this edition. Publication is verified separately through Sites deployment status.
