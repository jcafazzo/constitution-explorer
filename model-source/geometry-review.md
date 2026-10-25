# Adversarial geometry review and remediation

Scope: the five complete starship display meshes and the standalone propulsion study. This review changes browser display GLBs only; printable STL and slicer files were not changed.

## Findings and fixes

| Severity | Defect and root cause | Remediation |
| --- | --- | --- |
| High | Engineering pennants were flat boxes at a guessed radius; tapered hull sections cut through the stripe. Window boxes used similarly approximate radii. | Subdivided markings now project onto the actual STL triangles. Every emitted triangle has three supported surface vertices. |
| High | Neck window arrays extended outside the neck polygon, leaving detached rows and windows. | Exact triangle projection within a narrow neck-only axial band. Unsupported triangles are omitted; a window cannot attach to another hull behind the neck. |
| High | Pylon grilles were horizontal world-space boxes wider than the diagonal supports. | Grilles use a local basis along/across each pylon and project onto its actual forward face. Ribs use a distinct surface offset. Applied to Constitution and Ptolemy. |
| High | Nacelle registry Euler rotations made one side inverted; its planar text did not follow cylindrical curvature. Registry was also painted over inboard chiller equipment. | Outboard port and starboard text uses explicit right/up/outward bases, curved glyph projection and outward-normal assertions. Paired nacelles retain only outboard registry; the unobstructed sides of centerline units both carry upright text. |
| Medium | STL face normals survived vertex merging, preventing curved surfaces from smoothing. | Remove imported face-normal splits, weld positions, then generate crease-aware normals at 36 degrees. Rounded surfaces smooth while structural edges remain sharp. |
| Medium | Chiller panels and ribs floated above the nominal barrel and occupied coplanar layers. | Panels, ribs, borders and pennants conform to the actual barrel; staggered offsets prevent coplanar flicker. |
| Medium | Shared saucer formulas misplaced Federation bridge windows and ventral detail against its deeper hull. | Actual surface projection, class-specific bridge elevation and widened ventral surface bounds. |
| Medium | The standalone propulsion study combined a full acquisition sphere, a second hemisphere and a generic cylinder. | One continuous dimensioned lathed body replaces the overlapping primitives; a single exterior red hemisphere supplies the acquisition-dome finish. |

## Validation

- The generator fails on unsupported nacelle registry vertices, inward registry normals or nonfinite exported positions.
- Surface checks are exact barycentric intersections against the dimensioned source geometry, spatially indexed for efficient build time.
- Planar decoration layers sit 0.018–0.065 source metres from the supporting surface. Raised hardware and seam tube thickness are intentional geometry; these are not fabricated part tolerances.
- Registry checks confirm +Z letter-up, a right-handed baseline/up/outward basis, and measured outward normal alignment greater than 0.95 for every glyph vertex.
- Unsupported neck/pylon window or grille portions are clipped, not moved across empty space to a different hull.
- Independent final-GLB check against the original Constitution STL: 128 small dark face components (36 neck, 92 engineering), zero without a hull behind them and zero more than 0.3 m from the hull. Maximum sampled offset 0.0753 m. Baseline: 12 missing-hull components, 92 farther than 0.3 m, maximum 2.538 m. The independent component-centroid metric differs from per-vertex normal offsets.
- Parent review of matched port, starboard and quarter Blender renders confirmed upright outboard registry, a continuous pennant, flush pylon grilles and no neck floaters.

## Generated assets

| Asset | Triangles | GLB MB | Outward registry faces |
| --- | ---: | ---: | ---: |
| constitution.glb | 211,383 | 4.09 | 2 |
| saladin.glb | 78,463 | 1.71 | 2 |
| hermes.glb | 75,090 | 1.64 | 2 |
| ptolemy.glb | 109,033 | 2.33 | 2 |
| federation.glb | 154,292 | 3.22 | 4 |
| nacelle.glb | 37,573 | 0.75 | 1 |

Per-feature requested/accepted/rejected vertex counts, triangle counts, surface offsets, seed corrections and orientation measurements are recorded in `exterior-validation.json`.

## Limits

These remain dimension-led fan reconstructions. Hidden form, material finish, lettering typeface and small detail thickness are interpretations. Surface projection establishes attachment and orientation, not exact original-prop fidelity or suitability for fabrication. Rendering and fabrication validation are separate.
