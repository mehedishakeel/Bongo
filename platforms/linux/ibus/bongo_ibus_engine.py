#!/usr/bin/env python3
"""
Bongo IBus Engine Daemon for Linux
Provides native Avro phonetic Bengali typing on modern Linux desktops (GNOME, KDE, XFCE).
Integrates with IBus input method framework via GObject introspection.
"""

import os
import sys
import json
import ctypes
from pathlib import Path

# Setup GObject Introspection for IBus
import gi
try:
    gi.require_version('IBus', '1.0')
    from gi.repository import IBus, GLib, GObject
except ValueError as e:
    sys.stderr.write(f"Error: IBus 1.0 GObject library not found: {e}\n")
    sys.exit(1)


# Locate libbongo_engine shared library
def find_engine_library():
    search_paths = [
        # Local development / source paths
        Path(__file__).parent.parent / "engine" / "target" / "release" / "libbongo_engine.so",
        Path(__file__).parent.parent / "engine" / "target" / "debug" / "libbongo_engine.so",
        # Standard system install paths
        Path("/usr/lib/bongo/libbongo_engine.so"),
        Path("/usr/lib64/bongo/libbongo_engine.so"),
        Path("/usr/lib/x86_64-linux-gnu/bongo/libbongo_engine.so"),
        Path("/usr/lib/aarch64-linux-gnu/bongo/libbongo_engine.so"),
        Path("/usr/local/lib/bongo/libbongo_engine.so"),
    ]
    for p in search_paths:
        if p.is_file():
            return str(p)
    return "libbongo_engine.so"


class BongoNativeBinding:
    """ctypes binding to libbongo_engine.so"""
    def __init__(self):
        lib_path = find_engine_library()
        try:
            self.lib = ctypes.CDLL(lib_path)
        except OSError as e:
            sys.stderr.write(f"Warning: Could not load {lib_path}: {e}. Running with fallback.\n")
            self.lib = None
            return

        # Declare C signatures
        self.lib.bongo_engine_new.restype = ctypes.c_void_p
        self.lib.bongo_engine_free.argtypes = [ctypes.c_void_p]

        self.lib.bongo_engine_set_mode.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.lib.bongo_engine_set_emoji.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        self.lib.bongo_engine_has_session.argtypes = [ctypes.c_void_p]
        self.lib.bongo_engine_has_session.restype = ctypes.c_bool

        self.lib.bongo_engine_feed_char.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8, ctypes.c_uint8]
        self.lib.bongo_engine_feed_char.restype = ctypes.c_void_p

        self.lib.bongo_engine_backspace.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        self.lib.bongo_engine_backspace.restype = ctypes.c_void_p

        self.lib.bongo_engine_commit.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.lib.bongo_engine_reset.argtypes = [ctypes.c_void_p]

        self.lib.bongo_suggestion_count.argtypes = [ctypes.c_void_p]
        self.lib.bongo_suggestion_count.restype = ctypes.c_size_t

        self.lib.bongo_suggestion_get_candidate.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.lib.bongo_suggestion_get_candidate.restype = ctypes.c_char_p

        self.lib.bongo_suggestion_get_preview.argtypes = [ctypes.c_void_p]
        self.lib.bongo_suggestion_get_preview.restype = ctypes.c_char_p

        self.lib.bongo_suggestion_free.argtypes = [ctypes.c_void_p]
        self.lib.bongo_string_free.argtypes = [ctypes.c_char_p]


def load_settings():
    config_dir = Path.home() / ".config" / "bongo"
    config_file = config_dir / "settings.json"
    defaults = {
        "typing_mode": 0,       # 0: PhoneticFirst, 1: Smart, 2: PhoneticOnly
        "suggest_emoji": True,
        "candidate_font": "Noto Sans Bengali",
        "candidate_font_size": 16,
    }
    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
        except Exception as e:
            sys.stderr.write(f"Could not read settings: {e}\n")
    return defaults


