#!/usr/bin/env bash
# Downloads trained ONNX weights from the latest GitHub Release into backend/app/dominance/weights/
set -euo pipefail
REPO="kartikpagariya25/arterion-coronary-dominance"
DEST="$(dirname "$0")/../backend/app/dominance/weights"
mkdir -p "$DEST"
for f in dominance_model.onnx; do
  echo "Downloading $f ..."
  curl -fL --retry 3 -o "$DEST/$f" "https://github.com/$REPO/releases/latest/download/$f"
done
echo "Done."
