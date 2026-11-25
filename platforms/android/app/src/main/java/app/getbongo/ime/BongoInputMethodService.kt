package app.getbongo.ime

import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.res.Configuration
import android.inputmethodservice.InputMethodService
import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import androidx.core.content.ContextCompat
import app.getbongo.ime.ui.VoicePermissionActivity
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.util.TypedValue
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import java.io.File
import app.getbongo.ime.engine.BongoEngine
import app.getbongo.ime.model.ThemePalette
import app.getbongo.ime.model.UserPreferences
import app.getbongo.ime.ui.BongoKeyboardView
import app.getbongo.ime.ui.CandidateStripView
import app.getbongo.ime.ui.EmojiKeyboardView
import app.getbongo.ime.ui.SettingsActivity

/**
 * Main Android InputMethodService for Bongo.
 * Handles input routing between soft/hardware keyboard, the Bongo phonetic engine,
 * candidate selection strip, shortcuts toolbar (Ctrl, Tab, Esc, Clipboard, Voice),
 * emoji panel, and the target application's InputConnection.
 */
class BongoInputMethodService : InputMethodService() {

    private lateinit var bongoEngine: BongoEngine
    private lateinit var userPrefs: UserPreferences
    private lateinit var userDictionary: app.getbongo.ime.model.UserDictionaryManager
    private var keyboardView: BongoKeyboardView? = null
    private var emojiKeyboardView: EmojiKeyboardView? = null
    private var candidateStripView: CandidateStripView? = null
    private var keyboardFrame: FrameLayout? = null
    private var keyboardContainer: LinearLayout? = null
    private var leftOneHandedBar: LinearLayout? = null
    private var rightOneHandedBar: LinearLayout? = null
    private var dividerView: View? = null
    private var rootView: LinearLayout? = null

    private var isBanglaMode = true
    private var isCtrlActive = false
    private var isEmojiSearchMode = false
    private val emojiSearchRaw = StringBuilder()
    private var lastSpaceTime = 0L

    private val clipboardHistory = mutableListOf<String>()
    private var clipboardManager: ClipboardManager? = null
    private val clipListener = ClipboardManager.OnPrimaryClipChangedListener {
        updateLatestClip()
    }

