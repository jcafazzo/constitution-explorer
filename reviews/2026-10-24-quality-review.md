# Adversarial review: display geometry and viewer

Scope: the two user screenshots, all five exterior assets, the standalone propulsion study, and shared viewer behaviour. Fabrication STLs are separate assets and were not modified.

## Confirmed defects

1. **High: detached and intersecting surface details.** Estimated XYZ coordinates placed neck windows outside its polygon, pylon grilles across empty space, and flat red pennants partly inside curved engineering hulls. These are geometry failures, not lighting artifacts.
2. **High: inverted nacelle registry.** Euler rotations did not establish a readable, outward-facing text basis on both nacelle sides.
3. **Medium: faceted curved hulls.** The STL pipeline retained triangle normals through merging; a smooth-looking mesh was not verified at close range.
4. **Medium: close-view clipping.** The near plane was 4% of the entire bounding radius, even though the camera could approach 8% of that radius. Large visible sections could be sliced away.
5. **Medium: fitted view lost on resize.** Aspect ratio changed without refitting a preset view. The wide-layout grid also used an intrinsic minimum in its large-screen rule.
6. **Medium: reset retained orbit inertia.** Fit/preset reset left pending OrbitControls angular and pan deltas, allowing the camera to drift after fitting.
7. **Low: misleading view label.** A manually orbited model retained a Top/Side/Front label and selected preset button.

## Viewer remediation

- Reduce near plane from 4% to 0.05% of model radius, retaining close inspection. Minimum orbit distance increased from 8% to 18%; this is not a collision-avoidance system.
- Refit an untouched preset after aspect-ratio changes. Preserve intentional user zoom/orbit.
- Clear preset selection and label the view Interactive after manual navigation.
- Flush pending damping deltas before a fit; actual pointer-event tests show <1e-10 model-unit drift after 120 updates, versus 151.63 camera units without the fix.
- Name reset Fit model; constrain the canvas/grid to available width.
- Reduce excessive scene illumination to retain surface shading.

## Evidence and limits

Geometry repair and numerical attachment checks are described in the model-source geometry review. Source-derived appearance remains a reconstruction. Camera can still intentionally approach or pan through geometry; no physical collision system is claimed. Publication and live-browser checks are recorded after asset regeneration.

## Verification results

- Original attachment sample: 300 indexed face-components (84 neck, 216 engineering), 12 without hull behind them, 92 offset more than 0.3 m, worst 2.538 m.
- Rebuilt attachment sample: 128 indexed face-components (36 neck, 92 engineering), zero without hull, zero over 0.3 m, worst 0.0753 m. Counts differ because projected patch topology replaced disconnected boxes; these are not counts of unique windows.
- All nine GLBs parse through the viewer loader with finite vertices and valid normals. All 108 camera-fit cases pass across three aspect ratios and four camera presets.
- Actual OrbitControls event tests verify orbit/pan inertia is cleared before fitting.
- Port and starboard renders confirm upright outward registry text and continuous hull stripes. Three-quarter renders confirm the repaired pylon grilles stay on their supports.
- Existing colour-gallery and detail/source-sheet DOM checks pass.

Live WebGL review caught precision loss after reducing the near plane: fine surface layers flickered. Enabled the bundled Three.js logarithmic depth buffer to preserve detail separation across near/far inspection distances. Offline Cycles rendering did not expose this WebGL-specific defect.
