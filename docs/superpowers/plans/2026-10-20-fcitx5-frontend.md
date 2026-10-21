# Bongo fcitx5 Frontend Implementation Plan

> **For the implementing engineer:** Execute this plan task by task in the current checkout (`/home/taxin/Work/bongo`, branch `feat/fcitx5`). Use TDD: add the failing test, run it, implement, run it again, then commit. Do not skip the engine task; the fcitx5 settings path must have visible behavior.

**Goal:** Add a native fcitx5 frontend to Bongo on Linux, using the existing Rust phonetic engine, while keeping the IBus frontend for GNOME.

**Architecture:** A C++20 `fcitx::InputMethodEngine` addon loads `libbongo_engine.so` through `dlopen`, keeps one engine per fcitx5 input context, and maps Bongo suggestions to fcitx5's native preedit and candidate panel. A small Rust engine update makes the existing typing-mode and emoji settings effective and crash-safe.

**Tech stack:** C++20, CMake, fcitx5 5.1+, Rust 2021, Python 3 for installer/profile helper and repository tests.

**Design:** `docs/superpowers/specs/2026-10-20-fcitx5-frontend-design.md`

---

## Task 0: Baseline

**Files:** none.

- [x] Confirm the tree is clean and the design is committed.

```bash
cd /home/taxin/Work/bongo
git status --short
git log -1 --oneline
```

- [x] Run the existing suite.

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests pass. If they do not, stop and report the failure before changing code.

---

## Task 1: Make Linux engine settings effective and crash-safe

**Files:**
- Modify: `vendor/rust/riti/src/config.rs`
- Modify: `vendor/rust/riti/src/phonetic/suggestion.rs`
- Modify: `vendor/rust/riti/src/fixed/method.rs`
- Modify: `vendor/rust/riti/src/phonetic/method.rs`
- Modify: `platforms/linux/engine/src/lib.rs`
- Test: inline `#[cfg(test)]` tests in the files above

### 1.1 Add the failing Rust tests

- [x] In `platforms/linux/engine/src/lib.rs`, add a test module. It must cover:
  - `PhoneticOnly` produces a single direct transliteration for `ami`.
  - `PhoneticFirst` produces more than one candidate for `ami`.
  - Emoji are present for `:)` when emoji suggestions are on and absent when off.
  - An invalid typing-mode value falls back to `PhoneticFirst`.
- [x] In `vendor/rust/riti/src/phonetic/method.rs`, add a test that writes to a user directory that does not contain the selection file. The test must create a temporary directory, set it with `Config::set_user_dir`, feed `ami`, call `candidate_committed(1, &config)`, and assert that the call does not panic and that the directory remains usable.
- [x] Add a test that `PhoneticMethod::new` survives a malformed selection JSON file.

Use helpers so the raw pointers are always freed:

```rust
fn options(engine: *mut BongoLinuxEngine, keys: &[char]) -> Vec<String> {
    let mut suggestion = std::ptr::null_mut();
    for ch in keys {
        if !suggestion.is_null() {
            bongo_suggestion_free(suggestion);
        }
        suggestion = bongo_engine_feed_char(engine, *ch as u32, 0, 0);
    }
    let mut result = Vec::new();
    if !suggestion.is_null() {
        for index in 0..bongo_suggestion_count(suggestion) {
            let ptr = bongo_suggestion_get_candidate(suggestion, index);
            if !ptr.is_null() {
                result.push(unsafe { std::ffi::CStr::from_ptr(ptr) }
                    .to_string_lossy()
                    .into_owned());
                bongo_string_free(ptr);
            }
        }
        bongo_suggestion_free(suggestion);
    }
    result
}
```

