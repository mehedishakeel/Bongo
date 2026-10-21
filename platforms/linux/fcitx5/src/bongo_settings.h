// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <filesystem>
#include <string>
#include <string_view>

namespace bongo {

struct Settings {
    int typingMode = 0;
    int keyboardLayout = 0;
    bool suggestEmoji = true;

    Settings() = default;
    Settings(int mode, bool emoji, int layout = 0)
        : typingMode(mode), keyboardLayout(layout), suggestEmoji(emoji) {}
};

Settings parseSettings(std::string_view text);
Settings loadSettings(const std::filesystem::path &path);
std::filesystem::path settingsPath();
// Writes typing_mode / suggest_emoji into settings.json, preserving all
// other keys. Used by both bongo-settings and the fcitx5 config panel.
void applySettingsOverride(const std::filesystem::path &path,
                           const Settings &settings);

class SettingsWatcher {
public:
    const Settings &settings() const { return settings_; }
    bool reloadIfChanged();

private:
    std::filesystem::path path_ = settingsPath();
    std::filesystem::file_time_type mtime_{};
    bool loaded_ = false;
    Settings settings_;
};

} // namespace bongo
