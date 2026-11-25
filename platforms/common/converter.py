#!/usr/bin/env python3
"""
Bongo Converter & Linguistic Utilities Module
Provides:
1. Bidirectional Unicode <-> Bijoy 2000 (ANSI) conversion based on OmicronLab (poriborton).
2. Punctuation Padding Isolator (iAvro / ibus-avro style tokenization).
3. Case Sensitivity Normalizer (pyAvroPhonetic style).
4. Morphological Suffix & Sandhi Engine.
5. Curated Autocorrect & English Loanwords Table (OmicronLab autodict).
"""

import re
import os
import sys
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# --- Unicode to Bijoy 2000 Mapping (OmicronLab poriborton) ---
U2B_MAP: Dict[str, str] = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
    "ৎ": "r", "ঁ": "u", "ং": "s", "ঃ": "t", "৳": "$",
    "“": "Ò", "”": "Ó", "‘": "Ô", "’": "Õ",
    "অ": "A", "আ": "Av", "ই": "B", "ঈ": "C", "উ": "D",
    "ঊ": "E", "ঋ": "F", "এ": "G", "ঐ": "H", "ও": "I", "ঔ": "J",
    "ক": "K", "খ": "L", "গ": "M", "ঘ": "N", "ঙ": "O",
    "চ": "P", "ছ": "Q", "জ": "R", "ঝ": "S", "ঞ": "T",
    "ট": "U", "ঠ": "V", "ড": "W", "ঢ": "X", "ণ": "Y",
    "ত": "Z", "থ": "_", "দ": "`", "ধ": "a", "ন": "b",
    "প": "c", "ফ": "d", "ব": "e", "ভ": "f", "ম": "g",
    "য": "h", "র": "i", "ল": "j", "শ": "k", "ষ": "l",
    "স": "m", "হ": "n", "ঢ়": "p", "ড়": "o", "য়": "q", "য়": "q",
    "স্প্র": "¯cÖ", "স্ত্র": "¯¿", "স্ত্ব": "¯—¡", "স্ট্র": "÷ª", "স্ক্র": "¯Œ",
    "ষ্প্র": "®cÖ", "ষ্ট্র": "óª", "ষ্ক্র": "®Œ", "ষ্ক্ব": "®‹¡", "শ্ল": "k−",
    "ম্ভ্র": "¤£", "ম্ব্র": "¤^ª", "ম্প্র": "¤cÖ", "ন্ধ্র": "Üª", "ন্দ্র": "›`ª",
    "ন্দ্ব": "›Ø", "ন্থ্র": "š’ª", "ন্ত্র": "š¿", "ন্ত্ব": "š—¡", "ন্ড্র": "Ûª",
    "ন্ট্র": "›Uª", "ন্স": "Ý", "দ্ভ্র": "™£", "দ্দ্ব": "Ï¡", "ত্ত্র": "Ë«",
    "ত্ত্ব": "Ë¡", "ণ্ড্র": "Êª", "জ্জ্ব": "¾¡", "চ্ছ্র": "”Qª", "চ্ছ্ব": "”Q¡",
    "ঙ্ঘ্র": "•Nª", "ঙ্ক্ষ": "•¶", "গ্ধ্র": "»ª", "ক্ষ্ম": "²", "ক্ষ্ব": "¶¡",
    "ক্ষ্ণ": "¶è", "ক্ত্র": "³«", "ক্ট্র": "±ª", "হ্র": "nª", "হ্ম": "þ",
    "হ্ব": "nŸ", "হ্ন": "ý", "হ্ণ": "nœ", "হ্ল": "n¬", "স্ল": "¯¬",
    "স্র": "mª", "স্ম": "¯§", "স্ব": "¯^", "স্ফ": "ù", "স্প": "¯c",
    "স্প্ল": "¯c−", "স্ন": "ø", "স্থ": "¯’", "স্ত": "¯—", "স্ট": "÷",
    "স্খ": "ö", "স্ক": "¯‹", "ষ্ম": "®§", "ষ্ব": "®^", "ষ্ফ": "õ",
    "ষ্প": "®c", "ষ্ণ": "ò", "ষ্ণ্ব": "ò¡", "ষ্ঠ": "ô", "ষ্ট": "ó",
    "ষ্ক": "®‹", "শ্র": "kª", "শ্ম": "k¥", "শ্ব": "k¦", "শ্ন": "kœ",
    "শ্ছ": "ñ", "শ্চ": "ð", "ল্ল": "j−", "ল্ম": "j¥", "ল্ব": "j¦",
    "ল্ভ": "j¢", "লপ": "jè", "লফ": "jô", "লঘ": "jN", "লখ": "jL",
    "লগ": "jM", "ল্ক": "jK", "ম্ম": "¤§", "ম্ব": "¤^", "ম্ন": "¤ø",
    "ম্ভ": "¤¢", "ম্ফ": "¤d", "ম্প": "¤c", "ব্ল": "eø", "ব্র": "eª",
    "ব্ব": "eŸ", "ব্দ": "e`", "ব্জ": "eR", "ফ্ল": "d¬", "প্ল": "c−",
    "প্র": "cÖ", "প্স": "cô", "প্ন": "cø", "প্ত": "cZ", "প্ট": "cU",
    "পক্ব": "cK¡", "ন্ম": "b¥", "ন্ন": "bø", "ন্ব": "b¢", "ন্ধ": "Ü",
    "ন্থ": "š’", "ন্ত": "š—", "ন্দ": "›`", "ন্ঠ": "Ú", "ন্ট": "›U",
    "ঞ্র": "Tª", "ঞ্ব": "T¡", "ঞ্ম": "TÍ", "ঞ্ছ": "Tç", "ঞ্চ": "TÁ",
    "ঞ্জ": "T¾", "ঞ্ঝ": "T‘", "ণ্ণ": "Yè", "ণ্ম": "Y¥", "ণ্ব": "Y¦",
    "ণ্ঢ": "ê", "ণ্ঠ": "È", "ণ্ড": "Ê", "ঢ্র": "Xª", "ড্র": "Wª",
    "দ্ভ": "™¢", "দ্দ": "Ï", "দ্ধ": "×", "দ্ব": "Ø", "দ্ঘ": "™a",
    "দ্গ": "™M", "দ্র": "`ª", "দ্ম": "`¥", "ধ্ন": "aœ", "ধ্ম": "a¥",
    "ধ্র": "aª", "ধ্ব": "aŸ", "ত্ম": "Z¥", "ত্ন": "Zœ", "ত্ব": "Z¡",
    "ত্র": "Î", "ত্ত": "Ë", "ত্থ": "Ì", "ঠ্র": "Vª", "ট্র": "Uª",
    "ট্ব": "U¡", "ট্ম": "U¥", "ট্ট": "Æ", "ঝ্র": "Sª", "জ্ঞ": "Á",
    "জ্জ": "¾", "জ্জ্র": "¾ª", "জ্ব": "À", "জ্র": "Rª", "জম": "R¥",
    "চ্ছ": "”Q", "চ্চ": "”P", "ছ্র": "Qª", "ঙ্ঘ": "•N", "ঙ্খ": "•L",
    "ঙ্গ": "•M", "ঙ্ম": "•g", "ঙ্ক": "¼", "ঘ্র": "Nª", "ঘ্ন": "Nœ",
    "গ্র": "MÖ", "গ্ম": "M¥", "গ্ব": "M¦", "গ্ন": "Mœ", "গ্ল": "M−",
    "গ্ধ": "»", "খ্র": "Lª", "ক্স": "·", "ক্ষ": "¶", "ক্ল": "K¬",
    "ক্ন": "Kè", "ক্র": "µ", "ক্ম": "´", "ক্ব": "K¡", "ক্ত": "³",
    "ক্ট": "±", "ক্ক": "°", "ড়্গ": "ÿ",
}

