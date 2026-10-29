#!/usr/bin/env python3
"""
Bongo Input Method Service for Windows
Provides system-wide Avro phonetic Bengali typing on modern Windows (10/11).
Integrates with the bongo_engine Rust library (or built-in fallback) via ctypes,
intercepts keystrokes via low-level keyboard hooks (WH_KEYBOARD_LL),
and injects Unicode text via SendInput.
"""

import os
import sys
import time
import json
import re
import ctypes
from ctypes import wintypes
from functools import lru_cache
from pathlib import Path

# Add platforms/common to path for linguistic converter module
COMMON_DIR = Path(__file__).resolve().parent.parent.parent / "common"
if COMMON_DIR.is_dir() and str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

try:
    from converter import (
        separate_padding,
        fix_string_case,
        apply_sandhi_rules,
        AUTOCORRECT_LOANWORDS,
        unicode_to_bijoy,
        bijoy_to_unicode,
    )
except ImportError:
    def separate_padding(word: str):
        m1 = re.match(r"^([\-\]~!@#%&*()_=+[{}'\";<>\/?|.,:]+)", word or "")
        p = m1.group(1) if m1 else ""
        rest = (word or "")[len(p):]
        m2 = re.search(r"([\-\]~!@#%&*()_=+[{}'\";<>\/?|.,:]+)$", rest)
        s = m2.group(1) if m2 else ""
        return p, rest[:len(rest) - len(s)] if s else rest, s
    def fix_string_case(word: str):
        cased = set("OIUDGJNRSTYZ")
        return "".join(c if (c in cased or not c.isalpha()) else c.lower() for c in (word or ""))
    def apply_sandhi_rules(stem: str, suffix: str):
        return (stem or "") + (suffix or "")
    AUTOCORRECT_LOANWORDS = {
        "1st": "১ম", "2nd": "২য়", "3rd": "৩য়", "4th": "৪র্থ", "5th": "৫ম",
        "class": "ক্লাস", "click": "ক্লিক", "school": "স্কুল", "police": "পুলিশ",
        "google": "গুগল", "facebook": "ফেসবুক", "bongo": "বঙ্গ",
        "hya": "হ্যাঁ", "hea": "হ্যাঁ", "cad": "চাঁদ", "chad": "চাঁদ", "chada": "চাঁদা",
        "pac": "পাঁচ", "pach": "পাঁচ", "hata": "হাঁটা", "khuj": "খুঁজ", "khuje": "খুঁজে",
    }

class SafeStream:
    def write(self, s):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = SafeStream()
if sys.stderr is None:
    sys.stderr = SafeStream()

# Windows Configuration Path
def get_config_dir():
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Bongo"
    return Path.home() / ".config" / "bongo"

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "settings.json"

def get_log_file():
    log_dir = get_config_dir()
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return log_dir / "bongo_service.log"

LOG_FILE = get_log_file()

