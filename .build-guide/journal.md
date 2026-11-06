# Build journal — Equipment Locker

## Working record
- **Outcome / audience:** Site visitors browse hand-held Star Fleet equipment from the Franz Joseph manual as interactive 3D studies with source plates and transcribed specs.
- **In:** `#/equipment` index + 13 item pages: Phaser I (PDF 103), Phaser II (104–105), ray gun (106), sciences tricorder (112–114), medical tricorder (124–126), heartbeat reader (127), spray applicator (128), medical scanner (129), anabolic protoplaser (130–131), surgical scalpels (132), communicator (137), ear receiver (138), universal translator (139). Each: orbitable 3D study, source plate, sourced specs, GLB download.
- **Out / later:** printable STLs for equipment; interiors/small craft; star charts; manual browser.
- **Acceptance:** (1) every spec matches its sheet with PDF page + drawing code; (2) model principal dimensions within sheet scale; (3) existing checks (node --check, check-exports.mjs) still pass; (4) all 13 pages load with no console errors at desktop and phone widths; (5) independent reviewer compares models/specs to plates.
- **Decisions:** follow existing method — procedural Three.js generators in `model-source/` export GLB; sheet numbers kept separate from reconstructed shape. Ship = push to main after checks pass (user-approved 2026-11-06), which republishes GitHub Pages publicly.
- **Authority:** local edits, commits, push to main of jcafazzo/constitution-explorer. No paid APIs.
- **Arrangement:** one owner (main session); 3 bounded transcription subagents; 1 independent reviewer subagent; browser verification by owner. Current model only.
- **Window:** started 2026-11-06, ~3 h active work. Full-resolution plate renders are kept outside the repo (scratch); 1400px webp plates in `dist/assets/equipment/`.

## Evidence
| Check | Candidate | Layer | Provenance | State | Observation |
|---|---|---|---|---|---|
| Plate transcription (3 bounded agents) | — | source | independently observed | PASS | transcribe-a/b/c.json in session scratch; printed vs measured mostly ≤1%; flagged: ear receiver 40° ambiguous, size-2 protoplaser layout differs, scalpels unprinted |
| Envelope check, 13 models | working tree after da9ad83 | digital geometry | directly observed | PASS | `node model-source/build-equipment.mjs` → 13 PASS (±5–8%; communicator height & protoplaser/scalpel width excluded, disclosed) |
| node --check + check-exports.mjs | da9ad83 | source/unit | directly observed | PASS | all 5 STL export checks passed |
| Local pages, desktop + 375 px | working tree | local runtime | directly observed | PASS (spot) | index + 8 item pages viewed; no console errors; no horizontal scroll at 375 px |
| Independent review | da9ad83 | all | independent | FAIL → repaired | specs all verified; 4 geometry faults (scalpel cones inverted, protoplaser size 2 scaled copy, med. tricorder bay buried/lid inward, communicator grille wrong way) + disclosure/UI items; fixed in 030e700 |
| Envelope check after repair | 030e700 | digital geometry | directly observed | PASS | 13/13; communicator now checked on closed pose |
| 13 item pages + bad id + index, existing routes | 030e700 working tree | local runtime | directly observed | PASS | models load, specs render, no console errors; ship/compare/colours/bench unaffected |
| Re-check of repairs | 030e700 | geometry | independent | PASS | all 4 faults + Y-up confirmed fixed from multi-angle renders vs PDF 125/130/131/132/137; build byte-identical |
| Live GitHub Pages | — | deployment | — | NOT RUN | after review |

## Open findings
- Material colours: metallic parts rendered near-black without env map → metalness lowered (fixed after da9ad83).
- Ray gun trigger strip floated over tapering body → reseated on profile (fixed after da9ad83).

## Handoff
- Shipped by push to main (GitHub Pages workflow). Later candidates: printable equipment STLs; interiors & small craft (PDF 83–102, 123, 135–148); star charts (115–122); tricorder head tilt (side views show ≈30–45°).

## Round 2 — accuracy rework + raster colour plates (2026-11-06)
- **User request:** models "seem off"; use other tools / adversarial review; no SVG for uniforms. Agreed plan: Blender rebuild of all 13 scored against plates; colourised scans for uniforms, flags, insignia; PNG silhouettes; ~4 h window.
- **Tooling:** model-source/accuracy (exact-scale Blender ortho renders vs plate silhouettes: IoU + outline distance + overlays); model-source/blender (kit.py + one script per item, profile-driven from measured plate silhouettes).
- **Arrangement:** owner built harness + Phaser I pilot; 4 bounded builder agents (disjoint files) rebuilt the other 12; 3 independent adversarial reviewers (weapons/comms, tricorders/medical, colour plates).

| Check | Candidate | Layer | Provenance | State | Observation |
|---|---|---|---|---|---|
| Silhouette scores, all reliable views | a5eb149 | digital geometry | builders, directly observed | PASS | every reliable view IoU ≥ 0.94 and ≤ 0.6 mm mean; exceptions: ear-receiver profile 0.925 (drawing inconsistency, disclosed) |
| Baseline vs new | a5eb149 | digital geometry | builders | PASS | e.g. phaser-2 side 0.59→0.97, protoplaser-2 side 0.76→0.99, communicator end 0.71→0.98 |
| Raster colour plates | d08e2fb | local runtime | directly observed | PASS (spot) | 8 studies paint on canvas, no console errors; braid + badge per grade/division |
| Compare page skew | 7c… (deployed) | live | directly observed | PASS | silhouettes aspect 3.56 on live |
| Adversarial review ×3 | a5eb149 | all | independent | FAIL → repaired | weapons/comms: phaser-1 rework, dome shading (kit), comm grille, translator surfaces, ear materials; medical: heartbeat head, scanner screen/vanes + 10 flutes, protoplaser-2 J/K/F, vial ribs, scalpel triggers, tricorder strap/grille/rim/banding; colour: braid placement/size/diamonds, text damage, grade label, leaks, badge ghost, phone views |
| Re-score after repairs | working tree → push | digital geometry | builders + owner | PASS | all reliable views still IoU ≥ 0.94 / ≤ 0.6 mm (phaser-1 end view 0.92, ear profile 0.925 — disclosed) |
| Local sweep | pre-push | local runtime | directly observed | PASS | 13 equipment pages load models; 8 colour studies paint; index/compare/colours/equipment/ship OK |

### Open (not fixed this round)
- Medical lower-lid label plate reads mid-grey when the lid is open (lighting angle, not material).
- Scanner dial: "ROT 180° CW" read literally; silhouette identical either way — confirm with user if it matters.
- Ray gun: faint banding and a small dent in the trigger panel crown (low).
- Uniform scan-sample palette now affects swatches only (by design after review).
