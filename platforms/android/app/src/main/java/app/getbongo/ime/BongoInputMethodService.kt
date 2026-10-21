package app.getbongo.ime

import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
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
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.Toast
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
    private var keyboardView: BongoKeyboardView? = null
    private var emojiKeyboardView: EmojiKeyboardView? = null
    private var candidateStripView: CandidateStripView? = null
    private var keyboardFrame: FrameLayout? = null
    private var dividerView: View? = null
    private var rootView: LinearLayout? = null

    private var isBanglaMode = true
    private var isCtrlActive = false
    private var lastSpaceTime = 0L

    private val prefChangeListener = SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        handlePreferenceChange(key)
    }

    override fun onCreate() {
        super.onCreate()
        bongoEngine = BongoEngine()
        userPrefs = UserPreferences(this)
        bongoEngine.setLayout(userPrefs.keyboardLayout)
        userPrefs.registerListener(prefChangeListener)
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
            onCandidateSelected = { index, _ ->
                handleCandidateSelection(index)
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

        val frame = FrameLayout(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(getTargetKeyboardHeight())
            )
        }
        keyboardFrame = frame

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
        }

        frame.addView(keyboardView)
        frame.addView(emojiKeyboardView)

        root.addView(candidateStripView)
        root.addView(divider)
        root.addView(frame)

        return root
    }

    private fun showKeyboard() {
        emojiKeyboardView?.visibility = View.GONE
        keyboardView?.visibility = View.VISIBLE
        candidateStripView?.visibility = View.VISIBLE
    }

    private fun showEmojiKeyboard() {
        commitOngoingComposition()
        keyboardView?.visibility = View.GONE
        candidateStripView?.visibility = View.GONE
        emojiKeyboardView?.visibility = View.VISIBLE
    }

    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        showKeyboard()
        resetComposition()

        // Sync theme and height changes from settings
        val palette = ThemePalette.getPalette(userPrefs.theme)
        rootView?.setBackgroundColor(palette.surfaceColor)
        dividerView?.setBackgroundColor(palette.dividerColor)
        candidateStripView?.applyTheme(palette)
        keyboardView?.applyTheme(palette)

        keyboardFrame?.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(getTargetKeyboardHeight())
        )

        val actionLabel = when (info?.imeOptions?.and(EditorInfo.IME_MASK_ACTION)) {
            EditorInfo.IME_ACTION_GO -> "Go"
            EditorInfo.IME_ACTION_SEARCH -> "Search"
            EditorInfo.IME_ACTION_SEND -> "Send"
            EditorInfo.IME_ACTION_NEXT -> "Next"
            EditorInfo.IME_ACTION_DONE -> "Done"
            else -> if (info?.inputType != null && (info.inputType and EditorInfo.TYPE_TEXT_FLAG_MULTI_LINE) != 0) "⏎" else "Go"
        }
        val isUri = (info?.inputType != null && (info.inputType and EditorInfo.TYPE_MASK_VARIATION) == EditorInfo.TYPE_TEXT_VARIATION_URI)
        keyboardView?.setActionInfo(actionLabel, isUri)
    }

    private fun getTargetKeyboardHeight(): Int {
        val base = userPrefs.keyboardHeightDp
        return if (userPrefs.showNumberRow) base + 36 else base
    }


    override fun onFinishInputView(finishingInput: Boolean) {
        super.onFinishInputView(finishingInput)
        commitOngoingComposition()
        resetComposition()
    }

    private var speechRecognizer: SpeechRecognizer? = null
    private var isVoiceListening = false

    private fun cycleTheme() {
        val themes = listOf("midnight", "light", "oled")
        val currentIdx = themes.indexOf(userPrefs.theme.lowercase())
        val nextIdx = if (currentIdx == -1) 0 else (currentIdx + 1) % themes.size
        val chosenTheme = themes[nextIdx]
        userPrefs.theme = chosenTheme
        val palette = ThemePalette.getPalette(chosenTheme)
        rootView?.setBackgroundColor(palette.surfaceColor)
        dividerView?.setBackgroundColor(palette.dividerColor)
        keyboardView?.applyTheme(palette)
        candidateStripView?.applyTheme(palette)
        emojiKeyboardView?.applyTheme(palette)
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
        }
    }

    private fun handleClipboardAction() {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
        val clip = clipboard?.primaryClip
        if (clip != null && clip.itemCount > 0) {
            val text = clip.getItemAt(0)?.coerceToText(this)?.toString()
            if (!text.isNullOrEmpty()) {
                candidateStripView?.showClipboardPreview(text) { toPaste ->
                    currentInputConnection?.commitText(toPaste, 1)
                }
                return
            }
        }
        currentInputConnection?.performContextMenuAction(android.R.id.paste)
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

                if (ch == ',' || ch == '।' || (!isBanglaMode && ch == '.')) {
                    commitOngoingComposition()
                    ic.commitText(ch.toString(), 1)
                    return
                }

                if (isBanglaMode && (ch in 'a'..'z' || ch in 'A'..'Z' || ch in "0123456789`~@#\$%^&*()-_=+[{]}\\|;:'\",<.>/?")) {
                    bongoEngine.feedChar(ch, keyboardView?.isShifted == true)
                    val composing = bongoEngine.preedit
                    ic.setComposingText(composing, 1)
                    candidateStripView?.setCandidates(bongoEngine.candidates)
                } else {
                    commitOngoingComposition()
                    ic.commitText(ch.toString(), 1)
                }
            }
            is BongoKeyboardView.KeyAction.Backspace -> {
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val hasRemaining = bongoEngine.handleBackspace()
                    if (hasRemaining && bongoEngine.preedit.isNotEmpty()) {
                        ic.setComposingText(bongoEngine.preedit, 1)
                        candidateStripView?.setCandidates(bongoEngine.candidates)
                    } else {
                        ic.setComposingText("", 0)
                        candidateStripView?.clear()
                    }
                } else {
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
                }
            }
            is BongoKeyboardView.KeyAction.Space -> {
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val committed = bongoEngine.commitCandidate(0)
                    ic.commitText("$committed ", 1)
                    candidateStripView?.clear()
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
                }
            }
            is BongoKeyboardView.KeyAction.Return -> {
                if (isBanglaMode && bongoEngine.hasSession()) {
                    val committed = bongoEngine.commitCandidate(0)
                    ic.commitText(committed, 1)
                    candidateStripView?.clear()
                }
                val editorInfo = currentInputEditorInfo
                val imeOptions = editorInfo?.imeOptions ?: 0
                val actionId = imeOptions and EditorInfo.IME_MASK_ACTION
                if (actionId != EditorInfo.IME_ACTION_NONE && actionId != EditorInfo.IME_ACTION_UNSPECIFIED) {
                    ic.performEditorAction(actionId)
                } else {
                    sendDownUpKeyEvents(KeyEvent.KEYCODE_ENTER)
                }
            }
            is BongoKeyboardView.KeyAction.ToggleLanguage -> {
                commitOngoingComposition()
                isBanglaMode = !isBanglaMode
                keyboardView?.setBanglaMode(isBanglaMode)
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

    private fun handleCandidateSelection(index: Int) {
        val ic = currentInputConnection ?: return
        val committed = bongoEngine.commitCandidate(index)
        ic.commitText("$committed ", 1)
        candidateStripView?.clear()
    }

    private fun commitOngoingComposition() {
        val ic = currentInputConnection ?: return
        if (bongoEngine.hasSession()) {
            val committed = bongoEngine.commitCandidate(0)
            ic.commitText(committed, 1)
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
        }

        val palette = ThemePalette.getPalette(userPrefs.theme)
        rootView?.setBackgroundColor(palette.surfaceColor)
        dividerView?.setBackgroundColor(palette.dividerColor)
        candidateStripView?.applyTheme(palette)
        keyboardView?.applyTheme(palette)

        keyboardFrame?.layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(getTargetKeyboardHeight())
        )
        keyboardFrame?.requestLayout()
        rootView?.requestLayout()
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()
}
