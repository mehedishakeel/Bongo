#!/bin/bash
set -euo pipefail
BONGO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
[ "$(uname -s)" = Linux ] || { echo 'Linux required.' >&2; exit 1; }
missing_tools=()
for tool in cmake cpack cargo rustc rustdoc pkg-config make dpkg dpkg-shlibdeps; do
  command -v "$tool" >/dev/null 2>&1 || missing_tools+=("$tool")
done
if [ "${#missing_tools[@]}" -ne 0 ]; then
  echo "Missing build tools: ${missing_tools[*]}" >&2
  echo 'On Ubuntu/Debian, run:' >&2
  echo '  sudo apt update' >&2
  echo '  sudo apt install build-essential cmake cargo rustc pkg-config dpkg-dev qtbase5-dev libibus-1.0-dev libzstd-dev' >&2
  exit 1
fi
if ! command -v c++ >/dev/null 2>&1 && ! command -v g++ >/dev/null 2>&1; then
  echo 'Missing: C++ compiler.' >&2
  echo 'On Ubuntu/Debian, run:' >&2
  echo '  sudo apt install build-essential' >&2
  exit 1
fi
pkg-config --exists ibus-1.0 Qt5Widgets libzstd || {
  echo 'Missing Linux development libraries. On Ubuntu/Debian, run:' >&2
  echo '  sudo apt install qtbase5-dev libibus-1.0-dev libzstd-dev' >&2
  exit 1
}
BONGO_GITHUB_REPOSITORY="${BONGO_GITHUB_REPOSITORY:-mehedishakeel/Bongo}"
export DIST="${DIST:-$(dpkg --print-architecture)}"
UPDATE_ARGS=(
  "-DBONGO_UPDATE_URL=https://github.com/${BONGO_GITHUB_REPOSITORY}/releases/latest/download/linux.json"
  "-DBONGO_GITHUB_REPOSITORY=${BONGO_GITHUB_REPOSITORY}"
)
BUILD_DIR="$BONGO_ROOT/platforms/linux/build"
cmake -S "$BONGO_ROOT/platforms/linux" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release "${UPDATE_ARGS[@]}"
cmake --build "$BUILD_DIR" --parallel "${BONGO_BUILD_JOBS:-1}"
(cd "$BUILD_DIR" && cpack -G DEB)