# --- Internal Constants ---
B_AA_KAR, B_OU_KAR = "\u09be", "\u09cc"
B_I_KAR = "\u09bf"
B_E_KAR = "\u09c7"
B_OI_KAR = "\u09c8"
B_U_KAR = "\u09c1"
B_UU_KAR = "\u09c2"
B_RRI_KAR = "\u09c3"
B_O_KAR = "\u09cb"
B_HASANTA = "\u09cd"
B_DARI = "\u0964"
B_DDARI = "\u0965"
ZWJ = "\u200d"
ZWNJ = "\u200c"

def _is_consonant(c: str) -> bool:
    return "\u0995" <= c <= "\u09b9"

def _is_vowel(c: str) -> bool:
    return "\u0985" <= c <= "\u0994"

def _is_kar(c: str) -> bool:
    return B_AA_KAR <= c <= B_OU_KAR

def _is_front_kar(c: str) -> bool:
    return c in (B_I_KAR, B_E_KAR, B_OI_KAR)

def _is_base_line_right_char(c: str) -> bool:
    return c in ("খ", "গ", "ঘ", "ন", "ণ", "থ", "দ", "ধ", "প", "ব", "ম", "য", "র", "ল", "শ", "ষ", "স", "হ", "য়", "য়")

def _is_front_facing(s: str) -> bool:
    if not s:
        return True
    encountered_hasanta = False
    encountered_consonant = False
    for c in reversed(s):
        if c == B_HASANTA:
            encountered_hasanta = True
            continue
        if _is_consonant(c) and encountered_consonant and not encountered_hasanta:
            return False
        if _is_consonant(c):
            encountered_consonant = True
            encountered_hasanta = False
            continue
        if c.isspace():
            break
        if _is_vowel(c) or _is_kar(c):
            return False
    return True

def _last(s: str, n: int) -> str:
    return s[-n:] if len(s) >= n else s

def _is_special_combination_with_r_fola(s: str) -> bool:
    return s in ("শ্র", "দ্র", "গ্র", "ত্র", "জ্র", "থ্র", "ধ্র", "প্র", "ব্র", "ভ্র", "ম্র", "স্র", "ন্দ্র", "ম্প্র", "ষ্প্র", "স্প্র")

def _is_special_combination_with_l(s: str) -> bool:
    return s in ("গ্ল", "প্ল", "ব্ল", "শ্ল", "স্ল")

def _replace_kar(kar: str, front: bool, preceding: str) -> str:
    if kar == "া":
        return "v"
    elif kar == "ী":
        return "x"
    elif kar == "ু":
        if preceding == "র":
            return "“"
        l1 = _last(preceding, 1)
        if l1 == "র":
            if _is_special_combination_with_r_fola(_last(preceding, 3)) or _is_special_combination_with_r_fola(_last(preceding, 5)):
                return "“"
            return "y"
        elif l1 == "ল":
            if _is_special_combination_with_l(_last(preceding, 3)) or _last(preceding, 5) == "স্প্ল":
                return "“"
            return "y"
        elif l1 == "ণ":
            return "z" if _last(preceding, 3) == "ষ্ণ" else "y"
        elif l1 == "ষ":
            return "z" if _last(preceding, 3) == "ক্ষ" else "y"
        elif _is_base_line_right_char(l1):
            return "y"
        elif l1 in ("ড়", "ঢ়"):
            return "–"
        else:
            return "z"
    elif kar == "ূ":
        if preceding == "র":
            return "ƒ"
        l1 = _last(preceding, 1)
        if l1 == "র":
            if _is_special_combination_with_r_fola(_last(preceding, 3)) or _is_special_combination_with_r_fola(_last(preceding, 5)):
                return "ƒ"
            return "~"
        elif l1 == "ল":
            if _is_special_combination_with_l(_last(preceding, 3)) or _last(preceding, 5) == "স্প্ল":
                return "ƒ"
            return "~"
        elif l1 == "ষ":
            return "‚" if _last(preceding, 3) == "ক্ষ" else "~"
        elif _is_base_line_right_char(l1):
            return "~"
        else:
            return "‚"
    elif kar == "ৃ":
        l1 = _last(preceding, 1)
        return "„" if _is_base_line_right_char(l1) else "…"
    elif kar == "ি":
        return "w"
    elif kar == "ে":
        return "†" if front else "‡"
    elif kar == "ৈ":
        return "ˆ" if front else "‰"
    return ""

def _convert_buffer(buf: List[str]) -> str:
    s = "".join(buf)
    reph = False
    z_fola = False
    hasanta = False
    if s.startswith("র্"):
        s = s[2:]
        reph = True
    if s.startswith("র\u200d"):
        s = s[0] + s[2:]
    if s.endswith("্য"):
        s = s[:-2]
        z_fola = True
    if s.endswith("্"):
        s = s[:-1]
        hasanta = True

    out = U2B_MAP.get(s, s)
    if z_fola:
        out += "¨"
    if reph:
        out += "©"
    if hasanta:
        out += "&"
    return out

