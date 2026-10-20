// SPDX-License-Identifier: MPL-2.0
#include "bongo_keymap.h"

namespace bongo {
namespace {

bool hasShortcutModifier(fcitx::KeyStates states) {
    return states.test(fcitx::KeyState::Ctrl) ||
           states.test(fcitx::KeyState::Alt) ||
           states.test(fcitx::KeyState::Super) ||
           states.test(fcitx::KeyState::Super2) ||
           states.test(fcitx::KeyState::Hyper) ||
           states.test(fcitx::KeyState::Meta);
}

bool isTab(fcitx::KeySym sym) {
    return sym == FcitxKey_Tab || sym == FcitxKey_ISO_Left_Tab;
}

} // namespace

KeyDecision decideKey(fcitx::KeySym sym, fcitx::KeyStates states,
                      bool composing) {
    if (hasShortcutModifier(states)) {
        return {composing ? KeyAction::CommitAndPass : KeyAction::Ignore};
    }

    if (sym == FcitxKey_space) {
        return {composing ? KeyAction::CommitAndPass : KeyAction::Ignore};
    }
    if (sym == FcitxKey_Return || sym == FcitxKey_KP_Enter) {
        return {composing ? KeyAction::CommitAndConsume : KeyAction::Ignore};
    }
    if (sym == FcitxKey_Escape) {
        return {composing ? KeyAction::Reset : KeyAction::Ignore};
    }
    if (sym == FcitxKey_BackSpace) {
        return {composing ? KeyAction::Backspace : KeyAction::Ignore};
    }

    if (composing) {
        if (sym == FcitxKey_Up || sym == FcitxKey_KP_Up ||
            sym == FcitxKey_Page_Up ||
            sym == FcitxKey_ISO_Left_Tab ||
            (sym == FcitxKey_Tab && states.test(fcitx::KeyState::Shift))) {
            return {KeyAction::PreviousCandidate};
        }
        if (sym == FcitxKey_Tab || sym == FcitxKey_Down ||
            sym == FcitxKey_KP_Down || sym == FcitxKey_Page_Down) {
            return {KeyAction::NextCandidate};
        }
        if (!states.test(fcitx::KeyState::Shift) && sym >= FcitxKey_1 &&
            sym <= FcitxKey_9) {
            return {KeyAction::SelectCandidate,
                    static_cast<int>(sym - FcitxKey_1),
                    static_cast<uint32_t>(sym), false};
        }
    } else if (isTab(sym)) {
        return {KeyAction::Ignore};
    }

    const uint32_t codepoint = fcitx::Key::keySymToUnicode(sym);
    if (codepoint == 0) {
        return {KeyAction::Ignore};
    }
    // fcitx5 maps "special" keysyms (Delete, Clear, KP_Tab, ...) through
    // sym & 0x7f, which yields control codes that must not be typed into
    // the composition. Pass them to the application like the IBus engine
    // does since upstream commit 84a2137 and keep printable keysyms.
    if (codepoint < 0x20 || codepoint == 0x7f) {
        return {KeyAction::Ignore};
    }
    return {KeyAction::Text, -1, codepoint, states.test(fcitx::KeyState::Shift)};
}

} // namespace bongo
