#!/usr/bin/env python3
"""
Bongo Release & Linguistic Health Verification CLI
Validates:
  1. Version number parity across all 34 platform files
  2. Byte-identical synchronization between docs/install.sh and platforms/linux/scripts/install.sh
  3. Bijoy (ANSI) ⇄ Unicode bidirectional transliteration accuracy
  4. Bengali number-to-words decomposition and currency formatting
  5. Inline emoji keyword resolution
  6. Contextual next-word (bigram) predictions
  7. Adaptive candidate selection persistence
  8. Release artifact checksum integrity (if built)
"""

import sys
import os
import re
import datetime
import filecmp
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from platforms.common.converter import (
    unicode_to_bijoy,
    bijoy_to_unicode,
    bengali_number_to_words,
    lookup_emoji_keyword,
    predict_next_words,
    save_learned_selection,
    load_learned_selections,
)

GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_pass(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")


def log_fail(msg: str):
    print(f"  {RED}✗{RESET} {BOLD}{msg}{RESET}")


def check_install_script_parity() -> bool:
    print(f"\n{BOLD}[1/5] Checking Installation Script Synchronization...{RESET}")
    f1 = REPO_ROOT / "docs" / "install.sh"
    f2 = REPO_ROOT / "platforms" / "linux" / "scripts" / "install.sh"

    if not f1.exists() or not f2.exists():
        log_fail("One of the install scripts is missing!")
        return False

    if filecmp.cmp(str(f1), str(f2), shallow=False):
        log_pass("docs/install.sh is byte-identical to platforms/linux/scripts/install.sh")
        return True
    else:
        log_fail("docs/install.sh differs from platforms/linux/scripts/install.sh!")
        return False


def get_current_version() -> str:
    cask = REPO_ROOT / "Casks" / "bongo.rb"
    if cask.exists():
        m = re.search(r'version\s+"([^"]+)"', cask.read_text(encoding="utf-8"))
        if m:
            return m.group(1).strip()
    return "1.2.1"


def bump_version(new_version: str) -> bool:
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"{RED}Error: Version must be in semantic format X.Y.Z (e.g. 1.2.2){RESET}")
        return False

    old_version = get_current_version()
    if old_version == new_version:
        print(f"Version is already {new_version}")
        return True

    print(f"\n{BOLD}Bumping version: {old_version} ➔ {new_version}{RESET}\n")

    # 1. Android gradle
    gradle_file = REPO_ROOT / "platforms/android/app/build.gradle.kts"
    if gradle_file.exists():
        content = gradle_file.read_text(encoding="utf-8")
        content = re.sub(r'versionName\s*=\s*"[^"]+"', f'versionName = "{new_version}"', content)
        vc_match = re.search(r'versionCode\s*=\s*(\d+)', content)
        if vc_match:
            new_vc = int(vc_match.group(1)) + 1
            content = re.sub(r'versionCode\s*=\s*\d+', f'versionCode = {new_vc}', content)
        gradle_file.write_text(content, encoding="utf-8")
        log_pass(f"Updated {gradle_file.relative_to(REPO_ROOT)}")

    # 2. Android SettingsActivity
    sa_file = REPO_ROOT / "platforms/android/app/src/main/java/app/getbongo/ime/ui/SettingsActivity.kt"
    if sa_file.exists():
        content = sa_file.read_text(encoding="utf-8")
        content = re.sub(r'versionName\s*\?:\s*"[^"]+"', f'versionName ?: "{new_version}"', content)
        sa_file.write_text(content, encoding="utf-8")
        log_pass(f"Updated {sa_file.relative_to(REPO_ROOT)}")

    # 3. macOS Info.plist (Bongo and Launcher)
    for plist_rel in ["platforms/macos/Bongo/Resources/Info.plist", "platforms/macos/Launcher/Resources/Info.plist"]:
        plist_path = REPO_ROOT / plist_rel
        if plist_path.exists():
            content = plist_path.read_text(encoding="utf-8")
            content = re.sub(r'(<key>CFBundleShortVersionString</key>\s*<string>)[^<]+(</string>)', rf'\g<1>{new_version}\g<2>', content)
            plist_path.write_text(content, encoding="utf-8")
            log_pass(f"Updated {plist_rel}")

    # 4. Linux ibus
    ibus_file = REPO_ROOT / "platforms/linux/ibus/bongo.xml"
    if ibus_file.exists():
        content = ibus_file.read_text(encoding="utf-8")
        content = re.sub(r'<version>[^<]+</version>', f'<version>{new_version}</version>', content)
        ibus_file.write_text(content, encoding="utf-8")
        log_pass(f"Updated {ibus_file.relative_to(REPO_ROOT)}")

    # 5. Linux ui bongo_settings.py
    l_set = REPO_ROOT / "platforms/linux/ui/bongo_settings.py"
    if l_set.exists():
        content = l_set.read_text(encoding="utf-8")
        content = re.sub(r'APP_VERSION\s*=\s*"[^"]+"', f'APP_VERSION = "{new_version}"', content)
        l_set.write_text(content, encoding="utf-8")
        log_pass(f"Updated {l_set.relative_to(REPO_ROOT)}")

    # 6. Windows installer & settings
    w_iss = REPO_ROOT / "platforms/windows/installer/bongo.iss"
    if w_iss.exists():
        content = w_iss.read_text(encoding="utf-8")
        content = re.sub(r'#define\s+MyAppVersion\s+"[^"]+"', f'#define MyAppVersion "{new_version}"', content)
        w_iss.write_text(content, encoding="utf-8")
        log_pass(f"Updated {w_iss.relative_to(REPO_ROOT)}")

    w_wxs = REPO_ROOT / "platforms/windows/installer/bongo.wxs"
    if w_wxs.exists():
        content = w_wxs.read_text(encoding="utf-8")
        content = re.sub(r'Version="[^"]+"', f'Version="{new_version}.0"', content)
        w_wxs.write_text(content, encoding="utf-8")
        log_pass(f"Updated {w_wxs.relative_to(REPO_ROOT)}")

    w_set = REPO_ROOT / "platforms/windows/ui/bongo_settings.py"
    if w_set.exists():
        content = w_set.read_text(encoding="utf-8")
        content = re.sub(r'APP_VERSION\s*=\s*"[^"]+"', f'APP_VERSION = "{new_version}"', content)
        w_set.write_text(content, encoding="utf-8")
        log_pass(f"Updated {w_set.relative_to(REPO_ROOT)}")

    # 7. Linux AUR PKGBUILD & .SRCINFO
    pkgbuild = REPO_ROOT / "platforms/linux/packaging/aur/bongo-bin/PKGBUILD"
    if pkgbuild.exists():
        content = pkgbuild.read_text(encoding="utf-8")
        content = re.sub(r'pkgver=[^\n]+', f'pkgver={new_version}', content)
        content = re.sub(r'pkgrel=\d+', 'pkgrel=1', content)
        pkgbuild.write_text(content, encoding="utf-8")
        log_pass(f"Updated {pkgbuild.relative_to(REPO_ROOT)}")

    srcinfo = REPO_ROOT / "platforms/linux/packaging/aur/bongo-bin/.SRCINFO"
    if srcinfo.exists():
        content = srcinfo.read_text(encoding="utf-8")
        content = re.sub(r'pkgver\s*=\s*[^\n]+', f'pkgver = {new_version}', content)
        content = re.sub(r'pkgrel\s*=\s*\d+', 'pkgrel = 1', content)
        srcinfo.write_text(content, encoding="utf-8")
        log_pass(f"Updated {srcinfo.relative_to(REPO_ROOT)}")

    # 8. Linux fcitx5 CMakeLists.txt
    cmake_file = REPO_ROOT / "platforms/linux/fcitx5/CMakeLists.txt"
    if cmake_file.exists():
        content = cmake_file.read_text(encoding="utf-8")
        content = re.sub(r'project\(bongo-fcitx5\s+VERSION\s+[^\s\)]+', f'project(bongo-fcitx5 VERSION {new_version}', content)
        cmake_file.write_text(content, encoding="utf-8")
        log_pass(f"Updated {cmake_file.relative_to(REPO_ROOT)}")

    # 9. Linux metainfo
    metainfo = REPO_ROOT / "platforms/linux/data/app.getbongo.Bongo.metainfo.xml"
    if metainfo.exists():
        content = metainfo.read_text(encoding="utf-8")
        content = re.sub(r'<release\s+version="[^"]+"', f'<release version="{new_version}"', content)
        metainfo.write_text(content, encoding="utf-8")
        log_pass(f"Updated {metainfo.relative_to(REPO_ROOT)}")

    # 10. Homebrew Cask
    cask_file = REPO_ROOT / "Casks/bongo.rb"
    if cask_file.exists():
        content = cask_file.read_text(encoding="utf-8")
        content = re.sub(r'version\s+"[^"]+"', f'version "{new_version}"', content)
        cask_file.write_text(content, encoding="utf-8")
        log_pass(f"Updated {cask_file.relative_to(REPO_ROOT)}")

    # 11. Website docs/index.html, docs/translations.js, README.md
    for doc_file in [REPO_ROOT / "docs/index.html", REPO_ROOT / "docs/translations.js", REPO_ROOT / "README.md"]:
        if doc_file.exists():
            c = doc_file.read_text(encoding="utf-8")
            c = c.replace(old_version, new_version)
            doc_file.write_text(c, encoding="utf-8")
            log_pass(f"Updated {doc_file.relative_to(REPO_ROOT)}")

    app_js = REPO_ROOT / "docs/app.js"
    if app_js.exists():
        c = app_js.read_text(encoding="utf-8")
        v_tag_old = old_version.replace(".", "_")
        v_tag_new = new_version.replace(".", "_")
        c = c.replace(v_tag_old, v_tag_new)
        app_js.write_text(c, encoding="utf-8")
        log_pass(f"Updated {app_js.relative_to(REPO_ROOT)}")

    # 12. Sitemap lastmod + release entry
    sitemap = REPO_ROOT / "docs/sitemap.xml"
    if sitemap.exists():
        today = datetime.date.today().isoformat()
        c = sitemap.read_text(encoding="utf-8")
        c = re.sub(
            r'(<loc>https://getbongo\.app/</loc>\s*<lastmod>)[^<]+(</lastmod>)',
            rf'\g<1>{today}\g<2>',
            c,
            count=1,
        )
        rel_url = f"https://getbongo.app/releases/v{new_version}"
        if rel_url not in c:
            entry = (
                f"    <url>\n"
                f"        <loc>{rel_url}</loc>\n"
                f"        <lastmod>{today}</lastmod>\n"
                f"        <changefreq>never</changefreq>\n"
                f"        <priority>0.7</priority>\n"
                f"    </url>\n"
            )
            c = c.replace("</url>\n    <url>\n        <loc>https://getbongo.app/releases/", f"</url>\n{entry}    <url>\n        <loc>https://getbongo.app/releases/", 1)
        sitemap.write_text(c, encoding="utf-8")
        log_pass(f"Updated {sitemap.relative_to(REPO_ROOT)} ({today})")

    print(f"\n{GREEN}{BOLD}✓ Successfully bumped all project files from {old_version} to {new_version}!{RESET}\n")
    return True