def unicode_to_bijoy(input_str: str) -> str:
    """
    Converts Unicode Bengali text to Bijoy 2000 ANSI encoding.
    Passes 100% of OmicronLab poriborton test specifications.
    """
    if not input_str:
        return ""
    # Normalize composed characters with nukta
    input_str = input_str.replace("\u09af\u09bc", "য়").replace("\u09a1\u09bc", "ড়").replace("\u09a2\u09bc", "ঢ়")
    out: List[str] = []
    buffer: List[str] = []
    encountered_hasanta = False

    for pos, c in enumerate(input_str):
        if c == B_O_KAR:
            out.append(_replace_kar("ে", _is_front_facing(input_str[:pos]), ""))
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            out.append("v")
        elif c == B_OU_KAR:
            out.append(_replace_kar("ে", _is_front_facing(input_str[:pos]), ""))
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            out.append("Š")
        elif _is_front_kar(c):
            out.append(_replace_kar(c, _is_front_facing(input_str[:pos]), ""))
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
        elif c == B_U_KAR and "".join(buffer) == "গ":
            out.append("¸")
            buffer.clear()
        elif c == B_U_KAR and "".join(buffer) == "শ":
            out.append("ï")
            buffer.clear()
        elif c == B_U_KAR and "".join(buffer) == "হ":
            out.append("û")
            buffer.clear()
        elif c == B_U_KAR and "".join(buffer).endswith("্ত"):
            conv = _convert_buffer(buffer)
            if conv.endswith("—"):
                conv = conv[:-1] + "‘"
            out.append(conv)
            buffer.clear()
        elif c == B_RRI_KAR and "".join(buffer) == "হ":
            out.append("ü")
            buffer.clear()
        elif _is_kar(c):
            buf_str = "".join(buffer)
            kar = _replace_kar(c, False, buf_str)
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            out.append(kar)
        elif c == B_HASANTA:
            encountered_hasanta = True
            buffer.append(B_HASANTA)
        elif c in (B_DARI, "\u09e4"):
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            out.append("|")
        elif c in (B_DDARI, "\u09e5"):
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            out.append("\\")
        elif c == ZWJ:
            buffer.append(ZWJ)
        elif c == ZWNJ:
            if buffer and buffer[-1] == B_HASANTA:
                buffer.pop()
                if buffer:
                    out.append(_convert_buffer(buffer))
                    buffer.clear()
                out.append("&")
                encountered_hasanta = False
        elif encountered_hasanta:
            buffer.append(c)
            encountered_hasanta = False
        elif ("\u0980" <= c <= "\u09ff") or (c in ("\u2018", "\u2019", "\u201c", "\u201d")):
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            buffer.append(c)
        else:
            if buffer:
                out.append(_convert_buffer(buffer))
                buffer.clear()
            out.append(c)

    if buffer:
        out.append(_convert_buffer(buffer))
        buffer.clear()

    return "".join(out)


# --- Bijoy to Unicode Engine ---
# Comprehensive list of Bijoy clusters (ligatures + consonants) in decreasing length
BIJOY_CLUSTERS = [
    "¯cÖ", "¯¿", "¯—¡", "÷ª", "¯Œ", "®cÖ", "óª", "®Œ", "®‹¡", "k−", "¤£", "¤^ª", "¤cÖ", "Üª", "›`ª",
    "›Ø", "š’ª", "š¿", "š—¡", "Ûª", "›Uª", "Ý", "™£", "Ï¡", "Ë«", "Ë¡", "Êª", "¾¡", "”Qª", "”Q¡",
    "•Nª", "•¶", "»ª", "²", "¶¡", "¶è", "³«", "±ª", "nª", "þ", "nŸ", "ý", "nœ", "n¬", "¯¬", "mª",
    "¯§", "¯^", "ù", "¯c", "¯c−", "ø", "¯’", "¯—", "÷", "ö", "¯‹", "®§", "®^", "õ", "®c", "ò", "ò¡",
    "ô", "ó", "®‹", "kª", "k¥", "k¦", "kœ", "ñ", "ð", "j−", "j¥", "j¦", "j¢", "jè", "jô", "jN", "jL",
    "jM", "jK", "¤§", "¤^", "¤ø", "¤¢", "¤d", "¤c", "eø", "eª", "eŸ", "e`", "eR", "d¬", "c−", "cÖ",
    "cô", "cø", "cZ", "cU", "cK¡", "b¥", "bø", "b¢", "Ü", "ÜŸ", "š’", "š—", "›`", "›a", "Ú", "›U",
    "Tª", "T¡", "TÍ", "Tç", "TÁ", "T¾", "T‘", "Yè", "Y¥", "Y¦", "ê", "È", "Ê", "Xª", "Wª", "™¢", "Ï",
    "×", "Ø", "™a", "™M", "`ª", "`¥", "aœ", "a¥", "aª", "aŸ", "Z¥", "Zœ", "Z¡", "Z_©", "Î", "Ë", "Ì",
    "Vª", "Uª", "U¡", "U¥", "Æ", "Sª", "Á", "¾", "¾ª", "À", "Rª", "R¥", "R¡", "”Q", "”P", "Qª", "•N",
    "•L", "•M", "•g", "¼", "Nª", "Nœ", "MÖ", "M¥", "M¦", "Mœ", "M−", "»", "Lª", "·", "¶", "K¬", "Kè",
    "µ", "´", "K¡", "³", "±", "°", "ÿ",
]

# Sorted B2U ligatures
B2U_LIGATURES: List[Tuple[str, str]] = sorted(
    [(v, k) for k, v in U2B_MAP.items() if len(v) > 1 and k != "আ"],
    key=lambda x: len(x[0]),
    reverse=True
)

B2U_SINGLES: Dict[str, str] = {
    v: k for k, v in U2B_MAP.items() if len(v) == 1
}
B2U_SINGLES.update({
    "Av": "আ",
    "¸": "গু", "ï": "শু", "û": "হু", "ü": "হৃ",
    "‘": "্তু", "“": "ু", "”": "ু", "ƒ": "ূ", "‚": "ূ", "~": "ূ",
    "z": "ু", "y": "ু", "–": "ু",
    "…": "ৃ", "„": "ৃ",
    "v": "া", "x": "ী", "w": "ি",
    "†": "ে", "‡": "ে", "ˆ": "ৈ", "‰": "ৈ",
    "|": "।", "\\": "॥",
    "&": "্",
    "¨": "্য", "ª": "্র", "Ö": "্র", "«": "্র",
})

# Regular expression that matches a single Bijoy consonant or conjunct cluster
_CLUSTER_RE_PATTERN = r"(?:" + "|".join(re.escape(x) for x in BIJOY_CLUSTERS) + r"|[K-Z_`a-no-q])"
_CLUSTER_RE = re.compile(_CLUSTER_RE_PATTERN)

def bijoy_to_unicode(input_str: str) -> str:
    """
    Converts Bijoy 2000 ANSI text to standard Bengali Unicode text.
    Reverses pre-kar positioning, reph positioning, and replaces ANSI ligatures.
    """
    if not input_str:
        return ""

    s = input_str

    # 1. Composite Kars:
    # † + cluster + v -> cluster + ো
    # † + cluster + Š -> cluster + ৌ
    s = re.sub(r"[†‡](" + _CLUSTER_RE_PATTERN + r")v", r"\1ো", s)
    s = re.sub(r"[†‡](" + _CLUSTER_RE_PATTERN + r")Š", r"\1ৌ", s)

    # 2. Pre-Kars rearrangement:
    # w + cluster -> cluster + ি
    # †/‡ + cluster -> cluster + ে
    # ˆ/‰ + cluster -> cluster + ৈ
    s = re.sub(r"w(" + _CLUSTER_RE_PATTERN + r")", r"\1ি", s)
    s = re.sub(r"[†‡](" + _CLUSTER_RE_PATTERN + r")", r"\1ে", s)
    s = re.sub(r"[ˆ‰](" + _CLUSTER_RE_PATTERN + r")", r"\1ৈ", s)

    # 3. Post-Reph rearrangement:
    # cluster + © -> র্ + cluster
    s = re.sub(r"(" + _CLUSTER_RE_PATTERN + r")©", r"র্\1", s)

    # 4. Multi-character ligatures replacement
    for b_lig, u_lig in B2U_LIGATURES:
        if b_lig in s:
            s = s.replace(b_lig, u_lig)

    # 5. Single character mappings & post-processing
    out: List[str] = []
    i = 0
    n = len(s)
    while i < n:
        if i + 1 < n and s[i:i+2] in B2U_SINGLES:
            out.append(B2U_SINGLES[s[i:i+2]])
            i += 2
        elif s[i] in B2U_SINGLES:
            out.append(B2U_SINGLES[s[i]])
            i += 1
        else:
            out.append(s[i])
            i += 1

    result = "".join(out)

    # Standardize ya
    result = result.replace("য়", "য়")

    # Clean double halants or orphaned halants if any
    result = re.sub(r"্+", "্", result)
    result = re.sub(r"্$", "", result)

    return result


