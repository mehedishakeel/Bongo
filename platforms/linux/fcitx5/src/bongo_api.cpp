// SPDX-License-Identifier: MPL-2.0
#include "bongo_api.h"

#include <dlfcn.h>
#include <fcitx-utils/log.h>

#include <cstdlib>
#include <filesystem>
#include <vector>

namespace bongo {
namespace {

using EngineNew = void *(*)();
using EngineFree = void (*)(void *);
using SetMode = void (*)(void *, uint32_t);
using SetLayout = void (*)(void *, uint32_t);
using GetLayout = uint32_t (*)(void *);
using SetEmoji = void (*)(void *, bool);
using HasSession = bool (*)(void *);
using FeedChar = void *(*)(void *, uint32_t, uint8_t, uint8_t);
using Backspace = void *(*)(void *, bool);
using Commit = void (*)(void *, size_t);
using Reset = void (*)(void *);
using SuggestionCount = size_t (*)(const void *);
using GetCandidate = char *(*)(const void *, size_t);
using GetPreview = char *(*)(const void *);
using SuggestionFree = void (*)(void *);
using StringFree = void (*)(char *);

template <typename T> bool loadSymbol(void *handle, const char *name, T &fn) {
    fn = reinterpret_cast<T>(dlsym(handle, name));
    return fn != nullptr;
}

std::filesystem::path addonDirectory() {
    Dl_info info{};
    if (!dladdr(reinterpret_cast<void *>(&EngineApi::instance), &info) ||
        !info.dli_fname) {
        return {};
    }
    std::error_code error;
    auto path = std::filesystem::absolute(info.dli_fname, error);
    if (error) {
        return {};
    }
    return path.parent_path();
}

std::vector<std::filesystem::path> libraryCandidates() {
    std::vector<std::filesystem::path> candidates;
    if (const char *explicitPath = std::getenv("BONGO_ENGINE_LIB");
        explicitPath && *explicitPath) {
        candidates.emplace_back(explicitPath);
    }

    const auto addonDir = addonDirectory();
    if (!addonDir.empty()) {
        candidates.push_back(addonDir / ".." / "bongo" / "libbongo_engine.so");
        candidates.push_back(addonDir / ".." / ".." / "bongo" /
                             "libbongo_engine.so");
    }

    candidates.emplace_back("/usr/lib/bongo/libbongo_engine.so");
    candidates.emplace_back("/usr/lib64/bongo/libbongo_engine.so");
    candidates.emplace_back(
        "/usr/lib/x86_64-linux-gnu/bongo/libbongo_engine.so");
    candidates.emplace_back(
        "/usr/lib/aarch64-linux-gnu/bongo/libbongo_engine.so");
    candidates.emplace_back("/usr/local/lib/bongo/libbongo_engine.so");

    if (const char *home = std::getenv("HOME"); home && *home) {
        candidates.emplace_back(std::filesystem::path(home) / ".local" /
                                "lib" / "bongo" / "libbongo_engine.so");
    }
    candidates.emplace_back("libbongo_engine.so");
    return candidates;
}

} // namespace

struct EngineApi::Impl {
    void *handle = nullptr;
    EngineNew engineNew = nullptr;
    EngineFree engineFree = nullptr;
    SetMode setMode = nullptr;
    SetLayout setLayout = nullptr;
    GetLayout getLayout = nullptr;
    SetEmoji setEmoji = nullptr;
    HasSession hasSession = nullptr;
    FeedChar feedChar = nullptr;
    Backspace backspace = nullptr;
    Commit commit = nullptr;
    Reset reset = nullptr;
    SuggestionCount suggestionCount = nullptr;
    GetCandidate getCandidate = nullptr;
    GetPreview getPreview = nullptr;
    SuggestionFree suggestionFree = nullptr;
    StringFree stringFree = nullptr;

