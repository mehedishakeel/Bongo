#!/bin/bash
set -euo pipefail

BONGO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
[ "${EUID:-$(id -u)}" -ne 0 ] || { echo "Run this command without sudo." >&2; exit 1; }
[ "$(uname -s)" = Darwin ] || { echo "macOS required" >&2; exit 1; }
[ "$(uname -m)" = arm64 ] || { echo "Apple Silicon (arm64) required" >&2; exit 1; }
missing_apple_tools=()
for tool in swiftc clang codesign ditto hdiutil; do
    command -v "$tool" >/dev/null 2>&1 || missing_apple_tools+=("$tool")
done
if [ "${#missing_apple_tools[@]}" -ne 0 ]; then
    echo "Missing Apple developer tools: ${missing_apple_tools[*]}" >&2
    echo "Install them with: xcode-select --install" >&2
    exit 1
fi
if [ -x "/opt/homebrew/opt/rustup/bin/cargo" ]; then
    export PATH="/opt/homebrew/opt/rustup/bin:$PATH"
elif [ -x "/opt/homebrew/opt/rust/bin/cargo" ]; then
    export PATH="/opt/homebrew/opt/rust/bin:$PATH"
elif [ -x "/usr/local/opt/rust/bin/cargo" ]; then
    export PATH="/usr/local/opt/rust/bin:$PATH"
fi
export CLANG_MODULE_CACHE_PATH="${CLANG_MODULE_CACHE_PATH:-$BONGO_ROOT/.cache/clang}"

PROJECT_ROOT="$BONGO_ROOT/platforms/macos"
ENGINE_DIR="$PROJECT_ROOT/engine"
SWIFT_DIR="$PROJECT_ROOT/Bongo"
BUILD_DIR="$PROJECT_ROOT/build"
APP_NAME="Bongo"
APP_BUNDLE="$BUILD_DIR/Bongo Input Method.app"
LAUNCHER_DIR="$PROJECT_ROOT/Launcher"
LAUNCHER_BUNDLE="$BUILD_DIR/Bongo.app"
RELEASE_DIR="$PROJECT_ROOT/release"

# Parse arguments
BUILD_TYPE="${1:-release}"

echo "=== Bongo Apple Silicon Build ==="
echo "Build type: $BUILD_TYPE"
echo "Architecture: arm64 (Apple Silicon only)"
echo ""

# Ensure cargo is available
if ! command -v cargo &>/dev/null; then
    source "$HOME/.cargo/env" 2>/dev/null || true
fi
command -v cargo >/dev/null 2>&1 && command -v rustc >/dev/null 2>&1 || {
    echo "Install Rust first: brew install rustup && rustup default stable" >&2
    echo "See docs/BUILDING.md if Homebrew's rustup bin directory is not in PATH." >&2
    exit 1
}
if command -v rustup >/dev/null 2>&1 && ! rustup target list --installed | grep -qx 'aarch64-apple-darwin'; then
    echo "Missing Rust target. Run: rustup target add aarch64-apple-darwin" >&2
    exit 1
fi

# Step 1: Build Rust static library for Apple Silicon
echo ">>> Building Rust engine for Apple Silicon (aarch64-apple-darwin)..."

CARGO_ARGS=""
if [ "$BUILD_TYPE" = "release" ]; then
    CARGO_ARGS="--release"
fi

cd "$ENGINE_DIR"
cargo build --locked $CARGO_ARGS --target aarch64-apple-darwin
FINAL_LIB="$ENGINE_DIR/target/aarch64-apple-darwin/${BUILD_TYPE}/libavrobangla_engine.a"

echo ">>> Rust library built: $FINAL_LIB"

# Step 2: Create .app bundle structure
echo ">>> Creating app bundle..."
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy Info.plist
cp "$SWIFT_DIR/Resources/Info.plist" "$APP_BUNDLE/Contents/Info.plist"
if [ -n "${BONGO_GITHUB_REPOSITORY:-}" ]; then
    /usr/libexec/PlistBuddy -c "Set :BongoGitHubRepository $BONGO_GITHUB_REPOSITORY" \
        "$APP_BUNDLE/Contents/Info.plist"
fi

# Copy icons (PDF template icon for menu bar — macOS auto-inverts for dark mode + Globe overlay)
cp "$SWIFT_DIR/Resources/iconTemplate.pdf" "$APP_BUNDLE/Contents/Resources/iconTemplate.pdf"
cp "$SWIFT_DIR/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"

# riti compiles its dictionary/autocorrect/suffix/emoji data into the static
# library, so the data/ folder is not bundled.

# Create PkgInfo
echo -n "APPL????" > "$APP_BUNDLE/Contents/PkgInfo"