def log_msg(msg: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
    except Exception:
        pass
    try:
        if sys.stdout is not None:
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception:
        pass

DEFAULT_SETTINGS = {
    "keyboard_layout": 0,     # 0: Avro Phonetic, 1: National (Bijoy)
    "typing_mode": 0,         # 0: PhoneticFirst, 1: Smart, 2: PhoneticOnly
    "suggest_emoji": True,
    "candidate_font": "Noto Sans Bengali",
    "candidate_font_size": 16,
    "toggle_key": "F12",
    "autostart": True,
}

def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                settings.update(saved)
        except Exception:
            pass
    return settings

# Locate bongo_engine.dll
def find_engine_dll():
    search_paths = [
        Path(sys.executable).parent / "bongo_engine.dll",
        Path(__file__).resolve().parent / "bongo_engine.dll",
        Path(__file__).resolve().parent.parent / "build" / "bongo_engine.dll",
        Path(__file__).resolve().parent.parent / "engine" / "target" / "release" / "bongo_engine.dll",
        Path(__file__).resolve().parent.parent / "engine" / "target" / "debug" / "bongo_engine.dll",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Bongo" / "bongo_engine.dll",
        Path(r"C:\Program Files\Bongo\bongo_engine.dll"),
    ]
    for p in search_paths:
        if p.is_file():
            return str(p)
    return "bongo_engine.dll"

# Native C FFI Binding for bongo_engine.dll
class BongoNativeBinding:
    def __init__(self):
        self.lib = None
        dll_path = find_engine_dll()
        log_msg(f"Checking for bongo_engine.dll at: {dll_path}")
        try:
            self.lib = ctypes.CDLL(dll_path)
            self._setup_signatures()
            log_msg(f"Loaded native bongo_engine.dll successfully from {dll_path}")
        except Exception as e:
            log_msg(f"Note: native engine not loaded ({e}), using built-in pure Python Avro phonetic engine.")
            self.lib = None

    def _setup_signatures(self):
        self.lib.bongo_engine_new.restype = ctypes.c_void_p
        self.lib.bongo_engine_free.argtypes = [ctypes.c_void_p]

        self.lib.bongo_engine_set_layout.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.lib.bongo_engine_get_layout.argtypes = [ctypes.c_void_p]
        self.lib.bongo_engine_get_layout.restype = ctypes.c_uint32

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
        self.lib.bongo_suggestion_get_candidate.restype = ctypes.c_void_p

        self.lib.bongo_suggestion_get_preview.argtypes = [ctypes.c_void_p]
        self.lib.bongo_suggestion_get_preview.restype = ctypes.c_void_p

        self.lib.bongo_suggestion_free.argtypes = [ctypes.c_void_p]
        self.lib.bongo_string_free.argtypes = [ctypes.c_void_p]



# Pure Python Avro Phonetic Engine
AVRO_PATTERNS_DATA = json.loads(r'[{"find":"NgkSh","default":"ঙ্ক্ষ","rules":[]},{"find":"Ngkkh","default":"ঙ্ক্ষ","rules":[]},{"find":"kkhN","default":"ক্ষ্ণ","rules":[]},{"find":"kShN","default":"ক্ষ্ণ","rules":[]},{"find":"kkhm","default":"ক্ষ্ম","rules":[]},{"find":"kShm","default":"ক্ষ্ম","rules":[]},{"find":"NGch","default":"ঞ্ছ","rules":[]},{"find":"Nggh","default":"ঙ্ঘ","rules":[]},{"find":"Ngkh","default":"ঙ্খ","rules":[]},{"find":"NGjh","default":"ঞ্ঝ","rules":[]},{"find":"ngOU","default":"ঙ্গৌ","rules":[]},{"find":"ngOI","default":"ঙ্গৈ","rules":[]},{"find":"Ngkx","default":"ঙ্ক্ষ","rules":[]},{"find":"rri`","default":"ৃ","rules":[]},{"find":"shch","default":"শ্ছ","rules":[]},{"find":"ShTh","default":"ষ্ঠ","rules":[]},{"find":"Shph","default":"ষ্ফ","rules":[]},{"find":"psh","default":"পশ","rules":[]},{"find":"bhl","default":"ভ্ল","rules":[]},{"find":"bdh","default":"ব্ধ","rules":[]},{"find":"cNG","default":"চ্ঞ","rules":[]},{"find":"cch","default":"চ্ছ","rules":[]},{"find":"dhn","default":"ধ্ন","rules":[]},{"find":"dhm","default":"ধ্ম","rules":[]},{"find":"dgh","default":"দ্ঘ","rules":[]},{"find":"ddh","default":"দ্ধ","rules":[]},{"find":"dbh","default":"দ্ভ","rules":[]},{"find":"...","default":"...","rules":[]},{"find":"ghn","default":"ঘ্ন","rules":[]},{"find":"Ghn","default":"ঘ্ন","rules":[]},{"find":"gdh","default":"গ্ধ","rules":[]},{"find":"Gdh","default":"গ্ধ","rules":[]},{"find":"jjh","default":"জ্ঝ","rules":[]},{"find":"jNG","default":"জ্ঞ","rules":[]},{"find":"kxN","default":"ক্ষ্ণ","rules":[]},{"find":"kxm","default":"ক্ষ্ম","rules":[]},{"find":"kkh","default":"ক্ষ","rules":[]},{"find":"kSh","default":"ক্ষ","rules":[]},{"find":"ksh","default":"কশ","rules":[]},{"find":"lbh","default":"ল্ভ","rules":[]},{"find":"ldh","default":"ল্ধ","rules":[]},{"find":"lkh","default":"লখ","rules":[]},{"find":"lgh","default":"লঘ","rules":[]},{"find":"lph","default":"লফ","rules":[]},{"find":"mth","default":"ম্থ","rules":[]},{"find":"mph","default":"ম্ফ","rules":[]},{"find":"mbh","default":"ম্ভ","rules":[]},{"find":"mpl","default":"মপ্ল","rules":[]},{"find":"NGc","default":"ঞ্চ","rules":[]},{"find":"nch","default":"ঞ্ছ","rules":[]},{"find":"njh","default":"ঞ্ঝ","rules":[]},{"find":"ngh","default":"ঙ্ঘ","rules":[]},{"find":"Ngk","default":"ঙ্ক","rules":[]},{"find":"Ngx","default":"ঙ্ষ","rules":[]},{"find":"Ngg","default":"ঙ্গ","rules":[]},{"find":"Ngm","default":"ঙ্ম","rules":[]},{"find":"NGj","default":"ঞ্জ","rules":[]},{"find":"ndh","default":"ন্ধ","rules":[]},{"find":"nTh","default":"ন্ঠ","rules":[]},{"find":"NTh","default":"ণ্ঠ","rules":[]},{"find":"nth","default":"ন্থ","rules":[]},{"find":"nkh","default":"ঙ্খ","rules":[]},{"find":"ngo","default":"ঙ্গ","rules":[]},{"find":"nga","default":"ঙ্গা","rules":[]},{"find":"ngi","default":"ঙ্গি","rules":[]},{"find":"ngI","default":"ঙ্গী","rules":[]},{"find":"ngu","default":"ঙ্গু","rules":[]},{"find":"ngU","default":"ঙ্গূ","rules":[]},{"find":"nge","default":"ঙ্গে","rules":[]},{"find":"ngO","default":"ঙ্গো","rules":[]},{"find":"NDh","default":"ণ্ঢ","rules":[]},{"find":"nsh","default":"নশ","rules":[]},{"find":"Ngr","default":"ঙর","rules":[]},{"find":"NGr","default":"ঞর","rules":[]},{"find":"ngr","default":"ংর","rules":[]},{"find":"OI`","default":"ৈ","rules":[]},{"find":"OU`","default":"ৌ","rules":[]},{"find":"phl","default":"ফ্ল","rules":[]},{"find":"rri","default":"ৃ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঋ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঋ"}]},{"find":"rrZ","default":"রর\u200d্য","rules":[]},{"find":"rry","default":"রর\u200d্য","rules":[]},{"find":"Sch","default":"শ্ছ","rules":[]},{"find":"skl","default":"স্ক্ল","rules":[]},{"find":"skh","default":"স্খ","rules":[]},{"find":"sth","default":"স্থ","rules":[]},{"find":"sph","default":"স্ফ","rules":[]},{"find":"shc","default":"শ্চ","rules":[]},{"find":"sht","default":"শ্ত","rules":[]},{"find":"shn","default":"শ্ন","rules":[]},{"find":"shm","default":"শ্ম","rules":[]},{"find":"shl","default":"শ্ল","rules":[]},{"find":"Shk","default":"ষ্ক","rules":[]},{"find":"ShT","default":"ষ্ট","rules":[]},{"find":"ShN","default":"ষ্ণ","rules":[]},{"find":"Shp","default":"ষ্প","rules":[]},{"find":"Shf","default":"ষ্ফ","rules":[]},{"find":"Shm","default":"ষ্ম","rules":[]},{"find":"spl","default":"স্প্ল","rules":[]},{"find":"oo`","default":"ু","rules":[]},{"find":"tth","default":"ত্থ","rules":[]},{"find":"t``","default":"ৎ","rules":[]},{"find":"ee`","default":"ী","rules":[]},{"find":"bj","default":"ব্জ","rules":[]},{"find":"bd","default":"ব্দ","rules":[]},{"find":"bb","default":"ব্ব","rules":[]},{"find":"bl","default":"ব্ল","rules":[]},{"find":"bh","default":"ভ","rules":[]},{"find":"vl","default":"ভ্ল","rules":[]},{"find":"cc","default":"চ্চ","rules":[]},{"find":"ch","default":"ছ","rules":[]},{"find":"dv","default":"দ্ভ","rules":[]},{"find":"dm","default":"দ্ম","rules":[]},{"find":"DD","default":"ড্ড","rules":[]},{"find":"Dh","default":"ঢ","rules":[]},{"find":"dh","default":"ধ","rules":[]},{"find":"dg","default":"দ্গ","rules":[]},{"find":"dd","default":"দ্দ","rules":[]},{"find":".`","default":".","rules":[]},{"find":"..","default":"।।","rules":[]},{"find":"gN","default":"গ্ণ","rules":[]},{"find":"GN","default":"গ্ণ","rules":[]},{"find":"gn","default":"গ্ন","rules":[]},{"find":"Gn","default":"গ্ন","rules":[]},{"find":"gm","default":"গ্ম","rules":[]},{"find":"Gm","default":"গ্ম","rules":[]},{"find":"gl","default":"গ্ল","rules":[]},{"find":"Gl","default":"গ্ল","rules":[]},{"find":"gg","default":"জ্ঞ","rules":[]},{"find":"GG","default":"জ্ঞ","rules":[]},{"find":"Gg","default":"জ্ঞ","rules":[]},{"find":"gG","default":"জ্ঞ","rules":[]},{"find":"gh","default":"ঘ","rules":[]},{"find":"Gh","default":"ঘ","rules":[]},{"find":"hN","default":"হ্ণ","rules":[]},{"find":"hn","default":"হ্ন","rules":[]},{"find":"hm","default":"হ্ম","rules":[]},{"find":"hl","default":"হ্ল","rules":[]},{"find":"jh","default":"ঝ","rules":[]},{"find":"jj","default":"জ্জ","rules":[]},{"find":"kx","default":"ক্ষ","rules":[]},{"find":"kk","default":"ক্ক","rules":[]},{"find":"kT","default":"ক্ট","rules":[]},{"find":"kt","default":"ক্ত","rules":[]},{"find":"kl","default":"ক্ল","rules":[]},{"find":"ks","default":"ক্স","rules":[]},{"find":"kh","default":"খ","rules":[]},{"find":"lk","default":"ল্ক","rules":[]},{"find":"lg","default":"ল্গ","rules":[]},{"find":"lT","default":"ল্ট","rules":[]},{"find":"lD","default":"ল্ড","rules":[]},{"find":"lp","default":"ল্প","rules":[]},{"find":"lv","default":"ল্ভ","rules":[]},{"find":"lm","default":"ল্ম","rules":[]},{"find":"ll","default":"ল্ল","rules":[]},{"find":"lb","default":"ল্ব","rules":[]},{"find":"mn","default":"ম্ন","rules":[]},{"find":"mp","default":"ম্প","rules":[]},{"find":"mv","default":"ম্ভ","rules":[]},{"find":"mm","default":"ম্ম","rules":[]},{"find":"ml","default":"ম্ল","rules":[]},{"find":"mb","default":"ম্ব","rules":[]},{"find":"mf","default":"ম্ফ","rules":[]},{"find":"nj","default":"ঞ্জ","rules":[]},{"find":"Ng","default":"ঙ","rules":[]},{"find":"NG","default":"ঞ","rules":[]},{"find":"nk","default":"ঙ্ক","rules":[]},{"find":"ng","default":"ং","rules":[]},{"find":"nn","default":"ন্ন","rules":[]},{"find":"NN","default":"ণ্ণ","rules":[]},{"find":"Nn","default":"ণ্ন","rules":[]},{"find":"nm","default":"ন্ম","rules":[]},{"find":"Nm","default":"ণ্ম","rules":[]},{"find":"nd","default":"ন্দ","rules":[]},{"find":"nT","default":"ন্ট","rules":[]},{"find":"NT","default":"ণ্ট","rules":[]},{"find":"nD","default":"ন্ড","rules":[]},{"find":"ND","default":"ণ্ড","rules":[]},{"find":"nt","default":"ন্ত","rules":[]},{"find":"ns","default":"ন্স","rules":[]},{"find":"nc","default":"ঞ্চ","rules":[]},{"find":"O`","default":"ো","rules":[]},{"find":"OI","default":"ৈ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঐ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঐ"}]},{"find":"OU","default":"ৌ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঔ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঔ"}]},{"find":"pT","default":"প্ট","rules":[]},{"find":"pt","default":"প্ত","rules":[]},{"find":"pn","default":"প্ন","rules":[]},{"find":"pp","default":"প্প","rules":[]},{"find":"pl","default":"প্ল","rules":[]},{"find":"ps","default":"প্স","rules":[]},{"find":"ph","default":"ফ","rules":[]},{"find":"fl","default":"ফ্ল","rules":[]},{"find":"rZ","default":"র\u200d্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"ry","default":"র\u200d্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"rr","default":"রর","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Vowel"},{"type":"SuffixIsNot","scope":"Char","val":"r"},{"type":"SuffixIsNot","scope":"Punctuation"}],"replace":"র্"},{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"}],"replace":"্রর"}]},{"find":"Rg","default":"ড়্গ","rules":[]},{"find":"Rh","default":"ঢ়","rules":[]},{"find":"sk","default":"স্ক","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"sT","default":"স্ট","rules":[]},{"find":"st","default":"স্ত","rules":[]},{"find":"sn","default":"স্ন","rules":[]},{"find":"sp","default":"স্প","rules":[]},{"find":"sf","default":"স্ফ","rules":[]},{"find":"sm","default":"স্ম","rules":[]},{"find":"sl","default":"স্ল","rules":[]},{"find":"sh","default":"শ","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"St","default":"শ্ত","rules":[]},{"find":"Sn","default":"শ্ন","rules":[]},{"find":"Sm","default":"শ্ম","rules":[]},{"find":"Sl","default":"শ্ল","rules":[]},{"find":"Sh","default":"ষ","rules":[]},{"find":"oo","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"o`","default":"","rules":[]},{"find":"oZ","default":"অ্য","rules":[]},{"find":"TT","default":"ট্ট","rules":[]},{"find":"Tm","default":"ট্ম","rules":[]},{"find":"Th","default":"ঠ","rules":[]},{"find":"tn","default":"ত্ন","rules":[]},{"find":"tm","default":"ত্ম","rules":[]},{"find":"th","default":"থ","rules":[]},{"find":"tt","default":"ত্ত","rules":[]},{"find":"aZ","default":"অ্যা","rules":[]},{"find":"AZ","default":"অ্যা","rules":[]},{"find":"a`","default":"া","rules":[]},{"find":"A`","default":"া","rules":[]},{"find":"i`","default":"ি","rules":[]},{"find":"I`","default":"ী","rules":[]},{"find":"u`","default":"ু","rules":[]},{"find":"U`","default":"ূ","rules":[]},{"find":"ee","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"e`","default":"ে","rules":[]},{"find":":`","default":":","rules":[]},{"find":"^`","default":"^","rules":[]},{"find":",,","default":"্\u200c","rules":[]},{"find":"b","default":"ব","rules":[]},{"find":"v","default":"ভ","rules":[]},{"find":"c","default":"চ","rules":[]},{"find":"D","default":"ড","rules":[]},{"find":"d","default":"দ","rules":[]},{"find":".","default":"।","rules":[{"matches":[{"type":"SuffixIs","scope":"Number"}],"replace":"."}]},{"find":"g","default":"গ","rules":[]},{"find":"G","default":"গ","rules":[]},{"find":"h","default":"হ","rules":[]},{"find":"j","default":"জ","rules":[]},{"find":"J","default":"জ","rules":[]},{"find":"k","default":"ক","rules":[]},{"find":"l","default":"ল","rules":[]},{"find":"m","default":"ম","rules":[]},{"find":"0","default":"০","rules":[]},{"find":"1","default":"১","rules":[]},{"find":"2","default":"২","rules":[]},{"find":"3","default":"৩","rules":[]},{"find":"4","default":"৪","rules":[]},{"find":"5","default":"৫","rules":[]},{"find":"6","default":"৬","rules":[]},{"find":"7","default":"৭","rules":[]},{"find":"8","default":"৮","rules":[]},{"find":"9","default":"৯","rules":[]},{"find":"n","default":"ন","rules":[]},{"find":"N","default":"ণ","rules":[]},{"find":"O","default":"ো","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ও"}]},{"find":"f","default":"ফ","rules":[]},{"find":"p","default":"প","rules":[]},{"find":"R","default":"ড়","rules":[]},{"find":"r","default":"র","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"},{"type":"PrefixIsNot","scope":"Char","val":"Z"}],"replace":"্র"}]},{"find":"s","default":"স","rules":[]},{"find":"S","default":"শ","rules":[]},{"find":"o","default":"","rules":[{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIsNot","scope":"Char","val":"o"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIs","scope":"Char","val":"o"}],"replace":"অ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"অ"}]},{"find":"T","default":"ট","rules":[]},{"find":"t","default":"ত","rules":[]},{"find":"a","default":"া","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"},{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"য়া"},{"matches":[{"type":"PrefixIs","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"}]},{"find":"i","default":"ি","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"}]},{"find":"I","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"u","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"U","default":"ূ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"}]},{"find":"e","default":"ে","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"}]},{"find":"z","default":"য","rules":[]},{"find":"Z","default":"্য","rules":[]},{"find":"y","default":"্য","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Punctuation"}],"replace":"য়"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ইয়"}]},{"find":"Y","default":"য়","rules":[]},{"find":"q","default":"ক","rules":[]},{"find":"w","default":"ও","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIs","scope":"Vowel"}],"replace":"ওয়"},{"matches":[{"type":"PrefixIs","scope":"Consonant"}],"replace":"্ব"}]},{"find":"x","default":"ক্স","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"এক্স"}]},{"find":":","default":"ঃ","rules":[]},{"find":"^","default":"ঁ","rules":[]},{"find":",","default":",","rules":[]},{"find":"$","default":"৳","rules":[]},{"find":"`","default":"","rules":[]}]')
AVRO_DICTIONARY_DATA = json.loads(r'{"ami":["আমি","আম","আমায়","আমেরিকায়","আমার"],"amader":["আমাদের","আমোদ","আমড়া"],"amar":["আমার","আমরা","অমর"],"amra":["আমরা"],"amake":["আমাকে"],"tumi":["তুমি","তোমরা","তোমার"],"tomader":["তোমাদের"],"tomar":["তোমার"],"tomake":["তোমাকে"],"tomay":["তোমায়","তোমাকে"],"apni":["আপনি","আপনে","আপ্নি"],"apnader":["আপনাদের"],"apnar":["আপনার"],"apnake":["আপনাকে"],"she":["সে","শে"],"tini":["তিনি"],"tara":["তারা"],"tader":["তাদের"],"taderke":["তাদেরকে"],"ora":["ওরা"],"oder":["ওদের"],"era":["এরা"],"eder":["এদের"],"kemon":["কেমন","কেমনে"],"achen":["আছেন","আছি","আছে"],"achi":["আছি"],"ache":["আছে"],"achilo":["ছিল","আছিল"],"chilo":["ছিল"],"chilam":["ছিলাম"],"chile":["ছিলে"],"chilen":["ছিলেন"],"bhalo":["ভালো","ভাল","ভালা"],"valo":["ভালো","ভাল"],"bhalobashi":["ভালোবাসি","ভালোবাসা"],"valobashi":["ভালোবাসি"],"bhalobasha":["ভালোবাসা","ভালোবাসায়"],"valobasha":["ভালোবাসা"],"dhonnobad":["ধন্যবাদ","ধন্য","ধন"],"bangla":["বাংলা","বাঙলা","বাঙালি","বাংলাদেশ"],"bangladesh":["বাংলাদেশ","বাংলাদেশী"],"banglay":["বাংলায়","বাংলায়","বাঙলায়"],"shonar":["সোনার","শোনার","সুন্দর"],"sonar":["সোনার"],"gan":["গান","গণ","জ্ঞান"],"gai":["গাই","গায়ে"],"bongo":["বঙ্গ","বঙ্গবন্ধু","বঙ্গোপসাগর"],"lekho":["লেখো","লেখা","লেখক"],"likhi":["লিখি"],"likhte":["লিখতে"],"lekha":["লেখা"],"onek":["অনেক","অনেকে","অনুপ"],"shob":["সব","শব","সবাই"],"sob":["সব","সবাই"],"shobai":["সবাই"],"sobai":["সবাই"],"shobar":["সবার","শোবার"],"sobar":["সবার"],"shobaike":["সবাইকে"],"shanti":["শান্তি","শান্ত"],"kolkata":["কলকাতা","কলিকাতা"],"dhaka":["ঢাকা","ঢাকাই","ঢাক"],"robindronath":["রবীন্দ্রনাথ","রবি","রব"],"kazi":["কাজী","কাজি"],"nazrul":["নজরুল"],"koto":["কত","কতো"],"kichu":["কিছু","কিছুই"],"desh":["দেশ","দেশে","দেশের"],"deshe":["দেশে"],"desher":["দেশের"],"manush":["মানুষ","মানুষের","মানুষকে"],"manushe":["মানুষে"],"manusher":["মানুষের"],"bondhu":["বন্ধু","বন্ধুরা","বন্ধুর"],"bondhura":["বন্ধুরা"],"khabar":["খাবার","খবর"],"khobor":["খবর","খবরে"],"shundor":["সুন্দর","সুন্দরী"],"sundor":["সুন্দর"],"ranna":["রান্না","রান্নাঘর"],"kothay":["কোথায়","কথায়"],"shomoy":["সময়","সাময়িক"],"somoy":["সময়"],"protidin":["প্রতিদিন"],"notun":["নতুন","নূতন"],"purono":["পুরোনো","পুরনো"],"shobdo":["শব্দ","শব্দকোষ"],"sobdo":["শব্দ"],"ki":["কি","কী"],"keno":["কেন","কেনো"],"kobe":["কবে"],"kothao":["কোথাও"],"kokhon":["কখন","কখনো"],"ekhon":["এখন","এখনো"],"tokhon":["তখন","তখনো"],"jokhon":["যখন","যখনই"],"ei":["এই"],"oi":["ওই","ঐ"],"shei":["সেই"],"je":["যে","যেসব"],"o":["ও"],"ebong":["এবং"],"ar":["আর","আরও"],"kintu":["কিন্তু"],"ba":["বা"],"othoba":["অথবা"],"na":["না","নাই"],"hacche":["হচ্ছে"],"hocche":["হচ্ছে"],"hobe":["হবে","হবেন"],"hobar":["হবার"],"hoyeche":["হয়েছে"],"kaj":["কাজ","কাজে"],"kaje":["কাজে"],"basha":["বাসা","ভাষা"],"bhasha":["ভাষা","ভাষায়"],"bari":["বাড়ি","বারি"],"ghor":["ঘর","ঘরে"],"boi":["বই","বইয়ের"],"kotha":["কথা","কথায়"],"shune":["শুনে","শুনেছি"],"shunbo":["শুনব","শুনবো"],"shunte":["শুনতে"],"shuni":["শুনি"],"dekhe":["দেখে","দেখেছি"],"dekha":["দেখা","দেখার"],"dekho":["দেখো","দেখ"],"dekhi":["দেখি"],"dekhte":["দেখতে"],"ashun":["আসুন"],"ashbo":["আসব","আসবো"],"ashchi":["আসছি"],"aschi":["আসছি"],"ashlam":["আসলাম"],"jao":["যাও"],"jai":["যাই"],"jacchi":["যাচ্ছি"],"jabo":["যাব","যাবো"],"gelam":["গেলাম"],"geche":["গেছে","গিয়েছে"],"korbo":["করব","করবো"],"korchi":["করছি"],"kori":["করি"],"koro":["করো","কর"],"korben":["করবেন"],"kore":["করে","করেছি"],"korechi":["করেছি"],"shokal":["সকাল","সকালে"],"sokal":["সকাল"],"dupur":["দুপুর","দুপুরে"],"shondha":["সন্ধ্যা","সন্ধ্যায়"],"sondha":["সন্ধ্যা"],"rat":["রাত","রাতে"],"din":["দিন","দিনে"],"mash":["মাস","মাসে"],"bochor":["বছর","বছরে"],"mon":["মন","মনে"],"mone":["মনে","মনেও"],"janina":["জানিনা","জানি না"],"parina":["পারিনা","পারি না"],"pari":["পারি"],"parbo":["পারব","পারবো"],"parbe":["পারবে"],"bhabchi":["ভাবছি"],"bhabi":["ভাবি"],"bhabo":["ভাবো","ভাব"],"bhabte":["ভাবতে"],"khub":["খুব","খুবি"],"shotti":["সত্যি","সত্য"],"sotti":["সত্যি"],"shothik":["সঠিক"],"sothik":["সঠিক"],"bhul":["ভুল","ভুলে"],"thik":["ঠিক","ঠিকই"],"shohoj":["সহজ","সহজে"],"sohoj":["সহজ"],"kothin":["কঠিন"],"shobcheye":["সবচেয়ে","সবচাইতে"],"sobcheye":["সবচেয়ে"],"prothom":["প্রথম","প্রথমে"],"shesh":["শেষ","শেষে"],"shuru":["শুরু","শুরুতে"],"suru":["শুরু"],"subheccha":["শুভেচ্ছা"],"shubheccha":["শুভেচ্ছা"],"shuvo":["শুভ"],"shubh":["শুভ"],"computer":["কম্পিউটার"],"keyboard":["কীবোর্ড","কিবোর্ড"],"software":["সফটওয়্যার","সফটওয়্যার"],"native":["নেটিভ"],"apple":["অ্যাপল","আপেল"],"silicon":["সিলিকন"],"mac":["ম্যাক"],"macos":["ম্যাকওএস"],"macbook":["ম্যাকবুক"],"font":["ফন্ট"],"download":["ডাউনলোড"],"install":["ইনস্টল"],"free":["ফ্রি"],"typing":["টাইপিং"],"bengali":["বাঙালি","বেঙ্গলি"],"mehedi":["মেহেদি","মেহেদী"],"shakeel":["শাকিল","শাকীল"],"hya":["হ্যাঁ","হইয়া","হ্যা"],"hea":["হ্যাঁ","হেয়া"],"cad":["চাঁদ"],"chad":["চাঁদ","ছাদ"],"chada":["চাঁদা","ছাদা"],"pac":["পাঁচ"],"pach":["পাঁচ","পাছ"],"hata":["হাঁটা","হাতা","হাটা"],"hatchi":["হাঁটছি"],"hatte":["হাঁটতে"],"hatahati":["হাঁটাহাটি"],"khuj":["খুঁজ"],"khuja":["খোঁজা","খুঁজা"],"khoja":["খোঁজা"],"khuje":["খুঁজে","খুজে"],"khuji":["খুঁজি"],"khujchi":["খুঁজছি"],"khujcho":["খুঁজছো"],"khujchen":["খুঁজছেন"],"khujte":["খুঁজতে","খুজতে"],"khujbo":["খুঁজব","খুঁজবো"],"dhadha":["ধাঁধা","ধাধা"],"aka":["আঁকা","আকা"],"aki":["আঁকি"],"ake":["আঁকে"],"akchi":["আঁকছি"],"akte":["আঁকতে"],"akbo":["আঁকব","আঁকবো"],"bash":["বাঁশ","বাস","বাশ"],"has":["হাঁস","হাস"],"hash":["হাঁস","হাশ"],"hasi":["হাসি","হাঁসি"],"fapa":["ফাঁপা"],"fad":["ফাঁদ"],"fak":["ফাঁক"],"fashi":["ফাঁসি","ফাসি"],"jhap":["ঝাঁপ"],"chapa":["চাঁপা","চাপা"],"dhoya":["ধোঁয়া","ধোয়া"],"jhok":["ঝোঁক"],"bothe":["বঁটি"],"boti":["বঁটি","বটি"],"kacha":["কাঁচা","কাচা"],"shakha":["শাঁখা","শাখা"],"ghata":["ঘাঁটা","ঘাটা"],"chata":["ছাঁটা","ছাটা"],"gaye":["গাঁয়ে","গায়ে"],"badha":["বাধা","বাঁধা"],"dat":["দাঁত"],"idur":["ইঁদুর"],"katha":["কাঁথা","কথা"],"kathal":["কাঁঠাল"]}')

def _conditional_lowercase(c: str) -> str:
    lc = c.lower()
    return c if lc in ('o', 'i', 'u', 'd', 'g', 'j', 'n', 'r', 's', 't', 'y', 'z') else lc

def _is_vowel(c: str) -> bool:
    return c in 'aeiouAEIOU'

def _is_consonant(c: str) -> bool:
    return not _is_vowel(c) and (('a' <= c <= 'z') or ('A' <= c <= 'Z'))

def _is_punctuation(c: str) -> bool:
    return not (('a' <= c <= 'z') or ('A' <= c <= 'Z'))

def _is_digit(c: str) -> bool:
    return '0' <= c <= '9'

def _match_condition(cond: dict, prefix: str, suffix: str) -> bool:
    is_prefix = cond['type'] in ('PrefixIs', 'PrefixIsNot')
    is_pos = cond['type'] in ('PrefixIs', 'SuffixIs')
    ch = prefix if is_prefix else suffix
    scope = cond['scope']
    if scope == 'Vowel': ok = _is_vowel(ch)
    elif scope == 'Consonant': ok = _is_consonant(ch)
    elif scope == 'Punctuation': ok = _is_punctuation(ch)
    elif scope == 'Number': ok = _is_digit(ch)
    elif scope == 'Char': ok = (ch == cond.get('val'))
    else: ok = False
    return ok if is_pos else not ok

def _get_replacement(pat: dict, prefix: str, suffix: str) -> str:
    for rule in pat.get('rules', []):
        if all(_match_condition(m, prefix, suffix) for m in rule.get('matches', [])):
            return rule['replace']
    return pat['default']

class AvroPhoneticEngine:
    def __init__(self):
        self.patterns = AVRO_PATTERNS_DATA
        self.dictionary = AVRO_DICTIONARY_DATA

    @lru_cache(maxsize=4096)
    def convert_word(self, raw: str) -> str:
        if not raw:
            return ''
        inp = ''.join(_conditional_lowercase(c) for c in raw)
        prefix = ' '
        out = ''
        i = 0
        n = len(inp)
        while i < n:
            sub = inp[i:]
            matched = None
            for p in self.patterns:
                if sub.startswith(p['find']):
                    matched = p
                    break
            if matched:
                flen = len(matched['find'])
                suffix = inp[i + flen] if (i + flen < n) else ' '
                out += _get_replacement(matched, prefix, suffix)
                prefix = matched['find'][-1]
                i += flen
            else:
                prefix = inp[i]
                out += prefix
                i += 1
        return out

    @lru_cache(maxsize=4096)
    def _get_candidates_cached(self, word: str) -> tuple:
        cleaned = (word or '').strip()
        if not cleaned:
            return ()

        # 1. OmicronLab Punctuation Padding Isolator
        punct_prefix, stem, punct_suffix = separate_padding(cleaned)
        if not stem:
            return (cleaned,)

        # 2. Case Normalizer
        cased_stem = fix_string_case(stem)
        lower = stem.lower()
        cands = []
        seen = set()

        def add(c):
            if c and c not in seen:
                seen.add(c)
                cands.append(c)

        # 3. Curated Dictionary lookup
        if lower in self.dictionary:
            for c in self.dictionary[lower]:
                add(c)

        # 4. Autocorrect & English Loanwords (OmicronLab autodict)
        if lower in AUTOCORRECT_LOANWORDS:
            add(AUTOCORRECT_LOANWORDS[lower])

        # 5. Rule-based phonetic conversion
        rule_based = self.convert_word(cased_stem)
        add(rule_based)

        # 6. Fallback variations (TitleCase, Sibilant s/sh variants)
        if len(cands) < 5 and stem:
            add(self.convert_word(stem[0].upper() + stem[1:]))
        if len(cands) < 5:
            if 'sh' in lower:
                add(self.convert_word(re.sub(r'sh', 's', stem, flags=re.IGNORECASE)))
            elif 's' in lower:
                add(self.convert_word(re.sub(r's', 'sh', stem, flags=re.IGNORECASE)))
        add(stem)

        # Re-attach isolated punctuation padding
        return tuple(f"{punct_prefix}{c}{punct_suffix}" for c in cands[:5])

    def get_candidates(self, word: str) -> list:
        return list(self._get_candidates_cached(word))

BENGALI_DIGITS = {
    "0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
    "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯",
}


# Virtual-Key and Hook Constants (defined globally for cross-platform headless testing)
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_UP = 0x26
VK_DOWN = 0x28
VK_F12 = 0x7B

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
LLKHF_INJECTED = 0x00000010

# Win32 Candidate HUD Window Styles and Messages
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_POPUP = 0x80000000
SW_SHOWNOACTIVATE = 4
SW_HIDE = 0
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST = -1
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014
WM_DESTROY = 0x0002
WM_MOUSEACTIVATE = 0x0021
MA_NOACTIVATE = 3
WM_LBUTTONDOWN = 0x0201
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
CS_DROPSHADOW = 0x00020000
TRANSPARENT = 1
DT_LEFT = 0x00000000
DT_TOP = 0x00000000
DT_SINGLELINE = 0x00000020
DT_VCENTER = 0x00000004
DT_NOPREFIX = 0x00000800
SPI_GETWORKAREA = 0x0030
SRCCOPY = 0x00CC0020

# Win32 Structures and API Functions for Keyboard Injection and Candidate HUD
if sys.platform == "win32":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32

    # Accurate 64-bit Win32 types
    wintypes.HMODULE = ctypes.c_void_p
    wintypes.HHOOK = ctypes.c_void_p

    class POINT(ctypes.Structure):
        _fields_ = [
            ("x", wintypes.LONG),
            ("y", wintypes.LONG),
        ]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", RECT),
        ]

    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hdc", wintypes.HDC),
            ("fErase", wintypes.BOOL),
            ("rcPaint", RECT),
            ("fRestore", wintypes.BOOL),
            ("fIncUpdate", wintypes.BOOL),
            ("rgbReserved", ctypes.c_byte * 32),
        ]

    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HICON),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
            ("hIconSm", wintypes.HICON),
        ]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUT(ctypes.Structure):
        class _INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]
        _anonymous_ = ("u",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("u", _INPUT_UNION),
        ]

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

    # Win32 API Explicit Signatures (prevents 64-bit handle truncation / error 126)
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE

    kernel32.SetConsoleCtrlHandler.argtypes = [ctypes.c_void_p, wintypes.BOOL]
    kernel32.SetConsoleCtrlHandler.restype = wintypes.BOOL

    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HMODULE, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = wintypes.HHOOK

    user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallNextHookEx.restype = ctypes.c_ssize_t

    user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT

    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.PostQuitMessage.restype = None

    user32.GetKeyState.argtypes = [ctypes.c_int]
    user32.GetKeyState.restype = ctypes.c_short

    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short

    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = wintypes.BOOL

    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.TranslateMessage.restype = wintypes.BOOL

    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = ctypes.c_ssize_t

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL

    user32.GetCaretPos.argtypes = [ctypes.POINTER(POINT)]
    user32.GetCaretPos.restype = wintypes.BOOL

    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
    user32.ClientToScreen.restype = wintypes.BOOL

    user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL

    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL

    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetClientRect.restype = wintypes.BOOL

    user32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
    user32.SystemParametersInfoW.restype = wintypes.BOOL

    user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
    user32.RegisterClassExW.restype = wintypes.ATOM

    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
    ]
    user32.CreateWindowExW.restype = wintypes.HWND

    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT
    ]
    user32.SetWindowPos.restype = wintypes.BOOL

    user32.InvalidateRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT), wintypes.BOOL]
    user32.InvalidateRect.restype = wintypes.BOOL

    user32.UpdateWindow.argtypes = [wintypes.HWND]
    user32.UpdateWindow.restype = wintypes.BOOL

    user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
    user32.BeginPaint.restype = wintypes.HDC

    user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
    user32.EndPaint.restype = wintypes.BOOL

    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = ctypes.c_ssize_t

    user32.FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(RECT), wintypes.HBRUSH]
    user32.FillRect.restype = ctypes.c_int

    user32.FrameRect.argtypes = [wintypes.HDC, ctypes.POINTER(RECT), wintypes.HBRUSH]
    user32.FrameRect.restype = ctypes.c_int

    user32.DrawTextW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(RECT), wintypes.UINT]
    user32.DrawTextW.restype = ctypes.c_int

    # GDI32 Signatures
    gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]
    gdi32.CreateSolidBrush.restype = wintypes.HBRUSH

    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL

    gdi32.CreateFontW.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPCWSTR
    ]
    gdi32.CreateFontW.restype = wintypes.HFONT

    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ

    gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
    gdi32.SetTextColor.restype = wintypes.COLORREF

    gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
    gdi32.SetBkMode.restype = ctypes.c_int

    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC

    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP

    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL

    gdi32.BitBlt.argtypes = [
        wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD
    ]
    gdi32.BitBlt.restype = wintypes.BOOL

    gdi32.RoundRect.argtypes = [
        wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int
    ]
    gdi32.RoundRect.restype = wintypes.BOOL

    gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.COLORREF]
    gdi32.CreatePen.restype = wintypes.HPEN