class BongoEngine(IBus.Engine):
    __gtype_name__ = 'BongoEngine'

    def __init__(self):
        super().__init__()
        self.native = BongoNativeBinding()
        self.engine_ptr = self.native.lib.bongo_engine_new() if (self.native and self.native.lib) else None
        
        self._settings_mtime = 0
        self.settings = load_settings()
        self.apply_settings()

        # Lookup table for floating candidate HUD
        self.table = IBus.LookupTable.new(9, 0, True, True)
        self.table.set_orientation(IBus.Orientation.VERTICAL)

        self.preedit_str = ""
        self.candidates = []

    def check_reload_settings(self):
        config_file = Path.home() / ".config" / "bongo" / "settings.json"
        if config_file.is_file():
            try:
                mtime = config_file.stat().st_mtime
                if mtime > self._settings_mtime:
                    self._settings_mtime = mtime
                    self.settings = load_settings()
                    self.apply_settings()
            except Exception:
                pass

    def do_focus_in(self):
        self.check_reload_settings()

    def do_enable(self):
        self.check_reload_settings()

    def apply_settings(self):
        if not self.engine_ptr:
            return
        mode = self.settings.get("typing_mode", 0)
        emoji = self.settings.get("suggest_emoji", True)
        self.native.lib.bongo_engine_set_mode(self.engine_ptr, mode)
        self.native.lib.bongo_engine_set_emoji(self.engine_ptr, emoji)

    def do_process_key_event(self, keyval, keycode, state):
        # Ignore key release events
        is_press = (state & IBus.ModifierType.RELEASE_MASK) == 0
        if not is_press:
            return False

        # Ignore Ctrl or Alt key combinations (e.g. Ctrl+C, Ctrl+V)
        is_ctrl = bool(state & IBus.ModifierType.CONTROL_MASK)
        is_alt = bool(state & IBus.ModifierType.MOD1_MASK)
        is_super = bool(state & IBus.ModifierType.SUPER_MASK)
        if is_ctrl or is_alt or is_super:
            if self.has_session():
                self.commit_current()
            return False

        # Key navigation in candidate table
        if self.has_session():
            # Escape: cancel composition
            if keyval == IBus.KEY_Escape:
                self.reset_session()
                return True

            # Enter / Return: commit current candidate
            if keyval in (IBus.KEY_Return, IBus.KEY_KP_Enter):
                self.commit_current()
                return True

            # Space: commit primary candidate
            if keyval == IBus.KEY_space:
                self.commit_current()
                return True

            # Number keys (1..9): commit candidate at index
            if IBus.KEY_1 <= keyval <= IBus.KEY_9:
                idx = keyval - IBus.KEY_1
                if idx < len(self.candidates):
                    self.commit_candidate_at(idx)
                    return True

            # Arrow Down / Up: candidate selection
            if keyval in (IBus.KEY_Down, IBus.KEY_Page_Down):
                self.table.cursor_down()
                self.update_lookup_table()
                return True
            if keyval in (IBus.KEY_Up, IBus.KEY_Page_Up):
                self.table.cursor_up()
                self.update_lookup_table()
                return True

            # Backspace: delete character
            if keyval == IBus.KEY_BackSpace:
                self.handle_backspace()
                return True

        # Process standard printable character
        ch = IBus.keyval_to_unicode(keyval)
        if ch > 0 and (32 <= ch <= 126 or ch >= 128):
            # If not in session and character is whitespace/punctuation outside phonetic rules, pass through
            if not self.has_session() and chr(ch) in " \t\r\n":
                return False

            handled = self.feed_character(ch, state)
            if handled:
                return True

        return False

    def has_session(self):
        if not self.engine_ptr:
            return bool(self.preedit_str)
        return self.native.lib.bongo_engine_has_session(self.engine_ptr)

    def feed_character(self, ch, state):
        if not self.engine_ptr:
            return False

        is_shift = bool(state & IBus.ModifierType.SHIFT_MASK)
        modifier = 1 if is_shift else 0
        cursor_idx = self.table.get_cursor_pos() if self.has_session() else 0

        sugg_ptr = self.native.lib.bongo_engine_feed_char(self.engine_ptr, ch, modifier, cursor_idx)
        if not sugg_ptr:
            return False

        self.update_suggestions(sugg_ptr)
        self.native.lib.bongo_suggestion_free(sugg_ptr)
        return True

    def handle_backspace(self):
        if not self.engine_ptr:
            return
        sugg_ptr = self.native.lib.bongo_engine_backspace(self.engine_ptr, False)
        if sugg_ptr:
            self.update_suggestions(sugg_ptr)
            self.native.lib.bongo_suggestion_free(sugg_ptr)
        else:
            self.reset_session()

    def update_suggestions(self, sugg_ptr):
        count = self.native.lib.bongo_suggestion_count(sugg_ptr)
        self.candidates = []
        self.table.clear()

        for i in range(count):
            cand_ptr = self.native.lib.bongo_suggestion_get_candidate(sugg_ptr, i)
            if cand_ptr:
                cand_str = cand_ptr.decode('utf-8', errors='replace')
                self.candidates.append(cand_str)
                text = IBus.Text.new_from_string(cand_str)
                self.table.append_candidate(text)
                self.native.lib.bongo_string_free(cand_ptr)

        preview_ptr = self.native.lib.bongo_suggestion_get_preview(sugg_ptr)
        if preview_ptr:
            self.preedit_str = preview_ptr.decode('utf-8', errors='replace')
            self.native.lib.bongo_string_free(preview_ptr)
        elif self.candidates:
            self.preedit_str = self.candidates[0]
        else:
            self.preedit_str = ""

        if self.preedit_str:
            self.show_preedit()
            self.update_lookup_table()
        else:
            self.reset_session()

    def show_preedit(self):
        text = IBus.Text.new_from_string(self.preedit_str)
        text.append_attribute(IBus.AttrType.UNDERLINE, IBus.AttrUnderline.SINGLE, 0, len(self.preedit_str))
        self.update_preedit_text(text, len(self.preedit_str), True)

    def update_lookup_table(self):
        if self.candidates:
            self.update_lookup_table_fast(self.table, True)
        else:
            self.hide_lookup_table()

    def commit_current(self):
        if not self.candidates:
            if self.preedit_str:
                self.commit_text(IBus.Text.new_from_string(self.preedit_str))
            self.reset_session()
            return

        cursor = self.table.get_cursor_pos()
        if cursor >= len(self.candidates):
            cursor = 0
        self.commit_candidate_at(cursor)

    def commit_candidate_at(self, idx):
        if idx < len(self.candidates):
            chosen = self.candidates[idx]
            self.commit_text(IBus.Text.new_from_string(chosen))
            if self.engine_ptr:
                self.native.lib.bongo_engine_commit(self.engine_ptr, idx)
        self.reset_session()

    def reset_session(self):
        if self.engine_ptr:
            self.native.lib.bongo_engine_reset(self.engine_ptr)
        self.preedit_str = ""
        self.candidates = []
        self.table.clear()
        self.hide_preedit_text()
        self.hide_lookup_table()

    def do_focus_out(self):
        if self.has_session():
            self.commit_current()
        self.reset_session()

    def do_reset(self):
        self.reset_session()


class BongoApplication:
    def __init__(self, bus):
        self.bus = bus
        self.factory = IBus.Factory.new(self.bus.get_connection())
        self.factory.add_engine("bongo", GObject.type_from_name("BongoEngine"))

        if "--ibus" in sys.argv:
            self.bus.request_name("org.freedesktop.IBus.Bongo", 0)
        else:
            # Component registration
            component_path = "/usr/share/ibus/component/bongo.xml"
            if not os.path.exists(component_path):
                component_path = str(Path(__file__).parent / "bongo.xml")
            if os.path.exists(component_path):
                component = IBus.Component.new_from_file(component_path)
                self.bus.register_component(component)

    def run(self):
        loop = GLib.MainLoop()
        loop.run()


def main():
    IBus.init()
    bus = IBus.Bus.new()
    if not bus.is_connected():
        sys.stderr.write("Error: Could not connect to IBus daemon bus.\n")
        sys.exit(1)

    app = BongoApplication(bus)
    app.run()


if __name__ == '__main__':
    main()
