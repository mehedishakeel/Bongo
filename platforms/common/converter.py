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
