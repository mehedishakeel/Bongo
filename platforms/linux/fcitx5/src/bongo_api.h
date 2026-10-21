// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace bongo {

class EngineApi {
public:
    struct SuggestionDeleter {
        const EngineApi *api = nullptr;
        void operator()(void *pointer) const;
    };
    using SuggestionPtr = std::unique_ptr<void, SuggestionDeleter>;

    static EngineApi &instance();

    ~EngineApi();
    EngineApi(const EngineApi &) = delete;
    EngineApi &operator=(const EngineApi &) = delete;

    bool valid() const;

    void *newEngine() const;
    void freeEngine(void *engine) const;
    void setMode(void *engine, uint32_t mode) const;
    void setLayout(void *engine, uint32_t layout) const;
    uint32_t getLayout(void *engine) const;
    void setEmoji(void *engine, bool enabled) const;
    bool hasSession(void *engine) const;

    SuggestionPtr feedChar(void *engine, uint32_t codepoint, uint8_t modifier,
                           uint8_t selection) const;
    SuggestionPtr backspace(void *engine, bool wholeWord) const;

    void commit(void *engine, size_t index) const;
    void reset(void *engine) const;
    size_t suggestionCount(const void *suggestion) const;
    std::string candidate(const void *suggestion, size_t index) const;
    std::string preview(const void *suggestion) const;

    void freeSuggestion(void *suggestion) const;

private:
    EngineApi();

    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace bongo
