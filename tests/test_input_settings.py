"""Regression tests for the "Open Input Settings..." launcher on Linux.

The ``fcitx5-configtool`` executable shipped by the ``fcitx5`` package is only
a wrapper: when the real GUI (``fcitx5-config-qt``) is missing it opens
``~/.config/fcitx5`` in the file manager. On Omarchy/Hyprland that made
Bongo's "Open Input Settings..." button open Files instead of fcitx5's
configuration window.

These tests extract the helper and the button handler from
``platforms/linux/ui/bongo_settings.py`` with :mod:`ast`, so they run in CI
without GTK or PyGObject installed.
"""
import ast
import textwrap
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "platforms/linux/ui/bongo_settings.py"
SOURCE = SETTINGS.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(SETTINGS))


def _function_node(name):
    """Return the module-level function node called ``name``."""
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not defined at module level")


def _method_node(class_name, method_name):
    """Return the method node ``class_name.method_name``."""
    for node in TREE.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError(f"{class_name}.{method_name} was not found")


def _load_function(node, namespace=None):
    """Compile one function node into a real callable."""
    segment = ast.get_source_segment(SOURCE, node)
    module = ast.parse(textwrap.dedent(segment))
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(SETTINGS), "exec"), scope)
    return scope[node.name]


def _load_method(class_name, method_name, namespace):
    node = _method_node(class_name, method_name)
    segment = ast.get_source_segment(SOURCE, node)
    module = ast.parse(textwrap.dedent(segment))
    ast.fix_missing_locations(module)
    scope = dict(namespace)
    exec(compile(module, str(SETTINGS), "exec"), scope)
    return scope[node.name]


COMMANDS = _load_function(_function_node("input_settings_commands"))


class InputSettingsCommandsTests(unittest.TestCase):
    """The helper must never offer the file-manager-opening wrapper."""

    def _first_executables(self, desktop):
        return [cmd[0] for cmd in COMMANDS(desktop)]

    def test_never_uses_the_configtool_wrapper(self):
        for desktop in (
            "Hyprland",
            "Omarchy",
            "KDE",
            "GNOME",
            "Unity",
            "XFCE",
            "",
            None,
        ):
            with self.subTest(desktop=desktop):
                self.assertNotIn(
                    "fcitx5-configtool",
                    self._first_executables(desktop),
                    "the fcitx5-configtool wrapper opens the config directory "
                    "in a file manager when fcitx5-config-qt is missing",
                )

    def test_hyprland_prefers_the_real_fcitx5_gui(self):
        self.assertEqual(COMMANDS("Hyprland")[0], ["fcitx5-config-qt"])

    def test_omarchy_is_treated_as_a_fcitx5_desktop(self):
        commands = COMMANDS("OMARCHY")
        self.assertEqual(commands[0], ["fcitx5-config-qt"])
        self.assertNotIn(["fcitx5-configtool"], commands)

    def test_gnome_prefers_gnome_control_center(self):
        for desktop in ("GNOME", "ubuntu:GNOME", "Unity", "Pantheon"):
            with self.subTest(desktop=desktop):
                commands = COMMANDS(desktop)
                self.assertEqual(
                    commands[0], ["gnome-control-center", "keyboard"]
                )
                self.assertIn(["fcitx5-config-qt"], commands)

    def test_kde_falls_back_through_the_fcitx5_kcm(self):
        commands = COMMANDS("KDE")
        self.assertEqual(commands[0], ["fcitx5-config-qt"])
        self.assertIn(["kcmshell6", "kcm_fcitx5"], commands)
        self.assertIn(["kcmshell5", "kcm_fcitx5"], commands)

    def test_unknown_desktop_still_tries_the_fcitx5_gui_then_ibus(self):
        self.assertEqual(
            COMMANDS("XFCE"), [["fcitx5-config-qt"], ["ibus-setup"]]
        )


class OpenSystemKeyboardSettingsTests(unittest.TestCase):
    """The button handler must launch a real tool or explain what is missing."""

    class _Stub:
        def __init__(self):
            self.dialogs = []

        def show_dialog(self, title, message):
            self.dialogs.append((title, message))

    def _load(self, available):
        launched = []

        class FakeShutil:
            @staticmethod
            def which(executable):
                return f"/usr/bin/{executable}" if executable in available else None

        class FakeSubprocess:
            @staticmethod
            def Popen(cmd):
                launched.append(list(cmd))
                return object()

        namespace = {
            "os": types.SimpleNamespace(
                environ={"XDG_CURRENT_DESKTOP": "Hyprland"}
            ),
            "shutil": FakeShutil,
            "subprocess": FakeSubprocess,
            "input_settings_commands": COMMANDS,
        }
        handler = _load_method(
            "BongoSettingsApp", "open_system_keyboard_settings", namespace
        )
        return handler, self._Stub(), launched

    def test_wrapper_only_environment_launches_nothing_and_shows_a_dialog(self):
        """The reported Omarchy bug: only the wrapper exists."""
        handler, stub, launched = self._load({"fcitx5-configtool"})
        handler(stub, None)

        self.assertEqual(launched, [], "must not run the file-manager wrapper")
        self.assertEqual(len(stub.dialogs), 1)
        title, message = stub.dialogs[0]
        self.assertIn("unavailable", title.lower())
        self.assertIn("fcitx5-configtool", message)

    def test_installed_fcitx5_gui_is_launched(self):
        handler, stub, launched = self._load({"fcitx5-config-qt"})
        handler(stub, None)

        self.assertEqual(launched, [["fcitx5-config-qt"]])
        self.assertEqual(stub.dialogs, [])

    def test_nothing_available_shows_the_install_hint(self):
        handler, stub, launched = self._load(set())
        handler(stub, None)

        self.assertEqual(launched, [])
        self.assertEqual(len(stub.dialogs), 1)
        self.assertIn("sudo pacman -S fcitx5-configtool", stub.dialogs[0][1])


if __name__ == "__main__":
    unittest.main()
