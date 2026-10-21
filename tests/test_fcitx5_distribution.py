import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FCITX5 = ROOT / "platforms" / "linux" / "fcitx5"


class Fcitx5DistributionTests(unittest.TestCase):
    def test_addon_metadata(self):
        metadata = (FCITX5 / "data" / "bongo-addon.conf.in").read_text()
        self.assertIn("Library=libbongo", metadata)
        self.assertIn("Type=SharedLibrary", metadata)
        self.assertIn("OnDemand=True", metadata)
        self.assertIn("Category=InputMethod", metadata)
        self.assertIn("Configurable=True", metadata)

    def test_input_method_metadata(self):
        metadata = (FCITX5 / "data" / "bongo.im.conf").read_text()
        self.assertIn("Addon=bongo", metadata)
        self.assertIn("Icon=bongo", metadata)
        self.assertIn("LangCode=bn", metadata)
        self.assertIn("Label=ব", metadata)

    def test_cmake_uses_fcitx5_install_paths(self):
        cmake = (FCITX5 / "CMakeLists.txt").read_text()
        self.assertIn("REQUIRED_FCITX_VERSION 5.1.0", cmake)
        self.assertIn("find_package(Fcitx5Core", cmake)
        self.assertIn("FCITX_INSTALL_ADDONDIR", cmake)
        self.assertIn("FCITX_INSTALL_PKGDATADIR", cmake)

    def test_no_openbangla_frontend_code(self):
        for path in FCITX5.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".cpp", ".h", ".cmake", ".conf", ".in", ".md"}:
                continue
            text = path.read_text(errors="ignore")
            self.assertNotIn("OpenBangla", text, path)
            self.assertNotIn("GPL-3", text, path)

    def test_installer_builds_and_configures_fcitx5(self):
        install = (ROOT / "platforms" / "linux" / "scripts" / "install.sh").read_text()
        self.assertIn("BONGO_FCITX5", install)
        self.assertIn("configure-fcitx5.py", install)
        self.assertIn("FCITX5_SYSTEM_INSTALL", install)
        self.assertIn("bongo-fcitx5-setup", install)

    def test_installer_addon_dir_follows_installed_fcitx5(self):
        """The addon must land where the installed fcitx5 actually looks.

        /usr/lib/fcitx5 is the Arch layout only; Fedora uses lib64 and
        Debian/Ubuntu use a multiarch directory. Hardcoding either
        variant silently installs the addon where fcitx5 never loads
        from. Verify the installer derives it from pkg-config instead.
        """
        install = (ROOT / "platforms" / "linux" / "scripts" / "install.sh").read_text()
        self.assertIn("--variable=libdir Fcitx5Core", install)
        self.assertIn("FCITX_INSTALL_USE_FCITX_SYS_PATHS=OFF", install)
        self.assertIn("-DCMAKE_INSTALL_LIBDIR=", install)

    def test_installer_restarts_systemd_managed_fcitx5(self):
        """Restart fcitx5 through its systemd user unit when one owns it.

        Omarchy runs fcitx5 as omarchy-fcitx5.service (Restart=always).
        Killing the process and spawning `fcitx5 -d` makes that unit start
        a competing instance on every exit, so the manual and systemd
        instances fight over the DBus name and the unit crash-loops.
        The installer must detect the unit that owns the running PID and
        stop/start that unit instead.
        """
        install = (ROOT / "platforms" / "linux" / "scripts" / "install.sh").read_text()
        self.assertIn("FCITX5_SYSTEMD", install)
        self.assertIn("FCITX5_UNIT", install)
        self.assertIn("systemctl --user stop", install)
        self.assertIn("systemctl --user start", install)
        self.assertIn("list-units", install)
        self.assertIn("MainPID", install)

    def test_gnome_input_source_merge_preserves_existing_sources(self):
        """The GNOME merge must keep existing sources and handle empty lists.

        Runs the real shell function from install.sh so the tested code is the
        shipped code. GNOME itself is not needed for this string-level check.
        """
        install = (ROOT / "platforms" / "linux" / "scripts" / "install.sh").read_text()
        match = re.search(r"^bongo_ibus_add_source\(\) \{.*?^\}", install, re.M | re.S)
        self.assertIsNotNone(match, "bongo_ibus_add_source helper is missing")
        helper = match.group(0)
        cases = {
            "[('xkb', 'us')]": "[('xkb', 'us'), ('ibus', 'bongo')]",
            "[('xkb', 'us'), ('xkb', 'bd')]": (
                "[('xkb', 'us'), ('xkb', 'bd'), ('ibus', 'bongo')]"
            ),
            "@as []": "@as [('ibus', 'bongo')]",
            "[]": "[('ibus', 'bongo')]",
        }
        for current, expected in cases.items():
            result = subprocess.run(
                ["bash", "-c", f"{helper}\nbongo_ibus_add_source \"$1\"", "bash", current],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(expected, result.stdout.strip())

    def test_both_install_paths_enable_gnome_sources(self):
        """Local builds and remote deb installs both enable GNOME input sources."""
        install = (ROOT / "platforms" / "linux" / "scripts" / "install.sh").read_text()
        self.assertGreaterEqual(install.count("bongo_enable_gnome_source"), 3)
        self.assertIn("bongo_as_user ibus write-cache", install)
        self.assertIn("IBUS_SOURCE_ENABLED", install)
        # Only enabled units are treated as managing fcitx5 startup.
        self.assertIn("$2 ~ /^enabled/", install)

    def test_installer_detects_desktop_and_enables_two_groups(self):
        """Enablement is split into two groups: GNOME->IBus, rest->fcitx5.

        The installer must detect the running desktop instead of asking the
        user to configure everything by hand: add Bongo to the GNOME input
        sources on GNOME, and make fcitx5 start with the session on KDE and
        tiling Wayland compositors.
        """
        install = (ROOT / "platforms" / "linux" / "scripts" / "install.sh").read_text()
        self.assertIn("DESKTOP_KIND", install)
        self.assertIn("IM_FRAMEWORK", install)
        self.assertIn("gnome-shell", install)
        self.assertIn("Hyprland", install)
        self.assertIn("org.gnome.desktop.input-sources", install)
        self.assertIn("gsettings", install)
        self.assertIn("('ibus', 'bongo')", install)
        self.assertIn("org.fcitx.Fcitx5.desktop", install)
        self.assertIn("Exec=fcitx5 -d", install)

    def test_packages_recommend_fcitx5(self):
        deb = (ROOT / "platforms" / "linux" / "scripts" / "build-deb.sh").read_text()
        self.assertIn("Recommends:", deb)
        self.assertIn("fcitx5", deb)
        rpm = (ROOT / "platforms" / "linux" / "scripts" / "build-rpm.sh").read_text()
        self.assertIn("Recommends:    fcitx5", rpm)
        # %{_libdir} expands to the distribution's lib dir (lib64 on
        # Fedora), matching the installer's pkg-config-derived addon dir.
        self.assertIn("%{_libdir}/fcitx5", rpm)
        self.assertIn("%{_datadir}/fcitx5", rpm)

    def test_ci_builds_fcitx5_addon(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("libfcitx5core-dev", ci)
        self.assertIn("platforms/linux/fcitx5", ci)
        self.assertIn("configure-fcitx5.py", ci)


if __name__ == "__main__":
    unittest.main()