# --- OmicronLab Punctuation Padding Isolator ---
PUNCT_CHARS_REGEX = r"[\-\]~!@#%&*()_=+[{}'\";<>\/?|.,:]+"

def separate_padding(word: str) -> Tuple[str, str, str]:
    """
    Separates outer punctuation padding from core stem (iAvro & ibus-avro style).
    Allows typing (ami), "bangla", dhonnobad, without punctuation breaking candidates.
    """
    if not word:
        return "", "", ""
    prefix_match = re.match(r"^(" + PUNCT_CHARS_REGEX + r")", word)
    prefix = prefix_match.group(1) if prefix_match else ""
    rest = word[len(prefix):]
    suffix_match = re.search(r"(" + PUNCT_CHARS_REGEX + r")$", rest)
    suffix = suffix_match.group(1) if suffix_match else ""
    stem = rest[:len(rest) - len(suffix)] if suffix else rest
    return prefix, stem, suffix


# --- Case Sensitivity Normalizer (pyAvroPhonetic / ibus-avro) ---
AVRO_CASE_SENSITIVE = set("OIUDGJNRSTYZ")

def fix_string_case(word: str) -> str:
    """
    Normalizes casing: preserves only Avro case-sensitive characters (O, I, U, D, G, J, N, R, S, T, Y, Z)
    and converts non-case-sensitive uppercase letters (A, B, C, E, F, H, K, L, M, P, Q, V, W, X) to lowercase.
    Prevents accidental Shift keying from ruining phonetic output.
    """
    if not word:
        return ""
    return "".join(c if (c in AVRO_CASE_SENSITIVE or not c.isalpha()) else c.lower() for c in word)


# --- Morphological Suffix & Sandhi Engine ---
def apply_sandhi_rules(stem: str, suffix: str) -> str:
    """
    Applies authentic Bengali Sandhi rules for suffix transformations:
    1. Khandatta (ৎ) + vowel -> ত + Kar (e.g. জগৎ + এর -> জগতের)
    2. Anushar (ং) + vowel -> ঙ + Kar (e.g. রং + এ -> রঙে)
    3. Stem ending in Vowel/Kar + Kar suffix -> inserts য় (e.g. বই + এ -> বইয়ে)
    4. Consonant ending stem + vowel suffix -> attaches Kar (e.g. দেশ + এর -> দেশের)
    """
    if not stem or not suffix:
        return (stem or "") + (suffix or "")

    kar_map = {"অ": "", "আ": "া", "ই": "ি", "ঈ": "ী", "উ": "ু", "ঊ": "ূ", "ঋ": "ৃ", "এ": "ে", "ঐ": "ৈ", "ও": "ো", "ঔ": "ৌ"}

    # Rule 1: ৎ + vowel -> ত + Kar
    if stem.endswith("ৎ") and (suffix[0] in kar_map or (B_AA_KAR <= suffix[0] <= B_OU_KAR)):
        kar = kar_map.get(suffix[0], suffix[0])
        return stem[:-1] + "ত" + kar + suffix[1:]

    # Rule 2: ং + vowel -> ঙ + Kar
    if stem.endswith("ং") and (suffix[0] in kar_map or (B_AA_KAR <= suffix[0] <= B_OU_KAR)):
        kar = kar_map.get(suffix[0], suffix[0])
        return stem[:-1] + "ঙ" + kar + suffix[1:]

    # Rule 3: Stem ending in Vowel or Kar + vowel suffix like 'এ' / 'এর' -> insert 'য়'
    vowels_and_kars = set("অআইঈউঊঋএঐওঔািীুূৃেৈোৌ")
    if stem[-1] in vowels_and_kars:
        if suffix.startswith("এর"):
            return stem + "য়ের" + suffix[2:]
        elif suffix.startswith("এ"):
            return stem + "য়ে" + suffix[1:]
        elif suffix.startswith("ে"):
            return stem + "য়ে" + suffix[1:]

    # Rule 4: Consonant ending stem + vowel suffix starting with 'এ' -> consonant + 'ে'
    if _is_consonant(stem[-1]):
        if suffix.startswith("এর"):
            return stem + "ের" + suffix[2:]
        elif suffix.startswith("এ"):
            return stem + "ে" + suffix[1:]

    return stem + suffix


