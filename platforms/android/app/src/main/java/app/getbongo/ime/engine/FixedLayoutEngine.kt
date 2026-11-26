package app.getbongo.ime.engine

/**
 * Pure-Kotlin fixed Bengali layout engine implementing:
 * - Layout 1: National / Jatiyo BDS 1738:2004 (Bijoy compatible, vendor/rust/riti/data/National.json)
 * - Layout 2: Borno / SafeWorks (vendor/rust/riti/data/Borno.json)
 *
 * Mirrors riti's FixedMethod behavior including pre-base kar reordering (e.g. d+j -> কি),
 * two-part vowel joining, Hasanta+Kar independent vowel formation, and conjunct (যুক্তাক্ষর)
 * preservation when Hasanta follows a pre-base kar.
 */
class FixedLayoutEngine {

    companion object {
        const val LAYOUT_PHONETIC = 0
        const val LAYOUT_NATIONAL = 1
        const val LAYOUT_BORNO = 2

        private const val B_HASANTA = '\u09CD'
        private const val B_CHANDRA = '\u0981'
        private const val B_ZWNJ = '\u200C'
        private const val B_ZWJ = '\u200D'
        private const val B_R = '\u09B0'
        private const val B_ZA = '\u09AF'
        private const val B_LENGTH_MARK = '\u09D7'

        private const val B_AA = '\u0986'
        private const val B_I = '\u0987'
        private const val B_II = '\u0988'
        private const val B_U = '\u0989'
        private const val B_UU = '\u098A'
        private const val B_RRI = '\u098B'
        private const val B_E = '\u098F'
        private const val B_OI = '\u0990'
        private const val B_O = '\u0993'
        private const val B_OU = '\u0994'

        private const val B_AA_KAR = '\u09BE'
        private const val B_I_KAR = '\u09BF'
        private const val B_II_KAR = '\u09C0'
        private const val B_U_KAR = '\u09C1'
        private const val B_UU_KAR = '\u09C2'
        private const val B_RRI_KAR = '\u09C3'
        private const val B_E_KAR = '\u09C7'
        private const val B_OI_KAR = '\u09C8'
        private const val B_O_KAR = '\u09CB'
        private const val B_OU_KAR = '\u09CC'

        private val VOWELS = setOf('অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'ঌ', 'এ', 'ঐ', 'ও', 'ঔ')
        private val KARS = setOf(B_AA_KAR, B_I_KAR, B_II_KAR, B_U_KAR, B_UU_KAR, B_RRI_KAR, B_E_KAR, B_OI_KAR, B_O_KAR, B_OU_KAR)
        private val LEFT_STANDING_KARS = setOf(B_I_KAR, B_E_KAR, B_OI_KAR)
        private val PUNCT_MARKS = "`~!@#\$%^+*-_=+\\|\"/;:,./?><()[]{}"

        private val KAR_TO_VOWEL = mapOf(
            B_AA_KAR to B_AA,
            B_I_KAR to B_I,
            B_II_KAR to B_II,
            B_U_KAR to B_U,
            B_UU_KAR to B_UU,
            B_RRI_KAR to B_RRI,
            B_E_KAR to B_E,
            B_OI_KAR to B_OI,
            B_O_KAR to B_O,
            B_OU_KAR to B_OU
        )

        val NATIONAL_MAP: Map<Char, String> = mapOf(
            // Lowercase letters (Normal layer)
            'a' to "ৃ", 'b' to "ন", 'c' to "ে", 'd' to "ি", 'e' to "ড",
            'f' to "া", 'g' to "্", 'h' to "ব", 'i' to "হ", 'j' to "ক",
            'k' to "ত", 'l' to "দ", 'm' to "ম", 'n' to "স", 'o' to "গ",
            'p' to "ড়", 'q' to "ঙ", 'r' to "প", 's' to "ু", 't' to "ট",
            'u' to "জ", 'v' to "র", 'w' to "য", 'x' to "ও", 'y' to "চ",
            'z' to "্র",
            // Uppercase letters (Shift layer)
            'A' to "ঋ", 'B' to "ণ", 'C' to "ৈ", 'D' to "ী", 'E' to "ঢ",
            'F' to "অ", 'G' to "।", 'H' to "ভ", 'I' to "ঞ", 'J' to "খ",
            'K' to "থ", 'L' to "ধ", 'M' to "শ", 'N' to "ষ", 'O' to "ঘ",
            'P' to "ঢ়", 'Q' to "ং", 'R' to "ফ", 'S' to "ূ", 'T' to "ঠ",
            'U' to "ঝ", 'V' to "ল", 'W' to "য়", 'X' to "ৗ", 'Y' to "ছ",
            'Z' to "্য",
            // Symbols & digits from National.json
            '[' to "ো", '{' to "ৌ", ']' to "ৗ", '}' to "ৎ",
            '\\' to "ৎ", '|' to "॥", '^' to "ঁ", '_' to "ঃ",
            '+' to "ৃ", '$' to "৳",
            '0' to "০", '1' to "১", '2' to "২", '3' to "৩", '4' to "৪",
            '5' to "৫", '6' to "৬", '7' to "৭", '8' to "৮", '9' to "৯"
        )

        val BORNO_MAP: Map<Char, String> = mapOf(
            // Lowercase letters (Normal layer)
            'a' to "া", 'b' to "ব", 'c' to "চ", 'd' to "দ", 'e' to "ে",
            'f' to "ফ", 'g' to "গ", 'h' to "্", 'i' to "ি", 'j' to "জ",
            'k' to "ক", 'l' to "ল", 'm' to "ম", 'n' to "ন", 'o' to "ো",
            'p' to "প", 'q' to "ং", 'r' to "র", 's' to "স", 't' to "ত",
            'u' to "ু", 'v' to "ভ", 'w' to "ঢ", 'x' to "ষ", 'y' to "ধ",
            'z' to "য",
            // Uppercase letters (Shift layer)
            'A' to "অ", 'B' to "য়", 'C' to "ছ", 'D' to "ড", 'E' to "ৈ",
            'F' to "র্", 'G' to "ঘ", 'H' to "হ", 'I' to "ী", 'J' to "ঝ",
            'K' to "খ", 'L' to "।", 'M' to "ঞ", 'N' to "ণ", 'O' to "ৌ",
            'P' to "্র", 'Q' to "ঙ", 'R' to "ৃ", 'S' to "শ", 'T' to "ট",
            'U' to "ূ", 'V' to "্য", 'W' to "ঠ", 'X' to "ঢ়", 'Y' to "থ",
            'Z' to "ড়",
            // Symbols & digits from Borno.json
            '@' to "ঁ", '^' to "ঃ", '&' to "ৎ", '$' to "৳",
            '\\' to "ৱ", '|' to "ৰ",
            '0' to "০", '1' to "১", '2' to "২", '3' to "৩", '4' to "৪",
            '5' to "৫", '6' to "৬", '7' to "৭", '8' to "৮", '9' to "৯"
        )

        fun getDisplayLabel(key: Char, layout: Int, shifted: Boolean): String? {
            val lookupChar = if (shifted) key.uppercaseChar() else key.lowercaseChar()
            val map = when (layout) {
                LAYOUT_NATIONAL -> NATIONAL_MAP
                LAYOUT_BORNO -> BORNO_MAP
                else -> return null
            }
            return map[lookupChar]
        }
    }

    var currentLayout: Int = LAYOUT_NATIONAL
        private set

    private val buffer = StringBuilder()
    private var pendingKar: Char? = null

    fun setLayout(layout: Int) {
        currentLayout = layout
        reset()
    }

    fun hasSession(): Boolean = buffer.isNotEmpty() || pendingKar != null

    fun reset() {
        buffer.clear()
        pendingKar = null
    }

    fun preedit(): String {
        val pk = pendingKar
        return if (pk != null) buffer.toString() + pk else buffer.toString()
    }

    fun commitText(): String {
        val pk = pendingKar
        if (pk != null) {
            val rmc = buffer.lastOrNull()
            if (buffer.isEmpty() || rmc == null || rmc in VOWELS || rmc in PUNCT_MARKS || rmc.isWhitespace()) {
                buffer.append(KAR_TO_VOWEL[pk] ?: pk)
            } else {
                buffer.append(pk)
            }
            pendingKar = null
        }
        val result = buffer.toString()
        buffer.clear()
        return result
    }

    fun feedChar(rawChar: Char): String {
        val map = when (currentLayout) {
            LAYOUT_NATIONAL -> NATIONAL_MAP
            LAYOUT_BORNO -> BORNO_MAP
            else -> emptyMap()
        }
        val mapped = map[rawChar] ?: rawChar.toString()
        processMappedValue(mapped)
        return preedit()
    }

    fun handleBackspace(): Boolean {
        if (pendingKar != null) {
            pendingKar = null
            return hasSession()
        }
        if (buffer.isNotEmpty()) {
            buffer.deleteCharAt(buffer.length - 1)
            return hasSession()
        }
        return false
    }

    private fun processMappedValue(value: String) {
        if (value.isEmpty()) return
        val rmc = buffer.lastOrNull()

        // Zo-fola (্য) and Ro-fola (্র) insertion
        if (value == "$B_HASANTA$B_ZA" || value == "$B_HASANTA$B_R") {
            if (value == "$B_HASANTA$B_ZA" && rmc == B_R && (buffer.length < 2 || buffer[buffer.length - 2] != B_HASANTA)) {
                buffer.append(B_ZWJ)
            }
            if (rmc != null && rmc in LEFT_STANDING_KARS) {
                buffer.deleteCharAt(buffer.length - 1)
                buffer.append(value)
                buffer.append(rmc)
                return
            }
            buffer.append(value)
            return
        }

        // Old-style Reph insertion (র্)
        if (value == "$B_R$B_HASANTA") {
            val pKar = pendingKar
            if (pKar != null) {
                buffer.append(value)
                return
            }
            buffer.append(value)
            return
        }

        if (value.length == 1) {
            val ch = value[0]
            if (ch in KARS) {
                handleKarInput(ch)
                return
            }

            if (ch == B_HASANTA && rmc == B_HASANTA) {
                buffer.append(B_ZWNJ)
                return
            }

            if (ch == B_LENGTH_MARK && rmc == B_HASANTA) {
                buffer.deleteCharAt(buffer.length - 1)
                buffer.append(B_OU)
                return
            }

            if (ch == B_HASANTA && rmc != null && rmc in LEFT_STANDING_KARS) {
                pendingKar = rmc
                buffer.deleteCharAt(buffer.length - 1)
                buffer.append(B_HASANTA)
                return
            }

            if (rmc == B_E_KAR && ch == B_LENGTH_MARK) {
                buffer.deleteCharAt(buffer.length - 1)
                buffer.append(B_OU_KAR)
                return
            }
        }

        val pKar = pendingKar
        if (pKar != null) {
            buffer.append(value)
            if (value.last() == B_HASANTA) {
                return
            }
            buffer.append(pKar)
            pendingKar = null
            return
        }

        buffer.append(value)
    }

    private fun handleKarInput(kar: Char) {
        val rmc = buffer.lastOrNull()
        if (rmc != B_HASANTA && kar in LEFT_STANDING_KARS && pendingKar == null) {
            pendingKar = kar
            return
        }

        if (rmc == B_E_KAR && (kar == B_AA_KAR || kar == B_OU_KAR)) {
            buffer.deleteCharAt(buffer.length - 1)
            buffer.append(if (kar == B_AA_KAR) B_O_KAR else B_OU_KAR)
            return
        }

        val existingPending = pendingKar
        if (existingPending != null) {
            if (rmc == B_HASANTA) {
                buffer.deleteCharAt(buffer.length - 1)
                buffer.append(existingPending)
                pendingKar = null
                buffer.append(B_HASANTA)
            } else {
                if (buffer.isEmpty() || rmc == null || rmc in VOWELS || rmc in PUNCT_MARKS || rmc.isWhitespace()) {
                    buffer.append(KAR_TO_VOWEL[existingPending] ?: existingPending)
                }
                pendingKar = null
                handleKarInput(kar)
                return
            }
        }

        val updatedRmc = buffer.lastOrNull()
        if (buffer.isEmpty() || updatedRmc == null || updatedRmc in VOWELS || updatedRmc in PUNCT_MARKS || updatedRmc.isWhitespace()) {
            buffer.append(KAR_TO_VOWEL[kar] ?: kar)
        } else if (updatedRmc == B_CHANDRA) {
            buffer.deleteCharAt(buffer.length - 1)
            buffer.append(kar)
            buffer.append(B_CHANDRA)
        } else if (updatedRmc == B_HASANTA) {
            val indep = KAR_TO_VOWEL[kar]
            if (indep != null) {
                buffer.deleteCharAt(buffer.length - 1)
                buffer.append(indep)
            } else {
                buffer.append(kar)
            }
        } else {
            buffer.append(kar)
        }
    }
}
