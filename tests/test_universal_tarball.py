import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "platforms" / "linux"
SCRIPTS = LINUX / "scripts"
INSTALLER = SCRIPTS / "install.sh"
TARBALL_SCRIPT = SCRIPTS / "build-tarball.sh"


class PrebuiltInstallerTests(unittest.TestCase):
    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "the prebuilt installer targets Linux",
    )
    def test_prebuilt_installer_copies_payload_without_building(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            bundle = temp / "bundle"
            bundle.mkdir()
            shutil.copy2(INSTALLER, bundle / "install.sh")

            payload = bundle / "payload"
            (payload / "bin").mkdir(parents=True)
            (payload / "lib" / "bongo").mkdir(parents=True)
            (payload / "share" / "applications").mkdir(parents=True)
            (payload / "bin" / "bongo-settings").write_text("#!/bin/sh\n")
            (payload / "lib" / "bongo" / "libbongo_engine.so").write_text("engine")
            (payload / "share" / "applications" / "bongo.desktop").write_text(
                "[Desktop Entry]\n"
            )

            addon = bundle / "fcitx5"
            addon.mkdir()
            (addon / "libbongo.so").write_text("addon")

            stub_bin = temp / "stub-bin"
            stub_bin.mkdir()
            for tool in ("cargo", "cmake"):
                stub = stub_bin / tool
                stub.write_text(
                    f'#!/bin/sh\necho "{tool} was called" >&2\n'
                    f'echo "{tool}" >> "{temp}/build-tools-called"\nexit 99\n'
                )
                stub.chmod(0o755)
            fcitx5 = stub_bin / "fcitx5"
            fcitx5.write_text("#!/bin/sh\nexit 0\n")
            fcitx5.chmod(0o755)
            pkg_config = stub_bin / "pkg-config"
            pkg_config.write_text("#!/bin/sh\necho /usr/lib/x86_64-linux-gnu\n")
            pkg_config.chmod(0o755)

            dest = temp / "dest"
            env = os.environ.copy()
            env.update(
                {
                    "DESTDIR": str(dest),
                    "PREFIX": "/usr",
                    "HOME": str(temp / "home"),
                    "PATH": f"{stub_bin}:{env['PATH']}",
                    "BONGO_FCITX5": "0",
                }
            )
            env.pop("SUDO_USER", None)

            result = subprocess.run(
                ["bash", str(bundle / "install.sh"), "--prebuilt",
                 "--no-configure-fcitx5"],
                cwd=bundle,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode, 0,
                f"prebuilt install failed\nstdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}",
            )
            self.assertFalse(
                (temp / "build-tools-called").exists(),
                "prebuilt install must not invoke cargo/cmake",
            )
            self.assertTrue((dest / "usr" / "bin" / "bongo-settings").is_file())
            self.assertTrue(
                (dest / "usr" / "lib" / "bongo" / "libbongo_engine.so").is_file()
            )
            self.assertTrue(
                (dest / "usr" / "share" / "applications" / "bongo.desktop").is_file()
            )
            self.assertTrue(
                (
                    dest
                    / "usr"
                    / "lib"
                    / "x86_64-linux-gnu"
                    / "fcitx5"
                    / "libbongo.so"
                ).is_file(),
                "the addon must be installed in the target's fcitx5 addon dir",
            )


class UniversalTarballContractTests(unittest.TestCase):
    def test_build_script_assembles_a_versioned_x86_64_archive(self):
        self.assertTrue(
            TARBALL_SCRIPT.is_file(),
            "platforms/linux/scripts/build-tarball.sh is missing",
        )
        script = TARBALL_SCRIPT.read_text()
        self.assertIn('NAME="Bongo-${VERSION}-linux-${TARBALL_ARCH}"', script)
        self.assertIn('TARBALL_ARCH="x86_64"', script)
        self.assertIn('"${DIST_DIR}/${NAME}.tar.gz"', script)
        self.assertIn("payload", script)
        self.assertIn("install.sh", script)
        self.assertIn("MANIFEST.sha256", script)

    def test_release_workflow_builds_and_publishes_the_tarball(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()
        self.assertIn("build-tarball.sh", workflow)
        self.assertIn("*.tar.gz", workflow)
        self.assertIn("release-artifacts/*.tar.gz", workflow)
        self.assertIn("runs-on: ubuntu-24.04", workflow)
        self.assertNotIn("extra-cmake-modules", workflow)


class UniversalTarballDocsTests(unittest.TestCase):
    def test_readme_documents_the_universal_tarball(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("install.sh --prebuilt", readme)
        self.assertIn("linux-x86_64.tar.gz", readme)
        self.assertIn(
            "sudo ./platforms/linux/scripts/install.sh",
            readme,
            "source install should use the installer's auto default",
        )

    def test_linux_install_guide_documents_the_tarball(self):
        guide = (ROOT / "docs" / "LINUX-INSTALL.md").read_text()
        self.assertIn("install.sh --prebuilt", guide)
        self.assertIn("linux-x86_64.tar.gz", guide)

    def test_docs_drop_the_unshipped_rpm_and_force_flag(self):
        readme = (ROOT / "README.md").read_text()
        guide = (ROOT / "docs" / "LINUX-INSTALL.md").read_text()
        for text in (readme, guide):
            self.assertNotIn("dnf install ./bongo-", text)
            self.assertNotIn("sudo BONGO_FCITX5=1", text)


if __name__ == "__main__":
    unittest.main()
