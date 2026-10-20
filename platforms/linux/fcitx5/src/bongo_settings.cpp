// SPDX-License-Identifier: MPL-2.0
#include "bongo_settings.h"

#include <cstdlib>

namespace bongo {

Settings parseSettings(std::string_view) { return {}; }

Settings loadSettings(const std::filesystem::path &) { return {}; }

std::filesystem::path settingsPath() {
    if (const char *xdg = std::getenv("XDG_CONFIG_HOME"); xdg && *xdg) {
        return std::filesystem::path(xdg) / "bongo" / "settings.json";
    }
    if (const char *home = std::getenv("HOME"); home && *home) {
        return std::filesystem::path(home) / ".config" / "bongo" /
               "settings.json";
    }
    return {};
}

bool SettingsWatcher::reloadIfChanged() {
    if (path_.empty()) {
        settings_ = {};
        return false;
    }
    std::error_code error;
    const auto mtime = std::filesystem::last_write_time(path_, error);
    if (error) {
        if (!loaded_) {
            settings_ = {};
            loaded_ = true;
            return true;
        }
        return false;
    }
    if (loaded_ && mtime == mtime_) {
        return false;
    }
    settings_ = loadSettings(path_);
    mtime_ = mtime;
    loaded_ = true;
    return true;
}

} // namespace bongo