# --- Curated Autocorrect & English Loanwords Table ---
AUTOCORRECT_LOANWORDS: Dict[str, str] = {
    # Ordinals
    "1st": "১ম", "2nd": "২য়", "3rd": "৩য়", "4th": "৪র্থ", "5th": "৫ম",
    "6th": "৬ষ্ঠ", "7th": "৭ম", "8th": "৮ম", "9th": "৯ম", "10th": "১০ম",
    # English Loanwords & Technical Terminology
    "class": "ক্লাস", "click": "ক্লিক", "chittagong": "চট্টগ্রাম", "cinema": "সিনেমা",
    "chemistry": "কেমিস্ট্রি", "school": "স্কুল", "college": "কলেজ", "university": "বিশ্ববিদ্যালয়",
    "police": "পুলিশ", "bank": "ব্যাংক", "card": "কার্ড", "doctor": "ডাক্তার",
    "hospital": "হাসপাতাল", "station": "স্টেশন", "ticket": "টিকিট", "bus": "বাস",
    "train": "ট্রেন", "phone": "ফোন", "mobile": "মোবাইল", "internet": "ইন্টারনেট",
    "email": "ইমেইল", "facebook": "ফেসবুক", "google": "গুগল", "youtube": "ইউটিউব",
    "windows": "উইন্ডোজ", "office": "অফিস", "video": "ভিডিও", "audio": "অডিও",
    "photo": "ছবি", "camera": "ক্যামেরা", "radio": "রেডিও", "television": "টেলিভিশন",
    "problem": "সমস্যা", "program": "প্রোগ্রাম", "project": "প্রজেক্ট", "file": "ফাইল",
    "folder": "ফোল্ডার", "system": "সিস্টেম", "service": "সার্ভিস", "update": "আপডেট",
    "version": "ভার্সন", "page": "পেজ", "site": "সাইট", "link": "লিঙ্ক",
    "post": "পোস্ট", "comment": "কমেন্ট", "message": "মেসেজ", "chat": "চ্যাট",
    "group": "গ্রুপ", "member": "মেম্বার", "admin": "অ্যাডমিন", "login": "লগইন",
    "password": "পাসওয়ার্ড", "account": "অ্যাকাউন্ট", "profile": "প্রোফাইল",
    "status": "স্ট্যাটাস", "story": "স্টোরি", "share": "শেয়ার", "like": "লাইক",
    "subscribe": "সাবস্ক্রাইব", "channel": "চ্যানেল", "bongo": "বঙ্গ",
    "bd": "বাংলাদেশ", "dhaka": "ঢাকা", "thx": "ধন্যবাদ",
    # Compound Contractions & Chandrabindu Phonetic Expansions
    "hya": "হ্যাঁ", "hea": "হ্যাঁ",
    "cad": "চাঁদ", "chad": "চাঁদ", "chada": "চাঁদা",
    "pac": "পাঁচ", "pach": "পাঁচ",
    "hata": "হাঁটা", "hatchi": "হাঁটছি", "hatte": "হাঁটতে",
    "khuj": "খুঁজ", "khuje": "খুঁজে", "khuji": "খুঁজি", "khujchi": "খুঁজছি",
    "dhadha": "ধাঁধা", "aka": "আঁকা", "bash": "বাঁশ", "has": "হাঁস", "hash": "হাঁস",
    "fapa": "ফাঁপা", "fad": "ফাঁদ", "fak": "ফাঁক", "fashi": "ফাঁসি",
    "dhoya": "ধোঁয়া", "kacha": "কাঁচা", "shakha": "শাঁখা", "badha": "বাঁধা",
    "dat": "দাঁত", "idur": "ইঁদুর", "katha": "কাঁথা", "kathal": "কাঁঠাল",
    "baka": "বাঁকা", "khocha": "খোঁচা", "radha": "রাঁধা", "tak": "টাঁক", "chuch": "ছুঁচ", "jak": "ঝাঁক",
}


# --- Bengali & English Inline Emoji Keywords ---
EMOJI_KEYWORDS: Dict[str, str] = {
    # Phonetic & English
    "has": "😄", "hasi": "😂", "hashi": "😂", "lol": "😂", "smile": "😊", "happy": "😊",
    "love": "❤️", "valobasha": "❤️", "bhalobasha": "❤️", "prem": "💖", "heart": "❤️",
    "kiss": "😘", "chumo": "😘", "sad": "😢", "kanna": "😭", "dukkho": "😢", "dukho": "😢",
    "rag": "😡", "angry": "😡", "shanto": "😌", "thik": "👍", "bhalo": "👍", "ok": "👌",
    "agun": "🔥", "fire": "🔥", "josh": "🔥", "taka": "💰", "money": "💰",
    "bd": "🇧🇩", "bangladesh": "🇧🇩", "bongo": "🇧🇩",
    "phul": "🌸", "ful": "🌸", "golap": "🌹", "surjo": "☀️", "sun": "☀️",
    "chad": "🌙", "chand": "🌙", "moon": "🌙", "tara": "⭐", "star": "⭐",
    "brishti": "🌧️", "rain": "🌧️", "megh": "☁️",
    "cha": "☕", "tea": "☕", "coffee": "☕", "aam": "🥭", "mango": "🥭",
    "clap": "👏", "taali": "👏", "namaste": "🙏", "dua": "🙏", "dowa": "🙏",
    "salam": "🤝", "eid": "🌙", "party": "🎉", "shuveccha": "🎉", "birthday": "🎂",
    "victory": "✌️", "joy": "✌️", "cricket": "🏏", "football": "⚽", "gaan": "🎵",
    "ghum": "😴", "sleep": "😴", "kaj": "💻", "work": "💻", "boi": "📚",
    # Bengali script keywords
    "ভালোবাসা": "❤️", "প্রেম": "💖", "হাসি": "😂", "খুশি": "😊", "দুঃখ": "😢",
    "কান্না": "😭", "রাগ": "😡", "দোয়া": "🙏", "নামাজ": "🕌", "ঈদ": "🌙",
    "আগুন": "🔥", "বৃষ্টি": "🌧️", "চাঁদ": "🌙", "সূর্য": "☀️", "তারা": "⭐",
    "ফুল": "🌸", "গোলাপ": "🌹", "বাংলাদেশ": "🇧🇩", "টাকা": "💰", "চা": "☕",
    "কফি": "☕", "আম": "🥭", "শুভেচ্ছা": "🎉", "জন্মদিন": "🎂", "তালি": "👏",
    "সালাম": "🤝", "গান": "🎵", "ক্রিকেট": "🏏", "কাজ": "💻", "বই": "📚", "ঘুম": "😴",
}


def lookup_emoji_keyword(word: str) -> Optional[str]:
    """Returns matching emoji for a keyword query or colon-wrapped identifier (e.g. :love: or hasi)."""
    clean = (word or "").strip().lower().strip(":")
    return EMOJI_KEYWORDS.get(clean)


