import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "platforms" / "linux" / "scripts" / "configure-fcitx5.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("configure_fcitx5", HELPER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Fcitx5ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.profile = Path(self.temp.name) / "profile"
        self.helper = load_helper()

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_profile_is_created(self):
        self.assertTrue(self.helper.configure_profile(self.profile))
        text = self.profile.read_text()
        self.assertIn("[GroupOrder]", text)
        self.assertIn("Name=keyboard-us", text)
        self.assertIn("Name=bongo", text)
        self.assertIn("DefaultIM=bongo", text)

    def test_existing_profile_keeps_order_and_default(self):
        original = """[Groups/0]
Name=Default
Default Layout=us
DefaultIM=keyboard-us

[Groups/0/Items/0]
Name=keyboard-us
Layout=

[GroupOrder]
0=Default
"""
        self.profile.write_text(original)
        self.assertTrue(self.helper.configure_profile(self.profile))
        text = self.profile.read_text()
        self.assertIn("DefaultIM=keyboard-us", text)
        self.assertLess(text.index("Name=keyboard-us"), text.index("Name=bongo"))
        self.assertIn("[Groups/0/Items/1]", text)
        self.assertTrue((self.profile.parent / "profile.bongo-backup").exists())

    def test_existing_bongo_is_idempotent(self):
        original = """[Groups/0]
Name=Default
DefaultIM=keyboard-us

[Groups/0/Items/0]
Name=keyboard-us
Layout=

[Groups/0/Items/1]
Name=bongo
Layout=

[GroupOrder]
0=Default
"""
        self.profile.write_text(original)
        self.assertTrue(self.helper.configure_profile(self.profile))
        self.assertEqual(self.profile.read_text(), original)
        self.assertFalse((self.profile.parent / "profile.bongo-backup").exists())

    def test_malformed_profile_is_not_modified(self):
        original = "this is not an fcitx5 profile\n"
        self.profile.write_text(original)
        self.assertFalse(self.helper.configure_profile(self.profile))
        self.assertEqual(self.profile.read_text(), original)

    def test_first_group_from_group_order_is_used(self):
        original = """[Groups/0]
Name=First
DefaultIM=keyboard-us

[Groups/0/Items/0]
Name=keyboard-us
Layout=

[Groups/1]
Name=Second

[Groups/1/Items/0]
Name=other
Layout=

[GroupOrder]
0=Second
1=First
"""
        self.profile.write_text(original)
        self.assertTrue(self.helper.configure_profile(self.profile))
        text = self.profile.read_text()
        self.assertIn("[Groups/1/Items/1]", text)
        self.assertIn("Name=bongo", text)
        self.assertNotIn("[Groups/0/Items/1]", text)

    def test_manual_steps_are_actionable(self):
        steps = self.helper.manual_steps()
        self.assertIn("fcitx5-configtool", steps)
        self.assertIn("Bongo", steps)


if __name__ == "__main__":
    unittest.main()
