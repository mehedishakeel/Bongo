// SPDX-License-Identifier: MPL-2.0
#include "bongo.h"

#include <fcitx/event.h>
#include <fcitx/inputcontext.h>
#include <fcitx/inputcontextmanager.h>
#include <fcitx-utils/log.h>

#include "bongo_api.h"
#include "bongo_settings.h"

namespace bongo {

Bongo::Bongo(fcitx::Instance *instance)
    : instance_(instance),
      factory_([this](fcitx::InputContext &ic) {
        return new BongoState(&ic);
    }) {
    instance_->inputContextManager().registerProperty("bongo", &factory_);
    if (!EngineApi::instance().valid()) {
        FCITX_ERROR() << "Bongo: the native engine library is unavailable; "
                         "keys will pass through";
    }
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
    state(event.inputContext())
        ->deactivate(event.type() ==
                     fcitx::EventType::InputContextFocusOut);
}

void Bongo::reset(const fcitx::InputMethodEntry &,
                  fcitx::InputContextEvent &event) {
    state(event.inputContext())->reset();
}

void Bongo::loadConfigFromSettings() const {
    const auto settings = loadSettings(settingsPath());
    config_.typingMode.setValue(
        static_cast<BongoTypingMode>(settings.typingMode));
    config_.suggestEmoji.setValue(settings.suggestEmoji);
}

const fcitx::Configuration *Bongo::getConfig() const {
    loadConfigFromSettings();
    return &config_;
}

void Bongo::setConfig(const fcitx::RawConfig &config) {
    config_.load(config, true);
    // settings.json is the single source of truth shared with
    // bongo-settings (and the other platforms); fcitx5's own conf file is
    // only a transitive view provided through DBus.
    Settings settings;
    settings.typingMode = static_cast<int>(config_.typingMode.value());
    settings.suggestEmoji = config_.suggestEmoji.value();
    applySettingsOverride(settingsPath(), settings);
}

void Bongo::reloadConfig() {
    loadConfigFromSettings();
}


class BongoFactory final : public fcitx::AddonFactory {
public:
    fcitx::AddonInstance *create(fcitx::AddonManager *manager) override {
        return new Bongo(manager->instance());
    }
};

} // namespace bongo

FCITX_ADDON_FACTORY_V2(bongo, bongo::BongoFactory);