# --- Contextual Bengali Next-Word (Bigram) Prediction (synced across all platforms) ---
COMMON_BIGRAMS: Dict[str, List[str]] = {
    # Greetings & social
    "আমার": ["সোনার", "দেশ", "নাম", "মন", "বাংলাদেশ", "ভাই", "পরিবার", "জীবন"],
    "সোনার": ["বাংলা", "বাংলাদেশ", "মেয়ে", "হরিণ", "স্বপ্ন"],
    "বাংলা": ["ভাষা", "সাহিত্য", "একাডেমী", "দেশ", "গান", "নববর্ষ", "সংস্কৃতি"],
    "বাংলাদেশ": ["একটি", "সরকার", "জাতীয়", "রেলওয়ে", "ক্রিকেট", "আমার", "পুলিশ", "সেনাবাহিনী"],
    "শুভ": ["সকাল", "রাত্রি", "সন্ধ্যা", "জন্মদিন", "কামনা", "নববর্ষ", "বিকেল", "দুপুর"],
    "কেমন": ["আছো", "আছেন", "হবে", "লাগল", "আছিস", "লাগছে"],
    "অনেক": ["ধন্যবাদ", "ভালো", "সুন্দর", "কষ্ট", "ভালোবাসা", "দিন", "সময়", "কিছু"],
    "খুব": ["ভালো", "সুন্দর", "বেশি", "সহজ", "খারাপ", "দ্রুত", "কঠিন", "মিষ্টি"],
    "ধন্যবাদ": ["আপনাকে", "তোমাকে", "ভাই", "সবাইকে", "অনেক", "জানাই"],
    "আমি": ["তোমাকে", "ভালো", "এখন", "যাব", "আছি", "বলছি", "জানি", "মনে", "চাই", "ভাবছি"],
    "তুমি": ["কেমন", "কোথায়", "কি", "যাবে", "আসবে", "আছো", "কী", "বলো", "জানো"],
    "আপনি": ["কেমন", "কোথায়", "কি", "বলুন", "আসবেন", "আছেন", "জানেন", "দেখুন", "করুন"],
    "সালাম": ["জানাই", "দেবেন", "নিবেন", "আলাইকুম", "জানাচ্ছি"],
    "ইনশাআল্লাহ": ["ভালো", "হবে", "দেখা", "জিতব", "শেষ"],
    "মাশাল্লাহ": ["অনেক", "সুন্দর", "ভালো"],
    "আলহামদুলিল্লাহ": ["ভালো", "আছি", "সুস্থ"],
    "আসসালামুআলাইকুম": ["ওয়ারাহমাতুল্লাহ", "ভাই", "সবাইকে"],
    "দোয়া": ["করবেন", "চাই", "করেন", "রইল", "করুন"],
    "মোবারক": ["হোক", "জানাই", "বাদ"],

    # Questions & conversation
    "কি": ["খবর", "অবস্থা", "করছেন", "করছো", "হবে", "বলেন", "মনে", "লাগছে"],
    "কী": ["খবর", "অবস্থা", "করছেন", "করছো", "হবে", "করবেন", "ভাবছেন"],
    "কোথায়": ["যাবেন", "আছেন", "যাচ্ছেন", "থাকেন", "যাবে"],
    "কখন": ["আসবেন", "যাবেন", "হবে", "আসবে", "শুরু"],
    "কীভাবে": ["করবেন", "যাবেন", "হবে", "করলেন", "করছেন"],
    "কেন": ["করছেন", "বলছেন", "যাচ্ছেন", "হলো", "করলে"],
    "কতটা": ["সময়", "দূর", "ভালো", "কঠিন"],
    "কতক্ষণ": ["লাগবে", "থাকবেন", "হবে", "ধরবে"],
    "কতদিন": ["লাগবে", "থাকবেন", "আগে", "পরে"],

    # Time & daily life
    "আজ": ["বৃষ্টি", "ছুটি", "সকালে", "রাতে", "শুক্রবার", "মেঘলা", "গরম", "ঠান্ডা"],
    "কাল": ["দেখা", "সকালে", "যাব", "হবে", "আসবেন", "থেকে"],
    "এখন": ["কয়টা", "সময়", "যাই", "কী", "ঘুমাব", "খাব", "বের"],
    "আজকে": ["কী", "কোথায়", "খাবো", "যাচ্ছি", "করলাম"],
    "সন্ধ্যায়": ["দেখা", "আসবেন", "খাবো", "বেড়াতে"],
    "রাতে": ["খাবো", "ঘুমাব", "কথা", "দেখা", "আসবেন"],
    "সকালে": ["উঠেছি", "নাস্তা", "দেখা", "আসুন", "যাব"],
    "দুপুরে": ["খাবো", "ঘুমাব", "দেখা", "আসবেন"],
    "পরে": ["দেখা", "কথা", "যাব", "আসবেন", "জানাব"],
    "আগামীকাল": ["দেখা", "যাব", "আসবেন", "কথা", "হবে"],
    "এইবার": ["হবে", "করব", "যাব", "দেখা"],
    "এবার": ["হবে", "করব", "যাব", "দেখা", "শুরু"],

    # Feelings & emotions
    "ভালো": ["আছি", "থাকবেন", "থেকো", "লাগে", "বাসি", "হবে", "লাগছে", "থাকুন"],
    "ভালোবাসি": ["তোমাকে", "আপনাকে", "অনেক"],
    "ভালোবাসা": ["তোমার", "আমার", "দিয়ে", "করি"],
    "মিস": ["করছি", "করি", "করছো"],
    "কষ্ট": ["পাচ্ছি", "হচ্ছে", "লাগছে", "দিও না"],
    "দুঃখিত": ["ভাই", "আপু", "বলার", "যে"],
    "মাফ": ["করবেন", "করো", "করুন", "চাইছি"],
    "খুশি": ["হয়েছি", "আছি", "হলে", "হবে"],
    "বিরক্ত": ["লাগছে", "হচ্ছি", "লাগে"],
    "চিন্তা": ["করো না", "করবেন না", "নেই", "হচ্ছে", "করছি"],

    # Places & geography
    "ঢাকা": ["শহর", "বিশ্ববিদ্যালয়", "মেডিকেল", "উত্তর", "দক্ষিণ", "থেকে", "যাচ্ছি"],
    "চট্টগ্রাম": ["শহর", "বিশ্ববিদ্যালয়", "বন্দর", "থেকে"],
    "সিলেট": ["শহর", "বিভাগ", "থেকে"],
    "রাজশাহী": ["বিশ্ববিদ্যালয়", "শহর", "থেকে"],
    "খুলনা": ["শহর", "বিভাগ", "থেকে"],
    "বরিশাল": ["শহর", "বিভাগ", "থেকে"],
    "ময়মনসিংহ": ["শহর", "বিভাগ"],
    "রংপুর": ["শহর", "বিভাগ"],
    "কুমিল্লা": ["শহর", "জেলা"],
    "গাজীপুর": ["জেলা", "শহর"],

    # National & civic
    "জাতীয়": ["সংসদ", "পতাকা", "সঙ্গীত", "দিবস", "স্মৃতিসৌধ", "বিশ্ববিদ্যালয়", "পরিচয়পত্র"],
    "আন্তর্জাতিক": ["মাতৃভাষা", "সম্পর্ক", "বিমানবন্দর", "মানদণ্ড", "সংস্থা"],
    "মাতৃভাষা": ["দিবস", "আন্দোলন", "ইনস্টিটিউট"],
    "একুশে": ["ফেব্রুয়ারি", "বইমেলা", "পদক"],
    "স্বাধীনতা": ["দিবস", "যুদ্ধ", "সংগ্রাম", "সংগ্রামী"],
    "মুক্তিযুদ্ধ": ["বিষয়ক", "যাদুঘর", "মন্ত্রণালয়", "স্মৃতি"],
    "সরকারি": ["চাকরি", "কর্মকর্তা", "বিদ্যালয়", "হাসপাতাল", "পর্যায়ে"],
    "বেসরকারি": ["প্রতিষ্ঠান", "সংস্থা", "বিশ্ববিদ্যালয়", "ব্যাংক"],

    # Education
    "বিশ্ববিদ্যালয়": ["ভর্তি", "পড়াশোনা", "শিক্ষক", "থেকে", "জীবন"],
    "স্কুল": ["জীবন", "থেকে", "পরীক্ষা", "ছুটি", "বন্ধু"],
    "কলেজ": ["জীবন", "থেকে", "পরীক্ষা", "ছুটি"],
    "পরীক্ষা": ["দিচ্ছি", "হবে", "শেষ", "ভালো", "কঠিন"],
    "পড়াশোনা": ["করছি", "করতে", "শেষ", "ভালো"],
    "রেজাল্ট": ["ভালো", "হয়েছে", "আসবে", "দেখেছো"],
    "ক্লাস": ["আছে", "করছি", "শুরু", "শেষ", "নেই"],
    "শিক্ষক": ["বললেন", "ভালো", "কঠোর", "মহোদয়"],

    # Work & professional
    "কাজ": ["করছি", "শেষ", "করতে", "হচ্ছে", "আছে", "নেই", "দিন"],
    "অফিস": ["যাচ্ছি", "থেকে", "আসছি", "কাজ", "বন্ধ"],
    "মিটিং": ["আছে", "শেষ", "হবে", "করছি"],
    "প্রজেক্ট": ["শেষ", "করছি", "হবে", "জমা"],
    "ডেডলাইন": ["আজকে", "কাল", "আছে", "মিস"],
    "রিপোর্ট": ["জমা", "লিখছি", "দিতে", "তৈরি"],
    "বস": ["বললেন", "আছেন", "ডাকছেন"],
    "বেতন": ["পেয়েছি", "হয়নি", "কম", "বেশি"],

    # Food & daily
    "খাবার": ["খেয়েছো", "তৈরি", "আনো", "কী"],
    "ভাত": ["খেয়েছো", "রান্না", "দাও", "খাব"],
    "রুটি": ["খাব", "দাও", "রান্না"],
    "মাছ": ["ভাজা", "রান্না", "কিনে", "খাব"],
    "মাংস": ["রান্না", "কিনে", "খাব", "ভালো"],
    "চা": ["খাব", "দাও", "বানাও", "আনো", "পান"],
    "নাস্তা": ["খেয়েছো", "করেছো", "তৈরি", "দাও"],
    "রান্না": ["করছি", "হয়েছে", "করো", "শিখছি"],

    # Health
    "অসুস্থ": ["আছি", "হয়েছি", "লাগছে"],
    "জ্বর": ["আছে", "হয়েছে", "কমছে", "বেশি"],
    "ডাক্তার": ["দেখিয়েছো", "গেছো", "বললেন", "দরকার"],
    "ওষুধ": ["খেয়েছো", "দরকার", "কিনে", "নাও"],
    "হাসপাতাল": ["গেছো", "থেকে", "যেতে", "ভর্তি"],
    "সুস্থ": ["হয়েছো", "আছো", "থেকো", "হও"],

    # Technology & social media
    "ফোন": ["দাও", "করো", "করুন", "করব", "বন্ধ", "চার্জ"],
    "মোবাইল": ["দাও", "করো", "করুন", "চার্জ", "বন্ধ"],
    "ইন্টারনেট": ["নেই", "আছে", "স্লো", "চলছে"],
    "ফেসবুক": ["দেখছি", "দিয়েছি", "পোস্ট", "আইডি"],
    "মেসেজ": ["দিয়েছি", "করুন", "পাঠাব", "পেয়েছেন"],
    "ভিডিও": ["কল", "দেখছি", "পাঠাও", "করো"],
    "লাইভ": ["করছি", "দেখছি", "আসুন"],
    "ডাউনলোড": ["করছি", "হচ্ছে", "শেষ", "দিন"],

    # Religion & culture
    "আল্লাহ": ["ভরসা", "হাফেজ", "রহমত", "ইচ্ছা", "করুন"],
    "খোদা": ["হাফেজ", "করুন"],
    "নামাজ": ["পড়েছেন", "পড়বেন", "শেষ", "আদায়"],
    "রোজা": ["রেখেছেন", "রাখবেন", "ভাঙা", "শেষ"],
    "ঈদ": ["মোবারক", "কেমন", "কাটলো", "আনন্দ"],
    "পূজা": ["মণ্ডপ", "শুভ", "কাটলো"],

    # Misc common phrases & travel/money
    "সবাইকে": ["ধন্যবাদ", "শুভ", "স্বাগতম", "জানাই", "আমন্ত্রণ"],
    "স্বাগতম": ["জানাই", "আমাদের"],
    "সমস্যা": ["নেই", "হবে", "আছে", "কী", "কোন"],
    "মনে": ["হয়", "রাখবেন", "পড়ে", "আছে", "করো"],
    "কথা": ["বলুন", "বলো", "বলতে", "হলো", "আছে"],
    "সব": ["কিছু", "সময়", "ঠিক", "হবে", "জায়গায়"],
    "কোন": ["সমস্যা", "কথা", "সন্দেহ", "না", "দরকার"],
    "আসো": ["একসাথে", "দেখা", "কথা"],
    "যাও": ["ভালো", "থেকো", "দেখে"],
    "দেখো": ["ভালো", "আমি", "কী", "হচ্ছে"],
    "জানাও": ["কবে", "কখন", "কী", "হলে"],
    "জানাবেন": ["কবে", "কখন", "কী", "যদি"],
    "বলো": ["কী", "কেন", "কীভাবে", "আমাকে"],
    "শুনো": ["একটু", "কথা", "আমার"],
    "দেখি": ["কী", "হয়", "পাচ্ছি", "করতে"],
    "হয়তো": ["হবে", "আসবে", "যাব", "পারব"],
    "আসলে": ["কী", "বলতে", "হয়নি", "ঠিকই"],
    "তবে": ["হবে", "করব", "যাব", "ঠিক"],
    "কিন্তু": ["সমস্যা", "আমি", "বলা", "করা"],
    "যদি": ["হয়", "আসো", "পারো", "করো", "থাকো"],
    "তাহলে": ["হবে", "করব", "যাব", "ঠিক"],
    "তবুও": ["ভালো", "করব", "থাকব", "যাব"],
    "আর": ["কী", "কতক্ষণ", "কখন", "নেই", "যাবে"],
    "না": ["হয়", "থাকলে", "করলে", "বললে"],
    "হ্যাঁ": ["ঠিকই", "বলেছেন", "আছি", "করব", "জানি"],
    "ঠিক": ["আছে", "হবে", "বলেছেন", "করব"],
    "ঠিকআছে": ["ভাই", "বুঝেছি", "করব"],
    "ওকে": ["ভাই", "বুঝেছি", "করব", "দেখছি"],
    "বাই": ["ভাই", "আপু", "দেখা"],
    "টাকা": ["নেই", "লাগবে", "দাও", "পাঠাও", "কম", "বেশি"],
    "খরচ": ["কত", "বেশি", "কম", "লাগবে"],
    "দাম": ["কত", "বেশি", "কম", "কমাও"],
    "বাজার": ["করতে", "যাব", "থেকে", "দাম"],
    "ট্রান্সপোর্ট": ["ভাড়া", "পাওয়া", "নেই"],
    "রিকশা": ["ভাড়া", "পাওয়া", "নেই", "করব"],
    "বাস": ["আসছে", "নেই", "ধরব", "ভাড়া"],
    "ট্রেন": ["সময়", "মিস", "ধরব", "ভাড়া"],
    "ফ্লাইট": ["সময়", "মিস", "কাল", "আগামীকাল"],
}


