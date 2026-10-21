import hashlib
import os
import platform
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
DEB_SCRIPT = SCRIPTS / "build-deb.sh"


def host_arch():
    machine = platform.machine().lower()
    return {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "aarch64",
        "aarch64": "aarch64",
    }.get(machine, machine)


def write_manifest(bundle):
    entries = []
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            relative = path.relative_to(bundle).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{digest}  {relative}")
    (bundle / "MANIFEST.sha256").write_text("\n".join(entries) + "\n")


def make_bundle(
    temp,
    *,
    arch=None,
    addon=True,
    manifest=True,
    python_ok=True,
    ldd_broken=False,
):
    bundle = temp / "bundle"
    bundle.mkdir()
    shutil.copy2(INSTALLER, bundle / "install.sh")

    payload = bundle / "payload"
    (payload / "bin").mkdir(parents=True)
    (payload / "lib" / "bongo").mkdir(parents=True)
    (payload / "share" / "applications").mkdir(parents=True)
    (payload / "share" / "fcitx5" / "addon").mkdir(parents=True)
    (payload / "bin" / "bongo-settings").write_text("#!/bin/sh\n")
    (payload / "lib" / "bongo" / "libbongo_engine.so").write_text("engine")
    (payload / "share" / "applications" / "bongo.desktop").write_text(
        "[Desktop Entry]\n"
    )
    (payload / "share" / "fcitx5" / "addon" / "bongo.conf").write_text("[Addon]\n")
    if addon:
        (bundle / "fcitx5").mkdir()
        (bundle / "fcitx5" / "libbongo.so").write_text("addon")
    (bundle / "README.txt").write_text("Bongo test bundle\n")
    (bundle / "ARCH").write_text(f"{arch or host_arch()}\n")

    stub_bin = temp / "stub-bin"
    stub_bin.mkdir()

    def stub(name, body):
        path = stub_bin / name
        path.write_text(body)
        path.chmod(0o755)
        return path

    for tool in ("cargo", "cmake"):
        stub(
            tool,
            f'#!/bin/sh\necho "{tool} was called" >&2\n'
            f'echo "{tool}" >> "{temp}/build-tools-called"\nexit 99\n',
        )
    stub("fcitx5", "#!/bin/sh\nexit 0\n")
    stub("pkg-config", "#!/bin/sh\necho /usr/lib/x86_64-linux-gnu\n")
    stub("python3", "#!/bin/sh\nexit 0\n" if python_ok else "#!/bin/sh\nexit 1\n")
    stub(
        "ldd",
        "#!/bin/sh\necho 'libfcitx5core.so.5 => not found'\nexit 0\n"
        if ldd_broken
        else "#!/bin/sh\nexit 0\n",
    )
    stub(
        "restorecon",
        f'#!/bin/sh\necho "$@" >> "{temp}/restorecon-called"\nexit 0\n',
    )

    if manifest:
        write_manifest(bundle)
    return bundle, stub_bin


def run_installer(bundle, stub_bin, temp, args, dest=None):
    env = os.environ.copy()
    env.update(
        {
            "DESTDIR": str(dest) if dest else "",
            "PREFIX": "/usr",
            "HOME": str(temp / "home"),
            "PATH": f"{stub_bin}:{env['PATH']}",
            "BONGO_FCITX5": "0",
        }
    )
    env.pop("SUDO_USER", None)
    return subprocess.run(
        ["bash", str(bundle / "install.sh"), *args],
        cwd=bundle,
        env=env,
        capture_output=True,
        text=True,
    )


