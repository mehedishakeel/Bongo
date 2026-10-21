package app.getbongo.ime.ui

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.provider.Settings
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import app.getbongo.ime.R
import app.getbongo.ime.engine.BongoNative
import app.getbongo.ime.model.UserPreferences

/**
 * Modern, clean, uncluttered settings & activation screen for Bongo.
 * Uses grouped cards, dynamic activation hero card, and clean typography.
 */
class SettingsActivity : Activity() {

    private lateinit var userPrefs: UserPreferences
    private lateinit var heroCardContainer: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        userPrefs = UserPreferences(this)

        val root = ScrollView(this).apply {
            setBackgroundColor(Color.parseColor("#0d0d0f")) // Deep obsidian
            isFillViewport = true
            isHorizontalScrollBarEnabled = false
            isVerticalScrollBarEnabled = false
        }

        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(28), dp(18), dp(40))
        }

        // --- Clean Minimal Header ---
        val headerLayout = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(8), 0, dp(24))
        }

        val appIcon = ImageView(this).apply {
            setImageResource(R.mipmap.ic_launcher)
            layoutParams = LinearLayout.LayoutParams(dp(44), dp(44)).apply {
                setMargins(0, 0, dp(14), 0)
            }
        }


        val titleCol = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        val appTitle = TextView(this).apply {
            text = "Bongo"
            textSize = 22f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
        }
        val versionTag = TextView(this).apply {
            text = "Bengali Phonetic Keyboard • v0.3.0"
            textSize = 12f
            setTextColor(Color.parseColor("#8e8e93"))
        }
        titleCol.addView(appTitle)
        titleCol.addView(versionTag)

        headerLayout.addView(appIcon)
        headerLayout.addView(titleCol)
        container.addView(headerLayout)

        // --- Smart Activation Hero Card ---
        heroCardContainer = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        container.addView(heroCardContainer)
        container.addView(createSpacer(dp(22)))

        // --- Appearance Card ---
        container.addView(createSectionHeader("APPEARANCE"))
        val appearanceCard = createGroupCard()

        // Theme Selector
        appearanceCard.addView(createSettingTitle("Theme", "Visual appearance of keyboard"))
        val themeRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            weightSum = 3f
            setPadding(0, dp(8), 0, dp(14))
        }
        val themeOptions = listOf("midnight" to "Midnight", "oled" to "OLED Black", "light" to "Light")
        val themeButtons = mutableListOf<Button>()

        themeOptions.forEach { (key, label) ->
            val isSelected = userPrefs.theme == key
            val btn = Button(this).apply {
                text = label
                textSize = 12f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(if (isSelected) Color.WHITE else Color.parseColor("#9ca3af"))
                background = createPillBackground(isSelected)
                layoutParams = LinearLayout.LayoutParams(0, dp(38), 1f).apply {
                    setMargins(dp(3), 0, dp(3), 0)
                }
                setOnClickListener {
                    userPrefs.theme = key
                    themeButtons.forEachIndexed { i, b ->
                        val sel = themeOptions[i].first == key
                        b.setTextColor(if (sel) Color.WHITE else Color.parseColor("#9ca3af"))
                        b.background = createPillBackground(sel)
                    }
                }
            }
            themeButtons.add(btn)
            themeRow.addView(btn)
        }
        appearanceCard.addView(themeRow)
        appearanceCard.addView(createDivider())

        // Keyboard Height Selector
        appearanceCard.addView(createSettingTitle("Keyboard Height", "Vertical size on screen"))
        val heightRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            weightSum = 3f
            setPadding(0, dp(8), 0, dp(14))
        }
        val heightOptions = listOf(250 to "Compact", 270 to "Standard", 295 to "Tall")
        val heightButtons = mutableListOf<Button>()

        heightOptions.forEach { (h, label) ->
            val isSelected = userPrefs.keyboardHeightDp == h
            val btn = Button(this).apply {
                text = label
                textSize = 12f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(if (isSelected) Color.WHITE else Color.parseColor("#9ca3af"))
                background = createPillBackground(isSelected)
                layoutParams = LinearLayout.LayoutParams(0, dp(38), 1f).apply {
                    setMargins(dp(3), 0, dp(3), 0)
                }
                setOnClickListener {
                    userPrefs.keyboardHeightDp = h
                    heightButtons.forEachIndexed { i, b ->
                        val sel = heightOptions[i].first == h
                        b.setTextColor(if (sel) Color.WHITE else Color.parseColor("#9ca3af"))
                        b.background = createPillBackground(sel)
                    }
                }
            }
            heightButtons.add(btn)
            heightRow.addView(btn)
        }
        appearanceCard.addView(heightRow)
        appearanceCard.addView(createDivider())

        // Top Number Row Toggle
        appearanceCard.addView(createSwitchRow(
            "Permanent Number Row",
            "Show digits (1-0 / ১-০) directly above letters",
            userPrefs.showNumberRow
        ) { userPrefs.showNumberRow = it })

        container.addView(appearanceCard)
        container.addView(createSpacer(dp(22)))

        // --- Keyboard Layout Card ---
        container.addView(createSectionHeader("KEYBOARD LAYOUT"))
        val layoutCard = createGroupCard()

        layoutCard.addView(createSettingTitle("Default Layout", "Select active Bengali typing method"))

        val layoutRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(16), 0, dp(16), dp(16))
        }

        val layoutOptions = listOf("Avro Phonetic" to 0, "National / Bijoy" to 1)
        val layoutButtons = mutableListOf<Button>()

        layoutOptions.forEach { (name, id) ->
            val isSelected = userPrefs.keyboardLayout == id
            val btn = Button(this).apply {
                text = name
                isAllCaps = false
                textSize = 13f
                typeface = if (isSelected) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                setTextColor(if (isSelected) Color.WHITE else Color.parseColor("#98989e"))
                background = createPillBackground(isSelected)
                layoutParams = LinearLayout.LayoutParams(0, dp(38), 1f).apply {
                    setMargins(dp(3), 0, dp(3), 0)
                }
                setOnClickListener {
                    userPrefs.keyboardLayout = id
                    layoutButtons.forEachIndexed { idx, b ->
                        val sel = layoutOptions[idx].second == id
                        b.setTextColor(if (sel) Color.WHITE else Color.parseColor("#98989e"))
                        b.typeface = if (sel) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                        b.background = createPillBackground(sel)
                    }
                }
            }
            layoutButtons.add(btn)
            layoutRow.addView(btn)
        }
        layoutCard.addView(layoutRow)
        container.addView(layoutCard)
        container.addView(createSpacer(dp(22)))

        // --- Typing & Gestures Card ---
        container.addView(createSectionHeader("TYPING & GESTURES"))
        val gesturesCard = createGroupCard()

        gesturesCard.addView(createSwitchRow(
            "Key Popup Preview",
            "Magnify key bubble above finger on touch",
            userPrefs.keyPopupPreview
        ) { userPrefs.keyPopupPreview = it })
        gesturesCard.addView(createDivider())

        gesturesCard.addView(createSwitchRow(
            "Spacebar Trackpad Scrubbing",
            "Slide spacebar horizontally to move text cursor",
            userPrefs.cursorScrubbing
        ) { userPrefs.cursorScrubbing = it })
        gesturesCard.addView(createDivider())

        gesturesCard.addView(createSwitchRow(
            "Swipe Backspace to Delete",
            "Slide left from backspace to delete entire words",
            userPrefs.swipeDeleteWords
        ) { userPrefs.swipeDeleteWords = it })
        gesturesCard.addView(createDivider())

        gesturesCard.addView(createSwitchRow(
            "Double-tap Space for Dari",
            "Quickly double-tap space to insert । (or . in English)",
            userPrefs.doubleSpacePeriod
        ) { userPrefs.doubleSpacePeriod = it })
        gesturesCard.addView(createDivider())

        gesturesCard.addView(createSwitchRow(
            "Long-Press Letter Hints",
            "Hold down letters for symbols and digits",
            userPrefs.longPressSymbols
        ) { userPrefs.longPressSymbols = it })
        gesturesCard.addView(createDivider())

        gesturesCard.addView(createSwitchRow(
            "Bengali Numerals (১, ২, ৩)",
            "Use Bengali digits instead of English numerals",
            userPrefs.bengaliDigits
        ) { userPrefs.bengaliDigits = it })

        container.addView(gesturesCard)
        container.addView(createSpacer(dp(22)))

        // --- Feedback Card ---
        container.addView(createSectionHeader("FEEDBACK"))
        val feedbackCard = createGroupCard()

        feedbackCard.addView(createSwitchRow(
            "Haptic Vibration",
            "Tactile click vibration on keypress",
            userPrefs.hapticFeedback
        ) { userPrefs.hapticFeedback = it })
        feedbackCard.addView(createDivider())

        feedbackCard.addView(createSwitchRow(
            "Sound Effects",
            "Audio mechanical keyclick on tap",
            userPrefs.soundFeedback
        ) { userPrefs.soundFeedback = it })

        container.addView(feedbackCard)
        container.addView(createSpacer(dp(22)))

        // --- Core Engine Status Badge ---
        container.addView(createSectionHeader("CORE ENGINE"))
        val statusCard = createGroupCard()
        val statusRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(4), 0, dp(4))
        }
        val isNative = BongoNative.isLoaded
        val statusDot = View(this).apply {
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(if (isNative) Color.parseColor("#10b981") else Color.parseColor("#3b82f6"))
            }
            layoutParams = LinearLayout.LayoutParams(dp(10), dp(10)).apply {
                setMargins(0, 0, dp(10), 0)
            }
        }
        val statusText = TextView(this).apply {
            text = if (isNative) "Rust Native Core (Optimized 64-bit JNI)" else "Pure-Kotlin Engine (Resilient Fallback)"
            textSize = 13f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.parseColor("#e4e4e7"))
        }
        statusRow.addView(statusDot)
        statusRow.addView(statusText)
        statusCard.addView(statusRow)
        container.addView(statusCard)

        // Footer
        val footer = TextView(this).apply {
            text = "Bongo Bengali Keyboard • Free & Open Source\nPair programmed with care for Bengal"
            textSize = 11f
            setTextColor(Color.parseColor("#52525b"))
            gravity = Gravity.CENTER
            setPadding(0, dp(28), 0, dp(12))
        }
        container.addView(footer)

        root.addView(container)
        setContentView(root)

        updateHeroCard()
    }

    override fun onResume() {
        super.onResume()
        updateHeroCard()
    }

    private fun isBongoEnabled(): Boolean {
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager ?: return false
        return imm.enabledInputMethodList.any { it.packageName == packageName }
    }

    private fun isBongoSelected(): Boolean {
        val currentIme = Settings.Secure.getString(contentResolver, Settings.Secure.DEFAULT_INPUT_METHOD)
        return currentIme?.contains(packageName) == true
    }

    private fun updateHeroCard() {
        heroCardContainer.removeAllViews()

        val isEnabled = isBongoEnabled()
        val isSelected = isBongoSelected()

        val heroCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = GradientDrawable().apply {
                cornerRadius = dp(16).toFloat()
                if (isSelected) {
                    setColor(Color.parseColor("#131a15")) // Deep subtle emerald
                    setStroke(dp(1), Color.parseColor("#059669"))
                } else {
                    setColor(Color.parseColor("#171720")) // Deep indigo/neutral
                    setStroke(dp(1), Color.parseColor("#4f46e5"))
                }
            }
            setPadding(dp(18), dp(18), dp(18), dp(18))
        }

        if (isSelected) {
            // State: Ready to type
            val statusHeader = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            val checkmark = TextView(this).apply {
                text = "✓"
                textSize = 16f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.parseColor("#34d399"))
                setPadding(0, 0, dp(8), 0)
            }
            val statusLabel = TextView(this).apply {
                text = "Bongo is Active & Ready"
                textSize = 15f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.parseColor("#34d399"))
            }
            statusHeader.addView(checkmark)
            statusHeader.addView(statusLabel)
            heroCard.addView(statusHeader)

            val testField = EditText(this).apply {
                hint = "Tap here to test typing with Bongo..."
                setHintTextColor(Color.parseColor("#71717a"))
                setTextColor(Color.WHITE)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                background = GradientDrawable().apply {
                    cornerRadius = dp(10).toFloat()
                    setColor(Color.parseColor("#1c1c24"))
                    setStroke(dp(1), Color.parseColor("#2a2b36"))
                }
                setPadding(dp(14), dp(12), dp(14), dp(12))
                val lp = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    setMargins(0, dp(12), 0, 0)
                }
                layoutParams = lp
            }
            heroCard.addView(testField)

        } else if (!isEnabled) {
            // State 1: Enable in Settings
            val title = TextView(this).apply {
                text = "Activate Bongo Keyboard"
                textSize = 15f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.WHITE)
            }
            val desc = TextView(this).apply {
                text = "Enable Bongo in Android input settings to start typing."
                textSize = 12f
                setTextColor(Color.parseColor("#a1a1aa"))
                setPadding(0, dp(2), 0, dp(12))
            }
            val btn = Button(this).apply {
                text = "Enable in Android Settings"
                textSize = 13f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.WHITE)
                background = GradientDrawable().apply {
                    cornerRadius = dp(10).toFloat()
                    setColor(Color.parseColor("#4f46e5"))
                }
                setPadding(dp(16), dp(10), dp(16), dp(10))
                setOnClickListener {
                    startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))
                }
            }
            heroCard.addView(title)
            heroCard.addView(desc)
            heroCard.addView(btn)

        } else {
            // State 2: Select as default
            val title = TextView(this).apply {
                text = "Set as Default Keyboard"
                textSize = 15f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.WHITE)
            }
            val desc = TextView(this).apply {
                text = "Bongo is enabled. Switch your active input method to Bongo."
                textSize = 12f
                setTextColor(Color.parseColor("#a1a1aa"))
                setPadding(0, dp(2), 0, dp(12))
            }
            val btn = Button(this).apply {
                text = "Choose Bongo Keyboard"
                textSize = 13f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(Color.WHITE)
                background = GradientDrawable().apply {
                    cornerRadius = dp(10).toFloat()
                    setColor(Color.parseColor("#4f46e5"))
                }
                setPadding(dp(16), dp(10), dp(16), dp(10))
                setOnClickListener {
                    val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
                    imm?.showInputMethodPicker()
                }
            }
            heroCard.addView(title)
            heroCard.addView(desc)
            heroCard.addView(btn)
        }

        heroCardContainer.addView(heroCard)
    }

    private fun createSectionHeader(title: String): TextView = TextView(this).apply {
        text = title
        textSize = 11f
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(Color.parseColor("#6366f1")) // Indigo accent header
        setPadding(dp(4), 0, 0, dp(8))
    }

    private fun createGroupCard(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = GradientDrawable().apply {
            cornerRadius = dp(16).toFloat()
            setColor(Color.parseColor("#141417")) // Sleek card surface
            setStroke(dp(1), Color.parseColor("#222228"))
        }
        setPadding(dp(16), dp(14), dp(16), dp(14))
    }

    private fun createSettingTitle(title: String, subtitle: String): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(0, dp(4), 0, dp(4))

        val tvTitle = TextView(context).apply {
            text = title
            textSize = 14f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.parseColor("#f4f4f5"))
        }
        val tvSub = TextView(context).apply {
            text = subtitle
            textSize = 11f
            setTextColor(Color.parseColor("#71717a"))
        }
        addView(tvTitle)
        addView(tvSub)
    }

    private fun createSwitchRow(
        title: String,
        subtitle: String,
        initialChecked: Boolean,
        onChecked: (Boolean) -> Unit
    ): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        setPadding(0, dp(6), 0, dp(6))

        val textCol = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        val tvTitle = TextView(context).apply {
            text = title
            textSize = 14f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.parseColor("#f4f4f5"))
        }
        val tvSub = TextView(context).apply {
            text = subtitle
            textSize = 11f
            setTextColor(Color.parseColor("#71717a"))
        }
        textCol.addView(tvTitle)
        textCol.addView(tvSub)

        val sw = Switch(context).apply {
            isChecked = initialChecked
            setOnCheckedChangeListener { _, checked -> onChecked(checked) }
        }

        addView(textCol)
        addView(sw)
    }

    private fun createPillBackground(isSelected: Boolean): GradientDrawable = GradientDrawable().apply {
        cornerRadius = dp(10).toFloat()
        if (isSelected) {
            setColor(Color.parseColor("#4f46e5"))
            setStroke(dp(1), Color.parseColor("#6366f1"))
        } else {
            setColor(Color.parseColor("#1f1f26"))
            setStroke(dp(1), Color.parseColor("#2d2d38"))
        }
    }

    private fun createDivider(): View = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(1)
        ).apply {
            setMargins(0, dp(8), 0, dp(8))
        }
        setBackgroundColor(Color.parseColor("#1f1f26"))
    }

    private fun createSpacer(heightPx: Int): View = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            heightPx
        )
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()
}
