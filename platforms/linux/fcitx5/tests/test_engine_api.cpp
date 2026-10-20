// SPDX-License-Identifier: MPL-2.0
#include "bongo_api.h"

#include <cstdlib>
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

} // namespace

int main() {
    if (!std::getenv("BONGO_ENGINE_LIB")) {
        std::cout << "BONGO_ENGINE_LIB not set; skipping engine API test\n";
        return 0;
    }

    auto &api = bongo::EngineApi::instance();
    expect(api.valid(), "engine API loads");

    void *engine = api.newEngine();
    expect(engine != nullptr, "engine is created");
    if (!engine) {
        return 1;
    }

    api.setMode(engine, 0);
    auto suggestion = api.feedChar(engine, 'a', 0, 0);
    suggestion = api.feedChar(engine, 'm', 0, 0);
    suggestion = api.feedChar(engine, 'i', 0, 0);
    expect(api.suggestionCount(suggestion.get()) > 1,
           "engine returns candidates");
    expect(!api.candidate(suggestion.get(), 0).empty(),
           "first candidate is present");
    expect(!api.preview(suggestion.get()).empty(), "preview is present");
    expect(api.hasSession(engine), "composition session is active");

    api.commit(engine, 0);
    expect(!api.hasSession(engine), "commit ends the session");
    api.freeEngine(engine);

    if (failures) {
        std::cerr << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "engine API tests passed\n";
    return 0;
}
