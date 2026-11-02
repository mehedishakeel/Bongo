package app.getbongo.ime.ui

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.StateListDrawable
import android.media.AudioManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.util.AttributeSet
import android.util.TypedValue
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.PopupWindow
import android.widget.TextView
import app.getbongo.ime.model.ThemePalette
import app.getbongo.ime.model.UserPreferences

/**
 * Modern Bengali & English soft keyboard view for Bongo Android IME,
 * replicating the classic, beloved Ridmik keyboard layout, aesthetics, and gesture flow:
 * - 4-Row clean ergonomic QWERTY layout with subtle long-press symbol hints
 * - Spacebar swipe gesture to toggle seamlessly between English and Bongo (Bangla phonetic)
 * - Spacebar floating popup preview card showing active language on touch / swipe
 * - Key Popup Magnifier on touch
 * - Continuous Backspace auto-repeat on hold & swipe-left to delete words
 * - Dynamic Action button (Go, Search, Send, Next, Done, ⏎)
 * - Symbols and Shifted Symbols (=\<) screens matching Ridmik exactly
 * - Contextual URL mode (showing / instead of ,)
 * - Haptic and audio feedback
 */
class BongoKeyboardView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : LinearLayout(context, attrs, defStyleAttr) {

    private val userPrefs = UserPreferences(context)
    private val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    private val repeatHandler = Handler(Looper.getMainLooper())
    private val popupDismissHandler = Handler(Looper.getMainLooper())
    private val spaceDismissHandler = Handler(Looper.getMainLooper())

    var isShifted = false
        private set
    var isBangla = true
        private set
    var isSymbols = false
        private set
    var isSymbolsShifted = false
        private set

    var actionLabel: String = "Go"
        private set
    var isUriInput: Boolean = false
        private set

    private var palette: ThemePalette = ThemePalette.getPalette(userPrefs.theme)

    var onKeyClickListener: ((KeyAction) -> Unit)? = null

    // View recycling and in-place reference caching for zero-latency updates
    private val letterKeyViews = mutableMapOf<String, TextView>()
    private val letterKeyHintViews = mutableMapOf<String, TextView>()
    private var shiftKeyView: TextView? = null
    private var spaceKeyView: TextView? = null
    private var periodKeyView: TextView? = null
    private var commaKeyView: TextView? = null
    private var actionKeyView: TextView? = null

