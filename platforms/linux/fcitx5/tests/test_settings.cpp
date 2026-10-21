// SPDX-License-Identifier: MPL-2.0
#include "bongo_settings.h"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

namespace {

int failures = 0;

void expect(bool condition, const std::string &message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

void expectSettings(const bongo::Settings &actual, int mode, bool emoji,
                    const std::string &message, int layout = 0) {
    expect(actual.typingMode == mode, message + " typing_mode");
    expect(actual.keyboardLayout == layout, message + " keyboard_layout");
    expect(actual.suggestEmoji == emoji, message + " suggest_emoji");
}

} // namespace

int main() {
    expectSettings(bongo::parseSettings("{}"), 0, true, "empty object");
    expectSettings(
        bongo::parseSettings(
            R"({"typing_mode": 2, "suggest_emoji": false})"),
        2, false, "valid settings");
    expectSettings(bongo::parseSettings(R"({"typing_mode": 1})"), 1, true,
                   "mode only");
    expectSettings(bongo::parseSettings(R"({"suggest_emoji": false})"), 0,
                   false, "emoji only");
    expectSettings(bongo::parseSettings(R"({"keyboard_layout": 1})"), 0, true,
                   "layout only", 1);
    expectSettings(bongo::parseSettings(R"({"keyboard_layout": 5})"), 0, true,
                   "out of range layout", 0);
    expectSettings(bongo::parseSettings(R"({"typing_mode": 9})"), 0, true,
                   "out of range mode");
    expectSettings(bongo::parseSettings("{not json"), 0, true,
                   "malformed json");
    expectSettings(bongo::loadSettings("/nonexistent/bongo/settings.json"), 0,
                   true, "missing file");

    const auto temp =
        std::filesystem::temp_directory_path() / "bongo-fcitx5-settings-test";
    std::filesystem::remove_all(temp);
    std::filesystem::create_directories(temp / "bongo");
    const auto path = temp / "bongo" / "settings.json";
    {
        std::ofstream file(path);
        file << R"({"typing_mode": 2, "suggest_emoji": false})";
    }

    setenv("XDG_CONFIG_HOME", temp.c_str(), 1);
    bongo::SettingsWatcher watcher;
    expect(watcher.reloadIfChanged(), "first settings load reports a change");
    expectSettings(watcher.settings(), 2, false, "watcher initial settings");
    expect(!watcher.reloadIfChanged(), "unchanged settings are not reloaded");

    {
        std::ofstream file(path);
        file << R"({"typing_mode": 0, "suggest_emoji": true})";
    }
    expect(watcher.reloadIfChanged(), "modified settings are reloaded");
    expectSettings(watcher.settings(), 0, true, "watcher updated settings");

    unsetenv("XDG_CONFIG_HOME");
    std::filesystem::remove_all(temp);

    // fcitx5-configtool writes through applySettingsOverride; other keys
    // from bongo-settings (e.g. candidate_font) must survive, and values
    // must be updated in place with valid JSON.
    std::filesystem::create_directories(temp / "bongo");
    const auto path2 = temp / "bongo" / "settings.json";
    {
        std::ofstream file(path2);
        file << R"({
  "candidate_font": "Noto Sans Bengali",
  "typing_mode": 1,
  "suggest_emoji": true
})";
    }
    bongo::applySettingsOverride(path2, bongo::Settings{2, false});
    {
        std::ifstream file(path2);
        const std::string text((std::istreambuf_iterator<char>(file)),
                               std::istreambuf_iterator<char>());
        expect(text.find("\"candidate_font\": \"Noto Sans Bengali\"") !=
                   std::string::npos,
               "merge writer preserves unrelated keys");
        bongo::Settings parsed = bongo::parseSettings(text);
        expectSettings(parsed, 2, false, "merge writer updates both keys");
    }
    bongo::applySettingsOverride(path2, bongo::Settings{0, true});
    expectSettings(bongo::loadSettings(path2), 0, true,
                   "merge writer is re-appliable");

    std::filesystem::remove(path2);
    bongo::applySettingsOverride(path2, bongo::Settings{1, false});
    expectSettings(bongo::loadSettings(path2), 1, false,
                   "merge writer creates a file");

    std::filesystem::remove_all(temp);

    if (failures) {
        std::cerr << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "settings tests passed\n";
    return 0;
}
