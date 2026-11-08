#!/bin/sh
# Render + score one or more items: sh model-source/accuracy/run.sh [glb-dir] id ...
# Outputs in model-source/accuracy/out/<id>/ (masks, shaded renders, overlays, score.json).
DIR=${GLB_DIR:-dist/assets/equipment}
B=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
for id in "$@"; do
 out=model-source/accuracy/out/$id
 "$B" -b -P model-source/accuracy/render_views.py -- "$DIR/$id.glb" model-source/accuracy/views/$id.json "$id" "$out" >/dev/null 2>&1 || echo "render failed: $id"
 /usr/bin/python3 -E model-source/accuracy/score_views.py model-source/accuracy/views/$id.json "$id" "$out"
done
