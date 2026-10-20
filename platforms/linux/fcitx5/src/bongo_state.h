// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <fcitx/inputcontextproperty.h>

namespace fcitx {
class InputContext;
class KeyEvent;
} // namespace fcitx

namespace bongo {

class Bongo;

class BongoState final : public fcitx::InputContextProperty {
public:
    BongoState(Bongo *addon, fcitx::InputContext *ic);
    ~BongoState() override;

    void keyEvent(fcitx::KeyEvent &event);
    void activate();
    void deactivate();
    void reset();

private:
    Bongo *addon_;
    fcitx::InputContext *ic_;
};

} // namespace bongo
