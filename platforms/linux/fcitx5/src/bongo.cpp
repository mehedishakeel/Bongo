// SPDX-License-Identifier: MPL-2.0
#include "bongo.h"

#include <fcitx/event.h>
#include <fcitx/inputcontext.h>
#include <fcitx/inputcontextmanager.h>

namespace bongo {

Bongo::Bongo(fcitx::Instance *instance)
    : instance_(instance),
      factory_([this](fcitx::InputContext &ic) {
          return new BongoState(this, &ic);
      }) {
    instance_->inputContextManager().registerProperty("bongo", &factory_);
}

void Bongo::keyEvent(const fcitx::InputMethodEntry &,
                     fcitx::KeyEvent &keyEvent) {
    state(keyEvent.inputContext())->keyEvent(keyEvent);
}

void Bongo::activate(const fcitx::InputMethodEntry &,
                     fcitx::InputContextEvent &event) {
    state(event.inputContext())->activate();
}

void Bongo::deactivate(const fcitx::InputMethodEntry &,
                       fcitx::InputContextEvent &event) {
    state(event.inputContext())->deactivate();
}

void Bongo::reset(const fcitx::InputMethodEntry &,
                  fcitx::InputContextEvent &event) {
    state(event.inputContext())->reset();
}

class BongoFactory final : public fcitx::AddonFactory {
public:
    fcitx::AddonInstance *create(fcitx::AddonManager *manager) override {
        return new Bongo(manager->instance());
    }
};

} // namespace bongo

FCITX_ADDON_FACTORY_V2(bongo, bongo::BongoFactory);
