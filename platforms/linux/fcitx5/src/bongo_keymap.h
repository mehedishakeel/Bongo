// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <fcitx-utils/key.h>
#include <fcitx-utils/keysym.h>

#include <cstdint>

namespace bongo {

enum class KeyAction {
    Ignore,
    CommitAndPass,
    CommitAndConsume,
    Backspace,
    Reset,
    PreviousCandidate,
    NextCandidate,
    SelectCandidate,
    Text,
};

struct KeyDecision {
    KeyAction action = KeyAction::Ignore;
    int index = -1;
    uint32_t codepoint = 0;
    bool shift = false;
};

KeyDecision decideKey(fcitx::KeySym sym, fcitx::KeyStates states,
                      bool composing);

} // namespace bongo
