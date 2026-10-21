#!/bin/bash
set -euo pipefail

BONGO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
[ "${EUID:-$(id -u)}" -ne 0 ] || { echo "Run this command without sudo." >&2; exit 1; }
[ "$(uname -s)" = Darwin ] || { echo "macOS required" >&2; exit 1; }

missing_apple_tools=()
for tool in swiftc clang codesign ditto hdiutil lipo; do
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
mkdir -p "$CLANG_MODULE_CACHE_PATH"

PROJECT_ROOT="$BONGO_ROOT/platforms/macos"
ENGINE_DIR="$PROJECT_ROOT/engine"
SWIFT_DIR="$PROJECT_ROOT/Bongo"
BUILD_DIR="$PROJECT_ROOT/build"
APP_NAME="Bongo"
APP_BUNDLE="$BUILD_DIR/Bongo Input Method.app"
LAUNCHER_DIR="$PROJECT_ROOT/Launcher"
LAUNCHER_BUNDLE="$BUILD_DIR/Bongo.app"
RELEASE_DIR="$PROJECT_ROOT/release"

TARGET_ARCH="${1:-arm64}" # arm64, x86_64, intel, universal, or all
BUILD_TYPE="${2:-release}"

CARGO_ARGS=""
if [ "$BUILD_TYPE" = "release" ]; then
    CARGO_ARGS="--release"
fi

# Ensure cargo is available
if ! command -v cargo &>/dev/null; then
    source "$HOME/.cargo/env" 2>/dev/null || true
fi
command -v cargo >/dev/null 2>&1 && command -v rustc >/dev/null 2>&1 || {
    echo "Install Rust first: brew install rustup && rustup default stable" >&2
    exit 1
}

build_single_arch() {
    local ARCH="$1" # arm64 or x86_64
    local RUST_TARGET=""
    local SWIFT_TARGET=""
    
    if [ "$ARCH" = "arm64" ]; then
        RUST_TARGET="aarch64-apple-darwin"
        SWIFT_TARGET="arm64-apple-macos13.0"
    elif [ "$ARCH" = "x86_64" ]; then
        RUST_TARGET="x86_64-apple-darwin"
        SWIFT_TARGET="x86_64-apple-macos13.0"
    else
        echo "Unknown architecture: $ARCH" >&2
        exit 1
    fi

    echo ">>> Ensuring Rust target $RUST_TARGET..."
    if command -v rustup >/dev/null 2>&1 && ! rustup target list --installed | grep -qx "$RUST_TARGET"; then
        rustup target add "$RUST_TARGET"
    fi

    echo ">>> Building Rust engine ($RUST_TARGET)..."
    (cd "$ENGINE_DIR" && cargo build --locked $CARGO_ARGS --target "$RUST_TARGET")
    local LIB_PATH="$ENGINE_DIR/target/${RUST_TARGET}/${BUILD_TYPE}/libavrobangla_engine.a"

    local OUT_DIR="$BUILD_DIR/arch_${ARCH}"
    rm -rf "$OUT_DIR"
    mkdir -p "$OUT_DIR"

    echo ">>> Compiling Swift Input Method for $ARCH..."
    local SWIFT_SOURCES=(
        "$SWIFT_DIR/Sources/AppDelegate.swift"
        "$SWIFT_DIR/Sources/CandidatePanel.swift"
        "$SWIFT_DIR/Sources/Engine.swift"
        "$SWIFT_DIR/Sources/InputController.swift"
        "$SWIFT_DIR/Sources/WelcomeWindow.swift"
        "$SWIFT_DIR/Sources/main.swift"
    )

    swiftc "${SWIFT_SOURCES[@]}" \
        -O \
        -module-name "$APP_NAME" \
        -import-objc-header "$SWIFT_DIR/Sources/BridgeHeader.h" \
        -I "$ENGINE_DIR/include" \
        -L "$(dirname "$LIB_PATH")" \
        -lavrobangla_engine \
        -framework Cocoa \
        -framework InputMethodKit \
        -framework WebKit \
        -target "$SWIFT_TARGET" \
        -o "$OUT_DIR/$APP_NAME"

    echo ">>> Compiling Launcher for $ARCH..."
    swiftc "$LAUNCHER_DIR/Sources/main.swift" \
        -O \
        -module-name BongoLauncher \
        -framework Cocoa \
        -framework Carbon \
        -target "$SWIFT_TARGET" \
        -o "$OUT_DIR/BongoLauncher"
}

