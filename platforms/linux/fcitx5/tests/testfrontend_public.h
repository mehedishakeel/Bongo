// SPDX-License-Identifier: LGPL-2.1-or-later
// Minimal test-only declarations for fcitx5's testfrontend addon.
#pragma once

#include <fcitx-utils/key.h>
#include <fcitx/addoninstance.h>
#include <fcitx/inputcontext.h>

#include <string>

FCITX_ADDON_DECLARE_FUNCTION(TestFrontend, createInputContext,
                             ICUUID(const std::string &));
FCITX_ADDON_DECLARE_FUNCTION(TestFrontend, destroyInputContext, void(ICUUID));
FCITX_ADDON_DECLARE_FUNCTION(TestFrontend, keyEvent,
                             void(ICUUID, const fcitx::Key &, bool));
FCITX_ADDON_DECLARE_FUNCTION(TestFrontend, sendKeyEvent,
                             bool(ICUUID, const fcitx::Key &, bool));
FCITX_ADDON_DECLARE_FUNCTION(TestFrontend, pushCommitExpectation,
                             void(std::string));
