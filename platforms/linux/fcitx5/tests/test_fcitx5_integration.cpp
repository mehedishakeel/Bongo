// SPDX-License-Identifier: MPL-2.0
#include "testfrontend_public.h"

#include <fcitx-utils/eventdispatcher.h>
#include <fcitx-utils/key.h>
#include <fcitx-utils/log.h>
#include <fcitx/addonmanager.h>
#include <fcitx/inputcontext.h>
#include <fcitx/inputmethodgroup.h>
#include <fcitx/inputmethodmanager.h>
#include <fcitx/inputpanel.h>
#include <fcitx/instance.h>

#include <cstdlib>
#include <iostream>
#include <string>

using namespace fcitx;

namespace {

std::string preedit(fcitx::InputContext *ic) {
    const auto &panel = ic->inputPanel();
    const auto client = panel.clientPreedit().toString();
    return client.empty() ? panel.preedit().toString() : client;
}

bool expect(bool condition, const std::string &message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        return false;
    }
    return true;
}

} // namespace

int main() {
    char arg0[] = "bongo-fcitx5-integration-test";
    char arg1[] = "--disable=all";
    char arg2[] = "--enable=testfrontend,bongo";
    char *argv[] = {arg0, arg1, arg2};

    fcitx::Instance instance(3, argv);
    instance.addonManager().registerDefaultLoader(nullptr);

    bool ok = true;
    instance.eventDispatcher().schedule([&]() {
        auto *frontend = instance.addonManager().addon("testfrontend");
        auto *bongo = instance.addonManager().addon("bongo", true);
        ok = expect(frontend != nullptr, "testfrontend addon loaded") && ok;
        ok = expect(bongo != nullptr, "bongo addon loaded") && ok;
        if (!frontend || !bongo) {
            instance.exit();
            return;
        }

        auto group = instance.inputMethodManager().currentGroup();
        group.inputMethodList().clear();
        group.inputMethodList().emplace_back("bongo");
        group.setDefaultInputMethod("bongo");
        instance.inputMethodManager().setGroup(std::move(group));

        const auto uuid =
            frontend->call<ITestFrontend::createInputContext>("bongo-test");
        auto *ic = instance.inputContextManager().findByUUID(uuid);
        ok = expect(ic != nullptr, "input context created") && ok;
        if (!ic) {
            instance.exit();
            return;
        }

        auto key = [&](const char *name) {
            frontend->call<ITestFrontend::keyEvent>(uuid, fcitx::Key(name),
                                                     false);
        };

        key("a");
        key("m");
        key("i");
        ok = expect(preedit(ic) == "আমি", "preedit is ami") && ok;

        frontend->call<ITestFrontend::pushCommitExpectation>("আমি");
        key("space");
        ok = expect(preedit(ic).empty(), "space clears preedit") && ok;

        key("a");
        key("m");
        key("i");
        frontend->call<ITestFrontend::pushCommitExpectation>("আমই");
        key("2");
        ok = expect(preedit(ic).empty(), "digit selection clears preedit") && ok;

        key("a");
        key("m");
        key("i");
        key("Escape");
        ok = expect(preedit(ic).empty(), "escape clears preedit") && ok;

        key("a");
        key("m");
        key("i");
        key("BackSpace");
        ok = expect(!preedit(ic).empty() && preedit(ic) != "আমি",
                    "backspace edits preedit") &&
             ok;
        key("Escape");

        key("a");
        key("m");
        key("i");
        frontend->call<ITestFrontend::pushCommitExpectation>("আমি");
        key("Return");
        ok = expect(preedit(ic).empty(), "enter clears preedit") && ok;

        key("a");
        key("m");
        key("i");
        frontend->call<ITestFrontend::pushCommitExpectation>("আমি");
        key("Control+c");
        ok = expect(preedit(ic).empty(), "ctrl commits composition") && ok;

        instance.exit();
    });

    instance.exec();
    if (!ok) {
        return 1;
    }
    std::cout << "fcitx5 integration tests passed\n";
    return 0;
}
