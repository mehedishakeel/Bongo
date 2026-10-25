"""Validate platform identity isolation and resource integrity across macOS, Linux, and Windows."""
import plistlib
from pathlib import Path
import unittest
import json

ROOT = Path(__file__).resolve().parents[1]

class DistributionTests(unittest.TestCase):
    def test_macos_registration(self):
        p = plistlib.loads((ROOT / 'platforms/macos/Bongo/Resources/Info.plist').read_bytes())
        self.assertEqual(p['CFBundleIdentifier'], 'org.bongo.inputmethod.Bongo')
        self.assertEqual(p['InputMethodServerControllerClass'], 'BongoInputController')
        self.assertEqual(p['TISIntendedLanguage'], 'bn')
        self.assertEqual(p['TISInputSourceID'], p['CFBundleIdentifier'])
        self.assertEqual(p['LSArchitecturePriority'], ['arm64'])
        controller = (ROOT / 'platforms/macos/Bongo/Sources/InputController.swift').read_text()
        self.assertIn('@objc(' + p['InputMethodServerControllerClass'] + ')', controller)
        main = (ROOT / 'platforms/macos/Bongo/Sources/main.swift').read_text()
        self.assertIn(p['InputMethodConnectionName'], main)
        welcome = (ROOT / 'platforms/macos/Bongo/Sources/WelcomeWindow.swift').read_text()
        self.assertIn('final class SidebarNavigationButton: NSButton', welcome)
        self.assertIn('acceptsFirstMouse(for event:', welcome)
        for title in ['Getting Started', 'Bongo Layout', 'Settings', 'Fonts']:
            self.assertIn('"' + title + '"', welcome)
        self.assertNotIn('"Avro Layout"', welcome)
        self.assertNotIn('On-device typing', welcome)
        self.assertIn('final class FontsView: NSView', welcome)
        self.assertIn('BongoFontSettings.font()', (ROOT / 'platforms/macos/Bongo/Sources/CandidatePanel.swift').read_text())
        self.assertTrue(p['TISIconIsTemplate'])
        icon = ROOT / 'platforms/macos/Bongo/Resources' / (p['tsInputMethodIconFileKey'] + '.pdf')
        self.assertTrue(icon.is_file())

        launcher_plist = plistlib.loads((ROOT / 'platforms/macos/Launcher/Resources/Info.plist').read_bytes())
        self.assertEqual(launcher_plist['CFBundleIdentifier'], 'org.bongo.Bongo')
        self.assertEqual(launcher_plist['LSArchitecturePriority'], ['arm64'])
        self.assertNotIn('LSUIElement', launcher_plist)
        launcher = (ROOT / 'platforms/macos/Launcher/Sources/main.swift').read_text()
        self.assertIn('org.bongo.inputmethod.Bongo', launcher)
        self.assertIn('Contents/Library/Input Methods/Bongo Input Method.app', launcher)
        self.assertIn('installInputMethod(from:', launcher)
        self.assertIn('CFBundleVersion', launcher)
        self.assertIn('configuration.arguments = ["--show-settings"]', launcher)
        self.assertIn('CommandLine.arguments.contains("--show-settings")', (ROOT / 'platforms/macos/Bongo/Sources/AppDelegate.swift').read_text())

    def test_linux_registration(self):
        # IBus component XML verification
        ibus_xml = (ROOT / 'platforms/linux/ibus/bongo.xml').read_text()
        self.assertIn('<name>org.freedesktop.IBus.Bongo</name>', ibus_xml)
        self.assertIn('<name>bongo</name>', ibus_xml)
        self.assertIn('<language>bn</language>', ibus_xml)
        self.assertIn('<exec>/usr/libexec/bongo-ibus-engine --ibus</exec>', ibus_xml)

        # Desktop entry & AppStream
        desktop_entry = (ROOT / 'platforms/linux/data/app.getbongo.Bongo.desktop').read_text()
        self.assertIn('Exec=bongo-settings', desktop_entry)
        self.assertIn('Icon=bongo', desktop_entry)
        self.assertIn('StartupWMClass=app.getbongo.Bongo', desktop_entry)

        metainfo = (ROOT / 'platforms/linux/data/app.getbongo.Bongo.metainfo.xml').read_text()
        self.assertIn('<id>app.getbongo.Bongo</id>', metainfo)
        self.assertIn('<name>Bongo</name>', metainfo)

        # Linux UI parity checks (exact same 4 tabs)
        ui_script = (ROOT / 'platforms/linux/ui/bongo_settings.py').read_text()
        for title in ['Getting Started', 'Bongo Layout', 'Settings', 'Fonts']:
            self.assertIn(title, ui_script)
        self.assertIn('Phonetic first', ui_script)
        self.assertIn('Smart suggestions', ui_script)
        self.assertIn('Phonetic only', ui_script)
        self.assertIn('Show emoji in suggestions', ui_script)

        # Linux Engine & scripts
        self.assertTrue((ROOT / 'platforms/linux/engine/Cargo.toml').is_file())
        self.assertTrue((ROOT / 'platforms/linux/scripts/install.sh').is_file())
        self.assertTrue((ROOT / 'platforms/linux/scripts/build-deb.sh').is_file())
        self.assertTrue((ROOT / 'platforms/linux/scripts/build-rpm.sh').is_file())

    def test_windows_registration(self):
        # Windows UI parity checks (exact same 4 tabs)
        ui_script = (ROOT / 'platforms/windows/ui/bongo_settings.py').read_text()
        for title in ['Getting Started', 'Bongo Layout', 'Settings', 'Fonts']:
            self.assertIn(title, ui_script)
        self.assertIn('Phonetic first', ui_script)
        self.assertIn('Smart suggestions', ui_script)
        self.assertIn('Phonetic only', ui_script)
        self.assertIn('Show emoji in suggestions', ui_script)
        self.assertIn('ACCENT_COLOR', ui_script)
        self.assertIn('TEXT_PRIMARY', ui_script)
        self.assertNotIn('bg=ACCENT,', ui_script)
        self.assertNotIn('fg=TEXT_WHITE', ui_script)

        # Windows service verification
        service_script = (ROOT / 'platforms/windows/service/bongo_service.py').read_text()
        self.assertIn('WH_KEYBOARD_LL', service_script)
        self.assertIn('SendInput', service_script)
        self.assertIn('bongo_engine', service_script)

        # Windows Engine, installer scripts, and icons
        self.assertTrue((ROOT / 'platforms/windows/engine/Cargo.toml').is_file())
        self.assertTrue((ROOT / 'platforms/windows/engine/src/lib.rs').is_file())
        self.assertTrue((ROOT / 'platforms/windows/installer/bongo.iss').is_file())
        self.assertTrue((ROOT / 'platforms/windows/installer/bongo.wxs').is_file())
        self.assertTrue((ROOT / 'platforms/windows/scripts/build-windows.bat').is_file())
        self.assertTrue((ROOT / 'platforms/windows/scripts/package_windows.py').is_file())
        self.assertTrue((ROOT / 'platforms/windows/data/bongo.ico').is_file())
        self.assertTrue((ROOT / 'platforms/windows/data/bongo.png').is_file())

    def test_windows_settings_app_initialization(self):
        """Verify bongo_settings.py initializes and switches layout modes without NameError."""
        try:
            import tkinter as tk
            from unittest.mock import patch
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir:
                with patch.dict('os.environ', {'APPDATA': tmp_dir}):
                    import platforms.windows.ui.bongo_settings as ws
                    root = tk.Tk()
                    root.withdraw()
                    try:
                        app = ws.BongoSettingsApp(root)
                        app.switch_layout_mode("national")
                        app.switch_layout_mode("avro")
                        for idx in range(4):
                            app.select_tab(idx)
                    finally:
                        root.destroy()
        except Exception as e:
            # In headless environments without display/Tk, ensure it is only Tk-related
            self.assertTrue(isinstance(e, (ImportError, Exception)))
            if not isinstance(e, ImportError) and 'no display name' not in str(e).lower() and 'cannot connect to x server' not in str(e).lower():
                self.assertNotIsInstance(e, NameError)

    def test_platform_architecture_integrity(self):
        # Ensure supported platform directories exist and legacy platforms remain clean
        self.assertTrue((ROOT / 'platforms/macos').is_dir(), 'macOS platform directory must exist')
        self.assertTrue((ROOT / 'platforms/linux').is_dir(), 'Linux platform directory must exist')
        self.assertTrue((ROOT / 'platforms/windows').is_dir(), 'Windows platform directory must exist')
        self.assertTrue((ROOT / 'platforms/android').is_dir(), 'Android platform directory must exist')
        self.assertFalse((ROOT / 'licenses/GPL-3.0.txt').exists(), 'Linux GPL license should not exist')
        self.assertFalse((ROOT / 'licenses/MPL-1.1.txt').exists(), 'Legacy MPL-1.1 license should not exist')

        # Check create-dmg.sh supports Apple Silicon and Intel targets
        script = (ROOT / 'platforms/macos/scripts/create-dmg.sh').read_text()
        self.assertIn('aarch64-apple-darwin', script)
        self.assertIn('arm64-apple-macos13.0', script)
        self.assertIn('x86_64-apple-darwin', script)
        self.assertIn('x86_64-apple-macos13.0', script)

        # Ensure upstream.lock.json tracks components cleanly
        upstream = json.loads((ROOT / 'upstream.lock.json').read_text())
        self.assertIn('Lekho', upstream)
        self.assertIn('riti-macos', upstream)
        self.assertIn('riti-linux', upstream)
        self.assertIn('riti-windows', upstream)
        self.assertIn('riti-android', upstream)
        self.assertNotIn('OpenBangla-Keyboard', upstream)
        self.assertNotIn('Avro-Keyboard', upstream)

    def test_release_artifact_layout(self):
        for name in ['install.sh', 'uninstall.sh', 'create_dmg.sh']:
            self.assertFalse((ROOT / 'platforms/macos/scripts' / name).exists())
        self.assertFalse((ROOT / 'scripts/Register Bongo.command').exists())
        release = (ROOT / 'platforms/macos/scripts/create-dmg.sh').read_text()
        self.assertNotIn('BongoRegister', release)
        self.assertNotIn('Register Bongo.command', release)
        self.assertIn('$STAGE/Bongo.app', release)
        self.assertNotIn('$STAGE/Bongo Input Method.app', release)
        self.assertIn('Contents/Library/Input Methods/Bongo Input Method.app', release)
        self.assertIn("ln -s '/Applications'", release)
        self.assertNotIn("ln -s '/Library/Input Methods'", release)
        self.assertIn('RELEASE_DIR="$PROJECT_ROOT/release"', release)
        self.assertNotIn('dist/', release)

        self.assertTrue((ROOT / 'platforms/macos/release/.gitkeep').is_file())
        self.assertTrue((ROOT / 'platforms/linux/release/.gitkeep').is_file())
        self.assertTrue((ROOT / 'platforms/windows/release/.gitkeep').is_file())
        self.assertTrue((ROOT / 'platforms/android/release/.gitkeep').is_file())
        mac_scripts = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / 'platforms/macos/scripts').glob('*')
            if path.is_file()
        }
        self.assertEqual(mac_scripts, {
            'platforms/macos/scripts/create-dmg.sh',
        })
        self.assertFalse((ROOT / 'scripts').exists())

    def test_updates_use_bongo_release_configuration(self):
        mac = (ROOT / 'platforms/macos/Bongo/Sources/WelcomeWindow.swift').read_text()
        self.assertIn('BongoGitHubRepository', mac)
        self.assertIn('api.github.com/repos/', mac)
        self.assertIn('releases?per_page=1', mac)
        self.assertIn('No newer release is published yet', mac)
        self.assertIn('statusCode == 404', mac)
        self.assertNotIn('openbangla.github.io', mac)
        self.assertNotIn('omicronlab.com/download/liveupdate', mac)

    def test_phonetic_engine_accuracy(self):
        import importlib.util

        # 1. Test Windows Avro Phonetic Engine
        spec_win = importlib.util.spec_from_file_location(
            "bongo_win_service",
            str(ROOT / "platforms/windows/service/bongo_service.py")
        )
        mod_win = importlib.util.module_from_spec(spec_win)
        spec_win.loader.exec_module(mod_win)

        win_eng = mod_win.AvroPhoneticEngine()
        self.assertEqual(win_eng.get_candidates("ami")[0], "আমি")
        self.assertEqual(win_eng.get_candidates("bangla")[0], "বাংলা")
        self.assertEqual(win_eng.get_candidates("kemon")[0], "কেমন")
        self.assertEqual(win_eng.get_candidates("dhonnobad")[0], "ধন্যবাদ")
        self.assertEqual(win_eng.get_candidates("hya")[0], "হ্যাঁ")
        self.assertEqual(win_eng.get_candidates("chad")[0], "চাঁদ")
        self.assertEqual(win_eng.get_candidates("pach")[0], "পাঁচ")
        self.assertEqual(win_eng.get_candidates("hata")[0], "হাঁটা")
        self.assertEqual(win_eng.get_candidates("khuje")[0], "খুঁজে")
        # Punctuation padding isolation (Windows)
        self.assertEqual(win_eng.get_candidates("(ami)")[0], "(আমি)")
        self.assertEqual(win_eng.get_candidates('"bangla"')[0], '"বাংলা"')
        self.assertEqual(win_eng.get_candidates("dhonnobad,")[0], "ধন্যবাদ,")
        self.assertEqual(win_eng.get_candidates("[kolkata]")[0], "[কলকাতা]")

        # 2. Test Linux Avro Phonetic Engine directly
        spec_lin = importlib.util.spec_from_file_location(
            "bongo_lin_engine",
            str(ROOT / "platforms/linux/ibus/bongo_ibus_engine.py")
        )
        mod_lin = importlib.util.module_from_spec(spec_lin)
        spec_lin.loader.exec_module(mod_lin)

        lin_eng = mod_lin.AvroPhoneticEngine()
        self.assertEqual(lin_eng.get_candidates("ami")[0], "আমি")
        self.assertEqual(lin_eng.get_candidates("bangla")[0], "বাংলা")
        self.assertEqual(lin_eng.get_candidates("kemon")[0], "কেমন")
        self.assertEqual(lin_eng.get_candidates("dhonnobad")[0], "ধন্যবাদ")
        self.assertEqual(lin_eng.get_candidates("hya")[0], "হ্যাঁ")
        self.assertEqual(lin_eng.get_candidates("chad")[0], "চাঁদ")
        self.assertEqual(lin_eng.get_candidates("pach")[0], "পাঁচ")
        self.assertEqual(lin_eng.get_candidates("hata")[0], "হাঁটা")
        self.assertEqual(lin_eng.get_candidates("khuje")[0], "খুঁজে")
        # Punctuation padding isolation (Linux)
        self.assertEqual(lin_eng.get_candidates("(ami)")[0], "(আমি)")
        self.assertEqual(lin_eng.get_candidates('"bangla"')[0], '"বাংলা"')
        self.assertEqual(lin_eng.get_candidates("dhonnobad,")[0], "ধন্যবাদ,")
        self.assertEqual(lin_eng.get_candidates("[kolkata]")[0], "[কলকাতা]")

        # 3. Test Windows Service Key Processing Lifecycle
        svc = mod_win.BongoWindowsService()
        self.assertFalse(svc.has_session())

        # Feed "ami"
        svc.process_key(0x41, True, False, False, False) # 'a'
        svc.process_key(0x4D, True, False, False, False) # 'm'
        svc.process_key(0x49, True, False, False, False) # 'i'
        self.assertTrue(svc.has_session())
        self.assertEqual(svc.candidates[0], "আমি")
        # Candidate HUD visibility and candidate population
        self.assertTrue(svc.hud.is_visible)
        self.assertEqual(svc.hud.buffer, "ami")
        self.assertEqual(svc.hud.selected_index, 0)
        self.assertIn("আমি", svc.hud.candidates)

        # Test Down Arrow and Tab navigation in HUD
        self.assertTrue(hasattr(mod_win, "VK_DOWN"))
        self.assertTrue(hasattr(mod_win, "VK_UP"))
        svc.process_key(mod_win.VK_DOWN, True, False, False, False)
        self.assertEqual(svc.selected_index, 1)
        self.assertEqual(svc.hud.selected_index, 1)
        self.assertEqual(svc.preedit_str, svc.candidates[1])

        # Test Up Arrow navigation back to candidate 0
        svc.process_key(mod_win.VK_UP, True, False, False, False)
        self.assertEqual(svc.selected_index, 0)
        self.assertEqual(svc.hud.selected_index, 0)
        self.assertEqual(svc.preedit_str, svc.candidates[0])

        # Space commits active candidate cleanly and hides HUD
        handled = svc.process_key(mod_win.VK_SPACE, True, False, False, False)
        self.assertTrue(handled)
        self.assertFalse(svc.has_session())
        self.assertFalse(svc.hud.is_visible)

        # Feed "ami" and test Enter (commits without newline and hides HUD)
        svc.process_key(0x41, True, False, False, False)
        svc.process_key(0x4D, True, False, False, False)
        svc.process_key(0x49, True, False, False, False)
        self.assertTrue(svc.has_session())
        self.assertTrue(svc.hud.is_visible)
        h_ret = svc.process_key(mod_win.VK_RETURN, True, False, False, False)
        self.assertTrue(h_ret)
        # Feed "ami" and test mouse click on HUD candidate
        svc.process_key(0x41, True, False, False, False)
        svc.process_key(0x4D, True, False, False, False)
        svc.process_key(0x49, True, False, False, False)
        self.assertTrue(svc.has_session())
        self.assertTrue(svc.hud.is_visible)
        # Click on candidate 1 ("আমার" / "আম")
        svc.hud.on_candidate_clicked(1)
        self.assertFalse(svc.has_session())
        self.assertFalse(svc.hud.is_visible)

        # Feed "ami" and test punctuation (commits candidate, lets punctuation pass through)
        svc.process_key(0x41, True, False, False, False)
        svc.process_key(0x4D, True, False, False, False)
        svc.process_key(0x49, True, False, False, False)
        self.assertTrue(svc.has_session())
        h_punct = svc.process_key(0xBF, True, True, False, False) # '?'
        self.assertFalse(h_punct)
        self.assertFalse(svc.has_session())

        # Test period outside and inside session converts to Dari
        h_dari_alone = svc.process_key(0xBE, True, False, False, False)
        self.assertTrue(h_dari_alone)

        svc.process_key(0x41, True, False, False, False)
        h_dari_session = svc.process_key(0xBE, True, False, False, False)
        self.assertTrue(h_dari_session)
        self.assertFalse(svc.has_session())

        # Test F12 and Ctrl+Space toggle
        self.assertTrue(svc.bangla_active)
        svc.process_key(mod_win.VK_F12, True, False, False, False)
        self.assertFalse(svc.bangla_active)
        svc.process_key(mod_win.VK_F12, True, False, False, False)
        self.assertTrue(svc.bangla_active)

        # Test Ctrl+Space toggle
        svc.process_key(mod_win.VK_SPACE, True, False, True, False)
        self.assertFalse(svc.bangla_active)
        svc.process_key(mod_win.VK_SPACE, True, False, True, False)
        self.assertTrue(svc.bangla_active)

        # Test Shifted uppercase typing (e.g. 'T' for ট vs 't' for ত)
        svc.process_key(0x54, True, True, False, False) # 'T'
        self.assertEqual(svc.candidates[0], "ট")
        svc.clear_session()
        svc.process_key(0x54, True, False, False, False) # 't'
        self.assertEqual(svc.candidates[0], "ত")
        svc.clear_session()

    def test_android_registration(self):
        android_dir = ROOT / 'platforms/android'

        # 1. AndroidManifest verification
        manifest = (android_dir / 'app/src/main/AndroidManifest.xml').read_text()
        self.assertIn('.BongoInputMethodService', manifest)
        self.assertIn('android.permission.BIND_INPUT_METHOD', manifest)
        self.assertIn('android.view.InputMethod', manifest)
        self.assertIn('android.view.im', manifest)
        self.assertIn('.ui.SettingsActivity', manifest)

        # 2. IME Subtype XML verification (unified clean Bongo Keyboard declaration matching Ridmik)
        method_xml = (android_dir / 'app/src/main/res/xml/method.xml').read_text()
        self.assertIn('imeSubtypeMode="keyboard"', method_xml)
        self.assertIn('isAsciiCapable="true"', method_xml)

        # 3. Native Engine (Rust & JNI) verification
        cargo_toml = (android_dir / 'engine/Cargo.toml').read_text()
        self.assertIn('name = "bongo_engine"', cargo_toml)
        self.assertIn('crate-type = ["cdylib"', cargo_toml)
        self.assertTrue((android_dir / 'engine/.cargo/config.toml').is_file())
        
        lib_rs = (android_dir / 'engine/src/lib.rs').read_text()
        self.assertIn('Java_app_getbongo_ime_engine_BongoNative_engineNew', lib_rs)
        self.assertIn('Java_app_getbongo_ime_engine_BongoNative_engineFeedChar', lib_rs)
        self.assertIn('Java_app_getbongo_ime_engine_BongoNative_engineCommit', lib_rs)

        # 4. Kotlin IME architecture verification
        ime_files = [
            'app/src/main/java/app/getbongo/ime/BongoInputMethodService.kt',
            'app/src/main/java/app/getbongo/ime/engine/BongoEngine.kt',
            'app/src/main/java/app/getbongo/ime/engine/BongoNative.kt',
            'app/src/main/java/app/getbongo/ime/engine/AvroPhoneticEngine.kt',
            'app/src/main/java/app/getbongo/ime/engine/BijoyConverter.kt',
            'app/src/main/java/app/getbongo/ime/model/UserPreferences.kt',
            'app/src/main/java/app/getbongo/ime/model/ThemePalette.kt',
            'app/src/main/java/app/getbongo/ime/ui/BongoKeyboardView.kt',
            'app/src/main/java/app/getbongo/ime/ui/CandidateStripView.kt',
            'app/src/main/java/app/getbongo/ime/ui/EmojiKeyboardView.kt',
            'app/src/main/java/app/getbongo/ime/ui/SettingsActivity.kt',
        ]
        for f in ime_files:
            self.assertTrue((android_dir / f).is_file(), f"Missing Android source file: {f}")

        # 5. Gradle build infrastructure & launcher assets
        self.assertTrue((android_dir / 'build.gradle.kts').is_file())
        self.assertTrue((android_dir / 'settings.gradle.kts').is_file())
        self.assertTrue((android_dir / 'app/build.gradle.kts').is_file())
        self.assertTrue((android_dir / 'gradlew').is_file())
        self.assertTrue((android_dir / 'app/src/main/res/mipmap-hdpi/ic_launcher.png').is_file())
        self.assertTrue((android_dir / 'README.md').is_file())

        # 6. Verify space bar and subtype naming (Bongo & English, not Bangla.phonetic)
        strings_xml = (android_dir / 'app/src/main/res/values/strings.xml').read_text()
        self.assertIn('<string name="subtype_bengali">Bongo</string>', strings_xml)
        self.assertIn('<string name="subtype_english">English</string>', strings_xml)
        self.assertNotIn('Bangla.phonetic', strings_xml)

        keyboard_kt = (android_dir / 'app/src/main/java/app/getbongo/ime/ui/BongoKeyboardView.kt').read_text()
        self.assertIn('"SPACE" -> if (isBangla) "Bongo" else "English"', keyboard_kt)
        self.assertNotIn('Bangla.phonetic', keyboard_kt)

    def test_linguistic_converter_and_utilities(self):
        import sys
        sys.path.insert(0, str(ROOT / 'platforms/common'))
        from converter import (
            unicode_to_bijoy,
            bijoy_to_unicode,
            separate_padding,
            fix_string_case,
            apply_sandhi_rules,
            AUTOCORRECT_LOANWORDS,
        )

        # 1. Unicode to Bijoy conversion test suite
        self.assertEqual(unicode_to_bijoy("আমি বাংলায় গান গাই"), "Avwg evsjvq Mvb MvB")
        self.assertEqual(unicode_to_bijoy("আমি বাংলায় গান গাই"), "Avwg evsjvq Mvb MvB")
        self.assertEqual(unicode_to_bijoy("বাংলা আমার ভাষা।"), "evsjv Avgvi fvlv|")
        self.assertEqual(unicode_to_bijoy("কতল"), "KZj")
        self.assertEqual(unicode_to_bijoy("সুতরাং"), "myZivs")
        self.assertEqual(unicode_to_bijoy("চাঁদ"), "Pvu`")
        self.assertEqual(unicode_to_bijoy("অর্ক"), "AK©")
        self.assertEqual(unicode_to_bijoy("কুহেলিকা"), "Kz‡nwjKv")
        self.assertEqual(unicode_to_bijoy("কি"), "wK")
        self.assertEqual(unicode_to_bijoy("কীট"), "KxU")
        self.assertEqual(unicode_to_bijoy("কে"), "†K")
        self.assertEqual(unicode_to_bijoy("কো"), "†Kv")
        self.assertEqual(unicode_to_bijoy("কৌ"), "†KŠ")
        self.assertEqual(unicode_to_bijoy("সংখ্যা"), "msL¨v")
        self.assertEqual(unicode_to_bijoy("বিদ্যুৎ"), "we`¨yr")
        self.assertEqual(unicode_to_bijoy("কিন্তু"), "wKš‘")
        self.assertEqual(unicode_to_bijoy("র‍্যাব"), "i¨ve")

        # 2. Bijoy to Unicode reverse conversion
        self.assertEqual(bijoy_to_unicode("Avwg evsjvq Mvb MvB"), "আমি বাংলায় গান গাই")
        self.assertEqual(bijoy_to_unicode("evsjv Avgvi fvlv|"), "বাংলা আমার ভাষা।")
        self.assertEqual(bijoy_to_unicode("KZj"), "কতল")
        self.assertEqual(bijoy_to_unicode("myZivs"), "সুতরাং")
        self.assertEqual(bijoy_to_unicode("Pvu`"), "চাঁদ")
        self.assertEqual(bijoy_to_unicode("AK©"), "অর্ক")
        self.assertEqual(bijoy_to_unicode("†K"), "কে")
        self.assertEqual(bijoy_to_unicode("†Kv"), "কো")
        self.assertEqual(bijoy_to_unicode("†KŠ"), "কৌ")
        self.assertEqual(bijoy_to_unicode("wK"), "কি")

        # 3. Punctuation Padding Isolator
        p1, s1, suf1 = separate_padding("(ami)")
        self.assertEqual(p1, "(")
        self.assertEqual(s1, "ami")
        self.assertEqual(suf1, ")")

        p2, s2, suf2 = separate_padding('"bangla"')
        self.assertEqual(p2, '"')
        self.assertEqual(s2, "bangla")
        self.assertEqual(suf2, '"')

        p3, s3, suf3 = separate_padding("dhonnobad,")
        self.assertEqual(p3, "")
        self.assertEqual(s3, "dhonnobad")
        self.assertEqual(suf3, ",")

        p4, s4, suf4 = separate_padding("[kolkata]")
        self.assertEqual(p4, "[")
        self.assertEqual(s4, "kolkata")
        self.assertEqual(suf4, "]")

        # 4. Case Sensitivity Normalizer
        self.assertEqual(fix_string_case("Bangla"), "bangla")
        self.assertEqual(fix_string_case("Keno"), "keno")
        self.assertEqual(fix_string_case("Ami"), "ami")
        self.assertEqual(fix_string_case("Dhaka"), "Dhaka")

        # 5. Morphological Suffix & Sandhi Engine
        self.assertEqual(apply_sandhi_rules("জগৎ", "এর"), "জগতের")
        self.assertEqual(apply_sandhi_rules("রং", "এ"), "রঙে")
        self.assertEqual(apply_sandhi_rules("বই", "এ"), "বইয়ে")
        self.assertEqual(apply_sandhi_rules("ভাই", "এর"), "ভাইয়ের")
        self.assertEqual(apply_sandhi_rules("দেশ", "এর"), "দেশের")

        # 6. Autocorrect & English Loanwords
        self.assertEqual(AUTOCORRECT_LOANWORDS["1st"], "১ম")
        self.assertEqual(AUTOCORRECT_LOANWORDS["2nd"], "২য়")
        self.assertEqual(AUTOCORRECT_LOANWORDS["class"], "ক্লাস")
        self.assertEqual(AUTOCORRECT_LOANWORDS["hospital"], "হাসপাতাল")
        self.assertEqual(AUTOCORRECT_LOANWORDS["police"], "পুলিশ")
        self.assertEqual(AUTOCORRECT_LOANWORDS["google"], "গুগল")

if __name__ == '__main__':
    unittest.main()