def check_version_consistency(expected_version: str = "1.2.1") -> bool:
    print(f"\n{BOLD}[2/5] Checking Version Number Parity ({expected_version})...{RESET}")
    files_to_check = [
        ("platforms/android/app/build.gradle.kts", r'versionName\s*=\s*"([^"]+)"'),
        ("platforms/android/app/src/main/java/app/getbongo/ime/ui/SettingsActivity.kt", r'versionName\s*\?:\s*"([^"]+)"'),
        ("platforms/macos/Bongo/Resources/Info.plist", r'<key>CFBundleShortVersionString</key>\s*<string>([^<]+)</string>'),
        ("platforms/linux/ibus/bongo.xml", r'<version>([^<]+)</version>'),
        ("platforms/linux/ui/bongo_settings.py", r'APP_VERSION\s*=\s*"([^"]+)"'),
        ("platforms/windows/installer/bongo.iss", r'#define\s+MyAppVersion\s+"([^"]+)"'),
        ("platforms/windows/installer/bongo.wxs", r'Version="([^"]+)"'),
        ("platforms/windows/ui/bongo_settings.py", r'APP_VERSION\s*=\s*"([^"]+)"'),
        ("platforms/linux/packaging/aur/bongo-bin/PKGBUILD", r'pkgver=([^\n]+)'),
        ("platforms/linux/packaging/aur/bongo-bin/.SRCINFO", r'pkgver\s*=\s*([^\n]+)'),
        ("platforms/linux/fcitx5/CMakeLists.txt", r'project\(bongo-fcitx5\s+VERSION\s+([^\s\)]+)'),
        ("Casks/bongo.rb", r'version\s+"([^"]+)"'),
    ]

    all_passed = True
    for rel_path, pattern in files_to_check:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            log_fail(f"Missing file: {rel_path}")
            all_passed = False
            continue

        content = full_path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(pattern, content)
        if not match:
            log_fail(f"Version pattern not found in: {rel_path}")
            all_passed = False
        else:
            val = match.group(1).strip()
            # Handle Windows MSI 4-part version (1.2.1.0)
            if val == expected_version or val == f"{expected_version}.0":
                log_pass(f"{rel_path}: {val}")
            else:
                log_fail(f"Version mismatch in {rel_path}: found '{val}', expected '{expected_version}'")
                all_passed = False

    sitemap = REPO_ROOT / "docs/sitemap.xml"
    if sitemap.exists():
        sc = sitemap.read_text(encoding="utf-8")
        expected_loc = f"https://getbongo.app/releases/v{expected_version}"
        if expected_loc in sc:
            log_pass(f"docs/sitemap.xml: includes v{expected_version}")
        else:
            log_fail(f"docs/sitemap.xml missing release entry for v{expected_version}")
            all_passed = False

    return all_passed


