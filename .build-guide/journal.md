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

## Open findings

## Handoff