assemble_bundle() {
    local ARCH_MODE="$1" # arm64, x86_64, or universal
    local DMG_SUFFIX=""
    if [ "$ARCH_MODE" = "arm64" ]; then
        DMG_SUFFIX="arm64"
    elif [ "$ARCH_MODE" = "x86_64" ]; then
        DMG_SUFFIX="intel-x86_64"
    elif [ "$ARCH_MODE" = "universal" ]; then
        DMG_SUFFIX="universal"
    fi

    echo ""
    echo "========================================="
    echo "  Assembling Bongo Bundle ($ARCH_MODE)   "
    echo "========================================="

    rm -rf "$APP_BUNDLE" "$LAUNCHER_BUNDLE"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    mkdir -p "$APP_BUNDLE/Contents/Resources"

    cp "$SWIFT_DIR/Resources/Info.plist" "$APP_BUNDLE/Contents/Info.plist"
    if [ -n "${BONGO_GITHUB_REPOSITORY:-}" ]; then
        /usr/libexec/PlistBuddy -c "Set :BongoGitHubRepository $BONGO_GITHUB_REPOSITORY" \
            "$APP_BUNDLE/Contents/Info.plist"
    fi
    cp "$SWIFT_DIR/Resources/iconTemplate.pdf" "$APP_BUNDLE/Contents/Resources/iconTemplate.pdf"
    cp "$SWIFT_DIR/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
    if [ -f "$SWIFT_DIR/Resources/Bongo-logo.png" ]; then
        cp "$SWIFT_DIR/Resources/Bongo-logo.png" "$APP_BUNDLE/Contents/Resources/Bongo-logo.png"
    fi
    cp "$BONGO_ROOT/THIRD_PARTY_NOTICES.md" "$APP_BUNDLE/Contents/Resources/"
    cp -R "$BONGO_ROOT/licenses" "$APP_BUNDLE/Contents/Resources/"
    echo -n "APPL????" > "$APP_BUNDLE/Contents/PkgInfo"

    if [ "$ARCH_MODE" = "universal" ]; then
        echo ">>> Merging universal binaries with lipo..."
        lipo -create "$BUILD_DIR/arch_arm64/$APP_NAME" "$BUILD_DIR/arch_x86_64/$APP_NAME" -output "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
    else
        cp "$BUILD_DIR/arch_${ARCH_MODE}/$APP_NAME" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
    fi

    codesign --force --sign - \
        --entitlements "$SWIFT_DIR/Resources/Bongo.entitlements" \
        "$APP_BUNDLE"

    # Assemble launcher
    mkdir -p "$LAUNCHER_BUNDLE/Contents/MacOS" \
        "$LAUNCHER_BUNDLE/Contents/Resources" \
        "$LAUNCHER_BUNDLE/Contents/Library/Input Methods"
    cp "$LAUNCHER_DIR/Resources/Info.plist" "$LAUNCHER_BUNDLE/Contents/Info.plist"
    cp "$SWIFT_DIR/Resources/AppIcon.icns" "$LAUNCHER_BUNDLE/Contents/Resources/AppIcon.icns"
    if [ -f "$SWIFT_DIR/Resources/Bongo-logo.png" ]; then
        cp "$SWIFT_DIR/Resources/Bongo-logo.png" "$LAUNCHER_BUNDLE/Contents/Resources/Bongo-logo.png"
    fi
    cp "$BONGO_ROOT/THIRD_PARTY_NOTICES.md" "$LAUNCHER_BUNDLE/Contents/Resources/"
    cp -R "$BONGO_ROOT/licenses" "$LAUNCHER_BUNDLE/Contents/Resources/"
    ditto "$APP_BUNDLE" "$LAUNCHER_BUNDLE/Contents/Library/Input Methods/Bongo Input Method.app"
    echo -n "APPL????" > "$LAUNCHER_BUNDLE/Contents/PkgInfo"
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_BUNDLE/Contents/Info.plist")" "$LAUNCHER_BUNDLE/Contents/Info.plist"
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$APP_BUNDLE/Contents/Info.plist")" "$LAUNCHER_BUNDLE/Contents/Info.plist"

    if [ "$ARCH_MODE" = "universal" ]; then
        lipo -create "$BUILD_DIR/arch_arm64/BongoLauncher" "$BUILD_DIR/arch_x86_64/BongoLauncher" -output "$LAUNCHER_BUNDLE/Contents/MacOS/Bongo"
    else
        cp "$BUILD_DIR/arch_${ARCH_MODE}/BongoLauncher" "$LAUNCHER_BUNDLE/Contents/MacOS/Bongo"
    fi

    codesign --force --sign - "$LAUNCHER_BUNDLE"

    mkdir -p "$RELEASE_DIR"
    local STAGE
    STAGE=$(mktemp -d "$BUILD_DIR/.dmg-stage.XXXXXX")
    ditto "$LAUNCHER_BUNDLE" "$STAGE/Bongo.app"
    ln -s '/Applications' "$STAGE/Applications"
    local VERSION
    VERSION=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_BUNDLE/Contents/Info.plist")
    local DMG_PATH="$RELEASE_DIR/Bongo-${VERSION}-macos-${DMG_SUFFIX}.dmg"
    rm -f "$DMG_PATH"
    hdiutil create -volname Bongo -srcfolder "$STAGE" -ov -format UDZO "$DMG_PATH"
    rm -rf "$STAGE"
    (cd "$RELEASE_DIR" && shasum -a 256 "$(basename "$DMG_PATH")" > "$(basename "$DMG_PATH").sha256")
    echo "Release generated: $DMG_PATH"
}

case "$TARGET_ARCH" in
    arm64)
        build_single_arch "arm64"
        assemble_bundle "arm64"
        ;;
    x86_64|intel)
        build_single_arch "x86_64"
        assemble_bundle "x86_64"
        ;;
    universal)
        build_single_arch "arm64"
        build_single_arch "x86_64"
        assemble_bundle "universal"
        ;;
    all)
        build_single_arch "arm64"
        build_single_arch "x86_64"
        assemble_bundle "arm64"
        assemble_bundle "x86_64"
        assemble_bundle "universal"
        ;;
    *)
        echo "Usage: $0 [arm64|x86_64|universal|all] [release|debug]" >&2
        exit 1
        ;;
esac

/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -u "$APP_BUNDLE" "$LAUNCHER_BUNDLE" 2>/dev/null || true
echo "Build and packaging completed successfully!"
