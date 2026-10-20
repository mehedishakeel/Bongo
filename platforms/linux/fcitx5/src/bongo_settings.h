// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <filesystem>
#include <string>
#include <string_view>

namespace bongo {

struct Settings {
    int typingMode = 0;
    bool suggestEmoji = true;
};

Settings parseSettings(std::string_view text);
Settings loadSettings(const std::filesystem::path &path);
std::filesystem::path settingsPath();

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