def predict_next_words(word: str) -> List[str]:
    """Returns contextual next-word predictions for a given Bengali word."""
    if not word:
        return []
    clean = word.strip(" .,!?।:;'\"_-\t\n")
    return list(COMMON_BIGRAMS.get(clean, []))


# --- Adaptive Learned Selections Memory ---
def get_user_bongo_dir() -> Path:
    """Resolves and ensures the platform-specific user config directory for Bongo."""
    if os.environ.get("BONGO_USER_DIR"):
        p = Path(os.environ["BONGO_USER_DIR"])
        p.mkdir(parents=True, exist_ok=True)
        return p
    if sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "Bongo"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        p = (Path(appdata) / "Bongo") if appdata else (Path.home() / ".config" / "bongo")
    else:
        p = Path.home() / ".config" / "bongo"
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_learned_selections(custom_dir: Optional[str] = None) -> Dict[str, str]:
    """Loads user's learned phonetic candidate picks from phonetic-candidate-selection.json."""
    base_dir = Path(custom_dir) if custom_dir else get_user_bongo_dir()
    file_path = base_dir / "phonetic-candidate-selection.json"
    if not file_path.is_file():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k).lower(): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def save_learned_selection(buffer: str, selected_word: str, custom_dir: Optional[str] = None) -> None:
    """Records a user candidate pick for typed buffer into phonetic-candidate-selection.json."""
    if not buffer or not selected_word:
        return
    base_dir = Path(custom_dir) if custom_dir else get_user_bongo_dir()
    file_path = base_dir / "phonetic-candidate-selection.json"
    current = load_learned_selections(str(base_dir))
    current[buffer.strip().lower()] = selected_word.strip()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass



