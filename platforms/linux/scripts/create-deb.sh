#!/bin/bash
set -euo pipefail
BONGO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
[ "$(uname -s)" = Linux ] || { echo 'Linux required.' >&2; exit 1; }
for tool in cmake cargo pkg-config; do command -v "$tool" >/dev/null || { echo "Missing: $tool" >&2; exit 1; }; done
pkg-config --exists ibus-1.0 Qt5Widgets libzstd || { echo 'Install libibus-1.0-dev qtbase5-dev libzstd-dev.' >&2; exit 1; }
BONGO_GITHUB_REPOSITORY="${BONGO_GITHUB_REPOSITORY:-mehedishakeel/Bongo}"
UPDATE_ARGS=(
  "-DBONGO_UPDATE_URL=https://github.com/${BONGO_GITHUB_REPOSITORY}/releases/latest/download/linux.json"
  "-DBONGO_GITHUB_REPOSITORY=${BONGO_GITHUB_REPOSITORY}"
)
BUILD_DIR="$BONGO_ROOT/platforms/linux/build"
cmake -S "$BONGO_ROOT/platforms/linux" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release "${UPDATE_ARGS[@]}"
cmake --build "$BUILD_DIR" --parallel
(cd "$BUILD_DIR" && cpack -G DEB)
