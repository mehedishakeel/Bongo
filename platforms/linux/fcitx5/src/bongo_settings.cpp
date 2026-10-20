// SPDX-License-Identifier: MPL-2.0
#include "bongo_settings.h"

#include <charconv>
#include <cstdlib>
#include <fstream>
#include <iterator>

namespace bongo {
namespace {

std::string_view valueAfterKey(std::string_view text, std::string_view key) {
    const auto keyPos = text.find(key);
    if (keyPos == std::string_view::npos) {
        return {};
    }
    const auto colon = text.find(':', keyPos + key.size());
    if (colon == std::string_view::npos) {
        return {};
    }
    auto value = text.substr(colon + 1);
    while (!value.empty() &&
           (value.front() == ' ' || value.front() == '\t' ||
            value.front() == '\r' || value.front() == '\n')) {
        value.remove_prefix(1);
    }
    return value;
}

} // namespace

Settings parseSettings(std::string_view text) {
    Settings settings;

    if (const auto value = valueAfterKey(text, "\"typing_mode\"");
        !value.empty()) {
        int mode = 0;
        const auto *begin = value.data();
        const auto *end = begin + value.size();
        const auto result = std::from_chars(begin, end, mode);
        if (result.ec == std::errc() && mode >= 0 && mode <= 2) {
            settings.typingMode = mode;
        }
    }

    if (const auto value = valueAfterKey(text, "\"suggest_emoji\"");
        !value.empty()) {
        if (value.starts_with("false")) {
            settings.suggestEmoji = false;
        } else if (value.starts_with("true")) {
            settings.suggestEmoji = true;
        }
    }

    return settings;
}

Settings loadSettings(const std::filesystem::path &path) {
    if (path.empty()) {
        return {};
    }
    std::ifstream file(path);
    if (!file) {
        return {};
    }
    const std::string text((std::istreambuf_iterator<char>(file)),
                           std::istreambuf_iterator<char>());
    return parseSettings(text);
}

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
        if (!loaded_) {
            loaded_ = true;
            return true;
        }
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