def replace_inline_text(erase_count: int, new_text: str):
    """Atomically erases erase_count characters and injects new_text in one SendInput batch."""
    if sys.platform != "win32":
        return

    inputs = []
    # 1. Backspaces to erase previously injected text
    for _ in range(erase_count):
        down = INPUT()
        down.type = INPUT_KEYBOARD
        down.ki.wVk = VK_BACK
        down.ki.wScan = 0
        down.ki.dwFlags = 0
        down.ki.time = 0
        down.ki.dwExtraInfo = 0
        inputs.append(down)

        up = INPUT()
        up.type = INPUT_KEYBOARD
        up.ki.wVk = VK_BACK
        up.ki.wScan = 0
        up.ki.dwFlags = KEYEVENTF_KEYUP
        up.ki.time = 0
        up.ki.dwExtraInfo = 0
        inputs.append(up)

    # 2. Unicode characters for new text
    for ch in new_text:
        cp = ord(ch)
        if cp <= 0xFFFF:
            code_units = [cp]
        else:
            cp -= 0x10000
            code_units = [0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF)]
        for cu in code_units:
            down = INPUT()
            down.type = INPUT_KEYBOARD
            down.ki.wVk = 0
            down.ki.wScan = cu
            down.ki.dwFlags = KEYEVENTF_UNICODE
            down.ki.time = 0
            down.ki.dwExtraInfo = 0
            inputs.append(down)

            up = INPUT()
            up.type = INPUT_KEYBOARD
            up.ki.wVk = 0
            up.ki.wScan = cu
            up.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            up.ki.time = 0
            up.ki.dwExtraInfo = 0
            inputs.append(up)

    if inputs:
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        res = user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
        if res != n:
            err = kernel32.GetLastError()
            log_msg(f"SendInput injected {res}/{n} events (error {err})")
        return res


