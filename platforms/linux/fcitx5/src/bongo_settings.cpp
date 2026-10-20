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

std::string scalarJson(int value) { return std::to_string(value); }

std::string scalarJson(bool value) { return value ? "true" : "false"; }

// Replaces the value of `key` with `scalar`, or inserts the key right
// after the opening brace of an object. The result is valid JSON if the
// input was valid and flat (which is what bongo-settings writes).
std::string replaceOrInsertKey(std::string text, const std::string &key,
                               const std::string &scalar) {
    const std::string pattern = "\"" + key + "\"";
    const auto keyPos = text.find(pattern);
    if (keyPos != std::string::npos) {
        // The colon must be on the same line as the key; this keeps us
        // from replacing a value of some unrelated later key when the
        // key name only appears inside a string value.
        const auto lineEnd = text.find('\n', keyPos + pattern.size());
        const auto colon = text.find(':', keyPos + pattern.size());
        if (colon == std::string::npos ||
            (lineEnd != std::string::npos && colon > lineEnd)) {
            return text;
        }
        auto valuePos = colon + 1;
        while (valuePos < text.size() &&
               (text[valuePos] == ' ' || text[valuePos] == '\t' ||
                text[valuePos] == '\r')) {
            ++valuePos;
        }
        auto valueEnd = valuePos;
        while (valueEnd < text.size() && text[valueEnd] != ',' &&
               text[valueEnd] != '}' && text[valueEnd] != '\n') {
            ++valueEnd;
        }
        text.replace(valuePos, valueEnd - valuePos, scalar);
        return text;
    }

    const auto brace = text.find('{');
    if (brace == std::string::npos) {
        // Not an object at all; start over with a valid object.
        return "{\n  \"" + key + "\": " + scalar + "\n}\n";
    }
    auto first = brace + 1;
    while (first < text.size() && text[first] != '}' &&
           (text[first] == ' ' || text[first] == '\t' ||
            text[first] == '\r' || text[first] == '\n')) {
        ++first;
    }
    const std::string entry = "  \"" + key + "\": " + scalar;
    if (first >= text.size() || text[first] == '}') {
        // Nothing before the closing brace: no trailing comma.
        return text.insert(first, entry + "\n");
    }
    return text.insert(first, entry + ",\n");
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

void applySettingsOverride(const std::filesystem::path &path,
                           const Settings &settings) {
    if (path.empty()) {
        return;
    }
    std::error_code error;
    std::filesystem::create_directories(path.parent_path(), error);

    std::string text;
    {
        std::ifstream file(path);
        if (file) {
            text.assign((std::istreambuf_iterator<char>(file)),
                        std::istreambuf_iterator<char>());
        }
    }
    text = replaceOrInsertKey(std::move(text), "typing_mode",
                              scalarJson(settings.typingMode));
    text = replaceOrInsertKey(std::move(text), "suggest_emoji",
                              scalarJson(settings.suggestEmoji));

    std::ofstream file(path, std::ios::trunc);
    file << text;
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