    // Key Popup Magnifier
    private var activePopupAnchor: View? = null
    private val popupTextView = TextView(context).apply {
        gravity = Gravity.CENTER
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 26f)
        typeface = Typeface.DEFAULT_BOLD
    }
    private val popupWindow = PopupWindow(popupTextView, dp(52), dp(62)).apply {
        isClippingEnabled = false
        isTouchable = false
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            elevation = dp(8).toFloat()
        }
    }
    private val popupDismissRunnable = Runnable {
        try {
            if (popupWindow.isShowing) {
                popupWindow.dismiss()
            }
        } catch (_: Exception) {}
    }

    // Spacebar Floating Popup Preview Card
    private val spacePopupTextView = TextView(context).apply {
        gravity = Gravity.CENTER
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 17f)
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(Color.WHITE)
    }
    private val spacePopupWindow = PopupWindow(spacePopupTextView, dp(116), dp(44)).apply {
        isClippingEnabled = false
        isTouchable = false
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            elevation = dp(8).toFloat()
        }
    }
    private val spaceDismissRunnable = Runnable {
        try {
            if (spacePopupWindow.isShowing) {
                spacePopupWindow.dismiss()
            }
        } catch (_: Exception) {}
    }

    sealed class KeyAction {
        data class CharacterKey(val ch: Char) : KeyAction()
        object Shift : KeyAction()
        object Backspace : KeyAction()
        object DeleteWord : KeyAction()
        object Space : KeyAction()
        object Return : KeyAction()
        object ToggleLanguage : KeyAction()
        object ToggleSymbols : KeyAction()
        object ToggleEmoji : KeyAction()
        object SwitchImePicker : KeyAction()
        object OpenSettings : KeyAction()
        object OpenThemes : KeyAction()
        object ToggleVoice : KeyAction()
        object CursorLeft : KeyAction()
        object CursorRight : KeyAction()
        object Esc : KeyAction()
        object Tab : KeyAction()
        object Ctrl : KeyAction()
    }

    private companion object {
        val ROW1_HINTS_EN = mapOf('q' to '1', 'w' to '2', 'e' to '3', 'r' to '4', 't' to '5', 'y' to '6', 'u' to '7', 'i' to '8', 'o' to '9', 'p' to '0')
        val ROW1_HINTS_BN = mapOf('q' to '১', 'w' to '২', 'e' to '৩', 'r' to '৪', 't' to '৫', 'y' to '৬', 'u' to '৭', 'i' to '৮', 'o' to '৯', 'p' to '০')
        val ROW2_HINTS = mapOf('a' to '@', 's' to '#', 'd' to '&', 'f' to '*', 'g' to '-', 'h' to '!', 'j' to '?', 'k' to '(', 'l' to ')')
        val ROW3_HINTS = mapOf('z' to '"', 'b' to '\'', 'n' to ':', 'm' to '/')
        val SYM2_HINTS = mapOf('৳' to '$', '*' to '★', '-' to '_', '(' to '<', ')' to '>')
        val SYM3_HINTS = mapOf(':' to 'ঁ')
    }

    init {
        orientation = VERTICAL
        setBackgroundColor(palette.surfaceColor)
        setPadding(dp(2), dp(3), dp(2), dp(4))
        buildKeyboard()
    }

    fun applyTheme(newPalette: ThemePalette) {
        palette = newPalette
        setBackgroundColor(palette.surfaceColor)
        popupTextView.setTextColor(palette.keyTextColor)
        popupTextView.background = GradientDrawable().apply {
            cornerRadius = dp(10).toFloat()
            setColor(palette.keyNormalColor)
            setStroke(dp(1), palette.stripPrimaryBorder)
        }
        buildKeyboard()
    }

    fun setBanglaMode(active: Boolean) {
        if (isBangla != active) {
            isBangla = active
            if (!isSymbols && !isOptionsVisible && spaceKeyView != null) {
                updateLanguageViews()
            } else {
                buildKeyboard()
            }
        }
    }

    private fun updateLanguageViews() {
        if (isSymbols) {
            buildKeyboard()
            return
        }
        spaceKeyView?.text = if (isBangla) "◀   Bongo   ▶" else "◀   English   ▶"
        periodKeyView?.text = if (isBangla) "।" else "."

        if (!userPrefs.showNumberRow && userPrefs.longPressSymbols) {
            val numHints = if (userPrefs.bengaliDigits && isBangla) ROW1_HINTS_BN else ROW1_HINTS_EN
            for ((key, hintTv) in letterKeyHintViews) {
                if (key.length == 1) {
                    val hint = numHints[key[0]]
                    if (hint != null) {
                        hintTv.text = hint.toString()
                    }
                }
            }
        }
    }

    fun setShift(shifted: Boolean) {
        if (isShifted != shifted) {
            isShifted = shifted
            if (!isSymbols && !isOptionsVisible && letterKeyViews.isNotEmpty()) {
                updateShiftViews()
            } else {
                buildKeyboard()
            }
        }
    }

    private fun updateShiftViews() {
        for ((key, tv) in letterKeyViews) {
            tv.text = if (isShifted) key.uppercase() else key.lowercase()
        }
        shiftKeyView?.apply {
            text = if (isShifted) "⇪" else "⇧"
            setTextColor(if (isShifted) palette.stripPrimaryBorder else palette.keyTextColor)
        }
    }

    fun toggleShift() {
        setShift(!isShifted)
    }

    fun setActionInfo(label: String, isUri: Boolean) {
        val changed = actionLabel != label || isUriInput != isUri
        if (changed) {
            actionLabel = label
            isUriInput = isUri
            if (!isSymbols && !isOptionsVisible && actionKeyView != null) {
                actionKeyView?.text = if (label == "Search") "🔍" else label
                commaKeyView?.text = if (isUri) "/" else ","
            } else {
                buildKeyboard()
            }
        }
    }

    private fun performHaptic() {
        if (userPrefs.hapticFeedback) {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    vibrator?.vibrate(VibrationEffect.createPredefined(VibrationEffect.EFFECT_TICK))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator?.vibrate(8)
                }
            } catch (_: Exception) {}
        }
    }

    private fun playKeySound() {
        if (userPrefs.soundFeedback) {
            try {
                audioManager?.playSoundEffect(AudioManager.FX_KEYPRESS_STANDARD)
            } catch (_: Exception) {}
        }
    }

    private fun showKeyPopup(anchor: View, text: String) {
        if (!userPrefs.keyPopupPreview || !anchor.isAttachedToWindow || anchor.windowToken == null) return
        try {
            popupDismissHandler.removeCallbacks(popupDismissRunnable)
            activePopupAnchor = anchor
            popupTextView.text = text
            popupTextView.setTextColor(palette.keyTextColor)
            popupTextView.background = GradientDrawable().apply {
                cornerRadius = dp(10).toFloat()
                setColor(palette.keyNormalColor)
                setStroke(dp(1), palette.stripPrimaryBorder)
            }

            val loc = IntArray(2)
            anchor.getLocationInWindow(loc)
            val popupX = loc[0] + (anchor.width - dp(52)) / 2
            val popupY = loc[1] - dp(66)

            if (popupWindow.isShowing) {
                popupWindow.update(popupX, popupY, dp(52), dp(62))
            } else {
                popupWindow.showAtLocation(anchor, Gravity.NO_GRAVITY, popupX, popupY)
            }
        } catch (_: Exception) {}
    }

    private fun hideKeyPopup(anchor: View? = null) {
        try {
            if (anchor == null || activePopupAnchor == anchor) {
                activePopupAnchor = null
                popupDismissHandler.removeCallbacks(popupDismissRunnable)
                popupDismissHandler.postDelayed(popupDismissRunnable, 60L)
            }
        } catch (_: Exception) {}
    }

    private fun showSpacePopup(anchor: View, text: String) {
        if (!anchor.isAttachedToWindow || anchor.windowToken == null) return
        try {
            spaceDismissHandler.removeCallbacks(spaceDismissRunnable)
            spacePopupTextView.text = text
            spacePopupTextView.background = GradientDrawable().apply {
                cornerRadius = dp(8).toFloat()
                setColor(Color.parseColor("#48494d"))
                setStroke(dp(1), Color.parseColor("#333438"))
            }

            val loc = IntArray(2)
            anchor.getLocationInWindow(loc)
            val popupX = loc[0] + (anchor.width - dp(116)) / 2
            val popupY = loc[1] - dp(52)

            if (spacePopupWindow.isShowing) {
                spacePopupWindow.update(popupX, popupY, dp(116), dp(44))
            } else {
                spacePopupWindow.showAtLocation(anchor, Gravity.NO_GRAVITY, popupX, popupY)
            }
        } catch (_: Exception) {}
    }

    private fun hideSpacePopup() {
        try {
            spaceDismissHandler.removeCallbacks(spaceDismissRunnable)
            spaceDismissHandler.postDelayed(spaceDismissRunnable, 60L)
        } catch (_: Exception) {}
    }

    var isOptionsVisible = false
        private set

    fun toggleOptionsPanel() {
        isOptionsVisible = !isOptionsVisible
        buildKeyboard()
    }

    private fun buildOptionsPanel() {
        val root = LinearLayout(context).apply {
            orientation = VERTICAL
            gravity = Gravity.CENTER
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT)
            setPadding(dp(16), dp(16), dp(16), dp(16))
        }

        val row = LinearLayout(context).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT)
        }

        fun createOptionCircle(icon: String, label: String, onClick: () -> Unit): View {
            val itemContainer = LinearLayout(context).apply {
                orientation = VERTICAL
                gravity = Gravity.CENTER
                layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f)
            }

            val circle = TextView(context).apply {
                text = icon
                gravity = Gravity.CENTER
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 22f)
                val size = dp(56)
                layoutParams = LinearLayout.LayoutParams(size, size).apply {
                    bottomMargin = dp(6)
                }
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    setColor(palette.keyNormalColor)
                    setStroke(dp(1), palette.keyBorderColor)
                }
                isClickable = true
                isFocusable = true
                setOnClickListener {
                    performHaptic()
                    playKeySound()
                    onClick()
                }
            }
            itemContainer.addView(circle)

            val tvLabel = TextView(context).apply {
                text = label
                gravity = Gravity.CENTER
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                setTextColor(palette.keyTextColor)
            }
            itemContainer.addView(tvLabel)

            return itemContainer
        }

        row.addView(createOptionCircle("🎨", "Theme") {
            onKeyClickListener?.invoke(KeyAction.OpenThemes)
        })

        row.addView(createOptionCircle("⚙️", "Settings") {
            isOptionsVisible = false
            buildKeyboard()
            onKeyClickListener?.invoke(KeyAction.OpenSettings)
        })

        row.addView(createOptionCircle("🌐", if (isBangla) "English" else "Bongo") {
            isOptionsVisible = false
            onKeyClickListener?.invoke(KeyAction.ToggleLanguage)
        })

        row.addView(createOptionCircle("123", if (userPrefs.showNumberRow) "Hide # Row" else "Show # Row") {
            userPrefs.showNumberRow = !userPrefs.showNumberRow
            isOptionsVisible = false
            buildKeyboard()
        })

        root.addView(row)

        val closeBtn = TextView(context).apply {
            text = "✕ Back to Keyboard"
            gravity = Gravity.CENTER
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            setTextColor(palette.stripSecondaryText)
            setPadding(dp(16), dp(10), dp(16), dp(10))
            isClickable = true
            isFocusable = true
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(20)
                gravity = Gravity.CENTER_HORIZONTAL
            }
            background = GradientDrawable().apply {
                cornerRadius = dp(16).toFloat()
                setColor(palette.keySpecialColor)
            }
            setOnClickListener {
                isOptionsVisible = false
                buildKeyboard()
            }
        }
        root.addView(closeBtn)

        addView(root)
    }

    fun buildKeyboard() {
        popupDismissHandler.removeCallbacks(popupDismissRunnable)
        spaceDismissHandler.removeCallbacks(spaceDismissRunnable)
        if (popupWindow.isShowing) {
            popupWindow.dismiss()
        }
        if (spacePopupWindow.isShowing) {
            spacePopupWindow.dismiss()
        }
        activePopupAnchor = null

        letterKeyViews.clear()
        letterKeyHintViews.clear()
        shiftKeyView = null
        spaceKeyView = null
        periodKeyView = null
        commaKeyView = null
        actionKeyView = null

        removeAllViews()

        if (isOptionsVisible) {
            buildOptionsPanel()
            return
        }

        if (isSymbols) {
            if (isSymbolsShifted) {
                buildShiftedSymbolsKeyboard()
            } else {
                buildSymbolsKeyboard()
            }
        } else {
            buildLetterKeyboard()
        }
    }

    private fun buildLetterKeyboard() {
        // Optional 5th row: Permanent Number Row on top (if enabled in user settings)
        if (userPrefs.showNumberRow) {
            val numRow = if (userPrefs.bengaliDigits && isBangla) {
                listOf("১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯", "০")
            } else {
                listOf("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
            }
            addRow(numRow, hasSideSpacers = false, isNumberRow = true)
        }

        // Row 1: 10 keys (q to p)
        val r1 = listOf("q", "w", "e", "r", "t", "y", "u", "i", "o", "p")
        addRow(r1, hasSideSpacers = false, isNumberRow = false)

        // Row 2: 9 keys (a to l, centered with side spacers)
        val r2 = listOf("a", "s", "d", "f", "g", "h", "j", "k", "l")
        addRow(r2, hasSideSpacers = true, isNumberRow = false)

        // Row 3: Shift + 7 letters + Backspace
        val r3 = listOf("SHIFT", "z", "x", "c", "v", "b", "n", "m", "BACKSPACE")
        addRow(r3, hasSideSpacers = false, isNumberRow = false)

        // Row 4: ?123, Emoji, comma (or / in URL), space, period/dari, action
        val r4 = listOf("?123", "EMOJI", if (isUriInput) "/" else ",", "SPACE", if (isBangla) "।" else ".", "ACTION")
        addRow(r4, hasSideSpacers = false, isNumberRow = false)
    }

    private fun buildSymbolsKeyboard() {
        // Row 1: 10 digits
        val r1 = if (isBangla) {
            listOf("১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯", "০")
        } else {
            listOf("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
        }
        addRow(r1, hasSideSpacers = false, isNumberRow = false)

        // Row 2: 10 symbols
        val r2 = listOf("@", "#", "৳", "%", "&", "*", "-", "+", "(", ")")
        addRow(r2, hasSideSpacers = false, isNumberRow = false)

        // Row 3: =\\< + 7 symbols + Backspace
        val r3 = listOf("=\\<", "!", "\"", "'", ":", ";", "/", "?", "BACKSPACE")
        addRow(r3, hasSideSpacers = false, isNumberRow = false)

        // Row 4: ABC, comma, space, period/dari, action
        val r4 = listOf("ABC", ",", "SPACE", if (isBangla) "।" else ".", "ACTION")
        addRow(r4, hasSideSpacers = false, isNumberRow = false)
    }

    private fun buildShiftedSymbolsKeyboard() {
        // Row 1: Math & currency symbols
        val r1 = listOf("~", "`", "|", "৲", "√", "π", "÷", "×", "{", "}")
        addRow(r1, hasSideSpacers = false, isNumberRow = false)

        // Row 2: Tab, currency, brackets
        val r2 = listOf("TAB", "£", "$", "%", "^", "°", "_", "=", "[", "]")
        addRow(r2, hasSideSpacers = false, isNumberRow = false)

        // Row 3: ?123, symbols, Backspace
        val r3 = listOf("?123", "↕", "®", "©", "™", "\\", "<", ">", "BACKSPACE")
        addRow(r3, hasSideSpacers = false, isNumberRow = false)

        // Row 4: ABC, comma, space, period/dari, action
        val r4 = listOf("ABC", ",", "SPACE", if (isBangla) "।" else ".", "ACTION")
        addRow(r4, hasSideSpacers = false, isNumberRow = false)
    }

    private fun addRow(keys: List<String>, hasSideSpacers: Boolean, isNumberRow: Boolean) {
        val rowWeight = if (isNumberRow) 0.82f else 1.0f
        val rowLayout = LinearLayout(context).apply {
            orientation = HORIZONTAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, 0, rowWeight)
            gravity = Gravity.CENTER_VERTICAL
        }

        if (hasSideSpacers) {
            val leftSpacer = View(context).apply {
                layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, 0.5f)
            }
            rowLayout.addView(leftSpacer)
        }

        for (key in keys) {
            val keyView = createKeyView(key, isNumberRow)
            rowLayout.addView(keyView)
        }

        if (hasSideSpacers) {
            val rightSpacer = View(context).apply {
                layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, 0.5f)
            }
            rowLayout.addView(rightSpacer)
        }

        addView(rowLayout)
    }

    private fun getKeyWeight(key: String): Float = when (key) {
        "SPACE" -> if (isSymbols) 5.2f else 4.3f
        "RETURN", "ACTION" -> 1.35f
        "SHIFT", "BACKSPACE" -> 1.35f
        "?123", "ABC", "=\\<" -> 1.35f
        "EMOJI", ",", "/", ".", "।", "TAB", "↕" -> 1.0f
        "ESC", "CTRL" -> 1.0f
        else -> 1.0f
    }

    private fun getHintForKey(key: String, isNumberRow: Boolean): Char? {
        if (!userPrefs.longPressSymbols || isNumberRow) return null
        if (key.length != 1) return null
        val ch = key.first()

        if (isSymbols) {
            if (!isSymbolsShifted) {
                if (isBangla && ch in '১'..'০') {
                    val idx = "১২৩৪৫৬৭৮৯০".indexOf(ch)
                    if (idx != -1) return "1234567890"[idx]
                } else if (!isBangla && ch in '0'..'9') {
                    val idx = "1234567890".indexOf(ch)
                    if (idx != -1) return "১২৩৪৫৬৭৮৯০"[idx]
                }
                return SYM2_HINTS[ch] ?: SYM3_HINTS[ch]
            }
            return null
        }

        val lower = ch.lowercaseChar()
        val numHints = if (userPrefs.bengaliDigits && isBangla) ROW1_HINTS_BN else ROW1_HINTS_EN
        val row1 = if (userPrefs.showNumberRow) null else numHints[lower]
        return row1 ?: ROW2_HINTS[lower] ?: ROW3_HINTS[lower]
    }

    private fun createKeyView(key: String, isNumberRow: Boolean): View {
        val weight = getKeyWeight(key)
        val lp = LayoutParams(0, LayoutParams.MATCH_PARENT, weight).apply {
            setMargins(dp(2), dp(3), dp(2), dp(3))
        }

        val container = FrameLayout(context).apply {
            layoutParams = lp
            background = createKeyBackground(key)
            isClickable = true
            isFocusable = true
        }

        val displayLabel = when (key) {
            "SHIFT" -> if (isShifted) "⇪" else "⇧"
            "BACKSPACE" -> "⌫"
            "RETURN", "ACTION" -> when (actionLabel) {
                "Search" -> "🔍"
                else -> actionLabel
            }
            "SPACE" -> if (isBangla) "Bongo" else "English"
            "EMOJI" -> "☺"
            "?123" -> "?123"
            "ABC" -> "ABC"
            "=\\<" -> "=\\<"
            "TAB" -> "⇥"
            "↕" -> "↕"
            "ESC" -> "Esc"
            "CTRL" -> "Ctrl"
            else -> if (isShifted) key.uppercase() else key
        }

        val tv = TextView(context).apply {
            gravity = Gravity.CENTER
            setTextSize(TypedValue.COMPLEX_UNIT_SP, getKeyTextSize(key, isNumberRow))
            typeface = if (key in listOf("?123", "ABC", "=\\<", "RETURN", "ACTION") || (!isSpecialKey(key) && key != "SPACE")) {
                Typeface.DEFAULT_BOLD
            } else {
                Typeface.DEFAULT
            }
            setTextColor(getKeyTextColor(key))
            layoutParams = FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT)
            text = if (key == "SPACE") "◀   $displayLabel   ▶" else displayLabel
        }
        container.addView(tv)

        // Cache view references for instant zero-allocation updates
        if (!isNumberRow && !isSymbols) {
            if (key.length == 1 && key[0] in 'a'..'z') {
                letterKeyViews[key] = tv
            }
            when (key) {
                "SHIFT" -> shiftKeyView = tv
                "SPACE" -> spaceKeyView = tv
                ".", "।" -> periodKeyView = tv
                ",", "/" -> commaKeyView = tv
                "ACTION", "RETURN" -> actionKeyView = tv
            }
        }

        // Show superscript symbol hint on keys
        val hintChar = getHintForKey(key, isNumberRow)
        if (hintChar != null) {
            val hintTv = TextView(context).apply {
                text = hintChar.toString()
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 10f)
                setTextColor(palette.keyHintColor)
                gravity = Gravity.TOP or Gravity.END
                setPadding(0, dp(2), dp(4), 0)
                layoutParams = FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    Gravity.TOP or Gravity.END
                )
            }
            if (!isNumberRow && !isSymbols && key.length == 1 && key[0] in 'a'..'z') {
                letterKeyHintViews[key] = hintTv
            }
            container.addView(hintTv)
        }

        // Subscript '...' on keys with long-press menus (,, ., ।, ACTION)
        if (key in listOf(",", ".", "।", "ACTION", "RETURN") || (isUriInput && key == "/")) {
            val dotsTv = TextView(context).apply {
                text = "..."
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 8f)
                setTextColor(palette.keyHintColor)
                gravity = Gravity.BOTTOM or Gravity.END
                setPadding(0, 0, dp(4), dp(1))
                layoutParams = FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    Gravity.BOTTOM or Gravity.END
                )
            }
            container.addView(dotsTv)
        }

        // Setup interaction based on key type
        when (key) {
            "BACKSPACE" -> setupBackspaceGestures(container)
            "SPACE" -> setupSpacebarInteractions(container, tv)
            else -> setupNormalKeyTouch(container, key, displayLabel, hintChar, isNumberRow)
        }

        return container
    }

    private fun setupSpacebarInteractions(view: View, labelTv: TextView) {
        var startX = 0f
        var hasSwiped = false
        var isLongPressed = false
        val swipeThreshold = dp(22)
        val longPressHandler = Handler(Looper.getMainLooper())
        val longPressRunnable = Runnable {
            if (!hasSwiped) {
                isLongPressed = true
                performHaptic()
                hideSpacePopup()
                onKeyClickListener?.invoke(KeyAction.SwitchImePicker)
            }
        }

        view.setOnTouchListener { v, event ->
            try {
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        startX = event.x
                        hasSwiped = false
                        isLongPressed = false
                        v.isPressed = true
                        performHaptic()
                        playKeySound()
                        showSpacePopup(v, if (isBangla) "Bongo" else "English")
                        longPressHandler.postDelayed(longPressRunnable, 450L)
                        true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = event.x - startX
                        if (Math.abs(dx) > swipeThreshold) {
                            longPressHandler.removeCallbacks(longPressRunnable)
                        }
                        if (!hasSwiped && Math.abs(dx) > swipeThreshold) {
                            hasSwiped = true
                            isBangla = !isBangla
                            performHaptic()
                            playKeySound()
                            val newLabel = if (isBangla) "Bongo" else "English"
                            updateLanguageViews()
                            showSpacePopup(v, newLabel)
                            onKeyClickListener?.invoke(KeyAction.ToggleLanguage)
                        }
                        true
                    }
                    MotionEvent.ACTION_UP -> {
                        longPressHandler.removeCallbacks(longPressRunnable)
                        v.isPressed = false
                        hideSpacePopup()
                        if (!hasSwiped && !isLongPressed) {
                            onKeyClickListener?.invoke(KeyAction.Space)
                        }
                        hasSwiped = false
                        isLongPressed = false
                        true
                    }
                    MotionEvent.ACTION_CANCEL -> {
                        longPressHandler.removeCallbacks(longPressRunnable)
                        v.isPressed = false
                        hideSpacePopup()
                        hasSwiped = false
                        isLongPressed = false
                        true
                    }
                    else -> false
                }
            } catch (_: Exception) {
                false
            }
        }
    }

    private fun setupNormalKeyTouch(
        container: View,
        key: String,
        displayLabel: String,
        hintChar: Char?,
        isNumberRow: Boolean
    ) {
        val isLetterOrNum = !isSpecialKey(key) && key.length == 1
        var hasLongPressed = false
        var isInsideKey = false
        val longPressHandler = Handler(Looper.getMainLooper())

        val longPressRunnable = Runnable {
            if (isInsideKey && !hasLongPressed) {
                hasLongPressed = true
                container.isPressed = false
                hideKeyPopup(container)
                performHaptic()
                playKeySound()
                when {
                    hintChar != null -> {
                        onKeyClickListener?.invoke(KeyAction.CharacterKey(hintChar))
                    }
                    key == "," -> {
                        onKeyClickListener?.invoke(KeyAction.OpenSettings)
                    }
                    key == "." || key == "।" -> {
                        onKeyClickListener?.invoke(KeyAction.CharacterKey('?'))
                    }
                    key == "ACTION" || key == "RETURN" -> {
                        onKeyClickListener?.invoke(KeyAction.OpenSettings)
                    }
                }
            }
        }

        container.setOnTouchListener { v, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    hasLongPressed = false
                    isInsideKey = true
                    v.isPressed = true
                    performHaptic()
                    playKeySound()
                    if (isLetterOrNum) {
                        val currentLabel = if (isShifted) key.uppercase() else key
                        showKeyPopup(v, currentLabel)
                    }
                    longPressHandler.postDelayed(longPressRunnable, 380L)
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val slop = dp(14)
                    if (event.x < -slop || event.x > v.width + slop || event.y < -slop || event.y > v.height + slop) {
                        if (isInsideKey) {
                            isInsideKey = false
                            v.isPressed = false
                            longPressHandler.removeCallbacks(longPressRunnable)
                            hideKeyPopup(v)
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    longPressHandler.removeCallbacks(longPressRunnable)
                    v.isPressed = false
                    hideKeyPopup(v)
                    if (isInsideKey && !hasLongPressed) {
                        handleKeyClick(key)
                    }
                    isInsideKey = false
                    hasLongPressed = false
                    true
                }
                MotionEvent.ACTION_CANCEL -> {
                    longPressHandler.removeCallbacks(longPressRunnable)
                    v.isPressed = false
                    hideKeyPopup(v)
                    isInsideKey = false
                    hasLongPressed = false
                    true
                }
                else -> false
            }
        }
    }

    private fun setupBackspaceGestures(view: View) {
        var startX = 0f
        var isSwipingWord = false
        var wordsDeletedCount = 0
        var isRepeating = false
        var repeatCount = 0

        val repeatRunnable = object : Runnable {
            override fun run() {
                if (isRepeating && !isSwipingWord) {
                    performHaptic()
                    playKeySound()
                    onKeyClickListener?.invoke(KeyAction.Backspace)
                    repeatCount++
                    val nextDelay = if (repeatCount > 15) 35L else 55L
                    repeatHandler.postDelayed(this, nextDelay)
                }
            }
        }

        view.setOnTouchListener { v, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    v.isPressed = true
                    startX = event.x
                    isSwipingWord = false
                    wordsDeletedCount = 0
                    isRepeating = true
                    repeatCount = 0
                    performHaptic()
                    playKeySound()
                    onKeyClickListener?.invoke(KeyAction.Backspace)
                    repeatHandler.postDelayed(repeatRunnable, 350L)
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.x - startX
                    if (userPrefs.swipeDeleteWords && dx < -dp(28)) {
                        if (!isSwipingWord) {
                            isSwipingWord = true
                            isRepeating = false
                            repeatHandler.removeCallbacks(repeatRunnable)
                        }
                        val wordsToTrigger = ((-dx - dp(28)) / dp(32)).toInt() + 1
                        if (wordsToTrigger > wordsDeletedCount) {
                            val diff = wordsToTrigger - wordsDeletedCount
                            for (i in 0 until diff) {
                                performHaptic()
                                playKeySound()
                                onKeyClickListener?.invoke(KeyAction.DeleteWord)
                            }
                            wordsDeletedCount = wordsToTrigger
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    v.isPressed = false
                    isRepeating = false
                    repeatHandler.removeCallbacks(repeatRunnable)
                    true
                }
                else -> false
            }
        }
    }

    private fun getKeyTextSize(key: String, isNumberRow: Boolean): Float = when {
        isNumberRow -> 17f
        key == "SPACE" -> 14.5f
        key in listOf("SHIFT", "BACKSPACE") -> 18f
        key in listOf("?123", "ABC", "=\\<") -> 13.5f
        key in listOf("RETURN", "ACTION") -> 14f
        key in listOf("EMOJI", "TAB", "↕") -> 17f
        key in listOf("ESC", "CTRL") -> 12f
        else -> 21f
    }

    private fun getKeyTextColor(key: String): Int = when (key) {
        "SHIFT" -> if (isShifted) palette.stripPrimaryBorder else palette.keyTextColor
        "SPACE" -> Color.parseColor("#a8a9af")
        "?123", "ABC", "=\\<", "ACTION", "RETURN" -> Color.WHITE
        else -> palette.keyTextColor
    }

    private fun isSpecialKey(key: String): Boolean =
        key in listOf(
            "SHIFT", "BACKSPACE", "RETURN", "ACTION",
            "?123", "ABC", "=\\<", "EMOJI",
            "TAB", "↕", "ESC", "CTRL",
            ",", "/"
        )

    private fun createKeyBackground(key: String): StateListDrawable {
        val normalColor = when {
            isSpecialKey(key) -> palette.keySpecialColor
            else -> palette.keyNormalColor
        }

        val normal = GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(normalColor)
            setStroke(dp(1), palette.keyBorderColor)
        }

        val pressed = GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(palette.keyPressedColor)
        }

        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun handleKeyClick(key: String) {
        when (key) {
            "SHIFT" -> toggleShift()
            "BACKSPACE" -> onKeyClickListener?.invoke(KeyAction.Backspace)
            "SPACE" -> onKeyClickListener?.invoke(KeyAction.Space)
            "RETURN", "ACTION" -> onKeyClickListener?.invoke(KeyAction.Return)
            "EMOJI" -> onKeyClickListener?.invoke(KeyAction.ToggleEmoji)
            "ESC" -> onKeyClickListener?.invoke(KeyAction.Esc)
            "TAB" -> onKeyClickListener?.invoke(KeyAction.Tab)
            "CTRL" -> onKeyClickListener?.invoke(KeyAction.Ctrl)
            "=\\<" -> {
                isSymbolsShifted = true
                buildKeyboard()
            }
            "?123" -> {
                if (isSymbolsShifted) {
                    isSymbolsShifted = false
                    buildKeyboard()
                } else {
                    isSymbols = true
                    isSymbolsShifted = false
                    buildKeyboard()
                    onKeyClickListener?.invoke(KeyAction.ToggleSymbols)
                }
            }
            "ABC" -> {
                isSymbols = false
                isSymbolsShifted = false
                buildKeyboard()
                onKeyClickListener?.invoke(KeyAction.ToggleSymbols)
            }
            else -> {
                val ch = when (key) {
                    ".", "।" -> if (isBangla) '।' else '.'
                    ",", "/" -> if (isUriInput) '/' else ','
                    else -> if (isShifted) key.uppercase().first() else key.first()
                }
                onKeyClickListener?.invoke(KeyAction.CharacterKey(ch))
                if (isShifted) {
                    setShift(false)
                }
            }
        }
    }

    override fun onDetachedFromWindow() {
        popupDismissHandler.removeCallbacksAndMessages(null)
        spaceDismissHandler.removeCallbacksAndMessages(null)
        if (popupWindow.isShowing) {
            popupWindow.dismiss()
        }
        if (spacePopupWindow.isShowing) {
            spacePopupWindow.dismiss()
        }
        repeatHandler.removeCallbacksAndMessages(null)
        super.onDetachedFromWindow()
    }

    private fun dp(value: Int): Int =
        (value * context.resources.displayMetrics.density).toInt()
}
