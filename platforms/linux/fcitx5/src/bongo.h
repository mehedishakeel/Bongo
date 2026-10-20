// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <fcitx-config/configuration.h>
#include <fcitx-config/enum.h>
#include <fcitx-config/option.h>
#include <fcitx/addonfactory.h>
#include <fcitx/addonmanager.h>
#include <fcitx/inputcontextproperty.h>
#include <fcitx/inputmethodengine.h>
#include <fcitx/instance.h>
#include <fcitx-utils/i18n.h>

#include <string>

#include "bongo_state.h"

namespace bongo {

enum class BongoTypingMode { PhoneticFirst, Smart, PhoneticOnly };

FCITX_CONFIG_ENUM_NAME_WITH_I18N(BongoTypingMode, N_("Phonetic First"),
                                 N_("Smart"), N_("Phonetic Only"));

FCITX_CONFIGURATION(
    BongoAddonConfig,
    fcitx::Option<BongoTypingMode> typingMode{
        this, "typing_mode", _("Typing mode"), BongoTypingMode::PhoneticFirst};
    fcitx::Option<bool> suggestEmoji{this, "suggest_emoji",
                                     _("Suggest emoji"), true};)

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

    const fcitx::Configuration *getConfig() const override;
    void setConfig(const fcitx::RawConfig &config) override;
    void reloadConfig() override;

    BongoState *state(fcitx::InputContext *ic) {
        return ic->propertyFor(&factory_);
    }

private:
    void loadConfigFromSettings() const;

    fcitx::Instance *instance_;
    fcitx::FactoryFor<BongoState> factory_;
    mutable BongoAddonConfig config_;
};

} // namespace bongo