Run:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
cargo test --manifest-path platforms/linux/engine/Cargo.toml
cargo test --manifest-path vendor/rust/riti/Cargo.toml
```

Expected: the new tests fail because emoji/mode settings are not applied and the write path can panic.

### 1.2 Add `include_emoji` to `riti::Config`

- [x] Add a private `include_emoji: bool` field to `Config`.
- [x] Add public `get_include_emoji()` and `set_include_emoji(bool)`.
- [x] Set `include_emoji: true` in `impl Default for Config`.
- [x] Do not change any other `Config` constructor. The default keeps macOS, Windows, Android, and existing IBus behavior unchanged.
- [x] Gate both emoji blocks:
  - In `vendor/rust/riti/src/phonetic/suggestion.rs`, change `if !config.get_ansi_encoding()` to `if !config.get_ansi_encoding() && config.get_include_emoji()`.
  - In `vendor/rust/riti/src/fixed/method.rs`, do the same for the emoji block.

### 1.3 Apply settings in the Linux engine

- [x] Add `main_config: Config` and `shadow_config: Config` fields to `BongoLinuxEngine`.
- [x] Add a private constructor helper that creates the two configs:

```rust
fn make_configs(mode: TypingMode, show_emoji: bool) -> (Config, Config) {
    let mut main_config = Config::default();
    main_config.set_layout_file_path("avro_phonetic");
    main_config.set_phonetic_suggestion(mode != TypingMode::PhoneticOnly);
    main_config.set_include_emoji(show_emoji);

    let mut shadow_config = Config::default();
    shadow_config.set_layout_file_path("avro_phonetic");
    shadow_config.set_phonetic_suggestion(false);
    shadow_config.set_include_emoji(false);
    (main_config, shadow_config)
}
```

- [x] In `bongo_engine_new`, build the configs, build both contexts from them, and store the configs in the engine.
- [x] In `bongo_engine_set_mode`:
  - Normalize unknown values to `PhoneticFirst`.
  - If the normalized mode is unchanged, return.
  - Set `eng.mode`.
  - Set `main_config.set_phonetic_suggestion(mode != PhoneticOnly)`.
  - Call `eng.main_ctx.update_engine(&eng.main_config)`.
  - Call `eng.shadow_ctx.update_engine(&eng.shadow_config)` when present.
  - Finish both sessions and clear `current_phonetic`; the caller must not apply a new mode mid-composition, but the engine must not leave stale state.
- [x] In `bongo_engine_set_emoji`:
  - If unchanged, return.
  - Set `show_emoji`.
  - Set `main_config.set_include_emoji(enabled)` and `shadow_config.set_include_emoji(false)`.
  - Call `update_engine` on both contexts; do not finish the session, because emoji changes can be applied to the next suggestion.

### 1.4 Harden the selection write path

- [x] In `PhoneticMethod::new`, replace `serde_json::from_slice(&file).unwrap()` for the selection file with a fallback to an empty `HashMap` with `RandomState::new()` when parsing fails.
- [x] In `candidate_committed`:
  - Create the parent directory of `config.get_user_phonetic_selection_data()` with `std::fs::create_dir_all` when it has a parent.
  - Use `if let Ok(data) = serde_json::to_string(&self.selections)` and `let _ = write(path, data);` instead of `unwrap()`.
- [x] In `update_engine`, replace `file.metadata().unwrap().modified().unwrap()` and the autocorrect `serde_json::from_slice(...).unwrap()` with `if let Ok(...)` guards.
- [x] Keep the existing behavior when the files are valid.

### 1.5 Verify and commit

```bash
export PATH="$HOME/.cargo/bin:$PATH"
cargo test --manifest-path vendor/rust/riti/Cargo.toml
cargo test --manifest-path platforms/linux/engine/Cargo.toml
cargo build --manifest-path platforms/linux/engine/Cargo.toml --release
git diff --check
git add vendor/rust/riti platforms/linux/engine/src/lib.rs
git commit -m "fix(engine): apply typing mode and emoji settings safely"
```

Expected: tests pass, release library builds, no warnings from the new code that indicate ignored `Result`s in a way that changes behavior.

---

## Task 2: Create the fcitx5 addon skeleton and build

**Files:**
- Create: `platforms/linux/fcitx5/CMakeLists.txt`
- Create: `platforms/linux/fcitx5/data/bongo-addon.conf.in`
- Create: `platforms/linux/fcitx5/data/bongo.im.conf`
- Create: `platforms/linux/fcitx5/src/bongo.cpp`
- Create: `platforms/linux/fcitx5/src/bongo.h`
- Create: `platforms/linux/fcitx5/README.md`
- Create: `tests/test_fcitx5_distribution.py`

### 2.1 Add the static repository test first

- [x] Add `tests/test_fcitx5_distribution.py` with tests that assert:
  - The addon metadata contains `Library=libbongo`, `Type=SharedLibrary`, `OnDemand=True`, and `Category=InputMethod`.
  - The input method metadata contains `Addon=bongo`, `Icon=bongo`, `LangCode=bn`, and `Label=ব`.
  - `platforms/linux/fcitx5/CMakeLists.txt` requires fcitx5 5.1 and installs to `${FCITX_INSTALL_ADDONDIR}` and `${FCITX_INSTALL_PKGDATADIR}`.
  - No file under `platforms/linux/fcitx5` contains `OpenBangla` or a GPL identifier.
- [x] Run `python3 -m unittest tests.test_fcitx5_distribution -v` and confirm it fails because the files do not exist.

### 2.2 Add the minimal addon

- [x] `bongo.h` declares `class Bongo final : public fcitx::InputMethodEngine` with:
  - Constructor `explicit Bongo(fcitx::Instance *instance);`
  - `keyEvent`, `activate`, `deactivate`, and `reset` overrides.
  - A `FactoryFor<BongoState> factory_` member. `BongoState` is added in Task 3; for this task, use a temporary empty state class or implement the state header in the same commit. Prefer implementing Task 3's state skeleton here so the addon builds and the next task only fills behavior.
  - `BongoState *state(fcitx::InputContext *ic);`
- [x] `bongo.cpp` implements the addon factory:

```cpp
class BongoFactory final : public fcitx::AddonFactory {
public:
    fcitx::AddonInstance *create(fcitx::AddonManager *manager) override {
        return new Bongo(manager->instance());
    }
};

FCITX_ADDON_FACTORY_V2(bongo, BongoFactory);
```

- [x] Register the per-context property in the constructor:

```cpp
instance->inputContextManager().registerProperty("bongo", &factory_);
```

- [x] `data/bongo-addon.conf.in`:

```ini
[Addon]
Name=Bongo
Comment=Native Avro phonetic Bangla input method
Category=InputMethod
Version=@PROJECT_VERSION@
Library=libbongo
Type=SharedLibrary
OnDemand=True
Configurable=False