    private val prefChangeListener = SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        handlePreferenceChange(key)
    }

    override fun onCreate() {
        super.onCreate()
        bongoEngine = BongoEngine()
        userPrefs = UserPreferences(this)
        userDictionary = app.getbongo.ime.model.UserDictionaryManager(this)
        bongoEngine.customShortcuts = userDictionary.getShortcuts()
        bongoEngine.learnedSelections = userPrefs.getLearnedSelections()
        bongoEngine.setLayout(userPrefs.keyboardLayout)
        userPrefs.registerListener(prefChangeListener)

        // Load persistent clipboard history
        clipboardHistory.clear()
        clipboardHistory.addAll(userPrefs.getClipboardHistory())

        try {
            val cm = getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
            clipboardManager = cm
            cm?.addPrimaryClipChangedListener(clipListener)
            updateLatestClip()
        } catch (_: Exception) {}
    }

    private fun updateLatestClip() {
        try {
            val clip = clipboardManager?.primaryClip
            if (clip != null && clip.itemCount > 0) {
                val text = clip.getItemAt(0)?.coerceToText(this)?.toString()?.trim()
                if (!text.isNullOrEmpty()) {
                    clipboardHistory.remove(text)
                    clipboardHistory.add(0, text)
                    if (clipboardHistory.size > 20) {
                        clipboardHistory.removeAt(clipboardHistory.size - 1)
                    }
                    userPrefs.saveClipboardHistory(clipboardHistory)
                }
            }
        } catch (_: Exception) {}
    }

    override fun onCreateInputView(): View {
        val palette = ThemePalette.getPalette(userPrefs.theme)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(palette.surfaceColor)
        }
        rootView = root

        candidateStripView = CandidateStripView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(44)
            )
            applyTheme(palette)
            onCandidateSelected = { index, candidate ->
                handleCandidateSelection(index, candidate)
            }
            onShortcutAction = { action ->
                handleShortcutAction(action)
            }
        }

        val divider = View(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(1)
            )
            setBackgroundColor(palette.dividerColor)
        }
        dividerView = divider

        val containerLayout = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(getTargetKeyboardHeight())
            )
        }
        keyboardContainer = containerLayout

        val leftBar = createOneHandedSideBar(isLeft = true)
        leftOneHandedBar = leftBar

        val frame = FrameLayout(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.MATCH_PARENT,
                1f
            )
        }
        keyboardFrame = frame

        val rightBar = createOneHandedSideBar(isLeft = false)
        rightOneHandedBar = rightBar

        keyboardView = BongoKeyboardView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
            setBanglaMode(isBanglaMode)
            applyTheme(palette)
            onKeyClickListener = { action ->
                handleKeyAction(action)
            }
        }

        emojiKeyboardView = EmojiKeyboardView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
            visibility = View.GONE
            onEmojiSelected = { emoji ->
                currentInputConnection?.commitText(emoji, 1)
            }
            onBackToKeyboard = {
                showKeyboard()
            }
            onBackspace = {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_DEL)
            }
            onStartTypeSearch = {
                startEmojiSearch()
            }
        }

        frame.addView(keyboardView)
        frame.addView(emojiKeyboardView)

        containerLayout.addView(leftBar)
        containerLayout.addView(frame)
        containerLayout.addView(rightBar)
        applyOneHandedMode()

        root.addView(candidateStripView)
        root.addView(divider)
        root.addView(containerLayout)

        return root
    }

    private fun showKeyboard() {
        emojiKeyboardView?.visibility = View.GONE
        keyboardView?.visibility = View.VISIBLE
        candidateStripView?.visibility = View.VISIBLE
    }

    private fun showEmojiKeyboard() {
        exitEmojiSearch(restoreShortcuts = false)
        commitOngoingComposition()
        keyboardView?.visibility = View.GONE
        candidateStripView?.visibility = View.GONE
        emojiKeyboardView?.visibility = View.VISIBLE
    }

    private fun startEmojiSearch() {
        commitOngoingComposition()
        bongoEngine.resetSession()
        emojiSearchRaw.clear()
        isEmojiSearchMode = true
        showKeyboard()
        updateEmojiSearchStrip()
    }

    private fun exitEmojiSearch(restoreShortcuts: Boolean = true) {
        if (!isEmojiSearchMode) return
        isEmojiSearchMode = false
        emojiSearchRaw.clear()
        bongoEngine.resetSession()
        if (restoreShortcuts) {
            candidateStripView?.clear()
        }
    }

    private fun updateEmojiSearchStrip() {
        val raw = emojiSearchRaw.toString()
        val bangla = if (raw.isNotEmpty() && isBanglaMode) bongoEngine.preedit else ""
        val displayQuery = if (bangla.isNotEmpty() && bangla != raw) "$bangla ($raw)" else raw
        val matches = EmojiKeyboardView.searchEmojis(raw, bangla)
        candidateStripView?.showEmojiSearchBar(
            query = displayQuery,
            matches = matches,
            onEmojiPick = { emoji ->
                currentInputConnection?.commitText(emoji, 1)
                emojiKeyboardView?.recordEmojiUsed(emoji)
                exitEmojiSearch(restoreShortcuts = true)
            },
            onClose = {
                exitEmojiSearch(restoreShortcuts = true)
            }
        )
    }

    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        exitEmojiSearch(restoreShortcuts = false)
        showKeyboard()
        resetComposition()
        bongoEngine.customShortcuts = userDictionary.getShortcuts()
        updateLatestClip()

        // Sync theme and height changes from settings
        val palette = ThemePalette.getPalette(userPrefs.theme)
        rootView?.setBackgroundColor(palette.surfaceColor)
        dividerView?.setBackgroundColor(palette.dividerColor)
        candidateStripView?.applyTheme(palette)
        keyboardView?.applyTheme(palette)
        emojiKeyboardView?.applyTheme(palette)

        val inputType = info?.inputType ?: 0
        val imeOptions = info?.imeOptions ?: 0
        val isMultiLine = (inputType and EditorInfo.TYPE_MASK_CLASS == EditorInfo.TYPE_CLASS_TEXT) &&
                ((inputType and EditorInfo.TYPE_TEXT_FLAG_MULTI_LINE) != 0)
        val hasNoEnterAction = (imeOptions and EditorInfo.IME_FLAG_NO_ENTER_ACTION) != 0
        val actionId = imeOptions and EditorInfo.IME_MASK_ACTION

        val actionLabel = if (isMultiLine && !hasNoEnterAction) {
            "⏎"
        } else {
            when (actionId) {
                EditorInfo.IME_ACTION_GO -> "Go"
                EditorInfo.IME_ACTION_SEARCH -> "Search"
                EditorInfo.IME_ACTION_SEND -> "Send"
                EditorInfo.IME_ACTION_NEXT -> "Next"
                EditorInfo.IME_ACTION_DONE -> if (isMultiLine) "⏎" else "Done"
                else -> if (isMultiLine) "⏎" else "Go"
            }
        }
        val isUri = (inputType and EditorInfo.TYPE_MASK_VARIATION) == EditorInfo.TYPE_TEXT_VARIATION_URI
        keyboardView?.setActionInfo(actionLabel, isUri)

        val inputClass = inputType and EditorInfo.TYPE_MASK_CLASS
        val inputVariation = inputType and EditorInfo.TYPE_MASK_VARIATION
        val isPassword = (inputClass == EditorInfo.TYPE_CLASS_TEXT) && (
            inputVariation == EditorInfo.TYPE_TEXT_VARIATION_PASSWORD ||
            inputVariation == EditorInfo.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD ||
            inputVariation == EditorInfo.TYPE_TEXT_VARIATION_WEB_PASSWORD
        )
        val isNumberClass = inputClass == EditorInfo.TYPE_CLASS_NUMBER || inputClass == EditorInfo.TYPE_CLASS_PHONE

        // Auto-show number row in password or numeric fields for easy digit entry
        keyboardView?.setAutoNumberRow(isPassword || isNumberClass)

        // Update container height after auto-number-row & tablet/orientation evaluation
        updateKeyboardContainerHeight()

        // For security and accuracy, switch to English mode in password fields
        if (isPassword && isBanglaMode) {
            isBanglaMode = false
            keyboardView?.setBanglaMode(false)
        }
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        updateKeyboardContainerHeight()
        keyboardView?.buildKeyboard()
    }

    private fun isTablet(): Boolean =
        resources.configuration.smallestScreenWidthDp >= 600

    private fun isLandscape(): Boolean =
        resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE

    private fun updateKeyboardContainerHeight() {
        keyboardContainer?.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(getTargetKeyboardHeight())
        )
        keyboardContainer?.requestLayout()
    }

    private fun getTargetKeyboardHeight(): Int {
        val showNumRow = userPrefs.showNumberRow || (keyboardView?.isAutoNumberRow == true) || isTablet()
        if (isLandscape()) {
            val base = if (isTablet()) 210 else 164
            return if (showNumRow) base + 30 else base
        }
        val base = userPrefs.keyboardHeightDp
        return if (showNumRow) base + 36 else base
    }


    override fun onFinishInputView(finishingInput: Boolean) {
        super.onFinishInputView(finishingInput)
        exitEmojiSearch(restoreShortcuts = false)
        commitOngoingComposition()
        resetComposition()
    }

    private var speechRecognizer: SpeechRecognizer? = null
    private var isVoiceListening = false

    private fun cycleTheme() {
        val themes = listOf("midnight", "light", "oled", "emerald", "crimson", "nord")
        val currentIdx = themes.indexOf(userPrefs.theme.lowercase())
        val nextIdx = if (currentIdx == -1) 0 else (currentIdx + 1) % themes.size
        val chosenTheme = themes[nextIdx]
        userPrefs.theme = chosenTheme
        val palette = ThemePalette.getPalette(chosenTheme)
        rootView?.setBackgroundColor(palette.surfaceColor)
        dividerView?.setBackgroundColor(palette.dividerColor)
        leftOneHandedBar?.setBackgroundColor(palette.surfaceColor)
        rightOneHandedBar?.setBackgroundColor(palette.surfaceColor)
        keyboardView?.applyTheme(palette)
        candidateStripView?.applyTheme(palette)
        emojiKeyboardView?.applyTheme(palette)
    }

    private fun createOneHandedSideBar(isLeft: Boolean): LinearLayout {
        val palette = ThemePalette.getPalette(userPrefs.theme)
        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(dp(48), LinearLayout.LayoutParams.MATCH_PARENT)
            setBackgroundColor(palette.surfaceColor)

            val switchBtn = TextView(context).apply {
                text = if (isLeft) "▶" else "◀"
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
                typeface = Typeface.DEFAULT_BOLD
                gravity = Gravity.CENTER
                setTextColor(palette.stripSecondaryText)
                setPadding(dp(8), dp(16), dp(8), dp(16))
                isClickable = true
                isFocusable = true
                setOnClickListener {
                    userPrefs.oneHandedMode = if (isLeft) "right" else "left"
                    applyOneHandedMode()
                }
            }

            val expandBtn = TextView(context).apply {
                text = "⤢"
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
                typeface = Typeface.DEFAULT_BOLD
                gravity = Gravity.CENTER
                setTextColor(palette.stripSecondaryText)
                setPadding(dp(8), dp(16), dp(8), dp(16))
                isClickable = true
                isFocusable = true
                setOnClickListener {
                    userPrefs.oneHandedMode = "none"
                    applyOneHandedMode()
                }
            }

            addView(switchBtn)
            addView(View(context).apply { layoutParams = LinearLayout.LayoutParams(dp(1), dp(16)) })
            addView(expandBtn)
        }
    }

    private fun applyOneHandedMode() {
        when (userPrefs.oneHandedMode) {
            "left" -> {
                leftOneHandedBar?.visibility = View.GONE
                rightOneHandedBar?.visibility = View.VISIBLE
            }
            "right" -> {
                leftOneHandedBar?.visibility = View.VISIBLE
                rightOneHandedBar?.visibility = View.GONE
            }
            else -> {
                leftOneHandedBar?.visibility = View.GONE
                rightOneHandedBar?.visibility = View.GONE
            }
        }
        keyboardContainer?.requestLayout()
    }

    private fun handleShortcutAction(action: CandidateStripView.ShortcutAction) {
        val ic = currentInputConnection ?: return

        when (action) {
            is CandidateStripView.ShortcutAction.Emoji -> {
                showEmojiKeyboard()
            }
            is CandidateStripView.ShortcutAction.Theme -> {
                cycleTheme()
            }
            is CandidateStripView.ShortcutAction.Settings -> {
                val intent = Intent(this, SettingsActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                startActivity(intent)
            }
            is CandidateStripView.ShortcutAction.More -> {
                keyboardView?.toggleOptionsPanel()
            }
            is CandidateStripView.ShortcutAction.Esc -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_ESCAPE)
            }
            is CandidateStripView.ShortcutAction.Tab -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_TAB)
            }
            is CandidateStripView.ShortcutAction.ToggleCtrl -> {
                isCtrlActive = !isCtrlActive
                candidateStripView?.setCtrlActive(isCtrlActive)
            }
            is CandidateStripView.ShortcutAction.Clipboard -> {
                handleClipboardAction()
            }
            is CandidateStripView.ShortcutAction.VoiceInput -> {
                handleVoiceInputAction()
            }
            is CandidateStripView.ShortcutAction.SelectAll -> {
                ic.performContextMenuAction(android.R.id.selectAll)
            }
            is CandidateStripView.ShortcutAction.Copy -> {
                ic.performContextMenuAction(android.R.id.copy)
            }
            is CandidateStripView.ShortcutAction.Paste -> {
                ic.performContextMenuAction(android.R.id.paste)
            }
            is CandidateStripView.ShortcutAction.CursorLeft -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_DPAD_LEFT)
            }
            is CandidateStripView.ShortcutAction.CursorRight -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_DPAD_RIGHT)
            }
            is CandidateStripView.ShortcutAction.OneHanded -> {
                userPrefs.oneHandedMode = when (userPrefs.oneHandedMode) {
                    "none" -> "right"
                    "right" -> "left"
                    else -> "none"
                }
                applyOneHandedMode()
            }
        }
    }

    private fun handleClipboardAction() {
        updateLatestClip()
        if (clipboardHistory.isNotEmpty()) {
            candidateStripView?.showClipboardHistory(clipboardHistory.toList()) { toPaste ->
                currentInputConnection?.commitText(toPaste, 1)
            }
        } else {
            currentInputConnection?.performContextMenuAction(android.R.id.paste)
        }
    }

    private fun handleVoiceInputAction() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            val intent = Intent(this, VoicePermissionActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivity(intent)
            return
        }

        if (isVoiceListening) {
            stopVoiceListening()
            return
        }

        startVoiceListening()
    }

    private fun startVoiceListening() {
        val handler = Handler(Looper.getMainLooper())
        handler.post {
            try {
                if (!SpeechRecognizer.isRecognitionAvailable(this)) {
                    switchToVoiceImeOrNotify()
                    return@post
                }

                speechRecognizer?.destroy()
                speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).apply {
                    setRecognitionListener(object : RecognitionListener {
                        override fun onReadyForSpeech(params: Bundle?) {
                            isVoiceListening = true
                            candidateStripView?.showVoiceListening("Speak now...") {
                                stopVoiceListening()
                            }
                        }

                        override fun onBeginningOfSpeech() {
                            candidateStripView?.updateVoicePrompt("Listening...")
                        }

                        override fun onRmsChanged(rmsdB: Float) {}

                        override fun onBufferReceived(buffer: ByteArray?) {}

                        override fun onEndOfSpeech() {
                            candidateStripView?.updateVoicePrompt("Processing...")
                        }

                        override fun onError(error: Int) {
                            isVoiceListening = false
                            candidateStripView?.showShortcuts()
                            when (error) {
                                SpeechRecognizer.ERROR_NO_MATCH,
                                SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> {
                                    // User paused or finished speaking
                                }
                                SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> {
                                    val intent = Intent(this@BongoInputMethodService, VoicePermissionActivity::class.java).apply {
                                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                    }
                                    startActivity(intent)
                                }
                                else -> {
                                    Toast.makeText(this@BongoInputMethodService, "Speech recognition error: $error", Toast.LENGTH_SHORT).show()
                                }
                            }
                        }

                        override fun onResults(results: Bundle?) {
                            isVoiceListening = false
                            candidateStripView?.showShortcuts()
                            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                            if (!matches.isNullOrEmpty()) {
                                val recognized = matches[0]
                                val ic = currentInputConnection
                                if (ic != null && recognized.isNotEmpty()) {
                                    ic.finishComposingText()
                                    ic.commitText("$recognized ", 1)
                                }
                            }
                        }

                        override fun onPartialResults(partialResults: Bundle?) {
                            val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                            if (!matches.isNullOrEmpty()) {
                                val partial = matches[0]
                                val ic = currentInputConnection
                                ic?.setComposingText(partial, 1)
                            }
                        }

                        override fun onEvent(eventType: Int, params: Bundle?) {}
                    })
                }

                val recognizerIntent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, if (isBanglaMode) "bn-BD" else "en-US")
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                }

                isVoiceListening = true
                speechRecognizer?.startListening(recognizerIntent)
                candidateStripView?.showVoiceListening("Speak now...") {
                    stopVoiceListening()
                }
            } catch (e: Exception) {
                isVoiceListening = false
                candidateStripView?.showShortcuts()
                Toast.makeText(this, "Voice typing unavailable: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun stopVoiceListening() {
        isVoiceListening = false
        try {
            speechRecognizer?.stopListening()
        } catch (_: Exception) {}
        candidateStripView?.showShortcuts()
    }

    private fun switchToVoiceImeOrNotify() {
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
        val voiceSubtype = imm?.enabledInputMethodList?.firstOrNull { imi ->
            imi.packageName.contains("speech") || imi.packageName.contains("tts") || imi.id.contains("voice")
        }
        if (voiceSubtype != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            try {
                switchInputMethod(voiceSubtype.id)
                return
            } catch (_: Exception) {}
        }
        Toast.makeText(this, "Voice recognition service not available on device", Toast.LENGTH_SHORT).show()
    }

    private fun handleKeyAction(action: BongoKeyboardView.KeyAction) {
        val ic = currentInputConnection ?: return

        when (action) {
            is BongoKeyboardView.KeyAction.CharacterKey -> {
                val ch = action.ch

                // If Ctrl is active, dispatch Ctrl shortcut
                if (isCtrlActive) {
                    val lower = ch.lowercaseChar()
                    when (lower) {
                        'a' -> ic.performContextMenuAction(android.R.id.selectAll)
                        'c' -> ic.performContextMenuAction(android.R.id.copy)
                        'v' -> ic.performContextMenuAction(android.R.id.paste)
                        'x' -> ic.performContextMenuAction(android.R.id.cut)
                        'z' -> ic.performContextMenuAction(android.R.id.undo)
                        else -> {
                            val keyCode = when (lower) {
                                'd' -> KeyEvent.KEYCODE_D
                                'l' -> KeyEvent.KEYCODE_L
                                'w' -> KeyEvent.KEYCODE_W
                                'k' -> KeyEvent.KEYCODE_K
                                'u' -> KeyEvent.KEYCODE_U
                                'e' -> KeyEvent.KEYCODE_E
                                else -> KeyEvent.KEYCODE_UNKNOWN
                            }
                            if (keyCode != KeyEvent.KEYCODE_UNKNOWN) {
                                val now = SystemClock.uptimeMillis()
                                ic.sendKeyEvent(KeyEvent(now, now, KeyEvent.ACTION_DOWN, keyCode, 0, KeyEvent.META_CTRL_ON))
                                ic.sendKeyEvent(KeyEvent(now, now, KeyEvent.ACTION_UP, keyCode, 0, KeyEvent.META_CTRL_ON))
                            }
                        }
                    }
                    isCtrlActive = false
                    candidateStripView?.setCtrlActive(false)
                    return
                }

                if (isEmojiSearchMode) {
                    emojiSearchRaw.append(ch)
                    if (isBanglaMode && (ch in 'a'..'z' || ch in 'A'..'Z')) {
                        bongoEngine.feedChar(ch, keyboardView?.isShifted == true)
                    }
                    updateEmojiSearchStrip()
                    return
                }

                if (ch == '/' || ch == '\\' || ch == ',' || ch == '।' || (!isBanglaMode && ch == '.')) {
                    commitOngoingComposition()
                    ic.commitText(ch.toString(), 1)
                    return
                }

                if (isBanglaMode && (ch in 'a'..'z' || ch in 'A'..'Z' || ch in "0123456789`~@#\$%^&*()-_=+[{]}\\|;:'\",<.>/?")) {
                    bongoEngine.feedChar(ch, keyboardView?.isShifted == true)
                    val composing = bongoEngine.preedit
                    ic.setComposingText(composing, 1)
                    candidateStripView?.setCandidates(bongoEngine.candidates.take(userPrefs.candidateCount))
                } else {
                    commitOngoingComposition()
                    ic.commitText(ch.toString(), 1)
                }
            }
            is BongoKeyboardView.KeyAction.Backspace -> {
                if (isEmojiSearchMode) {
                    if (emojiSearchRaw.isNotEmpty()) {
                        emojiSearchRaw.deleteCharAt(emojiSearchRaw.length - 1)
                        if (isBanglaMode && bongoEngine.hasSession()) {
                            bongoEngine.handleBackspace()
                        }
                        updateEmojiSearchStrip()
                    } else {
                        exitEmojiSearch(restoreShortcuts = true)
                    }
                    return
                }
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val hasRemaining = bongoEngine.handleBackspace()
                    if (hasRemaining && bongoEngine.preedit.isNotEmpty()) {
                        ic.setComposingText(bongoEngine.preedit, 1)
                        candidateStripView?.setCandidates(bongoEngine.candidates.take(userPrefs.candidateCount))
                    } else {
                        ic.setComposingText("", 0)
                        candidateStripView?.clear()
                    }
                } else {
                    candidateStripView?.clear()
                    sendDownUpKeyEvents(KeyEvent.KEYCODE_DEL)
                }
            }
            is BongoKeyboardView.KeyAction.DeleteWord -> {
                if (bongoEngine.hasSession()) {
                    resetComposition()
                } else {
                    val before = ic.getTextBeforeCursor(80, 0)?.toString()
                    if (!before.isNullOrEmpty()) {
                        val trimmed = before.trimEnd()
                        val lastWordIndex = trimmed.lastIndexOfAny(charArrayOf(' ', '\n', '\t', '।', '.', ',', '!', '?', ';', ':'))
                        val charsToDelete = if (lastWordIndex == -1) before.length else (before.length - (lastWordIndex + 1))
                        ic.deleteSurroundingText(charsToDelete.coerceAtLeast(1), 0)
                    } else {
                        sendDownUpKeyEvents(KeyEvent.KEYCODE_DEL)
                    }
                    candidateStripView?.clear()
                }
            }
            is BongoKeyboardView.KeyAction.Space -> {
                if (isEmojiSearchMode) {
                    emojiSearchRaw.append(' ')
                    bongoEngine.resetSession()
                    updateEmojiSearchStrip()
                    return
                }
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val committed = bongoEngine.commitCandidate(0)
                    val finalText = if (userPrefs.bengaliDigits) committed.tobengaliDigits() else committed
                    ic.commitText("$finalText ", 1)
                    showNextWordPredictions(finalText)
                    lastSpaceTime = SystemClock.uptimeMillis()
                } else {
                    val now = SystemClock.uptimeMillis()
                    // Double-tap Space for Dari (।) / Period (.)
                    if (userPrefs.doubleSpacePeriod && (now - lastSpaceTime < 350L) && !bongoEngine.hasSession()) {
                        sendDownUpKeyEvents(KeyEvent.KEYCODE_DEL)
                        val period = if (isBanglaMode) "। " else ". "
                        ic.commitText(period, 1)
                        lastSpaceTime = 0L
                    } else {
                        ic.commitText(" ", 1)
                        lastSpaceTime = now
                    }
                    candidateStripView?.clear()
                }
            }
            is BongoKeyboardView.KeyAction.Return -> {
                if (isEmojiSearchMode) {
                    val raw = emojiSearchRaw.toString()
                    if (raw.isNotBlank()) {
                        val bangla = if (isBanglaMode) bongoEngine.preedit else ""
                        val topMatch = EmojiKeyboardView.searchEmojis(raw, bangla).firstOrNull()
                        if (topMatch != null) {
                            ic.commitText(topMatch, 1)
                            emojiKeyboardView?.recordEmojiUsed(topMatch)
                        }
                    }
                    exitEmojiSearch(restoreShortcuts = true)
                    return
                }
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val committed = bongoEngine.commitCandidate(0)
                    val finalText = if (userPrefs.bengaliDigits) committed.tobengaliDigits() else committed
                    ic.commitText(finalText, 1)
                    candidateStripView?.clear()
                }
                val editorInfo = currentInputEditorInfo
                val inputType = editorInfo?.inputType ?: 0
                val imeOptions = editorInfo?.imeOptions ?: 0
                val isMultiLine = (inputType and EditorInfo.TYPE_MASK_CLASS == EditorInfo.TYPE_CLASS_TEXT) &&
                        ((inputType and EditorInfo.TYPE_TEXT_FLAG_MULTI_LINE) != 0)
                val hasNoEnterAction = (imeOptions and EditorInfo.IME_FLAG_NO_ENTER_ACTION) != 0
                val actionId = imeOptions and EditorInfo.IME_MASK_ACTION

                if (isMultiLine && !hasNoEnterAction) {
                    sendDownUpKeyEvents(KeyEvent.KEYCODE_ENTER)
                } else if (actionId != EditorInfo.IME_ACTION_NONE && actionId != EditorInfo.IME_ACTION_UNSPECIFIED) {
                    ic.performEditorAction(actionId)
                } else {
                    sendDownUpKeyEvents(KeyEvent.KEYCODE_ENTER)
                }
            }
            is BongoKeyboardView.KeyAction.InsertNewline -> {
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val committed = bongoEngine.commitCandidate(0)
                    val finalText = if (userPrefs.bengaliDigits) committed.tobengaliDigits() else committed
                    ic.commitText(finalText, 1)
                    candidateStripView?.clear()
                }
                ic.commitText("\n", 1)
            }
            is BongoKeyboardView.KeyAction.ToggleLanguage -> {
                if (isEmojiSearchMode) {
                    isBanglaMode = !isBanglaMode
                    keyboardView?.setBanglaMode(isBanglaMode)
                    bongoEngine.resetSession()
                    updateEmojiSearchStrip()
                } else {
                    commitOngoingComposition()
                    isBanglaMode = !isBanglaMode
                    keyboardView?.setBanglaMode(isBanglaMode)
                }
            }
            is BongoKeyboardView.KeyAction.SwitchImePicker -> {
                commitOngoingComposition()
                val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
                imm?.showInputMethodPicker()
            }
            is BongoKeyboardView.KeyAction.OpenSettings -> {
                val intent = Intent(this, SettingsActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                startActivity(intent)
            }
            is BongoKeyboardView.KeyAction.ToggleEmoji -> {
                showEmojiKeyboard()
            }
            is BongoKeyboardView.KeyAction.CursorLeft -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_DPAD_LEFT)
            }
            is BongoKeyboardView.KeyAction.CursorRight -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_DPAD_RIGHT)
            }
            is BongoKeyboardView.KeyAction.Esc -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_ESCAPE)
            }
            is BongoKeyboardView.KeyAction.Tab -> {
                sendDownUpKeyEvents(KeyEvent.KEYCODE_TAB)
            }
            is BongoKeyboardView.KeyAction.Ctrl -> {
                isCtrlActive = !isCtrlActive
                candidateStripView?.setCtrlActive(isCtrlActive)
            }
            is BongoKeyboardView.KeyAction.OpenThemes -> {
                cycleTheme()
            }
            is BongoKeyboardView.KeyAction.ToggleVoice -> {
                handleVoiceInputAction()
            }
            is BongoKeyboardView.KeyAction.Shift,
            is BongoKeyboardView.KeyAction.ToggleSymbols -> {
                // UI state handled internally in BongoKeyboardView
            }
        }
    }

    private fun handleCandidateSelection(index: Int, candidate: String) {
        val ic = currentInputConnection ?: return
        if (bongoEngine.hasSession()) {
            val typedBuffer = bongoEngine.buffer
            val committed = bongoEngine.commitCandidate(index)
            if (typedBuffer.isNotEmpty()) {
                bongoEngine.learnSelection(typedBuffer, committed)
                userPrefs.learnSelection(typedBuffer, committed)
            }
            val finalText = if (userPrefs.bengaliDigits) committed.tobengaliDigits() else committed
            ic.commitText("$finalText ", 1)
            showNextWordPredictions(finalText)
        } else {
            // Next-word prediction tapped
            val finalCandidate = if (userPrefs.bengaliDigits) candidate.tobengaliDigits() else candidate
            ic.commitText("$finalCandidate ", 1)
            showNextWordPredictions(finalCandidate)
        }
    }

    /** Converts ASCII digits 0-9 in a string to Bengali digits ০-৯. */
    private fun String.tobengaliDigits(): String {
        val bengali = "০১২৩৪৫৬৭৮৯"
        return map { c -> if (c in '0'..'9') bengali[c - '0'] else c }.joinToString("")
    }

    private fun showNextWordPredictions(word: String) {
        if (!isBanglaMode) {
            candidateStripView?.clear()
            return
        }
        val predictions = bongoEngine.predictNextWords(word).take(userPrefs.candidateCount)
        if (predictions.isNotEmpty()) {
            candidateStripView?.setCandidates(predictions)
        } else {
            candidateStripView?.clear()
        }
    }

    private fun commitOngoingComposition() {
        val ic = currentInputConnection ?: return
        if (bongoEngine.hasSession()) {
            val committed = bongoEngine.commitCandidate(0)
            val finalText = if (userPrefs.bengaliDigits) committed.tobengaliDigits() else committed
            ic.commitText(finalText, 1)
            candidateStripView?.clear()
        }
    }

    private fun resetComposition() {
        bongoEngine.resetSession()
        isCtrlActive = false
        candidateStripView?.clear()
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (event == null) return super.onKeyDown(keyCode, event)

        // Shortcut to switch mode: Control + Space
        if (keyCode == KeyEvent.KEYCODE_SPACE && (event.isCtrlPressed || event.isMetaPressed)) {
            commitOngoingComposition()
            isBanglaMode = !isBanglaMode
            keyboardView?.setBanglaMode(isBanglaMode)
            return true
        }

        // Hardware keyboard support for active phonetic typing
        if (isBanglaMode) {
            when (keyCode) {
                KeyEvent.KEYCODE_DEL -> {
                    if (bongoEngine.hasSession()) {
                        handleKeyAction(BongoKeyboardView.KeyAction.Backspace)
                        return true
                    }
                }
                KeyEvent.KEYCODE_SPACE -> {
                    if (bongoEngine.hasSession()) {
                        handleKeyAction(BongoKeyboardView.KeyAction.Space)
                        return true
                    }
                }
                KeyEvent.KEYCODE_ENTER -> {
                    if (bongoEngine.hasSession()) {
                        handleKeyAction(BongoKeyboardView.KeyAction.Return)
                        return true
                    }
                }
                else -> {
                    val unicode = event.keyCharacterMap.get(keyCode, event.metaState)
                    if (unicode > 0 && unicode.toChar().isLetterOrDigit()) {
                        handleKeyAction(BongoKeyboardView.KeyAction.CharacterKey(unicode.toChar()))
                        return true
                    }
                }
            }
        }

        return super.onKeyDown(keyCode, event)
    }

    override fun onDestroy() {
        try {
            clipboardManager?.removePrimaryClipChangedListener(clipListener)
        } catch (_: Exception) {}
        stopVoiceListening()
        speechRecognizer?.destroy()
        speechRecognizer = null
        userPrefs.unregisterListener(prefChangeListener)
        bongoEngine.destroy()
        super.onDestroy()
    }

    private fun handlePreferenceChange(key: String?) {
        if (key == UserPreferences.KEY_KEYBOARD_LAYOUT) {
            bongoEngine.setLayout(userPrefs.keyboardLayout)
            bongoEngine.resetSession()          // flush any in-progress composition
            keyboardView?.buildKeyboard()       // redraw keys for new layout
        }
        if (key == UserPreferences.KEY_ONE_HANDED_MODE) {
            applyOneHandedMode()
        }
        if (key == UserPreferences.KEY_KEY_BORDERS) {
            keyboardView?.buildKeyboard()
        }

        val palette = ThemePalette.getPalette(userPrefs.theme)
        rootView?.setBackgroundColor(palette.surfaceColor)
        dividerView?.setBackgroundColor(palette.dividerColor)
        leftOneHandedBar?.setBackgroundColor(palette.surfaceColor)
        rightOneHandedBar?.setBackgroundColor(palette.surfaceColor)
        candidateStripView?.applyTheme(palette)
        keyboardView?.applyTheme(palette)
        emojiKeyboardView?.applyTheme(palette)

        updateKeyboardContainerHeight()
        rootView?.requestLayout()
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()
}