# Step 3: Compile Swift sources for Apple Silicon
echo ">>> Compiling Swift sources for Apple Silicon (arm64)..."

SWIFT_SOURCES=(
    "$SWIFT_DIR/Sources/AppDelegate.swift"
    "$SWIFT_DIR/Sources/CandidatePanel.swift"
    "$SWIFT_DIR/Sources/Engine.swift"
    "$SWIFT_DIR/Sources/InputController.swift"
    "$SWIFT_DIR/Sources/WelcomeWindow.swift"
    "$SWIFT_DIR/Sources/main.swift"
)

HEADER_SEARCH_PATH="$ENGINE_DIR/include"
BRIDGE_HEADER="$SWIFT_DIR/Sources/BridgeHeader.h"

SWIFT_FLAGS=(
    -O
    -module-name "$APP_NAME"
    -import-objc-header "$BRIDGE_HEADER"
    -I "$HEADER_SEARCH_PATH"
    -L "$(dirname "$FINAL_LIB")"
    -lavrobangla_engine
    -framework Cocoa
    -framework InputMethodKit
    -target arm64-apple-macos13.0
    -o "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
)

swiftc "${SWIFT_SOURCES[@]}" "${SWIFT_FLAGS[@]}"

# Include Bongo attribution with every build, not just release archives.
cp "$BONGO_ROOT/THIRD_PARTY_NOTICES.md" "$APP_BUNDLE/Contents/Resources/"
cp -R "$BONGO_ROOT/licenses" "$APP_BUNDLE/Contents/Resources/"

# Step 4: Sign the app (ad-hoc)
echo ">>> Signing app bundle..."
codesign --force --sign - \
    --entitlements "$SWIFT_DIR/Resources/Bongo.entitlements" \
    "$APP_BUNDLE"

# Build a normal Applications launcher. It opens the installed input-method
# process, which owns the settings and welcome window, so both entry points use
# one preferences store and one UI implementation.
echo ">>> Building Applications launcher for Apple Silicon..."
rm -rf "$LAUNCHER_BUNDLE"
mkdir -p "$LAUNCHER_BUNDLE/Contents/MacOS" \
    "$LAUNCHER_BUNDLE/Contents/Resources" \
    "$LAUNCHER_BUNDLE/Contents/Library/Input Methods"
cp "$LAUNCHER_DIR/Resources/Info.plist" "$LAUNCHER_BUNDLE/Contents/Info.plist"
cp "$SWIFT_DIR/Resources/AppIcon.icns" "$LAUNCHER_BUNDLE/Contents/Resources/AppIcon.icns"
cp "$BONGO_ROOT/THIRD_PARTY_NOTICES.md" "$LAUNCHER_BUNDLE/Contents/Resources/"
cp -R "$BONGO_ROOT/licenses" "$LAUNCHER_BUNDLE/Contents/Resources/"
ditto "$APP_BUNDLE" "$LAUNCHER_BUNDLE/Contents/Library/Input Methods/Bongo Input Method.app"
echo -n "APPL????" > "$LAUNCHER_BUNDLE/Contents/PkgInfo"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_BUNDLE/Contents/Info.plist")" "$LAUNCHER_BUNDLE/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$APP_BUNDLE/Contents/Info.plist")" "$LAUNCHER_BUNDLE/Contents/Info.plist"

swiftc "$LAUNCHER_DIR/Sources/main.swift" -O -module-name BongoLauncher -framework Cocoa -framework Carbon \
    -target arm64-apple-macos13.0 -o "$LAUNCHER_BUNDLE/Contents/MacOS/Bongo"
codesign --force --sign - "$LAUNCHER_BUNDLE"

echo ""
echo "=== Build complete ==="
echo "Input method: $APP_BUNDLE"
echo "Applications launcher: $LAUNCHER_BUNDLE"
echo ""

mkdir -p "$RELEASE_DIR"
STAGE=$(mktemp -d "$BUILD_DIR/.dmg-stage.XXXXXX")
trap 'rm -rf "$STAGE"' EXIT
ditto "$LAUNCHER_BUNDLE" "$STAGE/Bongo.app"
ln -s '/Applications' "$STAGE/Applications"
VERSION=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_BUNDLE/Contents/Info.plist")
DMG_PATH="$RELEASE_DIR/Bongo-${VERSION}-macos-arm64.dmg"
rm -f "$DMG_PATH"
hdiutil create -volname Bongo -srcfolder "$STAGE" -ov -format UDZO "$DMG_PATH"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u "$APP_BUNDLE" "$LAUNCHER_BUNDLE" 2>/dev/null || true
echo "Release: $DMG_PATH"
