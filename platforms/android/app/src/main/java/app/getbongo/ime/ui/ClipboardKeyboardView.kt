package app.getbongo.ime.ui

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.StateListDrawable
import android.text.TextUtils
import android.util.AttributeSet
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import app.getbongo.ime.model.ClipboardEntry
import app.getbongo.ime.model.ThemePalette

/**
 * Full interactive Clipboard Manager panel for Bongo IME.
 * Supports pinning important items, deleting individual entries, clearing unpinned items,
 * keyboard-backed search, and automatic sensitive-content expiration notices.
 */
class ClipboardKeyboardView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : LinearLayout(context, attrs, defStyleAttr) {

    var onPasteEntry: ((ClipboardEntry) -> Unit)? = null
    var onTogglePin: ((String) -> Unit)? = null
    var onDeleteEntry: ((String) -> Unit)? = null
    var onClearUnpinned: (() -> Unit)? = null
    var onStartSearch: (() -> Unit)? = null
    var onBackToKeyboard: (() -> Unit)? = null
    var onBackspace: (() -> Unit)? = null

    private var palette: ThemePalette = ThemePalette.getPalette("midnight")
    private var entries: List<ClipboardEntry> = emptyList()

    private val headerBar = LinearLayout(context)
    private val privacyLabel = TextView(context)
    private val searchBtn = TextView(context)
    private val clearBtn = TextView(context)
    private val dividerTop = View(context)
    private val scrollView = ScrollView(context)
    private val listContainer = LinearLayout(context)
    private val bottomBar = LinearLayout(context)
    private val abcBtn = TextView(context)
    private val pasteLatestBtn = TextView(context)
    private val backspaceBtn = TextView(context)

    init {
        orientation = VERTICAL
        setBackgroundColor(palette.surfaceColor)
        setupHeaderBar()
        setupScrollArea()
        setupBottomBar()
        render()
    }

    fun applyTheme(newPalette: ThemePalette) {
        palette = newPalette
        setBackgroundColor(palette.surfaceColor)
        headerBar.setBackgroundColor(palette.keySpecialColor)
        dividerTop.setBackgroundColor(palette.dividerColor)
        bottomBar.setBackgroundColor(palette.keySpecialColor)

        privacyLabel.setTextColor(palette.stripSecondaryText)
        searchBtn.setTextColor(palette.keyTextColor)
        searchBtn.background = createKeyBackground(false)
        clearBtn.setTextColor(Color.parseColor("#f87171"))
        clearBtn.background = createKeyBackground(false)

        abcBtn.setTextColor(palette.keyTextColor)
        abcBtn.background = createKeyBackground(true)
        pasteLatestBtn.setTextColor(palette.stripPrimaryText)
        pasteLatestBtn.background = createKeyBackground(false)
        backspaceBtn.setTextColor(palette.keyTextColor)
        backspaceBtn.background = createKeyBackground(true)

        render()
    }

    fun setEntries(items: List<ClipboardEntry>) {
        entries = items
        render()
    }