class PrebuiltInstallerTests(unittest.TestCase):
    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "the prebuilt installer targets Linux",
    )
    def test_prebuilt_installer_copies_payload_without_building(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp)
            dest = temp / "dest"

            result = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )

            self.assertEqual(
                result.returncode,
                0,
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
            restorecon_log = (temp / "restorecon-called").read_text()
            self.assertIn(str(dest / "usr" / "bin" / "bongo-settings"), restorecon_log)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_prebuilt_installer_rejects_a_corrupt_archive(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp)
            dest = temp / "dest"
            (bundle / "payload" / "lib" / "bongo" / "libbongo_engine.so").write_text(
                "tampered"
            )

            result = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MANIFEST.sha256", result.stderr)
            self.assertFalse((dest / "usr").exists())

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_prebuilt_installer_requires_a_manifest(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp, manifest=False)
            dest = temp / "dest"

            result = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MANIFEST.sha256", result.stderr)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_prebuilt_installer_rejects_the_wrong_architecture(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp, arch="ppc64le")
            dest = temp / "dest"

            result = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ppc64le", result.stderr)
            self.assertIn("this system", result.stderr)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_prebuilt_installer_reports_missing_python_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp, python_ok=False)
            dest = temp / "dest"

            result = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("python3-gi", result.stderr)
            self.assertIn("gtk4", result.stderr)
            self.assertFalse((dest / "usr").exists())

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_prebuilt_installer_warns_when_the_addon_cannot_load(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp, ldd_broken=True)
            dest = temp / "dest"

            result = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("Warning", result.stderr)
            self.assertIn("fcitx5 addon", result.stderr)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_uninstall_does_not_touch_preexisting_files(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp)
            dest = temp / "dest"
            unrelated = dest / "usr" / "share" / "unrelated.txt"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("keep me\n")

            install = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            manifest = (dest / "usr" / "share" / "bongo" / "install-manifest").read_text()
            self.assertNotIn("unrelated.txt", manifest)

            uninstall = run_installer(bundle, stub_bin, temp, ["--uninstall"], dest=dest)
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertTrue(unrelated.is_file())
            self.assertEqual(unrelated.read_text(), "keep me\n")

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux installer")
    def test_prebuilt_uninstall_removes_installed_files(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            bundle, stub_bin = make_bundle(temp)
            dest = temp / "dest"
            other_addon = (
                dest / "usr" / "lib" / "x86_64-linux-gnu" / "fcitx5" / "other.so"
            )
            other_addon.parent.mkdir(parents=True)
            other_addon.write_text("other package\n")

            install = run_installer(
                bundle,
                stub_bin,
                temp,
                ["--prebuilt", "--no-configure-fcitx5"],
                dest=dest,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue((dest / "usr" / "bin" / "bongo-settings").is_file())

            uninstall = run_installer(bundle, stub_bin, temp, ["--uninstall"], dest=dest)

            self.assertEqual(
                uninstall.returncode,
                0,
                f"uninstall failed\nstdout:\n{uninstall.stdout}\n"
                f"stderr:\n{uninstall.stderr}",
            )
            self.assertIn("uninstalled", uninstall.stdout.lower())
            self.assertFalse((dest / "usr" / "bin" / "bongo-settings").exists())
            self.assertFalse(
                (
                    dest
                    / "usr"
                    / "lib"
                    / "x86_64-linux-gnu"
                    / "fcitx5"
                    / "libbongo.so"
                ).exists()
            )
            self.assertFalse(
                (dest / "usr" / "share" / "bongo" / "install-manifest").exists()
            )
            self.assertTrue(other_addon.is_file())
            self.assertEqual(other_addon.read_text(), "other package\n")


class UniversalTarballContractTests(unittest.TestCase):
    def test_build_script_assembles_a_versioned_arch_archive(self):
        self.assertTrue(
            TARBALL_SCRIPT.is_file(),
            "platforms/linux/scripts/build-tarball.sh is missing",
        )
        script = TARBALL_SCRIPT.read_text()
        self.assertIn('NAME="Bongo-${VERSION}-linux-${TARBALL_ARCH}"', script)
        self.assertIn('TARBALL_ARCH="x86_64"', script)
        self.assertIn('TARBALL_ARCH="aarch64"', script)
        self.assertIn('BONGO_FCITX5="${BONGO_FCITX5:-1}"', script)
        self.assertIn("fcitx5 addon missing", script)
        self.assertIn('"${DIST_DIR}/${NAME}.tar.gz"', script)
        self.assertIn("payload", script)
        self.assertIn("install.sh", script)
        self.assertIn("MANIFEST.sha256", script)
        self.assertIn("ARCH", script)
        for tar_flag in (
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "--sort=name",
        ):
            self.assertIn(tar_flag, script)

    def test_release_workflow_builds_x86_64_and_arm64(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()
        self.assertIn("build-tarball.sh", workflow)
        self.assertIn("ubuntu-24.04-arm", workflow)
        self.assertIn("matrix", workflow)
        self.assertIn("bongo-linux-packages-", workflow)
        self.assertIn("*.tar.gz", workflow)
        self.assertIn("release-artifacts/*.tar.gz", workflow)
        self.assertIn("runner: ubuntu-24.04", workflow)
        self.assertIn("runner: ubuntu-24.04-arm", workflow)
        self.assertIn("runs-on: ${{ matrix.runner }}", workflow)
        self.assertNotIn("extra-cmake-modules", workflow)

    def test_ci_builds_the_tarball_and_tests_real_distributions(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("bongo-linux-tarball", workflow)
        self.assertIn("distro-matrix", workflow)
        self.assertIn("debian:13", workflow)
        self.assertIn("fedora:latest", workflow)
        self.assertIn("archlinux:latest", workflow)
        self.assertIn("ldd -r", workflow)


class UniversalTarballDocsTests(unittest.TestCase):
    def test_readme_documents_both_arches_and_uninstall(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("install.sh --prebuilt", readme)
        self.assertIn("linux-x86_64.tar.gz", readme)
        self.assertIn("linux-aarch64.tar.gz", readme)
        self.assertIn("install.sh --uninstall", readme)
        self.assertIn("glibc 2.39", readme)
        self.assertIn(
            "sudo ./platforms/linux/scripts/install.sh",
            readme,
            "source install should use the installer's auto default",
        )

    def test_linux_install_guide_documents_both_arches_and_uninstall(self):
        guide = (ROOT / "docs" / "LINUX-INSTALL.md").read_text()
        self.assertIn("install.sh --prebuilt", guide)
        self.assertIn("linux-x86_64.tar.gz", guide)
        self.assertIn("linux-aarch64.tar.gz", guide)
        self.assertIn("install.sh --uninstall", guide)
        self.assertIn("glibc 2.39", guide)

    def test_docs_drop_the_unshipped_rpm_and_force_flag(self):
        readme = (ROOT / "README.md").read_text()
        guide = (ROOT / "docs" / "LINUX-INSTALL.md").read_text()
        for text in (readme, guide):
            self.assertNotIn("dnf install ./bongo-", text)
            self.assertNotIn("sudo BONGO_FCITX5=1", text)

    def test_deb_builder_does_not_claim_unsupported_glibc_floors(self):
        script = DEB_SCRIPT.read_text()
        self.assertNotIn("22.04", script)
        self.assertIn("24.04", script)
        self.assertIn("glibc 2.39", script)


if __name__ == "__main__":
    unittest.main()
