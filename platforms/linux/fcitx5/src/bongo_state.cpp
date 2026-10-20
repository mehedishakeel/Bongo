// SPDX-License-Identifier: MPL-2.0
#include "bongo_state.h"

#include <fcitx-utils/keysym.h>
#include <fcitx-utils/log.h>
#include <fcitx/candidatelist.h>
#include <fcitx/event.h>
#include <fcitx/inputcontext.h>
#include <fcitx/inputpanel.h>
#include <fcitx/text.h>
#include <fcitx/userinterface.h>

#include <algorithm>
#include <memory>
#include <utility>

#include "bongo_keymap.h"

namespace bongo {

class BongoState::Candidate final : public fcitx::CandidateWord {
public:
    Candidate(BongoState *state, int index, std::string text)
        : fcitx::CandidateWord(fcitx::Text(std::move(text))), state_(state),
          index_(index) {}

    void select(fcitx::InputContext *) const override {
        state_->commitCandidate(index_);
    }

private:
    BongoState *state_;
    int index_;
};

BongoState::BongoState(Bongo *addon, fcitx::InputContext *ic)
    : addon_(addon), ic_(ic) {
    if (api_.valid()) {
        engine_ = api_.newEngine();
    }
    settingsWatcher_.reloadIfChanged();
    applySettings();
}

BongoState::~BongoState() {
    if (engine_) {
        api_.freeEngine(engine_);
        engine_ = nullptr;
    }
}

void BongoState::keyEvent(fcitx::KeyEvent &event) {
    if (event.isRelease()) {
        return;
    }

    updateSettingsIfChanged();

    const bool composing = hasSession() || !candidates_.empty();
    const auto decision =
        decideKey(event.key().sym(), event.key().states(), composing);

    switch (decision.action) {
    case KeyAction::Ignore:
        return;
    case KeyAction::CommitAndPass:
        if (composing) {
            commitCurrent();
        }
        return;
    case KeyAction::CommitAndConsume:
        if (composing) {
            commitCurrent();
        }
        event.filterAndAccept();
        return;
    case KeyAction::Backspace:
        backspace();
        event.filterAndAccept();
        return;
    case KeyAction::Reset:
        resetSession();
        event.filterAndAccept();
        return;
    case KeyAction::PreviousCandidate:
        moveCandidate(false);
        event.filterAndAccept();
        return;
    case KeyAction::NextCandidate:
        moveCandidate(true);
        event.filterAndAccept();
        return;
    case KeyAction::PreviousPage:
        movePage(false);
        event.filterAndAccept();
        return;
    case KeyAction::NextPage:
        movePage(true);
        event.filterAndAccept();
        return;
    case KeyAction::SelectCandidate:
        if (decision.index >= 0 &&
            decision.index < static_cast<int>(candidates_.size())) {
            commitCandidate(decision.index);
        }
        event.filterAndAccept();
        return;
    case KeyAction::Text:
        if (feedChar(decision.codepoint, decision.shift)) {
            event.filterAndAccept();
        }
        return;
    }
}

bool BongoState::feedChar(uint32_t codepoint, bool shift) {
    if (!engine_) {
        return false;
    }

    auto suggestion =
        api_.feedChar(engine_, codepoint, shift ? 1 : 0, selectedIndex());
    if (!suggestion) {
        if (hasSession() || !candidates_.empty()) {
            commitCurrent();
        }
        return false;
    }

    updateSuggestions(std::move(suggestion));
    return hasSession() || !candidates_.empty();
}

void BongoState::backspace() {
    if (!engine_) {
        return;
    }

    auto suggestion = api_.backspace(engine_, false);
    if (!suggestion) {
        clearPanel();
        return;
    }
    updateSuggestions(std::move(suggestion));
}

void BongoState::commitCurrent() {
    const int index = selectedIndex();
    if (index >= 0 && index < static_cast<int>(candidates_.size())) {
        commitCandidate(index);
        return;
    }

    if (!preedit_.empty()) {
        ic_->commitString(preedit_);
    }
    if (engine_) {
        api_.reset(engine_);
    }
    clearPanel();
    if (pendingSettings_) {
        applySettings();
    }
}

void BongoState::commitCandidate(int index) {
    if (index < 0 || index >= static_cast<int>(candidates_.size())) {
        commitCurrent();
        return;
    }

    const std::string text = candidates_[index];
    ic_->commitString(text);
    if (engine_) {
        api_.commit(engine_, static_cast<size_t>(index));
    }
    clearPanel();
    if (pendingSettings_) {
        applySettings();
    }
}

void BongoState::resetSession() {
    if (engine_) {
        api_.reset(engine_);
    }
    clearPanel();
    if (pendingSettings_) {
        applySettings();
    }
}

void BongoState::clearPanel() {
    ic_->inputPanel().reset();
    candidateList_ = nullptr;
    candidates_.clear();
    preedit_.clear();
    selected_ = 0;
    ic_->updatePreedit();
    ic_->updateUserInterface(fcitx::UserInterfaceComponent::InputPanel);
}

void BongoState::updateSuggestions(EngineApi::SuggestionPtr suggestion) {
    candidates_.clear();
    const size_t count = api_.suggestionCount(suggestion.get());
    for (size_t index = 0; index < count; ++index) {
        candidates_.push_back(api_.candidate(suggestion.get(), index));
    }

    preedit_ = api_.preview(suggestion.get());
    if (candidates_.empty() && !preedit_.empty()) {
        candidates_.push_back(preedit_);
    }

    if (candidates_.empty()) {
        clearPanel();
        return;
    }

    selected_ = 0;
    preedit_ = candidates_.front();

    auto list = std::make_unique<fcitx::CommonCandidateList>();
    fcitx::KeyList selectionKeys;
    for (int index = 0; index < 9; ++index) {
        selectionKeys.emplace_back(
            static_cast<fcitx::KeySym>(FcitxKey_1 + index));
    }
    list->setSelectionKey(selectionKeys);
    list->setPageSize(9);
    list->setLayoutHint(fcitx::CandidateLayoutHint::Vertical);
    list->setCursorPositionAfterPaging(
        fcitx::CursorPositionAfterPaging::ResetToFirst);
    list->setCursorIncludeUnselected(false);

    for (int index = 0; index < static_cast<int>(candidates_.size());
         ++index) {
        list->append(
            std::make_unique<Candidate>(this, index, candidates_[index]));
    }
    list->setGlobalCursorIndex(0);

    candidateList_ = list.get();
    ic_->inputPanel().setCandidateList(std::move(list));
    updatePreedit();
}

void BongoState::updatePreedit() {
    fcitx::Text text(preedit_, fcitx::TextFormatFlag::Underline);
    text.setCursor(static_cast<int>(preedit_.size()));
    if (ic_->capabilityFlags().test(fcitx::CapabilityFlag::Preedit)) {
        ic_->inputPanel().setClientPreedit(text);
    } else {
        ic_->inputPanel().setPreedit(text);
    }
    ic_->updatePreedit();
    ic_->updateUserInterface(fcitx::UserInterfaceComponent::InputPanel);
}

void BongoState::updateSettingsIfChanged() {
    if (!settingsWatcher_.reloadIfChanged()) {
        return;
    }
    if (hasSession() || !candidates_.empty()) {
        pendingSettings_ = true;
    } else {
        applySettings();
    }
}

void BongoState::applySettings() {
    pendingSettings_ = false;
    if (!engine_) {
        return;
    }
    const auto &settings = settingsWatcher_.settings();
    api_.setMode(engine_, static_cast<uint32_t>(settings.typingMode));
    api_.setEmoji(engine_, settings.suggestEmoji);
}

bool BongoState::hasSession() const {
    return engine_ && api_.hasSession(engine_);
}

int BongoState::selectedIndex() const {
    if (candidateList_) {
        const int index = candidateList_->globalCursorIndex();
        if (index >= 0) {
            return index;
        }
    }
    return selected_;
}

void BongoState::moveCandidate(bool next) {
    if (!candidateList_ || candidates_.empty()) {
        return;
    }
    if (next) {
        candidateList_->nextCandidate();
    } else {
        candidateList_->prevCandidate();
    }
    selected_ = candidateList_->globalCursorIndex();
    if (selected_ < 0) {
        selected_ = 0;
    }
    preedit_ = candidates_[static_cast<size_t>(
        std::min(selected_, static_cast<int>(candidates_.size()) - 1))];
    updatePreedit();
}

void BongoState::movePage(bool next) {
    if (!candidateList_ || candidates_.empty()) {
        return;
    }
    if (next) {
        candidateList_->next();
    } else {
        candidateList_->prev();
    }
    candidateList_->setCursorIndex(0);
    selected_ = candidateList_->globalCursorIndex();
    if (selected_ < 0) {
        selected_ = 0;
    }
    preedit_ = candidates_[static_cast<size_t>(
        std::min(selected_, static_cast<int>(candidates_.size()) - 1))];
    updatePreedit();
}

void BongoState::activate() {
    updateSettingsIfChanged();
    if (!hasSession() && !pendingSettings_) {
        applySettings();
    }
    resetSession();
}

void BongoState::deactivate() {
    if (hasSession() || !candidates_.empty()) {
        commitCurrent();
    } else {
        resetSession();
    }
}

void BongoState::reset() { resetSession(); }

} // namespace bongo
