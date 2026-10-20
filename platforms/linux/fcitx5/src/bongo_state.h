// SPDX-License-Identifier: MPL-2.0
#pragma once

#include <fcitx/candidatelist.h>
#include <fcitx/inputcontextproperty.h>

#include <string>
#include <vector>

#include "bongo_api.h"
#include "bongo_settings.h"

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
    void deactivate(bool focusOut);
    void reset();

private:
    class Candidate;

    bool feedChar(uint32_t codepoint, bool shift);
    void backspace();
    void commitCurrent();
    void commitCandidate(int index);
    void resetSession();
    void clearPanel();
    void updateSuggestions(EngineApi::SuggestionPtr suggestion);
    void updatePreedit();
    void updateSettingsIfChanged();
    void applySettings();
    bool hasSession() const;
    int selectedIndex() const;
    void moveCandidate(bool next);
    void movePage(bool next);

    Bongo *addon_;
    fcitx::InputContext *ic_;
    const EngineApi &api_ = EngineApi::instance();
    void *engine_ = nullptr;
    SettingsWatcher settingsWatcher_;
    bool pendingSettings_ = false;
    std::vector<std::string> candidates_;
    std::string preedit_;
    int selected_ = 0;
    fcitx::CommonCandidateList *candidateList_ = nullptr;
};

} // namespace bongo