def send_unicode_string(text: str):
    """Injects a Unicode string into the active window using SendInput."""
    replace_inline_text(0, text)


class BongoCandidateHUD:
    """
    Floating Candidate HUD Window for Windows.
    Renders live Avro phonetic suggestions near the typing cursor/caret.
    Uses native Win32 popup window with WS_EX_NOACTIVATE to avoid stealing focus.
    """
    def __init__(self, settings: dict, on_candidate_clicked=None):
        self.settings = settings
        self.on_candidate_clicked = on_candidate_clicked
        self.buffer = ""
        self.candidates = []
        self.selected_index = 0
        self.is_visible = False
        self.hwnd = None
        self._wnd_proc_ref = None
        self._font_bengali = None
        self._font_bengali_bold = None
        self._font_ui = None
        self._font_ui_bold = None
        self._font_header = None
        self._bg_brush = None
        self._border_pen = None
        self._active_brush = None
        self._active_border_brush = None
        self._sep_brush = None
        self._last_caret_pos = (200, 200)

        if sys.platform == "win32":
            self._init_win32()

    def _create_font(self, name: str, size: int, bold: bool = False):
        if sys.platform != "win32":
            return None
        weight = 700 if bold else 400
        height = -int(size * 96 / 72)
        return gdi32.CreateFontW(
            height, 0, 0, 0, weight,
            0, 0, 0,
            1,  # DEFAULT_CHARSET
            0, 0,
            5,  # CLEARTYPE_QUALITY
            0,
            name
        )

    def _init_win32(self):
        if sys.platform != "win32" or self.hwnd is not None:
            return
        try:
            self._wnd_proc_ref = WNDPROC(self._wnd_proc)
            hinst = kernel32.GetModuleHandleW(None)
            cls_name = "BongoCandidateHUDClass"

            wc = WNDCLASSEXW()
            wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
            wc.style = CS_HREDRAW | CS_VREDRAW | CS_DROPSHADOW
            wc.lpfnWndProc = self._wnd_proc_ref
            wc.cbClsExtra = 0
            wc.cbWndExtra = 0
            wc.hInstance = hinst
            wc.hIcon = None
            wc.hCursor = None
            wc.hbrBackground = None
            wc.lpszMenuName = None
            wc.lpszClassName = cls_name
            wc.hIconSm = None

            user32.RegisterClassExW(ctypes.byref(wc))

            ex_style = WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            style = WS_POPUP

            self.hwnd = user32.CreateWindowExW(
                ex_style,
                cls_name,
                "BongoCandidateHUD",
                style,
                -1000, -1000, 260, 150,
                None, None, hinst, None
            )

            font_name = self.settings.get("candidate_font", "Noto Sans Bengali")
            if font_name == "System Font (Default)":
                font_name = "Segoe UI"
            font_size = self.settings.get("candidate_font_size", 16)

            self._font_bengali = self._create_font(font_name, font_size, bold=False)
            self._font_bengali_bold = self._create_font(font_name, font_size, bold=True)
            self._font_ui = self._create_font("Segoe UI", 11, bold=False)
            self._font_ui_bold = self._create_font("Segoe UI", 11, bold=True)
            self._font_header = self._create_font("Segoe UI", 10, bold=False)

            self._bg_brush = gdi32.CreateSolidBrush(0x131111)           # #111113
            self._border_pen = gdi32.CreatePen(0, 1, 0x332E2E)          # #2e2e33
            self._active_brush = gdi32.CreateSolidBrush(0x382323)       # #232338
            self._active_border_brush = gdi32.CreateSolidBrush(0xF16663)  # #6366f1
            self._sep_brush = gdi32.CreateSolidBrush(0x2E2E33)          # #2e2e33

            log_msg("Bongo Candidate HUD window initialized.")
        except Exception as e:
            log_msg(f"Could not initialize Bongo Candidate HUD: {e}")
            self.hwnd = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_MOUSEACTIVATE:
            return MA_NOACTIVATE
        elif msg == WM_ERASEBKGND:
            return 1
        elif msg == WM_PAINT:
            self._paint(hwnd)
            return 0
        elif msg == WM_LBUTTONDOWN:
            click_y = (lparam >> 16) & 0xFFFF
            row_y = click_y - 31
            row_idx = row_y // 30
            if 0 <= row_idx < len(self.candidates):
                if self.on_candidate_clicked:
                    self.on_candidate_clicked(row_idx)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _paint(self, hwnd):
        if sys.platform != "win32":
            return
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        if not hdc:
            return

        rc = RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rc))
        w = max(rc.right - rc.left, 240)
        h = max(rc.bottom - rc.top, 60)

        mem_dc = gdi32.CreateCompatibleDC(hdc)
        mem_bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
        old_bmp = gdi32.SelectObject(mem_dc, mem_bmp)

        # 1. Fill background
        user32.FillRect(mem_dc, ctypes.byref(rc), self._bg_brush)

        # 2. Border
        old_pen = gdi32.SelectObject(mem_dc, self._border_pen)
        old_brush = gdi32.SelectObject(mem_dc, self._bg_brush)
        gdi32.RoundRect(mem_dc, 0, 0, w, h, 10, 10)

        gdi32.SetBkMode(mem_dc, TRANSPARENT)

        # 3. Header bar: Latin buffer and Avro Bengali tag
        gdi32.SelectObject(mem_dc, self._font_header)
        gdi32.SetTextColor(mem_dc, 0xF88C81)  # #818cf8
        aux_text = f"{self.buffer}  ·  বাংলা"
        rc_aux = RECT(12, 6, w - 12, 24)
        user32.DrawTextW(mem_dc, aux_text, -1, ctypes.byref(rc_aux), DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX)

        # Header divider line
        rc_sep = RECT(8, 27, w - 8, 28)
        user32.FillRect(mem_dc, ctypes.byref(rc_sep), self._sep_brush)

        # 4. Candidates list
        start_y = 31
        row_h = 30
        for i, cand in enumerate(self.candidates[:9]):
            y = start_y + (i * row_h)
            is_active = (i == self.selected_index)

            rc_row = RECT(6, y, w - 6, y + row_h - 2)
            if is_active:
                user32.FillRect(mem_dc, ctypes.byref(rc_row), self._active_brush)
                user32.FrameRect(mem_dc, ctypes.byref(rc_row), self._active_border_brush)

            # Shortcut number [1], [2]...
            num_text = f"{i + 1}"
            rc_num = RECT(14, y, 32, y + row_h - 2)
            gdi32.SelectObject(mem_dc, self._font_ui_bold if is_active else self._font_ui)
            gdi32.SetTextColor(mem_dc, 0xF88C81 if is_active else 0x7A7171)
            user32.DrawTextW(mem_dc, num_text, -1, ctypes.byref(rc_num), DT_LEFT | DT_VCENTER | DT_SINGLELINE)

            # Bengali candidate word
            rc_cand = RECT(36, y, w - 12, y + row_h - 2)
            gdi32.SelectObject(mem_dc, self._font_bengali_bold if is_active else self._font_bengali)
            gdi32.SetTextColor(mem_dc, 0xFFFFFF if is_active else 0xD8D4D4)
            user32.DrawTextW(mem_dc, cand, -1, ctypes.byref(rc_cand), DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX)

        gdi32.BitBlt(hdc, 0, 0, w, h, mem_dc, 0, 0, SRCCOPY)

        gdi32.SelectObject(mem_dc, old_bmp)
        gdi32.SelectObject(mem_dc, old_pen)
        gdi32.SelectObject(mem_dc, old_brush)
        gdi32.DeleteObject(mem_bmp)
        gdi32.DeleteDC(mem_dc)
        user32.EndPaint(hwnd, ctypes.byref(ps))

    def _get_caret_screen_pos(self):
        if sys.platform != "win32":
            return self._last_caret_pos
        try:
            # 1. Try GetGUIThreadInfo on active foreground thread
            hwnd_fg = user32.GetForegroundWindow()
            if hwnd_fg:
                tid = user32.GetWindowThreadProcessId(hwnd_fg, None)
                gui_info = GUITHREADINFO()
                gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
                if user32.GetGUIThreadInfo(tid, ctypes.byref(gui_info)):
                    if gui_info.hwndCaret and (gui_info.rcCaret.right > gui_info.rcCaret.left or gui_info.rcCaret.bottom > gui_info.rcCaret.top):
                        pt = POINT(gui_info.rcCaret.left, gui_info.rcCaret.bottom)
                        user32.ClientToScreen(gui_info.hwndCaret, ctypes.byref(pt))
                        if pt.x > 0 or pt.y > 0:
                            return pt.x, pt.y
                    elif gui_info.hwndFocus:
                        rc_focus = RECT()
                        if user32.GetWindowRect(gui_info.hwndFocus, ctypes.byref(rc_focus)):
                            return rc_focus.left + 15, rc_focus.bottom

            # 2. Try GetCaretPos
            pt_caret = POINT()
            if user32.GetCaretPos(ctypes.byref(pt_caret)):
                if pt_caret.x > 0 or pt_caret.y > 0:
                    hwnd_target = user32.GetFocus() or hwnd_fg
                    if hwnd_target:
                        user32.ClientToScreen(hwnd_target, ctypes.byref(pt_caret))
                        return pt_caret.x, pt_caret.y + 18

            # 3. Fallback to mouse cursor position
            pt_cursor = POINT()
            if user32.GetCursorPos(ctypes.byref(pt_cursor)):
                if pt_cursor.x > 0 or pt_cursor.y > 0:
                    return pt_cursor.x + 8, pt_cursor.y + 20

            # 4. Fallback to active window bounds
            if hwnd_fg:
                rc_win = RECT()
                if user32.GetWindowRect(hwnd_fg, ctypes.byref(rc_win)):
                    return rc_win.left + 50, rc_win.top + 100
        except Exception:
            pass
        return self._last_caret_pos

    def update(self, buffer: str, candidates: list, selected_index: int = 0):
        self.buffer = buffer or ""
        self.candidates = candidates or []
        self.selected_index = selected_index
        if not self.buffer or not self.candidates:
            self.hide()
            return

        self.is_visible = True
        if sys.platform != "win32" or not self.hwnd:
            return

        count = min(len(self.candidates), 9)
        h = 32 + (count * 30) + 6
        w = 260

        caret_x, caret_y = self._get_caret_screen_pos()
        self._last_caret_pos = (caret_x, caret_y)

        rc_work = RECT()
        user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rc_work), 0)

        x = caret_x
        y = caret_y + 4

        # If HUD extends past bottom of work area, flip above caret
        if y + h > rc_work.bottom:
            y = caret_y - h - 24

        # Keep fully on screen horizontally
        if x + w > rc_work.right:
            x = rc_work.right - w - 8
        if x < rc_work.left:
            x = rc_work.left + 8

        # Keep on screen vertically
        if y < rc_work.top:
            y = rc_work.top + 8

        user32.SetWindowPos(
            self.hwnd,
            HWND_TOPMOST,
            int(x), int(y), int(w), int(h),
            SWP_NOACTIVATE | SWP_SHOWWINDOW
        )
        user32.InvalidateRect(self.hwnd, None, True)
        user32.UpdateWindow(self.hwnd)

    def hide(self):
        self.is_visible = False
        if sys.platform == "win32" and self.hwnd:
            user32.ShowWindow(self.hwnd, SW_HIDE)

    def destroy(self):
        self.hide()
        if sys.platform == "win32":
            if self.hwnd:
                user32.DestroyWindow(self.hwnd)
                self.hwnd = None
            for font in (self._font_bengali, self._font_bengali_bold, self._font_ui, self._font_ui_bold, self._font_header):
                if font:
                    gdi32.DeleteObject(font)
            for gdi_obj in (self._bg_brush, self._border_pen, self._active_brush, self._active_border_brush, self._sep_brush):
                if gdi_obj:
                    gdi32.DeleteObject(gdi_obj)


