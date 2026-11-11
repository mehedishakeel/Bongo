package app.getbongo.ime.ui

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.StateListDrawable
import android.util.AttributeSet
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import app.getbongo.ime.model.ThemePalette

/**
 * Dual-mode candidate & utility strip above the keyboard:
 * - When typing: displays live phonetic candidate choices (with primary highlighted)
 * - When idle: displays fast shortcuts (Esc, Tab, Ctrl, Clipboard, Voice, Select All, Copy, Paste, Cursor ◀ ▶)
 */
class CandidateStripView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : HorizontalScrollView(context, attrs, defStyleAttr) {

    sealed class ShortcutAction {
        object Emoji : ShortcutAction()
        object Theme : ShortcutAction()
        object Settings : ShortcutAction()
        object More : ShortcutAction()
        object Esc : ShortcutAction()
        object Tab : ShortcutAction()
        object ToggleCtrl : ShortcutAction()
        object Clipboard : ShortcutAction()
        object VoiceInput : ShortcutAction()
        object SelectAll : ShortcutAction()
        object Copy : ShortcutAction()
        object Paste : ShortcutAction()
        object CursorLeft : ShortcutAction()
        object CursorRight : ShortcutAction()
    }

    private val container = LinearLayout(context).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        layoutParams = LayoutParams(LayoutParams.WRAP_CONTENT, LayoutParams.MATCH_PARENT)
        setPadding(dp(6), 0, dp(6), 0)
    }

    var onCandidateSelected: ((Int, String) -> Unit)? = null
    var onShortcutAction: ((ShortcutAction) -> Unit)? = null

    private var palette: ThemePalette = ThemePalette.getPalette("midnight")
    private var isCtrlActive = false
    private var ctrlTextView: TextView? = null
    private var isShowingCandidates = false

    init {
        isHorizontalScrollBarEnabled = false
        isFillViewport = true
        setBackgroundColor(palette.surfaceColor)
        addView(container)
        showShortcuts()
    }

    fun applyTheme(newPalette: ThemePalette) {
        palette = newPalette
        setBackgroundColor(palette.surfaceColor)
        showShortcuts()
    }

    fun setCtrlActive(active: Boolean) {
        isCtrlActive = active
        ctrlTextView?.let { tv ->
            tv.setTextColor(if (active) palette.stripPrimaryBorder else palette.stripSecondaryText)
            tv.background = createShortcutBackground(isPrimary = active)
        }
    }

    fun setCandidates(candidates: List<String>) {
        if (candidates.isEmpty()) {
            showShortcuts()
            return
        }

        if (!isShowingCandidates) {
            container.removeAllViews()
            ctrlTextView = null
            voicePromptView = null
            isShowingCandidates = true
        }

        candidates.forEachIndexed { index, candidate ->
            val isPrimary = index == 0
            val tv: TextView = if (index < container.childCount) {
                container.getChildAt(index) as TextView
            } else {
                TextView(context).apply {
                    setPadding(dp(14), dp(6), dp(14), dp(6))
                    gravity = Gravity.CENTER
                    isClickable = true
                    isFocusable = true
                    val lp = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).apply {
                        setMargins(dp(3), 0, dp(3), 0)
                    }
                    layoutParams = lp
                    container.addView(this)
                }
            }

            tv.visibility = View.VISIBLE
            tv.text = candidate
            tv.setTextSize(TypedValue.COMPLEX_UNIT_SP, if (isPrimary) 17f else 15f)
            tv.typeface = if (isPrimary) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
            tv.setTextColor(if (isPrimary) palette.stripPrimaryText else palette.stripSecondaryText)
            tv.background = createCandidateBackground(isPrimary)
            tv.setOnClickListener {
                onCandidateSelected?.invoke(index, candidate)
            }
        }

        // Hide excess views from previous longer candidates list
        if (container.childCount > candidates.size) {
            for (i in candidates.size until container.childCount) {
                container.getChildAt(i).visibility = View.GONE
            }
        }

        scrollTo(0, 0)
    }

    fun showClipboardHistory(clips: List<String>, onPaste: (String) -> Unit) {
        isShowingCandidates = false
        container.removeAllViews()
        ctrlTextView = null

        val closeBtn = TextView(context).apply {
            text = "✕"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            setTextColor(palette.stripSecondaryText)
            setPadding(dp(12), dp(6), dp(12), dp(6))
            gravity = Gravity.CENTER
            background = createShortcutBackground(false)
            setOnClickListener { showShortcuts() }
        }
        container.addView(closeBtn)

        if (clips.isEmpty()) {
            val emptyTv = TextView(context).apply {
                text = "Clipboard empty"
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
                setTextColor(palette.stripSecondaryText)
                setPadding(dp(12), dp(6), dp(12), dp(6))
                gravity = Gravity.CENTER
            }
            container.addView(emptyTv)
            return
        }

        for (clip in clips) {
            val snippet = if (clip.length > 25) clip.take(25).replace("\n", " ") + "…" else clip.replace("\n", " ")
            val clipPill = TextView(context).apply {
                text = "📋 $snippet"
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 13.5f)
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(palette.stripPrimaryText)
                setPadding(dp(12), dp(6), dp(12), dp(6))
                gravity = Gravity.CENTER
                background = createCandidateBackground(true)
                val lp = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(dp(3), 0, dp(3), 0)
                }
                layoutParams = lp
                setOnClickListener {
                    onPaste(clip)
                    showShortcuts()
                }
            }
            container.addView(clipPill)
        }
    }

    fun showClipboardPreview(clipText: String, onPaste: (String) -> Unit) {
        showClipboardHistory(listOf(clipText), onPaste)
    }

    fun clear() {
        showShortcuts()
    }

    private var voicePromptView: TextView? = null

    fun showVoiceListening(prompt: String = "Speak now...", onStop: () -> Unit) {
        isShowingCandidates = false
        container.removeAllViews()
        ctrlTextView = null

        val promptTv = TextView(context).apply {
            text = prompt
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(16), dp(8), dp(16), dp(8))
            val lp = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f)
            layoutParams = lp
        }
        voicePromptView = promptTv
        container.addView(promptTv)

        val micBtn = TextView(context).apply {
            text = "🎙️ Stop"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.parseColor("#1b5e20"))
            gravity = Gravity.CENTER
            setPadding(dp(18), dp(7), dp(18), dp(7))
            background = GradientDrawable().apply {
                cornerRadius = dp(16).toFloat()
                setColor(Color.parseColor("#ffc107")) // Amber/yellow like Ridmik
            }
            isClickable = true
            isFocusable = true
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(dp(6), dp(4), dp(12), dp(4))
            }
            layoutParams = lp
            setOnClickListener {
                onStop()
            }
        }
        container.addView(micBtn)
    }

    fun updateVoicePrompt(prompt: String) {
        voicePromptView?.text = prompt
    }

    fun showShortcuts() {
        isShowingCandidates = false
        container.removeAllViews()
        ctrlTextView = null
        voicePromptView = null

        val shortcuts = listOf(
            Triple("😊", ShortcutAction.Emoji, false),
            Triple("🎨", ShortcutAction.Theme, false),
            Triple("📋", ShortcutAction.Clipboard, false),
            Triple("⚙️", ShortcutAction.Settings, false),
            Triple("•••", ShortcutAction.More, false),
            Triple("🎙️", ShortcutAction.VoiceInput, false),
            Triple("Esc", ShortcutAction.Esc, false),
            Triple("Tab", ShortcutAction.Tab, false),
            Triple("Ctrl", ShortcutAction.ToggleCtrl, isCtrlActive),
            Triple("Select All", ShortcutAction.SelectAll, false),
            Triple("Copy", ShortcutAction.Copy, false),
            Triple("Paste", ShortcutAction.Paste, false),
            Triple("◀", ShortcutAction.CursorLeft, false),
            Triple("▶", ShortcutAction.CursorRight, false)
        )

        for ((label, action, isHighlighted) in shortcuts) {
            val tv = TextView(context).apply {
                text = label
                val isEmojiOrIcon = label in listOf("😊", "🎨", "📋", "⚙️", "•••", "🎙️", "◀", "▶")
                setTextSize(TypedValue.COMPLEX_UNIT_SP, if (isEmojiOrIcon) 15f else 13f)
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(if (isHighlighted) palette.stripPrimaryBorder else palette.stripSecondaryText)
                setPadding(dp(11), dp(5), dp(11), dp(5))
                gravity = Gravity.CENTER
                isClickable = true
                isFocusable = true
                background = createShortcutBackground(isHighlighted)

                val lp = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(dp(2), 0, dp(2), 0)
                }
                layoutParams = lp

                setOnClickListener {
                    onShortcutAction?.invoke(action)
                }
            }

            if (action is ShortcutAction.ToggleCtrl) {
                ctrlTextView = tv
            }

            container.addView(tv)
        }
    }

    private fun createCandidateBackground(isPrimary: Boolean): StateListDrawable {
        val normal = GradientDrawable().apply {
            cornerRadius = dp(16).toFloat()
            if (isPrimary) {
                setColor(palette.stripPrimaryBg)
                setStroke(dp(1), palette.stripPrimaryBorder)
            } else {
                setColor(palette.stripSecondaryBg)
                setStroke(dp(1), palette.keyBorderColor)
            }
        }

        val pressed = GradientDrawable().apply {
            cornerRadius = dp(16).toFloat()
            setColor(palette.keyPressedColor)
        }

        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun createShortcutBackground(isPrimary: Boolean): StateListDrawable {
        val normal = GradientDrawable().apply {
            cornerRadius = dp(8).toFloat()
            if (isPrimary) {
                setColor(palette.stripPrimaryBg)
                setStroke(dp(1), palette.stripPrimaryBorder)
            } else {
                setColor(Color.TRANSPARENT)
            }
        }

        val pressed = GradientDrawable().apply {
            cornerRadius = dp(8).toFloat()
            setColor(palette.keyPressedColor)
        }

        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun dp(value: Int): Int =
        (value * context.resources.displayMetrics.density).toInt()
}