    bool load() {
        for (const auto &candidate : libraryCandidates()) {
            const std::string path = candidate.string();
            void *loaded = dlopen(path.c_str(), RTLD_NOW | RTLD_LOCAL);
            if (!loaded) {
                const char *error = dlerror();
                FCITX_WARN() << "Bongo: cannot load engine " << path << ": "
                             << (error ? error : "unknown error");
                continue;
            }

            bool complete =
                loadSymbol(loaded, "bongo_engine_new", engineNew) &&
                loadSymbol(loaded, "bongo_engine_free", engineFree) &&
                loadSymbol(loaded, "bongo_engine_set_mode", setMode) &&
                loadSymbol(loaded, "bongo_engine_set_layout", setLayout) &&
                loadSymbol(loaded, "bongo_engine_get_layout", getLayout) &&
                loadSymbol(loaded, "bongo_engine_set_emoji", setEmoji) &&
                loadSymbol(loaded, "bongo_engine_has_session", hasSession) &&
                loadSymbol(loaded, "bongo_engine_feed_char", feedChar) &&
                loadSymbol(loaded, "bongo_engine_backspace", backspace) &&
                loadSymbol(loaded, "bongo_engine_commit", commit) &&
                loadSymbol(loaded, "bongo_engine_reset", reset) &&
                loadSymbol(loaded, "bongo_suggestion_count", suggestionCount) &&
                loadSymbol(loaded, "bongo_suggestion_get_candidate",
                           getCandidate) &&
                loadSymbol(loaded, "bongo_suggestion_get_preview", getPreview) &&
                loadSymbol(loaded, "bongo_suggestion_free", suggestionFree) &&
                loadSymbol(loaded, "bongo_string_free", stringFree);
            if (!complete) {
                FCITX_WARN()
                    << "Bongo: engine " << path
                    << " is missing required symbols";
                dlclose(loaded);
                continue;
            }

            handle = loaded;
            FCITX_INFO() << "Bongo: loaded engine from " << path;
            return true;
        }
        return false;
    }

    void unload() {
        if (handle) {
            dlclose(handle);
            handle = nullptr;
        }
    }
};

EngineApi &EngineApi::instance() {
    static EngineApi api;
    return api;
}

EngineApi::EngineApi() : impl_(std::make_unique<Impl>()) {
    impl_->load();
}

EngineApi::~EngineApi() { impl_->unload(); }

bool EngineApi::valid() const { return impl_ && impl_->handle != nullptr; }

void EngineApi::SuggestionDeleter::operator()(void *pointer) const {
    if (pointer && api) {
        api->freeSuggestion(pointer);
    }
}

void *EngineApi::newEngine() const {
    return valid() ? impl_->engineNew() : nullptr;
}

void EngineApi::freeEngine(void *engine) const {
    if (valid() && engine) {
        impl_->engineFree(engine);
    }
}

void EngineApi::setMode(void *engine, uint32_t mode) const {
    if (valid() && engine) {
        impl_->setMode(engine, mode);
    }
}

void EngineApi::setLayout(void *engine, uint32_t layout) const {
    if (valid() && engine && impl_->setLayout) {
        impl_->setLayout(engine, layout);
    }
}

uint32_t EngineApi::getLayout(void *engine) const {
    if (valid() && engine && impl_->getLayout) {
        return impl_->getLayout(engine);
    }
    return 0;
}

void EngineApi::setEmoji(void *engine, bool enabled) const {
    if (valid() && engine) {
        impl_->setEmoji(engine, enabled);
    }
}

bool EngineApi::hasSession(void *engine) const {
    return valid() && engine && impl_->hasSession(engine);
}

EngineApi::SuggestionPtr
EngineApi::feedChar(void *engine, uint32_t codepoint, uint8_t modifier,
                    uint8_t selection) const {
    if (!valid() || !engine) {
        return {nullptr, SuggestionDeleter{this}};
    }
    return {impl_->feedChar(engine, codepoint, modifier, selection),
            SuggestionDeleter{this}};
}

EngineApi::SuggestionPtr EngineApi::backspace(void *engine,
                                              bool wholeWord) const {
    if (!valid() || !engine) {
        return {nullptr, SuggestionDeleter{this}};
    }
    return {impl_->backspace(engine, wholeWord), SuggestionDeleter{this}};
}

void EngineApi::commit(void *engine, size_t index) const {
    if (valid() && engine) {
        impl_->commit(engine, index);
    }
}

void EngineApi::reset(void *engine) const {
    if (valid() && engine) {
        impl_->reset(engine);
    }
}

size_t EngineApi::suggestionCount(const void *suggestion) const {
    return valid() && suggestion ? impl_->suggestionCount(suggestion) : 0;
}

std::string EngineApi::candidate(const void *suggestion, size_t index) const {
    if (!valid() || !suggestion) {
        return {};
    }
    char *value = impl_->getCandidate(suggestion, index);
    if (!value) {
        return {};
    }
    std::string result(value);
    impl_->stringFree(value);
    return result;
}

std::string EngineApi::preview(const void *suggestion) const {
    if (!valid() || !suggestion) {
        return {};
    }
    char *value = impl_->getPreview(suggestion);
    if (!value) {
        return {};
    }
    std::string result(value);
    impl_->stringFree(value);
    return result;
}

void EngineApi::freeSuggestion(void *suggestion) const {
    if (valid() && suggestion) {
        impl_->suggestionFree(suggestion);
    }
}

} // namespace bongo