class BongoWindowsService:
    def __init__(self):
        self.settings = load_settings()
        self._settings_mtime = 0

        self.bangla_active = True  # Active by default on start; toggled via F12
        self.phonetic_engine = AvroPhoneticEngine()
        self.native = BongoNativeBinding()
        self.engine_ptr = self.native.lib.bongo_engine_new() if (self.native and self.native.lib) else None

        self.buffer = ""
        self.candidates = []
        self.selected_index = 0
        self.preedit_str = ""
        self.last_injected_len = 0

        self.hud = BongoCandidateHUD(self.settings, on_candidate_clicked=self.commit_candidate)

        self.apply_settings()

        self.hook_id = None
        self.hook_proc_ref = None

    def apply_settings(self):
        if not self.engine_ptr or not self.native or not self.native.lib:
            return
        layout = self.settings.get("keyboard_layout", 0)
        mode = self.settings.get("typing_mode", 0)
        emoji = self.settings.get("suggest_emoji", True)
        self.native.lib.bongo_engine_set_layout(self.engine_ptr, layout)
        self.native.lib.bongo_engine_set_mode(self.engine_ptr, mode)
        self.native.lib.bongo_engine_set_emoji(self.engine_ptr, emoji)

    def check_reload_settings(self):
        if CONFIG_FILE.is_file():
            try:
                mtime = CONFIG_FILE.stat().st_mtime
                if mtime > self._settings_mtime:
                    self._settings_mtime = mtime
                    self.settings = load_settings()
                    self.apply_settings()
            except Exception:
                pass

    def toggle_mode(self):
        if self.has_session():
            self.commit_candidate(self.selected_index)
        self.hud.hide()
        self.selected_index = 0
        self.bangla_active = not self.bangla_active
        mode_str = "Bangla" if self.bangla_active else "English"
        log_msg(f"Bongo: Switched to {mode_str} Mode")
        sys.stdout.write(f"Bongo: Switched to {mode_str} Mode\n")
        sys.stdout.flush()

    def has_session(self):
        if self.engine_ptr and self.native and self.native.lib:
            return self.native.lib.bongo_engine_has_session(self.engine_ptr)
        return bool(self.buffer)

    def feed_character(self, ch: str):
        self.buffer += ch
        self.selected_index = 0
        if self.engine_ptr and self.native and self.native.lib:
            try:
                cp = ord(ch)
                modifier = 1 if ch.isupper() else 0
                sugg_ptr = self.native.lib.bongo_engine_feed_char(self.engine_ptr, cp, modifier, 0)
                if sugg_ptr:
                    self.update_suggestions(sugg_ptr)
                    self.native.lib.bongo_suggestion_free(sugg_ptr)
                    self._sync_inline_text()
                    if self.settings.get("typing_mode", 0) != 2 and self.candidates:
                        self.hud.update(self.buffer, self.candidates, self.selected_index)
                    return True
            except Exception:
                pass

        # Built-in Avro phonetic transliteration
        self.candidates = self.phonetic_engine.get_candidates(self.buffer)
        self.preedit_str = self.candidates[0] if self.candidates else self.buffer
        self._sync_inline_text()
        if self.settings.get("typing_mode", 0) != 2 and self.candidates:
            self.hud.update(self.buffer, self.candidates, self.selected_index)
        return True

    def _sync_inline_text(self):
        target = self.preedit_str or (self.candidates[0] if self.candidates else "")
        replace_inline_text(self.last_injected_len, target)
        self.last_injected_len = sum(2 if ord(c) > 0xFFFF else 1 for c in target)

    def update_suggestions(self, sugg_ptr):
        count = self.native.lib.bongo_suggestion_count(sugg_ptr)
        self.candidates = []
        for i in range(count):
            c_ptr = self.native.lib.bongo_suggestion_get_candidate(sugg_ptr, i)
            if c_ptr:
                c_str = ctypes.string_at(c_ptr).decode("utf-8", errors="replace")
                self.candidates.append(c_str)
                self.native.lib.bongo_string_free(c_ptr)

        p_ptr = self.native.lib.bongo_suggestion_get_preview(sugg_ptr)
        if p_ptr:
            self.preedit_str = ctypes.string_at(p_ptr).decode("utf-8", errors="replace")
            self.native.lib.bongo_string_free(p_ptr)
        elif self.candidates:
            self.preedit_str = self.candidates[0]
        else:
            self.preedit_str = ""

    def handle_backspace(self):
        self.selected_index = 0
        if self.engine_ptr and self.native and self.native.lib:
            try:
                sugg_ptr = self.native.lib.bongo_engine_backspace(self.engine_ptr, False)
                if sugg_ptr:
                    self.update_suggestions(sugg_ptr)
                    self.native.lib.bongo_suggestion_free(sugg_ptr)
                    self._sync_inline_text()
                    if self.settings.get("typing_mode", 0) != 2 and self.candidates:
                        self.hud.update(self.buffer, self.candidates, self.selected_index)
                    else:
                        self.hud.hide()
                    return
                else:
                    self.clear_session()
                    return
            except Exception:
                pass

        if self.buffer:
            self.buffer = self.buffer[:-1]
            if not self.buffer:
                self.clear_session()
            else:
                self.candidates = self.phonetic_engine.get_candidates(self.buffer)
                self.preedit_str = self.candidates[0] if self.candidates else self.buffer
                self._sync_inline_text()
                if self.settings.get("typing_mode", 0) != 2 and self.candidates:
                    self.hud.update(self.buffer, self.candidates, self.selected_index)
                else:
                    self.hud.hide()

    def commit_candidate(self, index=None):
        if index is None:
            index = self.selected_index
        if 0 <= index < len(self.candidates):
            chosen = self.candidates[index]
            if chosen != self.preedit_str:
                replace_inline_text(self.last_injected_len, chosen)
                self.last_injected_len = sum(2 if ord(c) > 0xFFFF else 1 for c in chosen)
                self.preedit_str = chosen

        if self.engine_ptr and self.native and self.native.lib:
            self.native.lib.bongo_engine_commit(self.engine_ptr, index)
        # Inline text is already on screen, so simply finalize session state
        self.hud.hide()
        self.buffer = ""
        self.candidates = []
        self.selected_index = 0
        self.preedit_str = ""
        self.last_injected_len = 0

    def clear_session(self):
        """Erases any actively composed inline text and resets engine state."""
        self.hud.hide()
        self.selected_index = 0
        if self.last_injected_len > 0:
            replace_inline_text(self.last_injected_len, "")
            self.last_injected_len = 0
        self.reset_session()

    def reset_session(self):
        self.hud.hide()
        self.selected_index = 0
        if self.engine_ptr and self.native and self.native.lib:
            self.native.lib.bongo_engine_reset(self.engine_ptr)
        self.buffer = ""
        self.candidates = []
        self.preedit_str = ""
        self.last_injected_len = 0

    def process_key(self, vk_code: int, is_down: bool, is_shift: bool, is_ctrl: bool, is_alt: bool, is_caps: bool = False) -> bool:
        """
        Returns True if the keystroke was handled/swallowed,
        or False to let it pass through to the system.
        """
        if not is_down:
            return False

        # Toggle shortcut: F12 or Ctrl+Space
        if vk_code == VK_F12 or (is_ctrl and vk_code == VK_SPACE):
            self.toggle_mode()
            return True

        if not self.bangla_active:
            return False

        # Pass through Ctrl or Alt combos (e.g. Ctrl+C, Alt+Tab)
        if is_ctrl or is_alt:
            if self.has_session():
                self.commit_candidate(self.selected_index)
            return False

        # In-session navigation and candidate selection
        if self.has_session():
            if vk_code == VK_ESCAPE:
                self.clear_session()
                return True

            if vk_code == VK_SPACE:
                self.commit_candidate(self.selected_index)
                send_unicode_string(" ")
                return True

            if vk_code == VK_RETURN:
                # Commits active candidate cleanly without inserting an extra newline
                self.commit_candidate(self.selected_index)
                return True

            if vk_code == VK_BACK:
                self.handle_backspace()
                return True

            # Candidate cycling navigation (Down Arrow, Tab -> next candidate)
            if vk_code in (VK_DOWN, VK_TAB):
                if len(self.candidates) > 1:
                    self.selected_index = (self.selected_index + 1) % min(len(self.candidates), 9)
                    chosen = self.candidates[self.selected_index]
                    replace_inline_text(self.last_injected_len, chosen)
                    self.last_injected_len = sum(2 if ord(c) > 0xFFFF else 1 for c in chosen)
                    self.preedit_str = chosen
                    if self.settings.get("typing_mode", 0) != 2:
                        self.hud.update(self.buffer, self.candidates, self.selected_index)
                    return True

            # Candidate cycling navigation (Up Arrow -> previous candidate)
            if vk_code == VK_UP:
                if len(self.candidates) > 1:
                    self.selected_index = (self.selected_index - 1) % min(len(self.candidates), 9)
                    chosen = self.candidates[self.selected_index]
                    replace_inline_text(self.last_injected_len, chosen)
                    self.last_injected_len = sum(2 if ord(c) > 0xFFFF else 1 for c in chosen)
                    self.preedit_str = chosen
                    if self.settings.get("typing_mode", 0) != 2:
                        self.hud.update(self.buffer, self.candidates, self.selected_index)
                    return True

            # Number keys 1-9 for candidate selection if multiple candidates exist (and Shift is not held)
            if not is_shift and 0x31 <= vk_code <= 0x39:
                idx = vk_code - 0x31
                if idx < len(self.candidates) and len(self.candidates) > 1:
                    self.commit_candidate(idx)
                    return True
                else:
                    # Single candidate or index out of range: commit word and type Bengali numeral
                    self.commit_candidate(self.selected_index)
                    digit_char = chr(vk_code)
                    bn_digit = BENGALI_DIGITS.get(digit_char, digit_char)
                    send_unicode_string(bn_digit)
                    return True

            # Digit 0 inside session: commit word and type Bengali numeral '০'
            if not is_shift and vk_code == 0x30:
                self.commit_candidate(self.selected_index)
                send_unicode_string("০")
                return True

            # Period key inside session: commit word and type Bengali Dari (।)
            if not is_shift and vk_code == 0xBE:
                self.commit_candidate(self.selected_index)
                send_unicode_string("।")
                return True

        # Digits 0-9 outside session: convert to Bengali numerals
        if not self.has_session() and not is_shift and 0x30 <= vk_code <= 0x39:
            digit_char = chr(vk_code)
            bn_digit = BENGALI_DIGITS.get(digit_char, digit_char)
            send_unicode_string(bn_digit)
            return True

        # Period outside session converts to Bengali Dari (।)
        if not self.has_session() and not is_shift and vk_code == 0xBE:
            send_unicode_string("।")
            return True

        # Backtick / tilde key (used in Avro phonetic rules, e.g. o`, a`, t``)
        if vk_code == 0xC0 and not is_shift:
            self.feed_character("`")
            return True

        # Shifted symbol keys used in Avro phonetic transliteration
        if is_shift:
            if vk_code == 0x34:  # Shift + 4 -> '$' -> '৳'
                self.feed_character("$")
                return True
            if vk_code == 0x36:  # Shift + 6 -> '^' -> 'ঁ'
                self.feed_character("^")
                return True
            if vk_code == 0xBA:  # Shift + ; -> ':' -> 'ঃ'
                self.feed_character(":")
                return True

        # Process standard alphabet characters (A-Z)
        if 0x41 <= vk_code <= 0x5A:
            is_upper = is_shift ^ is_caps
            char_code = vk_code + (0 if is_upper else 32)
            ch = chr(char_code)
            self.feed_character(ch)
            return True

        # Any unhandled key while in session: commit candidate before letting key pass through
        # (prevents backspacing over punctuation or navigation events on subsequent keystrokes)
        if self.has_session():
            self.commit_candidate(self.selected_index)
            return False

        return False

    def run_windows_hook(self):
        """Sets up Windows low-level keyboard hook and message loop."""
        if sys.platform != "win32":
            log_msg("Bongo Service: Windows environment required for hook loop.")
            return

        log_msg("Installing low-level keyboard hook (WH_KEYBOARD_LL)...")

        def low_level_keyboard_proc(n_code, w_param, l_param):
            try:
                if n_code >= 0 and l_param:
                    hook_data = KBDLLHOOKSTRUCT.from_address(l_param)

                    # Immediately pass through keystrokes injected by SendInput (prevents recursion)
                    if hook_data.flags & LLKHF_INJECTED:
                        return user32.CallNextHookEx(self.hook_id, n_code, w_param, l_param)

                    is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                    vk = hook_data.vkCode

                    VK_CAPITAL = 0x14
                    is_shift = bool((user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) or (user32.GetKeyState(VK_SHIFT) & 0x8000))
                    is_ctrl = bool((user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) or (user32.GetKeyState(VK_CONTROL) & 0x8000))
                    is_alt = bool((user32.GetAsyncKeyState(VK_MENU) & 0x8000) or (user32.GetKeyState(VK_MENU) & 0x8000))
                    is_caps = bool(user32.GetKeyState(VK_CAPITAL) & 0x0001)

                    handled = self.process_key(vk, is_down, is_shift, is_ctrl, is_alt, is_caps)
                    if handled:
                        return 1  # Swallow event
            except (KeyboardInterrupt, SystemExit):
                user32.PostQuitMessage(0)
                return 0
            except Exception as e:
                log_msg(f"Exception in hook proc: {e}")

            return user32.CallNextHookEx(self.hook_id, n_code, w_param, l_param)

        self.hook_proc_ref = HOOKPROC(low_level_keyboard_proc)
        h_mod = kernel32.GetModuleHandleW(None)
        self.hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self.hook_proc_ref,
            h_mod,
            0
        )

        if not self.hook_id:
            err_code = kernel32.GetLastError()
            log_msg(f"Error: Failed to install low-level keyboard hook (code {err_code}).")
            sys.stderr.write(f"Error: Failed to install low-level keyboard hook (code {err_code}).\n")
            return

        log_msg(f"Low-level keyboard hook installed successfully (hook_id={self.hook_id}).")

        def console_ctrl_handler(ctrl_type):
            log_msg(f"Console control signal received ({ctrl_type}), posting quit message.")
            user32.PostQuitMessage(0)
            return 1

        PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
        self._ctrl_handler_ref = PHANDLER_ROUTINE(console_ctrl_handler)
        kernel32.SetConsoleCtrlHandler(self._ctrl_handler_ref, True)

        msg_welcome = "Bongo Windows Service active. Press F12 or Ctrl+Space to toggle Bangla/English.\n"
        log_msg(msg_welcome.strip())
        sys.stdout.write(msg_welcome)
        sys.stdout.flush()

        # Initialize Candidate HUD window on hook thread
        self.hud._init_win32()

        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            log_msg(f"Error in Windows message loop: {e}")
        finally:
            self.hud.destroy()
            if self.hook_id:
                user32.UnhookWindowsHookEx(self.hook_id)
                self.hook_id = None
                log_msg("Unhooked low-level keyboard hook.")


