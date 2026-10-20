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
        self.assertIn("Configurable=False", metadata)

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

    def test_packages_recommend_fcitx5(self):
        deb = (ROOT / "platforms" / "linux" / "scripts" / "build-deb.sh").read_text()
        self.assertIn("Recommends:", deb)
        self.assertIn("fcitx5", deb)
        rpm = (ROOT / "platforms" / "linux" / "scripts" / "build-rpm.sh").read_text()
        self.assertIn("Recommends:    fcitx5", rpm)
        self.assertIn("%{_libdir}/fcitx5", rpm)
        self.assertIn("%{_datadir}/fcitx5", rpm)

    def test_ci_builds_fcitx5_addon(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("libfcitx5core-dev", ci)
        self.assertIn("platforms/linux/fcitx5", ci)
        self.assertIn("configure-fcitx5.py", ci)


if __name__ == "__main__":
    unittest.main()