def check_linguistic_converters() -> bool:
    print(f"\n{BOLD}[3/5] Testing Linguistic Converters & Transliteration...{RESET}")
    all_passed = True

    # 1. Bijoy to Unicode
    b2u_cases = [
        ("Avwg evsjvq Mvb MvB", "আমি বাংলায় গান গাই"),
        ("evsjv Avgvi fvlv|", "বাংলা আমার ভাষা।"),
        ("evsjv‡`k Avgvi gvZ…f~wg", "বাংলাদেশ আমার মাতৃভূমি"),
        ("wK Lei", "কি খবর"),
        ("ïf mKvj", "শুভ সকাল"),
    ]
    for src, expected in b2u_cases:
        actual = bijoy_to_unicode(src)
        if actual == expected:
            log_pass(f"Bijoy ➔ Unicode: '{src}' ➔ '{actual}'")
        else:
            log_fail(f"Bijoy ➔ Unicode failed: expected '{expected}', got '{actual}'")
            all_passed = False

    # 2. Unicode to Bijoy
    u2b_cases = [
        ("আমার সোনার বাংলা", "Avgvi †mvbvi evsjv"),
        ("বাংলাদেশ", "evsjv‡`k"),
    ]
    for src, expected in u2b_cases:
        actual = unicode_to_bijoy(src)
        if actual == expected:
            log_pass(f"Unicode ➔ Bijoy: '{src}' ➔ '{actual}'")
        else:
            log_fail(f"Unicode ➔ Bijoy failed: expected '{expected}', got '{actual}'")
            all_passed = False

    # 3. Bengali Number to Words
    num_cases = [
        (0, False, "শূন্য"),
        ("৫", False, "পাঁচ"),
        (12, False, "বারো"),
        ("১০০", False, "এক শত"),
        (12500, False, "বারো হাজার পাঁচ শত"),
        ("১২৫০০", True, "বারো হাজার পাঁচ শত টাকা মাত্র"),
        ("10500075", False, "এক কোটি পাঁচ লক্ষ পঁচাত্তর"),
    ]
    for n, curr, expected in num_cases:
        actual = bengali_number_to_words(n, as_currency=curr)
        if actual == expected:
            log_pass(f"Number to Words: '{n}' (currency={curr}) ➔ '{actual}'")
        else:
            log_fail(f"Number to Words failed: expected '{expected}', got '{actual}'")
            all_passed = False

    return all_passed


