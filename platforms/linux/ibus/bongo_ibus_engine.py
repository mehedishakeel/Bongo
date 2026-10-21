#!/usr/bin/env python3
"""
Bongo IBus Engine Daemon for Linux
Provides native Avro phonetic Bengali typing on modern Linux desktops (GNOME, KDE, XFCE).
Integrates with IBus input method framework via GObject introspection.
"""

import os
import sys
import json
import re
import ctypes
import time
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

LOG_FILE = Path("/tmp/bongo_ibus.log")

def log_msg(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# Setup GObject Introspection for IBus
try:
    import gi
    gi.require_version('IBus', '1.0')
    from gi.repository import IBus, GLib, GObject
except (ImportError, ValueError):
    IBus = None
    GLib = None
    GObject = None

BaseEngine = IBus.Engine if IBus is not None else object
BaseFactory = IBus.Factory if IBus is not None else object


# Locate libbongo_engine shared library
def find_engine_library():
    search_paths = [
        # Local development / source paths
        Path(__file__).resolve().parent.parent / "engine" / "target" / "release" / "libbongo_engine.so",
        Path(__file__).resolve().parent.parent / "engine" / "target" / "debug" / "libbongo_engine.so",
        # Executable-relative path (e.g. /usr/libexec/.. -> /usr/lib/bongo/libbongo_engine.so)
        Path(__file__).resolve().parent.parent / "lib" / "bongo" / "libbongo_engine.so",
        # User local installation paths
        Path.home() / ".local" / "lib" / "bongo" / "libbongo_engine.so",
        Path.home() / ".local" / "lib" / "libbongo_engine.so",
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

    def get_candidates(self, word: str) -> list:
        cleaned = (word or '').strip()
        if not cleaned:
            return []

        # 1. OmicronLab Punctuation Padding Isolator
        punct_prefix, stem, punct_suffix = separate_padding(cleaned)
        if not stem:
            return [cleaned]

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

        # 4. Autocorrect & Compound expansions (OmicronLab autodict)
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
        return [f"{punct_prefix}{c}{punct_suffix}" for c in cands[:5]]

class BongoNativeBinding:
    """ctypes binding to libbongo_engine.so"""
    def __init__(self):
        lib_path = find_engine_library()
        try:
            self.lib = ctypes.CDLL(lib_path)
            self._setup_signatures()
            log_msg(f"BongoNativeBinding: successfully loaded native engine from '{lib_path}'")
        except (OSError, AttributeError, Exception) as e:
            log_msg(f"BongoNativeBinding: could not load '{lib_path}': {e}. Using built-in Avro engine.")
            self.lib = None
            return

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


def load_settings():
    config_dir = Path.home() / ".config" / "bongo"
    config_file = config_dir / "settings.json"
    defaults = {
        "keyboard_layout": 0,   # 0: Avro Phonetic, 1: National (Bijoy)
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


def extract_char_and_codepoint(keyval):
    """
    Safely extract (char_str, codepoint) from an IBus keyval.
    Handles IBus.keyval_to_unicode returning either a Python str or int in PyGObject.
    Filters out non-printable / control codes (< 0x20 or 0x7F) like BackSpace (0x08).
    """
    if IBus is not None:
        try:
            res = IBus.keyval_to_unicode(keyval)
            if isinstance(res, str):
                if res and res != '\x00':
                    cp = ord(res)
                    if cp >= 0x20 and cp != 0x7f:
                        return res, cp
            elif isinstance(res, int) and res > 0:
                if res >= 0x20 and res != 0x7f:
                    try:
                        return chr(res), res
                    except (ValueError, OverflowError):
                        pass
        except Exception:
            pass

    # Direct ASCII fallback
    if 32 <= keyval <= 126:
        return chr(keyval), keyval
    return '', 0


class BongoEngine(BaseEngine):
    __gtype_name__ = 'BongoEngine'

    def __init__(self, bus=None, obj_path=None, **kwargs):
        if IBus is not None and bus is not None and obj_path is not None:
            super().__init__(
                connection=bus.get_connection(),
                object_path=obj_path,
                **kwargs
            )
        elif IBus is not None:
            super().__init__(**kwargs)
        else:
            super().__init__()

        self.bus = bus
        self.obj_path = obj_path
        self.phonetic_engine = AvroPhoneticEngine()
        self.native = BongoNativeBinding()
        self.engine_ptr = self.native.lib.bongo_engine_new() if (self.native and self.native.lib) else None
        log_msg(f"BongoEngine initialized: obj_path={obj_path}, native={bool(self.engine_ptr)}")

        self._settings_mtime = 0
        self.settings = load_settings()
        self.apply_settings()

        # Lookup table for floating candidate HUD
        if IBus is not None:
            self.table = IBus.LookupTable.new(9, 0, True, True)
            self.table.set_orientation(IBus.Orientation.VERTICAL)
        else:
            self.table = None

        self.buffer = ""
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
        log_msg(f"BongoEngine: do_focus_in ({self.obj_path})")
        self.check_reload_settings()
        if IBus is not None:
            try:
                prop_list = IBus.PropList()
                prop = IBus.Property.new(
                    "setup",
                    IBus.PropType.NORMAL,
                    IBus.Text.new_from_string("Bongo Settings"),
                    "preferences-system",
                    IBus.Text.new_from_string("Configure Bongo"),
                    True,
                    True,
                    IBus.PropState.UNCHECKED,
                    None
                )
                prop_list.append(prop)
                self.register_properties(prop_list)
            except Exception as e:
                log_msg(f"register_properties error: {e}")

    def do_focus_out(self):
        log_msg(f"BongoEngine: do_focus_out ({self.obj_path})")
        if self.has_session():
            self.commit_current()
        self.reset_session()

    def do_enable(self):
        log_msg(f"BongoEngine: do_enable ({self.obj_path})")
        self.check_reload_settings()

    def do_disable(self):
        log_msg(f"BongoEngine: do_disable ({self.obj_path})")
        self.reset_session()

    def do_reset(self):
        log_msg(f"BongoEngine: do_reset ({self.obj_path})")
        self.reset_session()

    def do_property_activate(self, prop_name, state):
        log_msg(f"BongoEngine: do_property_activate ({prop_name})")
        if prop_name == "setup":
            import subprocess
            try:
                subprocess.Popen(["/usr/bin/bongo-settings"])
            except Exception as e:
                log_msg(f"Could not launch bongo-settings: {e}")

    def apply_settings(self):
        if not self.engine_ptr:
            return
        layout = self.settings.get("keyboard_layout", 0)
        mode = self.settings.get("typing_mode", 0)
        emoji = self.settings.get("suggest_emoji", True)
        self.native.lib.bongo_engine_set_layout(self.engine_ptr, layout)
        self.native.lib.bongo_engine_set_mode(self.engine_ptr, mode)
        self.native.lib.bongo_engine_set_emoji(self.engine_ptr, emoji)

    def do_process_key_event(self, keyval, keycode, state):
        try:
            return self._handle_key_event(keyval, keycode, state)
        except Exception as e:
            import traceback
            log_msg(f"UNHANDLED ERROR in do_process_key_event: {e}\n{traceback.format_exc()}")
            return False

    def _handle_key_event(self, keyval, keycode, state):
        if IBus is None:
            return False

        # Ignore key release events
        is_press = (state & IBus.ModifierType.RELEASE_MASK) == 0
        if not is_press:
            return False

        # Filter out Lock / NumLock masks for state checks
        effective_state = state & ~(IBus.ModifierType.LOCK_MASK | IBus.ModifierType.MOD2_MASK)

        # Ignore Ctrl, Alt, or Super combinations (e.g. Ctrl+C, Ctrl+V, Alt+Tab, Super+Space)
        is_ctrl = bool(effective_state & IBus.ModifierType.CONTROL_MASK)
        is_alt = bool(effective_state & IBus.ModifierType.MOD1_MASK)
        is_super = bool(effective_state & (IBus.ModifierType.SUPER_MASK | IBus.ModifierType.MOD4_MASK))
        if is_ctrl or is_alt or is_super:
            if self.has_session():
                self.commit_current()
            return False

        key_name = IBus.keyval_name(keyval) if IBus else str(keyval)
        log_msg(f"Key event: keyval={keyval:#x} ({key_name}), keycode={keycode}, state={state:#x}, in_session={self.has_session()}")

        # Key navigation & controls in candidate table
        if self.has_session():
            # Escape: cancel composition
            if keyval == IBus.KEY_Escape:
                log_msg("Action: Escape pressed, resetting session")
                self.reset_session()
                return True

            # Enter / Return: commit current candidate
            if keyval in (IBus.KEY_Return, IBus.KEY_KP_Enter):
                log_msg("Action: Enter pressed, committing current candidate")
                self.commit_current()
                return True

            # Space: commit primary candidate, then let space pass through to the app
            if keyval == IBus.KEY_space:
                log_msg("Action: Space pressed, committing candidate and passing space")
                self.commit_current()
                return False

            # Tab / Shift+Tab: candidate navigation
            if keyval in (IBus.KEY_Tab, IBus.KEY_ISO_Left_Tab):
                is_shift = bool(effective_state & IBus.ModifierType.SHIFT_MASK)
                if is_shift:
                    self.table.cursor_up()
                else:
                    self.table.cursor_down()
                self._update_candidate_selection()
                return True

            # Number keys (1..9): commit candidate at index if multiple candidates exist
            if not bool(effective_state & IBus.ModifierType.SHIFT_MASK) and IBus.KEY_1 <= keyval <= IBus.KEY_9:
                idx = keyval - IBus.KEY_1
                if idx < len(self.candidates) and len(self.candidates) > 1:
                    log_msg(f"Action: Number key {idx+1} pressed, committing candidate index {idx}")
                    self.commit_candidate_at(idx)
                    return True

            # Arrow Down / Up / Page Down / Page Up: candidate selection
            if keyval in (IBus.KEY_Down, IBus.KEY_Page_Down):
                self.table.cursor_down()
                self._update_candidate_selection()
                return True
            if keyval in (IBus.KEY_Up, IBus.KEY_Page_Up):
                self.table.cursor_up()
                self._update_candidate_selection()
                return True

            # Backspace: delete character
            if keyval == IBus.KEY_BackSpace:
                log_msg("Action: BackSpace pressed in active session")
                self.handle_backspace()
                return True

        # Process standard printable character
        char_str, codepoint = extract_char_and_codepoint(keyval)
        if char_str and codepoint > 0:
            # Ignore non-printable / control characters (e.g. BackSpace 0x08, Delete 0x7F)
            # when there is no active composition session so the application handles them natively
            if codepoint < 0x20 or codepoint == 0x7f:
                return False

            # If not in session and character is whitespace (e.g. Space 0x20), pass through to the host app
            if not self.has_session() and char_str in " \t\r\n":
                return False

            handled = self.feed_character(char_str, codepoint, effective_state)
            if handled:
                return True

        return False

    def has_session(self):
        if self.engine_ptr and self.native and self.native.lib:
            try:
                return self.native.lib.bongo_engine_has_session(self.engine_ptr)
            except Exception:
                pass
        return bool(self.buffer or self.preedit_str)

    def feed_character(self, char_str, codepoint, state):
        is_shift = bool(state & IBus.ModifierType.SHIFT_MASK)
        modifier = 1 if is_shift else 0
        cursor_idx = self.table.get_cursor_pos() if (self.table and self.has_session()) else 0

        log_msg(f"feed_character: char='{char_str}', codepoint={codepoint}, is_shift={is_shift}")

        if self.engine_ptr and self.native and self.native.lib:
            try:
                sugg_ptr = self.native.lib.bongo_engine_feed_char(self.engine_ptr, codepoint, modifier, cursor_idx)
                log_msg(f"native feed_char returned sugg_ptr={sugg_ptr}, has_session={self.has_session()}")
                if sugg_ptr:
                    if self.has_session():
                        self.update_suggestions(sugg_ptr)
                    else:
                        preview_ptr = self.native.lib.bongo_suggestion_get_preview(sugg_ptr)
                        if preview_ptr:
                            text = ctypes.string_at(preview_ptr).decode('utf-8', errors='replace')
                            self.native.lib.bongo_string_free(preview_ptr)
                            if text and IBus is not None:
                                log_msg(f"Committing standalone char from native: '{text}'")
                                self.commit_text(IBus.Text.new_from_string(text))
                        self.reset_session()
                    self.native.lib.bongo_suggestion_free(sugg_ptr)
                    return True
            except Exception as e:
                import traceback
                log_msg(f"feed_character native error: {e}\n{traceback.format_exc()}")

        # Built-in Avro phonetic transliteration fallback
        self.buffer += char_str
        self.candidates = self.phonetic_engine.get_candidates(self.buffer)
        self.preedit_str = self.candidates[0] if self.candidates else self.buffer
        log_msg(f"feed_character fallback: buffer='{self.buffer}', preedit='{self.preedit_str}', candidates={self.candidates[:3]}")

        if self.table is not None:
            self.table.clear()
            for cand in self.candidates:
                self.table.append_candidate(IBus.Text.new_from_string(cand))

        if self.preedit_str:
            self.show_preedit()
            self._render_lookup_table()
        else:
            self.reset_session()
        return True

    def handle_backspace(self):
        if self.engine_ptr and self.native and self.native.lib:
            try:
                sugg_ptr = self.native.lib.bongo_engine_backspace(self.engine_ptr, False)
                if sugg_ptr:
                    self.update_suggestions(sugg_ptr)
                    self.native.lib.bongo_suggestion_free(sugg_ptr)
                    return
                else:
                    self.reset_session()
                    return
            except Exception as e:
                log_msg(f"handle_backspace native error: {e}")

        if self.buffer:
            self.buffer = self.buffer[:-1]
            if not self.buffer:
                self.reset_session()
            else:
                self.candidates = self.phonetic_engine.get_candidates(self.buffer)
                self.preedit_str = self.candidates[0] if self.candidates else self.buffer
                if self.table is not None:
                    self.table.clear()
                    for cand in self.candidates:
                        self.table.append_candidate(IBus.Text.new_from_string(cand))
                self.show_preedit()
                self._render_lookup_table()

    def update_suggestions(self, sugg_ptr):
        count = self.native.lib.bongo_suggestion_count(sugg_ptr)
        self.candidates = []
        if self.table is not None:
            self.table.clear()

        for i in range(count):
            cand_ptr = self.native.lib.bongo_suggestion_get_candidate(sugg_ptr, i)
            if cand_ptr:
                cand_str = ctypes.string_at(cand_ptr).decode('utf-8', errors='replace')
                self.candidates.append(cand_str)
                if self.table is not None:
                    text = IBus.Text.new_from_string(cand_str)
                    self.table.append_candidate(text)
                self.native.lib.bongo_string_free(cand_ptr)

        preview_ptr = self.native.lib.bongo_suggestion_get_preview(sugg_ptr)
        if preview_ptr:
            self.preedit_str = ctypes.string_at(preview_ptr).decode('utf-8', errors='replace')
            self.native.lib.bongo_string_free(preview_ptr)
        elif self.candidates:
            self.preedit_str = self.candidates[0]
        else:
            self.preedit_str = ""

        log_msg(f"update_suggestions: preedit='{self.preedit_str}', count={count}, top_candidates={self.candidates[:3]}")

        if self.preedit_str:
            self.show_preedit()
            self._render_lookup_table()
        else:
            self.reset_session()

    def show_preedit(self):
        if IBus is None or not self.preedit_str:
            return
        try:
            text = IBus.Text.new_from_string(self.preedit_str)
            self.update_preedit_text(text, len(self.preedit_str), True)
            self.show_preedit_text()
        except Exception as e:
            log_msg(f"show_preedit error: {e}")

    def _update_candidate_selection(self):
        cursor = self.table.get_cursor_pos() if self.table is not None else 0
        if 0 <= cursor < len(self.candidates):
            self.preedit_str = self.candidates[cursor]
            self.show_preedit()
        self._render_lookup_table()

    def _render_lookup_table(self):
        if IBus is None or self.table is None:
            return
        try:
            if self.candidates:
                self.update_lookup_table(self.table, True)
                self.show_lookup_table()
            else:
                self.hide_lookup_table()
        except Exception as e:
            log_msg(f"_render_lookup_table error: {e}")

    def commit_current(self):
        if not self.candidates:
            if self.preedit_str and IBus is not None:
                log_msg(f"commit_current committing preedit: '{self.preedit_str}'")
                self.commit_text(IBus.Text.new_from_string(self.preedit_str))
            self.reset_session()
            return

        cursor = self.table.get_cursor_pos() if self.table is not None else 0
        if cursor >= len(self.candidates):
            cursor = 0
        self.commit_candidate_at(cursor)

    def commit_candidate_at(self, idx):
        if idx < len(self.candidates):
            chosen = self.candidates[idx]
            log_msg(f"commit_candidate_at[{idx}]: committing '{chosen}'")
            if IBus is not None:
                self.commit_text(IBus.Text.new_from_string(chosen))
            if self.engine_ptr and self.native and self.native.lib:
                try:
                    self.native.lib.bongo_engine_commit(self.engine_ptr, idx)
                except Exception as e:
                    log_msg(f"native commit error: {e}")
        elif self.preedit_str:
            log_msg(f"commit_candidate_at fallback preedit: '{self.preedit_str}'")
            if IBus is not None:
                self.commit_text(IBus.Text.new_from_string(self.preedit_str))
            if self.engine_ptr and self.native and self.native.lib:
                try:
                    self.native.lib.bongo_engine_reset(self.engine_ptr)
                except Exception:
                    pass
        self._clear_ui_state()

    def reset_session(self):
        if self.engine_ptr and self.native and self.native.lib:
            try:
                self.native.lib.bongo_engine_reset(self.engine_ptr)
            except Exception:
                pass
        self._clear_ui_state()

    def _clear_ui_state(self):
        self.buffer = ""
        self.preedit_str = ""
        self.candidates = []
        if self.table is not None:
            self.table.clear()
        if IBus is not None:
            try:
                self.hide_preedit_text()
                self.hide_lookup_table()
            except Exception:
                pass

    def do_destroy(self):
        log_msg(f"BongoEngine: do_destroy ({self.obj_path})")
        if self.engine_ptr and self.native and self.native.lib:
            try:
                self.native.lib.bongo_engine_free(self.engine_ptr)
                self.engine_ptr = None
            except Exception:
                pass
        if IBus is not None:
            super().do_destroy()


class BongoFactory(BaseFactory):
    def __init__(self, bus):
        if IBus is not None:
            super().__init__(
                connection=bus.get_connection(),
                object_path=IBus.PATH_FACTORY
            )
        self.bus = bus
        self.engine_id = 0
        log_msg("BongoFactory initialized")

    def create_engine_instance(self, engine_name):
        log_msg(f"BongoFactory.create_engine_instance requested for: '{engine_name}'")
        if engine_name == "bongo":
            self.engine_id += 1
            obj_path = f"/org/freedesktop/IBus/Engine/{self.engine_id}"
            try:
                engine = BongoEngine(self.bus, obj_path)
                log_msg(f"BongoEngine instance #{self.engine_id} created successfully at {obj_path}")
                return engine
            except Exception as e:
                log_msg(f"Failed to create BongoEngine: {e}")
                import traceback
                log_msg(traceback.format_exc())
                return None
        log_msg(f"Unknown engine name requested: '{engine_name}'")
        return None

    def do_create_engine(self, engine_name):
        return self.create_engine_instance(engine_name)


class BongoApplication:
    def __init__(self, bus):
        self.bus = bus
        self.factory = BongoFactory(self.bus)

        try:
            self.factory.connect("create-engine", self._on_create_engine)
        except Exception as e:
            log_msg(f"Warning: could not connect create-engine signal: {e}")

        flags = 0
        try:
            if hasattr(IBus, 'BusNameFlag'):
                flags = IBus.BusNameFlag.ALLOW_REPLACEMENT | IBus.BusNameFlag.REPLACE_EXISTING
        except Exception:
            flags = 0

        self.bus.request_name("org.freedesktop.IBus.Bongo", flags)
        log_msg("Requested D-Bus name 'org.freedesktop.IBus.Bongo'")

        if "--ibus" not in sys.argv:
            component_path = "/usr/share/ibus/component/bongo.xml"
            if not os.path.exists(component_path):
                component_path = str(Path(__file__).parent / "bongo.xml")
            if os.path.exists(component_path):
                try:
                    component = IBus.Component.new_from_file(component_path)
                    self.bus.register_component(component)
                    log_msg(f"Registered IBus component from {component_path}")
                except Exception as e:
                    log_msg(f"Failed to register component: {e}")

    def _on_create_engine(self, factory, engine_name):
        return self.factory.create_engine_instance(engine_name)

    def run(self):
        log_msg("Starting GLib.MainLoop...")
        loop = GLib.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            log_msg("GLib.MainLoop stopped by KeyboardInterrupt")


def main():
    log_msg(f"=== Bongo IBus Engine started (pid={os.getpid()}, argv={sys.argv}) ===")
    if IBus is None:
        log_msg("Error: IBus 1.0 GObject library not found.")
        sys.stderr.write("Error: IBus 1.0 GObject library not found.\n")
        sys.exit(1)
    IBus.init()
    bus = IBus.Bus.new()
    if not bus.is_connected():
        log_msg("Error: Could not connect to IBus daemon bus.")
        sys.stderr.write("Error: Could not connect to IBus daemon bus.\n")
        sys.exit(1)

    app = BongoApplication(bus)
    app.run()


if __name__ == '__main__':
    main()
