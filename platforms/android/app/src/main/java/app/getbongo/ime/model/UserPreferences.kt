package app.getbongo.ime.model

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

/**
 * Manages user preferences for Bongo Android IME.
 */
class UserPreferences(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var typingMode: Int
        get() = prefs.getInt(KEY_TYPING_MODE, 0)
        set(value) = prefs.edit().putInt(KEY_TYPING_MODE, value).apply()

    var keyboardLayout: Int
        get() = prefs.getInt(KEY_KEYBOARD_LAYOUT, 0)
        set(value) = prefs.edit().putInt(KEY_KEYBOARD_LAYOUT, value).apply()

    var suggestEmoji: Boolean
        get() = prefs.getBoolean(KEY_SUGGEST_EMOJI, true)
        set(value) = prefs.edit().putBoolean(KEY_SUGGEST_EMOJI, value).apply()

    var hapticFeedback: Boolean
        get() = prefs.getBoolean(KEY_HAPTIC, true)
        set(value) = prefs.edit().putBoolean(KEY_HAPTIC, value).apply()

    var soundFeedback: Boolean
        get() = prefs.getBoolean(KEY_SOUND, false)
        set(value) = prefs.edit().putBoolean(KEY_SOUND, value).apply()

    var theme: String
        get() = prefs.getString(KEY_THEME, "midnight") ?: "midnight"
        set(value) = prefs.edit().putString(KEY_THEME, value).apply()

    var keyboardHeightDp: Int
        get() = prefs.getInt(KEY_KEYBOARD_HEIGHT, 270)
        set(value) = prefs.edit().putInt(KEY_KEYBOARD_HEIGHT, value).apply()

    var doubleSpacePeriod: Boolean
        get() = prefs.getBoolean(KEY_DOUBLE_SPACE_PERIOD, true)
        set(value) = prefs.edit().putBoolean(KEY_DOUBLE_SPACE_PERIOD, value).apply()

    var longPressSymbols: Boolean
        get() = prefs.getBoolean(KEY_LONG_PRESS_SYMBOLS, true)
        set(value) = prefs.edit().putBoolean(KEY_LONG_PRESS_SYMBOLS, value).apply()

    var cursorScrubbing: Boolean
        get() = prefs.getBoolean(KEY_CURSOR_SCRUBBING, true)
        set(value) = prefs.edit().putBoolean(KEY_CURSOR_SCRUBBING, value).apply()

    var bengaliDigits: Boolean
        get() = prefs.getBoolean(KEY_BENGALI_DIGITS, false)
        set(value) = prefs.edit().putBoolean(KEY_BENGALI_DIGITS, value).apply()

    var showNumberRow: Boolean
        get() = prefs.getBoolean(KEY_SHOW_NUMBER_ROW, false)
        set(value) = prefs.edit().putBoolean(KEY_SHOW_NUMBER_ROW, value).apply()

    var keyPopupPreview: Boolean
        get() = prefs.getBoolean(KEY_POPUP_PREVIEW, true)
        set(value) = prefs.edit().putBoolean(KEY_POPUP_PREVIEW, value).apply()

    var swipeDeleteWords: Boolean
        get() = prefs.getBoolean(KEY_SWIPE_DELETE, true)
        set(value) = prefs.edit().putBoolean(KEY_SWIPE_DELETE, value).apply()

    var vibrationDurationMs: Int
        get() = prefs.getInt(KEY_VIBRATION_DURATION, 25)
        set(value) = prefs.edit().putInt(KEY_VIBRATION_DURATION, value).apply()

    var showKeyBorders: Boolean
        get() = prefs.getBoolean(KEY_KEY_BORDERS, false)
        set(value) = prefs.edit().putBoolean(KEY_KEY_BORDERS, value).apply()

    var oneHandedMode: String
        get() = prefs.getString(KEY_ONE_HANDED_MODE, "none") ?: "none"
        set(value) = prefs.edit().putString(KEY_ONE_HANDED_MODE, value).apply()

    var learnedSelectionsJson: String
        get() = prefs.getString(KEY_LEARNED_SELECTIONS, "{}") ?: "{}"
        set(value) = prefs.edit().putString(KEY_LEARNED_SELECTIONS, value).apply()

    var clipboardHistoryJson: String
        get() = prefs.getString(KEY_CLIPBOARD_HISTORY, "[]") ?: "[]"
        set(value) = prefs.edit().putString(KEY_CLIPBOARD_HISTORY, value).apply()

    var candidateCount: Int
        get() = prefs.getInt(KEY_CANDIDATE_COUNT, 9).coerceIn(3, 9)
        set(value) = prefs.edit().putInt(KEY_CANDIDATE_COUNT, value.coerceIn(3, 9)).apply()

    var glideTyping: Boolean
        get() = prefs.getBoolean(KEY_GLIDE_TYPING, true)
        set(value) = prefs.edit().putBoolean(KEY_GLIDE_TYPING, value).apply()

    var autoCapitalization: Boolean
        get() = prefs.getBoolean(KEY_AUTO_CAP, true)
        set(value) = prefs.edit().putBoolean(KEY_AUTO_CAP, value).apply()

    var statsWordsTyped: Int
        get() = prefs.getInt(KEY_STATS_WORDS, 0)
        set(value) = prefs.edit().putInt(KEY_STATS_WORDS, value).apply()

    var statsBanglaWords: Int
        get() = prefs.getInt(KEY_STATS_BN_WORDS, 0)
        set(value) = prefs.edit().putInt(KEY_STATS_BN_WORDS, value).apply()

    var statsEnglishWords: Int
        get() = prefs.getInt(KEY_STATS_EN_WORDS, 0)
        set(value) = prefs.edit().putInt(KEY_STATS_EN_WORDS, value).apply()

    var statsGlidesUsed: Int
        get() = prefs.getInt(KEY_STATS_GLIDES, 0)
        set(value) = prefs.edit().putInt(KEY_STATS_GLIDES, value).apply()

    fun recordTypedWord(isBangla: Boolean, isGlide: Boolean = false) {
        val editor = prefs.edit()
            .putInt(KEY_STATS_WORDS, statsWordsTyped + 1)
        if (isBangla) {
            editor.putInt(KEY_STATS_BN_WORDS, statsBanglaWords + 1)
        } else {
            editor.putInt(KEY_STATS_EN_WORDS, statsEnglishWords + 1)
        }
        if (isGlide) {
            editor.putInt(KEY_STATS_GLIDES, statsGlidesUsed + 1)
        }
        editor.apply()
    }

    fun resetTypingStats() {
        prefs.edit()
            .putInt(KEY_STATS_WORDS, 0)
            .putInt(KEY_STATS_BN_WORDS, 0)
            .putInt(KEY_STATS_EN_WORDS, 0)
            .putInt(KEY_STATS_GLIDES, 0)
            .apply()
    }

    fun getClipboardEntries(nowMs: Long = System.currentTimeMillis()): MutableList<ClipboardEntry> =
        ClipboardStoreLogic.parseJson(clipboardHistoryJson, nowMs)

    fun saveClipboardEntries(entries: List<ClipboardEntry>) {
        clipboardHistoryJson = ClipboardStoreLogic.toJson(entries)
    }

    fun getClipboardHistory(): MutableList<String> =
        getClipboardEntries().map { it.text }.toMutableList()

    fun saveClipboardHistory(list: List<String>) {
        val entries = list.mapIndexed { idx, txt ->
            ClipboardEntry(id = "clip_${idx}_${txt.hashCode()}", text = txt, timestampMs = System.currentTimeMillis())
        }
        saveClipboardEntries(entries)
    }

    fun getLearnedSelections(): MutableMap<String, String> {
        val res = mutableMapOf<String, String>()
        try {
            val json = JSONObject(learnedSelectionsJson)
            val keys = json.keys()
            while (keys.hasNext()) {
                val k = keys.next()
                res[k.lowercase()] = json.getString(k)
            }
        } catch (_: Exception) {}
        return res
    }

    fun learnSelection(typed: String, candidate: String) {
        val cleanTyped = typed.trim().lowercase()
        val cleanCandidate = candidate.trim()
        if (cleanTyped.isEmpty() || cleanCandidate.isEmpty()) return
        val current = getLearnedSelections()
        current[cleanTyped] = cleanCandidate
        val obj = JSONObject()
        current.forEach { (k, v) -> obj.put(k, v) }
        learnedSelectionsJson = obj.toString()
    }

    fun clearLearnedSelections() {
        learnedSelectionsJson = "{}"
    }

    fun registerListener(listener: SharedPreferences.OnSharedPreferenceChangeListener) {
        prefs.registerOnSharedPreferenceChangeListener(listener)
    }

    fun unregisterListener(listener: SharedPreferences.OnSharedPreferenceChangeListener) {
        prefs.unregisterOnSharedPreferenceChangeListener(listener)
    }

    companion object {
        const val PREFS_NAME = "bongo_preferences"
        const val KEY_KEYBOARD_LAYOUT = "keyboard_layout"
        const val KEY_TYPING_MODE = "typing_mode"
        const val KEY_SUGGEST_EMOJI = "suggest_emoji"
        const val KEY_HAPTIC = "haptic_feedback"
        const val KEY_SOUND = "sound_feedback"
        const val KEY_THEME = "theme"
        const val KEY_KEYBOARD_HEIGHT = "keyboard_height"
        const val KEY_DOUBLE_SPACE_PERIOD = "double_space_period"
        const val KEY_LONG_PRESS_SYMBOLS = "long_press_symbols"
        const val KEY_CURSOR_SCRUBBING = "cursor_scrubbing"
        const val KEY_BENGALI_DIGITS = "bengali_digits"
        const val KEY_SHOW_NUMBER_ROW = "show_number_row"
        const val KEY_POPUP_PREVIEW = "key_popup_preview"
        const val KEY_SWIPE_DELETE = "swipe_delete_words"
        const val KEY_VIBRATION_DURATION = "vibration_duration_ms"
        const val KEY_KEY_BORDERS = "show_key_borders"
        const val KEY_ONE_HANDED_MODE = "one_handed_mode"
        const val KEY_LEARNED_SELECTIONS = "learned_selections"
        const val KEY_CLIPBOARD_HISTORY = "clipboard_history"
        const val KEY_CANDIDATE_COUNT = "candidate_count"
        const val KEY_GLIDE_TYPING = "glide_typing"
        const val KEY_AUTO_CAP = "auto_capitalization"
        const val KEY_STATS_WORDS = "stats_words_typed"
        const val KEY_STATS_BN_WORDS = "stats_bangla_words"
        const val KEY_STATS_EN_WORDS = "stats_english_words"
        const val KEY_STATS_GLIDES = "stats_glides_used"
    }
}
