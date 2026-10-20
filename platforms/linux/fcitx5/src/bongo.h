// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <fcitx/addonfactory.h>
#include <fcitx/addonmanager.h>
#include <fcitx/inputcontextproperty.h>
#include <fcitx/inputmethodengine.h>
#include <fcitx/instance.h>

#include "bongo_state.h"

namespace bongo {

class Bongo final : public fcitx::InputMethodEngine {
public:
    explicit Bongo(fcitx::Instance *instance);

    void keyEvent(const fcitx::InputMethodEntry &entry,
                  fcitx::KeyEvent &keyEvent) override;
    void activate(const fcitx::InputMethodEntry &entry,
                  fcitx::InputContextEvent &event) override;
    void deactivate(const fcitx::InputMethodEntry &entry,
                    fcitx::InputContextEvent &event) override;
    void reset(const fcitx::InputMethodEntry &entry,
               fcitx::InputContextEvent &event) override;

    BongoState *state(fcitx::InputContext *ic) {
        return ic->propertyFor(&factory_);
    }

private:
    fcitx::Instance *instance_;
    fcitx::FactoryFor<BongoState> factory_;
};

} // namespace bongo