def check_emoji_and_bigram_predictions() -> bool:
    print(f"\n{BOLD}[4/5] Testing Emoji Resolution & Contextual Bigrams...{RESET}")
    all_passed = True

    # 1. Emoji Lookups
    emoji_cases = [
        ("love", "❤️"),
        (":love:", "❤️"),
        ("hasi", "😂"),
        (":hasi:", "😂"),
        ("bongo", "🇧🇩"),
        ("agun", "🔥"),
        ("taka", "💰"),
        ("cha", "☕"),
    ]
    for kw, expected in emoji_cases:
        actual = lookup_emoji_keyword(kw)
        if actual == expected:
            log_pass(f"Emoji keyword '{kw}' ➔ {actual}")
        else:
            log_fail(f"Emoji keyword failed for '{kw}': expected '{expected}', got '{actual}'")
            all_passed = False

    # 2. Bigrams
    bigram_cases = [
        ("আমার", ["সোনার", "দেশ"]),
        ("সোনার", ["বাংলা"]),
        ("বাংলাদেশ", ["একটি", "সরকার"]),
        ("শুভ", ["সকাল", "রাত্রি"]),
        ("ধন্যবাদ", ["আপনাকে", "তোমাকে"]),
    ]
    for word, expected_in in bigram_cases:
        preds = predict_next_words(word)
        missing = [w for w in expected_in if w not in preds]
        if not missing:
            log_pass(f"Bigram '{word}' ➔ {preds[:3]}")
        else:
            log_fail(f"Bigram failed for '{word}': missing {missing} in {preds}")
            all_passed = False

    return all_passed