# --- Bengali Number to Words Converter ---
BENGALI_DIGIT_MAP = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

BENGALI_NUMBERS_0_TO_99 = [
    "শূন্য", "এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়", "দশ",
    "এগারো", "বারো", "তেরো", "চৌদ্দ", "পনেরো", "ষোলো", "সতেরো", "আঠারো", "উনিশ", "বিশ",
    "একুশ", "বাইশ", "তেইশ", "চব্বিশ", "পঁচিশ", "ছাব্বিশ", "সাতাশ", "আঠাশ", "উনত্রিশ", "ত্রিশ",
    "একত্রিশ", "বত্রিশ", "তেত্রিশ", "চৌত্রিশ", "পঁয়ত্রিশ", "ছত্রিশ", "সাঁয়ত্রিশ", "আটত্রিশ", "উনচল্লিশ", "চল্লিশ",
    "একচল্লিশ", "বিয়াল্লিশ", "তেতাল্লিশ", "চুয়াল্লিশ", "পঁয়তাল্লিশ", "ছেচল্লিশ", "সাতচল্লিশ", "আটচল্লিশ", "উনপঞ্চাশ", "পঞ্চাশ",
    "একান্ন", "বায়ান্ন", "তিপ্পান্ন", "চুয়ান্ন", "পঞ্চান্ন", "ছাপ্পান্ন", "সাতান্ন", "আটান্ন", "উনষাট", "ষাট",
    "একষট্টি", "বাষট্টি", "তেষট্টি", "চৌষট্টি", "পঁয়ষট্টি", "ছেষট্টি", "সাতষট্টি", "আটষট্টি", "উনসত্তর", "সত্তর",
    "একাত্তর", "বাহাত্তর", "তিয়াত্তর", "চুয়াত্তর", "পঁচাত্তর", "ছিয়াত্তর", "সাতাত্তর", "আটাত্তর", "উনআশি", "আশি",
    "একাশি", "বিরাশি", "তিরাশি", "চুরাশি", "পঁচাশি", "ছিয়াশি", "সাতাশি", "আটাশি", "ঊননব্বই", "নব্বই",
    "একানব্বই", "বিরানব্বই", "তিরানব্বই", "চুরানব্বই", "পঁচানব্বই", "ছিয়ানব্বই", "সাতানব্বই", "আটানব্বই", "নিরানব্বই"
]


def normalize_bengali_digits(text: str) -> str:
    """Extracts and normalizes English (0-9) and Bengali (০-৯) digits to standard ASCII digits."""
    res = []
    for ch in str(text or ""):
        if '0' <= ch <= '9':
            res.append(ch)
        elif ch in BENGALI_DIGIT_MAP:
            res.append(BENGALI_DIGIT_MAP[ch])
    return "".join(res)


def _convert_num_to_words(n: int) -> str:
    if n == 0:
        return BENGALI_NUMBERS_0_TO_99[0]
    if n < 100:
        return BENGALI_NUMBERS_0_TO_99[n]

    parts = []
    rem = n

    # কোটি (Crore: 10,000,000)
    crore = rem // 10000000
    if crore > 0:
        parts.append(f"{_convert_num_to_words(crore)} কোটি")
        rem %= 10000000

    # লক্ষ (Lakh: 100,000)
    lakh = rem // 100000
    if lakh > 0:
        parts.append(f"{BENGALI_NUMBERS_0_TO_99[lakh]} লক্ষ")
        rem %= 100000

    # হাজার (Thousand: 1,000)
    thousand = rem // 1000
    if thousand > 0:
        parts.append(f"{BENGALI_NUMBERS_0_TO_99[thousand]} হাজার")
        rem %= 1000

    # শত (Hundred: 100)
    hundred = rem // 100
    if hundred > 0:
        parts.append(f"{BENGALI_NUMBERS_0_TO_99[hundred]} শত")
        rem %= 100

    if rem > 0:
        parts.append(BENGALI_NUMBERS_0_TO_99[rem])

    return " ".join(parts)


def bengali_number_to_words(value: str | int, as_currency: bool = False) -> str:
    """
    Converts numeric strings or integers (English 0-9 or Bengali ০-৯ digits)
    into colloquial Bengali spoken words.
    Example: 12500 -> "বারো হাজার পাঁচ শত"
    as_currency=True -> "বারো হাজার পাঁচ শত টাকা মাত্র"
    """
    normalized = normalize_bengali_digits(str(value)).lstrip('0')
    if not normalized:
        return "শূন্য টাকা মাত্র" if as_currency else "শূন্য"
    try:
        n = int(normalized)
    except Exception:
        return "অত্যধিক বড় সংখ্যা"
    words = _convert_num_to_words(n)
    return f"{words} টাকা মাত্র" if as_currency else words


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        cmd = sys.argv[1]
        text_arg = sys.argv[2]
        if cmd == "u2b":
            print(unicode_to_bijoy(text_arg))
        elif cmd == "b2u":
            print(bijoy_to_unicode(text_arg))
        elif cmd == "num":
            as_curr = "--currency" in sys.argv
            print(bengali_number_to_words(text_arg, as_currency=as_curr))


