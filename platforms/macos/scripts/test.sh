#!/bin/bash
# Headless integration test: drives the real BongoInputController (+ shared riti
# engine) with synthesized key events against a mock text client. Uses a scratch
# user dir (BONGO_USER_DIR), so real learned selections are never touched.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE_DIR="$PROJECT_ROOT/engine"
SRC="$PROJECT_ROOT/Bongo/Sources"
OUT="$PROJECT_ROOT/build/test"
BONGO_ROOT="$(cd "$PROJECT_ROOT/../.." && pwd)"

source "$HOME/.cargo/env" 2>/dev/null || true
if [ -x "/opt/homebrew/opt/rustup/bin/cargo" ]; then
    export PATH="/opt/homebrew/opt/rustup/bin:$PATH"
elif [ -x "/opt/homebrew/opt/rust/bin/cargo" ]; then
    export PATH="/opt/homebrew/opt/rust/bin:$PATH"
fi
export CLANG_MODULE_CACHE_PATH="${CLANG_MODULE_CACHE_PATH:-$BONGO_ROOT/.cache/clang}"
command -v cargo >/dev/null 2>&1 || { echo "Rust/Cargo is required." >&2; exit 1; }

echo ">>> Building Rust engine..."
(cd "$ENGINE_DIR" && cargo build --locked --release --target aarch64-apple-darwin)

echo ">>> Compiling integration test..."
mkdir -p "$OUT"
swiftc -O -module-name BongoTest \
    "$SRC/InputController.swift" "$SRC/Engine.swift" "$SRC/CandidatePanel.swift" \
    "$PROJECT_ROOT/tests/integration/main.swift" \
    -import-objc-header "$SRC/BridgeHeader.h" \
    -I "$ENGINE_DIR/include" \
    -L "$ENGINE_DIR/target/aarch64-apple-darwin/release" -lavrobangla_engine \
    -framework Cocoa -framework InputMethodKit \
    -target arm64-apple-macos13.0 \
    -o "$OUT/bongo_test"

echo ">>> Running..."
TEST_USER_DIR="$(mktemp -d "${TMPDIR:-/tmp}/bongo-test.XXXXXX")"
trap 'rm -rf "$TEST_USER_DIR"' EXIT
BONGO_USER_DIR="$TEST_USER_DIR" "$OUT/bongo_test"