[Addon/Dependencies]
0=core:@REQUIRED_FCITX_VERSION@
```

- [x] `data/bongo.im.conf`:

```ini
[InputMethod]
Name=Bongo
Icon=bongo
Addon=bongo
Configurable=False
Label=ব
LangCode=bn
```

- [x] `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.16)
project(bongo-fcitx5 VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(REQUIRED_FCITX_VERSION 5.1.0)

find_package(Fcitx5Core ${REQUIRED_FCITX_VERSION} REQUIRED)
find_package(Fcitx5Module REQUIRED COMPONENTS Core)

include(GNUInstallDirs)
include(CTest)

add_fcitx5_addon(bongo
    src/bongo.cpp
    src/bongo_state.cpp
    src/bongo_api.cpp
    src/bongo_settings.cpp
)
target_include_directories(bongo PRIVATE src)
target_link_libraries(bongo PRIVATE Fcitx5::Core ${CMAKE_DL_LIBS})

install(TARGETS bongo DESTINATION "${FCITX_INSTALL_ADDONDIR}")
configure_file(data/bongo-addon.conf.in "${CMAKE_CURRENT_BINARY_DIR}/bongo-addon.conf" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/bongo-addon.conf"
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/addon"
        RENAME bongo.conf)
install(FILES data/bongo.im.conf
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/inputmethod"
        RENAME bongo.conf)
```

If `find_package(Fcitx5Module REQUIRED COMPONENTS Core)` fails because the component is not required for `add_fcitx5_addon`, use `find_package(Fcitx5Module REQUIRED)` and keep the include that provides the macro. `add_fcitx5_addon` is in `Fcitx5Utils`; including `Fcitx5Core` loads it transitively.

- [x] Add a short `README.md` with build commands:

```bash
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/fcitx5
```

### 2.3 Build and inspect

```bash
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_INSTALL_PREFIX=/tmp/bongo-fcitx5-prefix
cmake --build build/fcitx5
find build/fcitx5 -maxdepth 2 -type f -name 'libbongo.so' -o -name 'bongo.conf'
python3 -m unittest tests.test_fcitx5_distribution -v
```

Expected: `libbongo.so` and the configured `bongo.conf` exist, and the static test passes.

### 2.4 Commit

```bash
git add platforms/linux/fcitx5 tests/test_fcitx5_distribution.py
git commit -m "feat(fcitx5): add addon skeleton and metadata"
```

---

## Task 3: Implement the engine loader, settings parser, and per-context state

**Files:**
- Create: `platforms/linux/fcitx5/src/bongo_api.h`
- Create: `platforms/linux/fcitx5/src/bongo_api.cpp`
- Create: `platforms/linux/fcitx5/src/bongo_settings.h`
- Create: `platforms/linux/fcitx5/src/bongo_settings.cpp`
- Create: `platforms/linux/fcitx5/src/bongo_state.h`
- Create: `platforms/linux/fcitx5/src/bongo_state.cpp`
- Create: `platforms/linux/fcitx5/tests/test_settings.cpp`
- Modify: `platforms/linux/fcitx5/CMakeLists.txt`

### 3.1 Write the settings tests first

- [x] Add `tests/test_settings.cpp` with a tiny `expect` macro and these cases:
  - Empty object returns `{0, true}`.
  - `{"typing_mode": 2, "suggest_emoji": false}` returns `{2, false}`.
  - `{"typing_mode": 9, "suggest_emoji": true}` returns `{0, true}`.
  - Malformed JSON returns defaults.
  - A missing file returns defaults.
- [x] Add the test target to CMake:

```cmake
add_executable(test-settings tests/test_settings.cpp src/bongo_settings.cpp)
target_include_directories(test-settings PRIVATE src)
target_link_libraries(test-settings PRIVATE Fcitx5::Core)
add_test(NAME bongo-settings COMMAND test-settings)
```

If `bongo_settings.cpp` does not need fcitx5, link only the standard library; the include path is enough. Keep the test independent of the engine.

- [x] Run the test and confirm it fails because the parser is missing.

### 3.2 Implement `bongo_settings`

- [x] `bongo_settings.h`:

```cpp
struct Settings {
    int typingMode = 0;
    bool suggestEmoji = true;
};

Settings parseSettings(std::string_view text);
Settings loadSettings(const std::filesystem::path &path);
std::filesystem::path settingsPath();

class SettingsWatcher {
public:
    const Settings &settings() const;
    bool reloadIfChanged();
private:
    std::filesystem::path path_;
    std::filesystem::file_time_type mtime_{};
    bool loaded_ = false;
    Settings settings_;
};
```

- [x] `settingsPath()` uses `XDG_CONFIG_HOME/bongo/settings.json`, then `HOME/.config/bongo/settings.json`, then an empty path.
- [x] `parseSettings` finds the exact keys `"typing_mode"` and `"suggest_emoji"`. It accepts whitespace and ignores unrelated keys. It validates `typing_mode` to 0–2. It must not throw on malformed input.
- [x] `loadSettings` reads the file; on any error it returns defaults.
- [x] `SettingsWatcher::reloadIfChanged` stats the file. If the file is missing, it loads defaults once. If the mtime changed, it reloads. It returns `true` when the effective settings changed.
- [x] Add a temporary-file test for `SettingsWatcher`; use `std::filesystem::temp_directory_path()` and remove the files at the end.

### 3.3 Implement `bongo_api`

- [x] Define a `SuggestionPtr` and `StringPtr` with custom deleters that call `bongo_suggestion_free` and `bongo_string_free`.
- [x] `EngineApi` is a singleton with:
  - `bool valid()`
  - `void *newEngine()`
  - `void freeEngine(void *)`
  - `void setMode(void *, uint32_t)`
  - `void setEmoji(void *, bool)`
  - `bool hasSession(void *)`
  - `SuggestionPtr feedChar(void *, uint32_t, uint8_t, uint8_t)`
  - `SuggestionPtr backspace(void *, bool)`
  - `void commit(void *, size_t)`
  - `void reset(void *)`
  - `size_t suggestionCount(const void *)`
  - `std::string candidate(const void *, size_t)`
  - `std::string preview(const void *)`
- [x] Resolve the library in this order:
  1. `BONGO_ENGINE_LIB`.
  2. `$ORIGIN/../bongo/libbongo_engine.so`.
  3. `$ORIGIN/../../bongo/libbongo_engine.so`.
  4. `/usr/lib/bongo/libbongo_engine.so`.
  5. `/usr/lib64/bongo/libbongo_engine.so`.
  6. `/usr/lib/x86_64-linux-gnu/bongo/libbongo_engine.so`.
  7. `/usr/lib/aarch64-linux-gnu/bongo/libbongo_engine.so`.
  8. `/usr/local/lib/bongo/libbongo_engine.so`.
  9. `$HOME/.local/lib/bongo/libbongo_engine.so`.
  10. `libbongo_engine.so` (loader default path).
- [x] Use `dlopen(path, RTLD_NOW | RTLD_LOCAL)`, then `dlsym` every function. If any required symbol is missing, close the handle and mark the API invalid.
- [x] Log the successful path at info level and each failure at warning level with `FCITX_WARN()`. Do not log the full environment.
- [x] Never dereference a null function pointer. `valid()` must be checked by the state before any call.

### 3.4 Implement `BongoState` skeleton

- [x] `BongoState` derives from `fcitx::InputContextProperty`.
- [x] Constructor stores `Bongo *addon_`, `fcitx::InputContext *ic_`, creates the engine if `EngineApi::valid()`, applies settings, and sets the initial settings mtime.
- [x] Destructor frees the engine after resetting the input panel; do not call `commitString` in the destructor.
- [x] Methods:
  - `void keyEvent(fcitx::KeyEvent &event);`
  - `void activate();`
  - `void deactivate();`
  - `void reset();`
- [x] The constructor must not crash when the engine library is missing. In that case `keyEvent` returns immediately and logs once.
- [x] The addon's `keyEvent` obtains the state with `ic->propertyFor(&factory_)` and delegates.

### 3.5 Verify and commit

```bash
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja -DBUILD_TESTING=ON
cmake --build build/fcitx5
ctest --test-dir build/fcitx5 --output-on-failure
python3 -m unittest tests.test_fcitx5_distribution -v
git diff --check
git add platforms/linux/fcitx5
git commit -m "feat(fcitx5): load engine and read Bongo settings"
```

Expected: settings tests pass; the addon builds; the static test passes.

---

## Task 4: Implement key handling, preedit, candidates, and lifecycle

**Files:**
- Modify: `platforms/linux/fcitx5/src/bongo_state.cpp`
- Modify: `platforms/linux/fcitx5/src/bongo_state.h`
- Modify: `platforms/linux/fcitx5/src/bongo.cpp`
- Create: `platforms/linux/fcitx5/tests/smoke.md`

### 4.1 Implement the behavior table

- [x] Ignore key releases.
- [x] Read `event.key().sym()`, `event.key().states()`, and `fcitx::Key::keySymToUnicode(sym)`.
- [x] Treat Ctrl, Alt, and Super as pass-through shortcuts. If a session exists, commit the current candidate first.
- [x] If the engine is missing or a printable key is not handled while composing, commit the current candidate and pass the key through. Never leave a dangling preedit.
- [x] Handle keys in this order:
  1. Escape: reset engine, clear panel, `filterAndAccept`.
  2. Space: commit current, do not accept, so the space reaches the application.
  3. Return and KP_Enter: commit current, `filterAndAccept`.
  4. BackSpace: engine backspace, update panel, `filterAndAccept`.
  5. Up/Tab/ISO_Left_Tab/KP_Up: previous candidate; Down/KP_Down: next candidate; Page_Up: previous page; Page_Down: next page. All accepted.
  6. `1`–`9` without Shift: select that candidate if it exists; accepted.
  7. Printable Unicode: feed the codepoint with shift state and current candidate index; accepted if the engine returns a suggestion or has a session.
- [x] Update the composition:
  - `updateSuggestions(SuggestionPtr)` collects all candidates with `suggestionCount`/`candidate`.
  - Use `preview` as the preedit when candidates are empty; otherwise use the selected candidate.
  - Build a `fcitx::CommonCandidateList`, set page size 9, selection keys `1`–`9`, cursor-after-paging `ResetToFirst`, layout hint vertical, append `BongoCandidate` words with their 1-based labels.
  - Set `ic_->inputPanel().setCandidateList(std::move(list))`, then keep a raw pointer to the owned list for navigation.
  - If the client supports `CapabilityFlag::Preedit`, call `setClientPreedit(Text(preedit))`; otherwise call `setPreedit(Text(preedit))`. Call `ic_->updatePreedit()` and `updateUserInterface(InputPanel)`.
- [x] `BongoCandidate::select` calls `state_->commitCandidate(index)`.
- [x] `commitCandidate`:
  - Validate the index.
  - Capture the text.
  - `ic_->commitString(text)`.
  - `api_->commit(engine_, index)`.
  - Clear the panel and state.
- [x] `commitCurrent` commits the selected candidate. If there are no candidates but a preedit exists, commit the preedit and reset the engine.
- [x] `clearPanel` calls `ic_->inputPanel().reset()`, clears candidates/preedit/cursor, and updates preedit/UI.
- [x] `resetSession` calls `api_->reset`, then `clearPanel`.
- [x] `activate` reloads settings, applies them if no session, and resets stale engine state.
- [x] `deactivate` commits an active composition, then clears the panel, matching IBus focus-out.
- [x] `reset` discards the composition and clears the panel.
- [x] `keyEvent` reloads settings only when the mtime changes. Apply new mode/emoji only when no composition is active; if a composition is active, store the settings and apply after the next commit/reset.

### 4.2 Add the manual smoke checklist

- [x] Create `tests/smoke.md` with the Omarchy checks:
  - `fcitx5-remote -n` lists `bongo` after install.
  - Type `ami` in a GTK4 entry; preedit appears; candidates show; space commits and inserts a space.
  - Type `ami`, press `1`; first candidate commits.
  - Backspace edits the preedit.
  - Escape clears the preedit.
  - Down/Tab/PageDown move the selection; the preedit follows.
  - Ctrl+C while composing commits and passes the shortcut.
  - Focus another window while composing; the composition commits.
  - Change `typing_mode` to 2; next composition is direct phonetic only.
  - Change `suggest_emoji` to false; `:)` no longer shows emoji.
  - Select a candidate in Smart mode with a missing `~/.local/share/openbangla-keyboard` directory; fcitx5 does not crash.

### 4.3 Build and run static checks

```bash
cmake --build build/fcitx5
ctest --test-dir build/fcitx5 --output-on-failure
python3 -m unittest tests.test_fcitx5_distribution -v
git diff --check
```

### 4.4 Commit

```bash
git add platforms/linux/fcitx5
git commit -m "feat(fcitx5): map Bongo keys, preedit, and candidates"
```

---

## Task 5: Installer and fcitx5 profile setup

**Files:**
- Create: `platforms/linux/scripts/configure-fcitx5.py`
- Create: `tests/test_fcitx5_profile.py`
- Modify: `platforms/linux/scripts/install.sh`
- Modify: `tests/test_fcitx5_distribution.py`

### 5.1 Write the profile helper tests first

- [x] Add `tests/test_fcitx5_profile.py` that imports functions from `configure-fcitx5.py` via `importlib`.
- [x] Tests:
  - A missing profile gets a minimal valid profile containing `keyboard-us` and `bongo`.
  - An existing profile with `keyboard-us` gets `bongo` appended to the first group.
  - A profile that already contains `bongo` is unchanged.
  - A malformed profile is left unchanged and the function reports failure.
  - `DefaultIM` and existing item order are preserved.
  - A backup file is created on the first modification.
- [x] Run the test and confirm it fails because the helper does not exist.

### 5.2 Implement `configure-fcitx5.py`

- [x] Use only the Python standard library (`argparse`, `configparser` only if it preserves enough, `os`, `pathlib`, `pwd`, `shutil`, `sys`).
- [x] Do not use `configparser` to rewrite the file; use line-based editing so comments and order are preserved.
- [x] Resolve the target profile:
  - `--profile` overrides everything.
  - If run as root with `SUDO_USER`, edit that user's `XDG_CONFIG_HOME` or `~/.config/fcitx5/profile`.
  - Otherwise use the current user's config.
- [x] If the profile is missing, write the minimal default shown in the design.
- [x] Find the first group number from `[GroupOrder]`; find `[Groups/<n>]`.
- [x] If any `[Groups/<n>/Items/*]` has `Name=bongo`, print `already configured` and exit 0.
- [x] Determine the next item index. Insert a new item section after the last item in that group. Do not reorder anything.
- [x] Back up to `profile.bongo-backup` before the first change; do not overwrite an existing backup.
- [x] If the structure is not understood, print a clear message and exit nonzero without writing.
- [x] When root edits a user's file, `os.chown` the profile and backup to the target user/group.
- [x] Add `--print-manual-steps` for installers that must not edit the profile.
- [x] Add a `main()` and `if __name__ == "__main__": raise SystemExit(main())`.

### 5.3 Modify `install.sh`

- [x] Add `BONGO_FCITX5="${BONGO_FCITX5:-auto}"` and parse `--no-configure-fcitx5`.
- [x] Detect:
  - Runtime: `command -v fcitx5`.
  - Headers: `pkg-config --exists Fcitx5Core` and `pkg-config --exists Fcitx5Module` (or `cmake` config presence).
  - IBus: `command -v ibus`.
- [x] Keep the existing IBus build/install path.
- [x] Build the engine once; install it to `${PREFIX}/lib/bongo` as today.
- [x] If `BONGO_FCITX5=1` or (`auto` and headers exist):
  - Configure with `cmake -S "${LINUX_ROOT}/fcitx5" -B "${LINUX_ROOT}/build/fcitx5" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="${PREFIX}"`.
  - Build and `DESTDIR="${DESTDIR}" cmake --install`.
  - For a source install with `DESTDIR` empty and `EUID != 0`, do not install the addon user-local. Print:
    `sudo BONGO_FCITX5=1 bash platforms/linux/scripts/install.sh`
    and skip only the fcitx5 system files.
- [x] Install `configure-fcitx5.py` as `${PREFIX}/bin/bongo-fcitx5-setup` with executable permissions.
- [x] After a successful system install, if not `--no-configure-fcitx5` and `DESTDIR` is empty:
  - If `SUDO_USER` is set, run `runuser -u "$SUDO_USER" -- python3 "$SCRIPT_DIR/configure-fcitx5.py"`.
  - Otherwise run the helper as the current user.
  - If the helper fails, print the manual steps and continue; installation is still valid.
- [x] Error only when neither IBus nor fcitx5 is installed. If fcitx5 is installed but headers are missing, print the distro package hint and continue with IBus.
- [x] Keep the existing output structure and `DESTDIR` semantics.

### 5.4 Test the installer staging

```bash
export PATH="$HOME/.cargo/bin:$PATH"
rm -rf /tmp/bongo-stage
DESTDIR=/tmp/bongo-stage PREFIX=/usr BONGO_FCITX5=1 \
  bash platforms/linux/scripts/install.sh
find /tmp/bongo-stage -type f \( -name 'libbongo.so' -o -name 'bongo.conf' -o -name 'bongo-fcitx5-setup' \) -print
python3 -m unittest tests.test_fcitx5_profile tests.test_fcitx5_distribution -v
bash -n platforms/linux/scripts/install.sh
```

Expected: all three files are staged in the correct `usr/...` paths, tests pass, and shell syntax is valid.

### 5.5 Commit

```bash
git add platforms/linux/scripts/install.sh platforms/linux/scripts/configure-fcitx5.py tests
git commit -m "feat(installer): install and configure the fcitx5 addon"
```

---

## Task 6: Packaging and CI

**Files:**
- Modify: `platforms/linux/scripts/build-deb.sh`
- Modify: `platforms/linux/scripts/build-rpm.sh`
- Modify: `.github/workflows/ci.yml`

### 6.1 Debian package

- [x] Set `BONGO_FCITX5="${BONGO_FCITX5:-auto}"` when invoking `install.sh`.
- [x] Change `Depends` so IBus is not mandatory:
  - `Depends: python3, python3-gi, gir1.2-gtk-4.0 | gir1.2-gtk-3.0`
  - `Recommends: ibus, gir1.2-ibus-1.0, fcitx5`
  - `Suggests: fcitx5-configtool`
- [x] Keep the package name/version/architecture unchanged.
- [x] Verify the staged tree includes the fcitx5 files when `BONGO_FCITX5=1`.

### 6.2 RPM package

- [x] Set `BONGO_FCITX5="${BONGO_FCITX5:-auto}"` when invoking `install.sh`.
- [x] Change `Requires` so IBus is not mandatory; use `Requires: python3, python3-gobject, gtk4` and `Recommends: ibus, fcitx5`.
- [x] Add the fcitx5 addon, metadata, and `bongo-fcitx5-setup` to `%files`.
- [x] Use `%{_libdir}/fcitx5/libbongo.so` for the addon path; use `%{_datadir}/fcitx5/...` for metadata. Do not hardcode `lib64` in the spec.
- [x] Keep the existing IBus files.

### 6.3 CI

- [x] In the `linux` job, install fcitx5 development packages before the build:
  - `sudo apt-get update`
  - `sudo apt-get install -y libfcitx5core-dev fcitx5-modules-dev`
  - If `fcitx5-modules-dev` is unavailable on the runner, use `libfcitx5core-dev` and check whether `Fcitx5Module` is provided; skip the fcitx5 build with a warning rather than failing the job.
- [x] Set `BONGO_FCITX5=1` only when the headers are present.
- [x] Add a CMake configure/build/ctest step for `platforms/linux/fcitx5`.
- [x] Keep `bash -n` checks for the new Python helper (`python3 -m py_compile ...`).

### 6.4 Verify and commit

```bash
bash -n platforms/linux/scripts/build-deb.sh
bash -n platforms/linux/scripts/build-rpm.sh
python3 -m py_compile platforms/linux/scripts/configure-fcitx5.py
python3 -m unittest discover -s tests -v
git diff --check
git add platforms/linux/scripts/build-deb.sh platforms/linux/scripts/build-rpm.sh .github/workflows/ci.yml
git commit -m "build(linux): package and test the fcitx5 frontend"
```

---

## Task 7: Documentation and Omarchy integration test

**Files:**
- Modify: `platforms/linux/README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/LINUX-INSTALL.md`
- Modify: `README.md` only if the Linux feature list needs fcitx5 mentioned
- Modify: `platforms/linux/fcitx5/README.md`

### 7.1 Documentation

- [x] In `platforms/linux/README.md`, add fcitx5 to the architecture tree and explain that KDE/Omarchy/Hyprland should use fcitx5 while GNOME uses IBus.
- [x] In `docs/LINUX-INSTALL.md`, add:
  - Arch/Omarchy: `sudo pacman -S fcitx5 fcitx5-configtool` (headers ship with fcitx5 on Arch), then `sudo bash platforms/linux/scripts/install.sh`.
  - Debian/Ubuntu: `sudo apt install fcitx5 fcitx5-configtool libfcitx5core-dev`, then install.
  - Fedora: `sudo dnf install fcitx5 fcitx5-configtool fcitx5-devel`, then install.
  - How to verify: `fcitx5-remote -n`, `fcitx5-configtool`, `Ctrl+Space`.
  - GNOME: keep using IBus; fcitx5 is optional.
- [x] In `docs/ARCHITECTURE.md`, describe the two Linux frontends sharing the same engine C ABI.
- [x] In `platforms/linux/fcitx5/README.md`, document the system-wide install and the candidate-font limitation.

### 7.2 Install system-wide and test on Omarchy

- [x] Build and install with sudo (done via `pkexec` with `SUDO_USER`/`HOME` set so the profile helper edits the desktop user's config).

- [x] Restart fcitx5 (the installer now stops fcitx5 before editing the profile and restarts it afterwards; `fcitx5-remote -r` alone does not load a newly installed addon).

- [x] Confirm the addon and input method are visible:

```bash
fcitx5-remote -m bongo        # -> bongo
test -f /usr/lib/fcitx5/libbongo.so
test -f /usr/share/fcitx5/addon/bongo.conf
test -f /usr/share/fcitx5/inputmethod/bongo.conf
ls -l /usr/lib/bongo/libbongo_engine.so
```

- [x] Confirm the profile contains `bongo` (survives a stop -> configure -> start round trip):

```bash
grep -n 'Name=bongo' ~/.config/fcitx5/profile
```

- [x] Test in a GTK4 entry, a Qt6 app, foot, and VS Code as described in `platforms/linux/fcitx5/tests/smoke.md`, using `wtype` key injection.
- [x] Fix mismatches found: IBus-matching keymap (digit selection, PageUp/PageDown), focus-out duplicate commit; each fix re-tested and reinstalled.
- [x] Verify the IBus files still exist and are unchanged by the fcitx5 work:

```bash
git diff --stat upstream/main -- platforms/linux/ibus platforms/linux/engine/src platforms/linux/ui
```

Expected: only the intended engine changes; IBus engine and UI behavior are unchanged.

### 7.3 Commit

```bash
git add README.md docs platforms/linux/README.md platforms/linux/fcitx5/README.md
git commit -m "docs: document the fcitx5 Linux frontend"
```

---

## Task 8: Final verification and publish

- [ ] Run the full suite:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
python3 -m unittest discover -s tests -v
cargo test --manifest-path vendor/rust/riti/Cargo.toml
cargo test --manifest-path platforms/linux/engine/Cargo.toml
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja -DBUILD_TESTING=ON
cmake --build build/fcitx5
ctest --test-dir build/fcitx5 --output-on-failure
bash -n platforms/linux/scripts/install.sh
bash -n platforms/linux/scripts/build-deb.sh
bash -n platforms/linux/scripts/build-rpm.sh
python3 -m py_compile platforms/linux/scripts/configure-fcitx5.py
git diff --check
```

- [ ] Inspect the final diff for accidental IBus or macOS/Windows changes.
- [ ] Confirm `git status --short` is clean.
- [ ] Push the branch and open a draft PR against `mehedishakeel/Bongo:main`:

```bash
git push -u origin feat/fcitx5
gh pr create --repo mehedishakeel/Bongo --base main --head taxin-404:feat/fcitx5 \
  --draft --title "feat(linux): add native fcitx5 frontend" \
  --body "Adds a native fcitx5 addon for Bongo, reusing the Rust engine and keeping IBus for GNOME. Includes installer/package integration and tests."
```

- [ ] Report the PR URL, the tested paths, and any remaining manual test gaps (Qt/Electron, GNOME IBus regression).

---

## Task 9: Native fcitx5-configtool addon configuration (post-review improvement)

fcitx5 users should configure Bongo from the tools they already use. The addon
now implements `getConfig()`/`setConfig()`/`reloadConfig()` with a native
configuration model so the addon appears with its own page under
fcitx5-configtool's "Addons" tab.

Design (kept from the notes above): `~/.config/bongo/settings.json` remains the
single source of truth. The native page is a view plus a writer — `setConfig()`
merges `typing_mode` and `suggest_emoji` into settings.json and preserves every
other key; `getConfig()` always reads settings.json. If the user later edits
from `bongo-settings` or another platform's GUI, both stay consistent.

- [x] `BongoAddonConfig` (Enum `typing_mode` + Boolean `suggest_emoji`) with
      `Configurable=True` in `bongo-addon.conf.in`.
- [x] `applySettingsOverride()` merge writer in `bongo_settings.cpp`
      (same-line colon bound, no trailing-comma, preserves unknown keys) with
      unit tests in `test_settings.cpp`.
- [x] Distribution test asserts `Configurable=True`.
- [x] Live: GetConfig returns values + description over DBus; SetConfig
      (gdbus) updates settings.json in place while preserving
      `candidate_font`; restored values read back correctly. See
      `tests/smoke.md` ("Native addon configuration").
- [x] Live: typing still commits (`ami ` → `আমি `) after the reconfigured
      addon reinstall.
- Known gap: configtool's own page render was shown once but the visual
      walkthrough was half-done (window closed mid-test); the DBus contract
      fcitx5-configtool uses is verified above.

## Task 10: Restart systemd-managed fcitx5 through its unit (functional)

Debugging "nothing works on Hyprland" surfaced a real installer flaw: on
Omarchy, fcitx5 runs as `omarchy-fcitx5.service` (Restart=always). The
installer stopped it with `fcitx5-remote -e` and restarted a bare
`fcitx5 -d`; the unit then kept trying to start a competing instance that
exited because the manual one held the DBus name — an auto-restart loop, and
the live instance was no longer supervised by the session.

- [x] Detect the systemd user unit whose `MainPID` owns the running fcitx5
      (query as the desktop user via `runuser` + the user manager).
- [x] Stop/start that unit around the profile rewrite instead of killing and
      spawning a bare process; keep the old path when no unit owns fcitx5.
- [x] Failure message names the unit when the systemd path is used.
- [x] Distribution test locks the detection in.
- [x] Live reinstall on Omarchy verifies the unit keeps its PID ownership
      (installer logged "Stopping fcitx5 via omarchy-fcitx5.service", the
      unit came back with a new MainPID, stayed active without restarts,
      and Ctrl+Space + typing still work).

## Task 11: Desktop auto-detection with two enablement groups (functional)

User request: the installer should detect the desktop and enable Bongo itself,
grouped as **GNOME (IBus)** and **native fcitx5** (KDE, Hyprland, other WMs) —
two groups, not four desktop-specific paths.

- [x] Detect the running desktop by process (`gnome-shell`, `plasmashell`,
      `Hyprland`/`sway`/`river`/`wayfire`/`labwc`) before the remote/local
      split, so detection also works through `sudo`/`pkexec` where
      `XDG_CURRENT_DESKTOP` is dropped.
- [x] Map detection to `IM_FRAMEWORK=ibus|fcitx5`; fall back to whichever
      framework is installed when no session is visible (SSH).
- [x] Group 1 (GNOME): append `('ibus', 'bongo')` to
      `org.gnome.desktop.input-sources sources`, preserving existing sources,
      and print the previous value. Runs in the user's session via a shared
      `bongo_as_user` helper.
- [x] Group 2 (fcitx5): keep the profile rewrite, and add a session autostart
      entry (`~/.config/autostart/org.fcitx.Fcitx5.desktop`) only when no
      systemd unit and no existing entry starts fcitx5. Print `exec-once`
      guidance for Wayland WMs when startup is not managed.
- [x] Apply the GNOME enablement to the remote `curl | bash` deb path as well.
- [x] Keep the pure merge logic in `bongo_ibus_add_source` so distribution
      tests execute the shipped function with sample gsettings values.
- [x] Tests: 27 Python distribution tests pass, including the merge cases
      (`[('xkb','us')]`, two sources, `@as []`, `[]`) and both-path coverage.
- [x] Live verification on Omarchy (Hyprland): installer detected `wlwm`,
      chose fcitx5, logged `fcitx5 starts at login via
      omarchy-fcitx5.service`, restarted through the unit
      (`NRestarts=0` afterwards), profile kept `DefaultIM=bongo`.
- [ ] GNOME path not live-tested locally (no GNOME/IBus on this machine);
      verified with a fake `gsettings` harness for append/already-present/
      empty-list and left for maintainer GNOME testing.
- [ ] Remote deb path can only enable the IBus group today because the
      released 1.0.1 deb has no fcitx5 addon; enable fcitx5 there when the
      release deb ships the addon.

## Task 12: CI portability fixes found by the first CI run

- [x] Linux: Ubuntu 24.04 ships fcitx5 5.1.7, whose `Fcitx5Macros.cmake`
      lacks `add_fcitx5_addon` (added in a later release). `CMakeLists.txt`
      now defines an equivalent MODULE-library helper when the command is
      missing.
- [x] Reproduced CI's exact configure error locally against the real Ubuntu
      5.1.7 dev/runtime debs extracted to a prefix; after the fallback,
      configure + build + CTest (3/3) pass against those packages.
- [x] macOS: the Task 1 patches to `vendor/rust/riti` invalidated
      `.cargo-checksum.json`; the macOS engine resolves its git riti
      dependency through `vendor/rust`, so `cargo build --locked` rejected
      the four edited files. Updated the checksums and added a repository
      test that recomputes every vendored crate checksum.
- [x] Verified: `cargo build --locked` in `platforms/macos/engine` succeeds
      (was exit 101), native CTest 4/4, 29 Python tests pass.

## Deferred: settings UI look-and-feel on Omarchy/Hyprland

User feedback: the GTK settings window "feels nothing to do with Hyprland".
Decision (2026-10-20): **function only for now** — the look and feel of the
settings app is the maintainer's product call and a redesign would add
subjective noise to a PR already queued for v1.1.0 review. Revisit after the
fcitx5 frontend merges, with maintainer direction on the desired desktop
integration (theme matching, launch style, window rules).

---

## Notes for the Implementer

- The fcitx5 addon library must be system-wide. Do not try to load it from `~/.local/lib/fcitx5`; fcitx5 does not discover that path reliably.
- The engine library can be user-local because the addon runs as the user; the installer still installs it to `${PREFIX}/lib/bongo` for consistency.
- `~/.config/bongo/settings.json` is the source of truth. Do not add a second fcitx5-specific config file.
- The fcitx5 candidate font follows the fcitx5 theme. Do not read `candidate_font` in the addon.
- Keep the `Label=ব` and `LangCode=bn` metadata; the label is the user's visible input-method marker.
- When in doubt, match `platforms/linux/ibus/bongo_ibus_engine.py`, not OpenBangla's frontend.
