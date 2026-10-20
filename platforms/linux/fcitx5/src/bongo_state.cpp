// SPDX-License-Identifier: MPL-2.0
#include "bongo_state.h"

#include <fcitx/inputcontext.h>
#include <fcitx/event.h>

namespace bongo {

BongoState::BongoState(Bongo *addon, fcitx::InputContext *ic)
    : addon_(addon), ic_(ic) {}

BongoState::~BongoState() = default;

void BongoState::keyEvent(fcitx::KeyEvent &) {}

void BongoState::activate() {}

void BongoState::deactivate() {}

void BongoState::reset() {}

} // namespace bongo