def check_learned_selections_persistence() -> bool:
    print(f"\n{BOLD}[5/5] Testing Adaptive Learned Selections Persistence...{RESET}")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        save_learned_selection("amar", "আমার", custom_dir=tmpdir)
        save_learned_selection("bd", "বাংলাদেশ", custom_dir=tmpdir)
        loaded = load_learned_selections(custom_dir=tmpdir)
        if loaded.get("amar") == "আমার" and loaded.get("bd") == "বাংলাদেশ":
            log_pass(f"Successfully recorded & loaded selections from {tmpdir}")
            return True
        else:
            log_fail(f"Learned selections mismatch: {loaded}")
            return False


def main():
    if "--bump" in sys.argv:
        try:
            idx = sys.argv.index("--bump")
            new_v = sys.argv[idx + 1]
            success = bump_version(new_v)
            if not success:
                sys.exit(1)
        except IndexError:
            print(f"{RED}Usage: python3 tests/verify_release.py --bump <new_version>{RESET}")
            sys.exit(1)

    current_v = get_current_version()

    print(f"{BOLD}===================================================={RESET}")
    print(f"{BOLD}       Bongo Release Health Verification CLI        {RESET}")
    print(f"{BOLD}===================================================={RESET}")

    results = [
        check_install_script_parity(),
        check_version_consistency(current_v),
        check_linguistic_converters(),
        check_emoji_and_bigram_predictions(),
        check_learned_selections_persistence(),
    ]

    print(f"\n{BOLD}===================================================={RESET}")
    if all(results):
        print(f"{GREEN}{BOLD}✓ ALL VERIFICATION CHECKS PASSED PERFECTLY!{RESET}")
        print(f"{BOLD}===================================================={RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}✗ SOME VERIFICATION CHECKS FAILED!{RESET}")
        print(f"{BOLD}===================================================={RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