    private fun setupHeaderBar() {
        headerBar.apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(42))
            setBackgroundColor(palette.keySpecialColor)
            setPadding(dp(10), dp(4), dp(8), dp(4))
        }

        privacyLabel.apply {
            text = "🔒 On-device · Passwords blocked"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 11.5f)
            setTextColor(palette.stripSecondaryText)
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f)
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
        }

        searchBtn.apply {
            text = "🔍"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            gravity = Gravity.CENTER
            setTextColor(palette.keyTextColor)
            setPadding(dp(10), dp(4), dp(10), dp(4))
            background = createKeyBackground(false)
            contentDescription = "Search clipboard"
            layoutParams = LayoutParams(LayoutParams.WRAP_CONTENT, LayoutParams.MATCH_PARENT).apply {
                setMargins(dp(4), 0, dp(4), 0)
            }
            setOnClickListener { onStartSearch?.invoke() }
        }

        clearBtn.apply {
            text = "Clear"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setTextColor(Color.parseColor("#f87171"))
            setPadding(dp(10), dp(4), dp(10), dp(4))
            background = createKeyBackground(false)
            contentDescription = "Clear unpinned clipboard history"
            layoutParams = LayoutParams(LayoutParams.WRAP_CONTENT, LayoutParams.MATCH_PARENT)
            setOnClickListener { onClearUnpinned?.invoke() }
        }

        headerBar.addView(privacyLabel)
        headerBar.addView(searchBtn)
        headerBar.addView(clearBtn)
        addView(headerBar)

        dividerTop.apply {
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(1))
            setBackgroundColor(palette.dividerColor)
        }
        addView(dividerTop)
    }

    private fun setupScrollArea() {
        scrollView.apply {
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f)
            isFillViewport = true
        }
        listContainer.apply {
            orientation = VERTICAL
            setPadding(dp(8), dp(8), dp(8), dp(8))
        }
        scrollView.addView(listContainer)
        addView(scrollView)
    }

    private fun setupBottomBar() {
        bottomBar.apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(46))
            setBackgroundColor(palette.keySpecialColor)
            setPadding(dp(8), dp(4), dp(8), dp(4))
        }

        abcBtn.apply {
            text = "ABC"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14.5f)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(palette.keyTextColor)
            gravity = Gravity.CENTER
            background = createKeyBackground(true)
            layoutParams = LayoutParams(dp(72), LayoutParams.MATCH_PARENT).apply {
                setMargins(dp(3), dp(2), dp(3), dp(2))
            }
            setOnClickListener { onBackToKeyboard?.invoke() }
        }

        pasteLatestBtn.apply {
            text = "Paste Latest"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(palette.stripPrimaryText)
            gravity = Gravity.CENTER
            background = createKeyBackground(false)
            layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, 1f).apply {
                setMargins(dp(3), dp(2), dp(3), dp(2))
            }
            setOnClickListener {
                entries.firstOrNull()?.let { onPasteEntry?.invoke(it) }
            }
        }

        backspaceBtn.apply {
            text = "⌫"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 17f)
            setTextColor(palette.keyTextColor)
            gravity = Gravity.CENTER
            background = createKeyBackground(true)
            layoutParams = LayoutParams(dp(64), LayoutParams.MATCH_PARENT).apply {
                setMargins(dp(3), dp(2), dp(3), dp(2))
            }
            setOnClickListener { onBackspace?.invoke() }
        }

        bottomBar.addView(abcBtn)
        bottomBar.addView(pasteLatestBtn)
        bottomBar.addView(backspaceBtn)
        addView(bottomBar)
    }

    private fun render() {
        listContainer.removeAllViews()
        pasteLatestBtn.isEnabled = entries.isNotEmpty()
        pasteLatestBtn.alpha = if (entries.isEmpty()) 0.45f else 1.0f

        if (entries.isEmpty()) {
            val emptyCard = LinearLayout(context).apply {
                orientation = VERTICAL
                gravity = Gravity.CENTER
                setPadding(dp(20), dp(32), dp(20), dp(32))
                background = GradientDrawable().apply {
                    cornerRadius = dp(12).toFloat()
                    setColor(palette.keyNormalColor)
                    setStroke(dp(1), palette.keyBorderColor)
                }
            }
            val title = TextView(context).apply {
                text = "📋 Clipboard is empty"
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(palette.keyTextColor)
                gravity = Gravity.CENTER
            }
            val sub = TextView(context).apply {
                text = "Copy text anywhere to save it here. Pin important clips with 📌; sensitive clips auto-expire after 1 hour."
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                setTextColor(palette.stripSecondaryText)
                gravity = Gravity.CENTER
                setPadding(0, dp(6), 0, 0)
            }
            emptyCard.addView(title)
            emptyCard.addView(sub)
            listContainer.addView(emptyCard)
            return
        }

        for (entry in entries) {
            listContainer.addView(createEntryCard(entry))
        }
        scrollView.smoothScrollTo(0, 0)
    }

    private fun createEntryCard(entry: ClipboardEntry): View {
        val card = LinearLayout(context).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(12), dp(10), dp(8), dp(10))
            background = createEntryBackground(entry.isPinned)
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, dp(3), 0, dp(3))
            }
            isClickable = true
            isFocusable = true
            setOnClickListener { onPasteEntry?.invoke(entry) }
        }

        val textCol = LinearLayout(context).apply {
            orientation = VERTICAL
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(0, 0, dp(8), 0)
            }
        }

        val previewTv = TextView(context).apply {
            text = entry.text.replace("\n", " ")
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13.5f)
            setTextColor(palette.keyTextColor)
            maxLines = 2
            ellipsize = TextUtils.TruncateAt.END
        }
        textCol.addView(previewTv)

        if (entry.isPinned || entry.isSensitive) {
            val badgeTv = TextView(context).apply {
                text = when {
                    entry.isPinned -> "📌 Pinned"
                    else -> "⏱ Sensitive · Auto-expires in 1h"
                }
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 10.5f)
                setTextColor(if (entry.isPinned) palette.stripPrimaryBorder else Color.parseColor("#fbbf24"))
                setPadding(0, dp(2), 0, 0)
            }
            textCol.addView(badgeTv)
        }
        card.addView(textCol)

        val pinBtn = TextView(context).apply {
            text = if (entry.isPinned) "📌" else "📍"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(6), dp(8), dp(6))
            contentDescription = if (entry.isPinned) "Unpin clip" else "Pin clip"
            alpha = if (entry.isPinned) 1.0f else 0.55f
            setOnClickListener { onTogglePin?.invoke(entry.id) }
        }
        card.addView(pinBtn)

        val delBtn = TextView(context).apply {
            text = "✕"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(palette.stripSecondaryText)
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(6), dp(8), dp(6))
            contentDescription = "Delete clip"
            setOnClickListener { onDeleteEntry?.invoke(entry.id) }
        }
        card.addView(delBtn)

        return card
    }

    private fun createEntryBackground(isPinned: Boolean): StateListDrawable {
        val normal = GradientDrawable().apply {
            cornerRadius = dp(10).toFloat()
            setColor(palette.keyNormalColor)
            setStroke(
                dp(1),
                if (isPinned) palette.stripPrimaryBorder else palette.keyBorderColor
            )
        }
        val pressed = GradientDrawable().apply {
            cornerRadius = dp(10).toFloat()
            setColor(palette.keyPressedColor)
        }
        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun createKeyBackground(isSpecial: Boolean): StateListDrawable {
        val normal = GradientDrawable().apply {
            cornerRadius = dp(8).toFloat()
            setColor(if (isSpecial) palette.surfaceColor else palette.keyNormalColor)
            setStroke(dp(1), palette.keyBorderColor)
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
        (value * resources.displayMetrics.density).toInt()
}
