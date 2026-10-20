// SPDX-License-Identifier: MPL-2.0
#include "bongo_keymap.h"

#include <fcitx-utils/key.h>
#include <fcitx-utils/keysym.h>

#include <iostream>
#include <string>

namespace {

int failures = 0;

void expectAction(bongo::KeyDecision decision, bongo::KeyAction action,
                  const std::string &message) {
    if (decision.action != action) {
        std::cerr << "FAIL: " << message << " (got "
                  << static_cast<int>(decision.action) << ")\n";
        ++failures;
    }
}

} // namespace

int main() {
    using namespace fcitx;
    const KeyStates none;
    const KeyStates ctrl = KeyState::Ctrl;
    const KeyStates shift = KeyState::Shift;

    expectAction(bongo::decideKey(FcitxKey_space, none, true),
                 bongo::KeyAction::CommitAndPass, "space composing");
    expectAction(bongo::decideKey(FcitxKey_space, none, false),
                 bongo::KeyAction::Ignore, "space idle");
    expectAction(bongo::decideKey(FcitxKey_Return, none, true),
                 bongo::KeyAction::CommitAndConsume, "enter composing");
    expectAction(bongo::decideKey(FcitxKey_KP_Enter, none, true),
                 bongo::KeyAction::CommitAndConsume, "keypad enter composing");
    expectAction(bongo::decideKey(FcitxKey_Escape, none, true),
                 bongo::KeyAction::Reset, "escape composing");
    expectAction(bongo::decideKey(FcitxKey_BackSpace, none, true),
                 bongo::KeyAction::Backspace, "backspace composing");
    expectAction(bongo::decideKey(FcitxKey_Up, none, true),
                 bongo::KeyAction::PreviousCandidate, "up");
    expectAction(bongo::decideKey(FcitxKey_Tab, none, true),
                 bongo::KeyAction::NextCandidate, "tab");
    expectAction(bongo::decideKey(FcitxKey_ISO_Left_Tab, shift, true),
                 bongo::KeyAction::PreviousCandidate, "shift tab");
    expectAction(bongo::decideKey(FcitxKey_Page_Up, none, true),
                 bongo::KeyAction::PreviousCandidate,
                 "page up selects the previous candidate");
    expectAction(bongo::decideKey(FcitxKey_Page_Down, none, true),
                 bongo::KeyAction::NextCandidate,
                 "page down selects the next candidate");

    const auto select = bongo::decideKey(FcitxKey_1, none, true);
    expectAction(select, bongo::KeyAction::SelectCandidate, "digit selects");
    if (select.index != 0) {
        std::cerr << "FAIL: digit index\n";
        ++failures;
    }
    expectAction(bongo::decideKey(FcitxKey_1, shift, true),
                 bongo::KeyAction::Text, "shifted digit is text");
    expectAction(bongo::decideKey(FcitxKey_1, none, false),
                 bongo::KeyAction::Text, "digit idle is text");

    const auto text = bongo::decideKey(FcitxKey_a, none, false);
    expectAction(text, bongo::KeyAction::Text, "letter is text");
    if (text.codepoint != 'a' || text.shift) {
        std::cerr << "FAIL: letter codepoint\n";
        ++failures;
    }

    const auto upper = bongo::decideKey(FcitxKey_A, shift, false);
    expectAction(upper, bongo::KeyAction::Text, "shifted letter is text");
    if (upper.codepoint != 'A' || !upper.shift) {
        std::cerr << "FAIL: shifted letter codepoint\n";
        ++failures;
    }

    expectAction(bongo::decideKey(FcitxKey_c, ctrl, true),
                 bongo::KeyAction::CommitAndPass, "ctrl while composing");
    expectAction(bongo::decideKey(FcitxKey_c, ctrl, false),
                 bongo::KeyAction::Ignore, "ctrl while idle");

    // Control-producing keysyms must pass through to the application
    // instead of being fed to the engine (see the matching IBus fix on
    // upstream main: BackSpace/Delete/Clear etc. keep working when no
    // composition is active and are never treated as text).
    expectAction(bongo::decideKey(FcitxKey_BackSpace, none, false),
                 bongo::KeyAction::Ignore, "backspace while idle passes through");
    expectAction(bongo::decideKey(FcitxKey_Delete, none, false),
                 bongo::KeyAction::Ignore, "delete while idle passes through");
    expectAction(bongo::decideKey(FcitxKey_Delete, none, true),
                 bongo::KeyAction::Ignore, "delete while composing passes through");
    expectAction(bongo::decideKey(FcitxKey_Clear, none, false),
                 bongo::KeyAction::Ignore, "clear passes through");
    expectAction(bongo::decideKey(FcitxKey_KP_Tab, none, false),
                 bongo::KeyAction::Ignore, "kp_tab passes through");
    expectAction(bongo::decideKey(FcitxKey_KP_Enter, none, false),
                 bongo::KeyAction::Ignore, "kp_enter while idle passes through");

    if (failures) {
        std::cerr << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "keymap tests passed\n";
    return 0;
}
