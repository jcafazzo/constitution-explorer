#!/bin/sh
# Renders catalogue thumbnails with headless Chrome. Run from the repo root: sh model-source/make-equipment-thumbs.sh
set -e
PORT=4179; python3 -m http.server $PORT >/dev/null 2>&1 & PID=$!; sleep 1
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; TMP=$(mktemp -d)
for id in $(python3 -c "import json;print(' '.join(x['id'] for x in json.load(open('dist/assets/equipment/equipment.json'))))"); do
 "$CHROME" --headless=new --disable-gpu --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars --window-size=640,480 --virtual-time-budget=8000 --screenshot="$TMP/$id.png" "http://localhost:$PORT/model-source/equipment-thumb.html?id=$id" >/dev/null 2>&1
 cwebp -quiet -q 80 "$TMP/$id.png" -o "dist/assets/equipment/thumb-$id.webp"; echo "thumb-$id.webp"
done
kill $PID; rm -rf "$TMP"
