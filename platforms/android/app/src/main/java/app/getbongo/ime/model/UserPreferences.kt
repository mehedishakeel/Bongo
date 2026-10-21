package app.getbongo.ime.model

import android.content.Context
import android.content.SharedPreferences

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
    }
}