_MUTEX_HANDLE = None

def check_single_instance():
    """Ensures only a single instance of the Bongo Windows service runs concurrently."""
    global _MUTEX_HANDLE
    if sys.platform != "win32":
        return True
    mutex_name = "Local\\BongoWindowsServiceMutex"
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    h_mutex = kernel32.CreateMutexW(None, True, mutex_name)
    ERROR_ALREADY_EXISTS = 183
    last_err = kernel32.GetLastError()
    if last_err == ERROR_ALREADY_EXISTS:
        log_msg("Another instance of Bongo Windows Service is already running.")
        return False
    if not h_mutex:
        log_msg(f"Warning: CreateMutexW returned NULL (error {last_err}), continuing service.")
        return True
    _MUTEX_HANDLE = h_mutex
    log_msg("Acquired single-instance mutex.")
    return True


def main():
    log_msg(f"Bongo Windows Service starting (args: {sys.argv})")

    # If launched interactively without --daemon, launch the settings/welcome window
    if sys.platform == "win32" and "--daemon" not in sys.argv:
        try:
            import subprocess
            candidates = [
                Path(sys.executable).parent / "bongo-settings.exe",
                Path(__file__).resolve().parent.parent / "ui" / "bongo_settings.py",
            ]
            for c in candidates:
                if c.is_file():
                    log_msg(f"Launching settings window: {c}")
                    if c.suffix == ".py":
                        subprocess.Popen([sys.executable, str(c)])
                    else:
                        subprocess.Popen([str(c)])
                    break
        except Exception as e:
            log_msg(f"Warning launching settings UI: {e}")

    if sys.platform == "win32":
        if not check_single_instance():
            log_msg("Bongo Windows Service is already running. Exiting duplicate instance.")
            sys.stdout.write("Bongo Windows Service is already running.\n")
            sys.stdout.flush()
            return

    service = BongoWindowsService()
    if sys.platform == "win32":
        service.run_windows_hook()
    else:
        log_msg("Bongo Windows Service initialized in headless cross-platform mode.")
        sys.stdout.write("Bongo Windows Service initialized in headless cross-platform mode.\n")


if __name__ == "__main__":
    main()

