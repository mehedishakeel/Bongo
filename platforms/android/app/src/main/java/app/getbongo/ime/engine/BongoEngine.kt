package app.getbongo.ime.engine

import android.util.Log

/**
 * Unified Bongo Transliteration Engine for Android.
 * Connects directly to the Rust core (BongoNative) via JNI when available,
 * and falls back seamlessly to the pure-Kotlin AvroPhoneticEngine.
 */
class BongoEngine {
    private val TAG = "BongoEngine"

    private var nativePtr: Long = 0
    private val fallbackEngine = AvroPhoneticEngine()

    var buffer = ""
        private set
    var candidates = listOf<String>()
        private set
    var preedit = ""
        private set

    init {
        if (BongoNative.isLoaded) {
            try {
                nativePtr = BongoNative.engineNew()
                Log.i(TAG, "Native BongoEngine instantiated at 0x${nativePtr.toString(16)}")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to instantiate native engine: ${e.message}")
                nativePtr = 0
            }
        }
    }

    fun setLayout(layout: Int) {
        if (nativePtr != 0L) {
            try {
                BongoNative.setLayout(nativePtr, layout)
            } catch (e: Exception) {
                Log.w(TAG, "Error in native setLayout: ${e.message}")
            }
        }
    }

    fun hasSession(): Boolean {
        if (nativePtr != 0L) {
            return BongoNative.engineHasSession(nativePtr)
        }
        return buffer.isNotEmpty()
    }

    fun feedChar(ch: Char, isShift: Boolean): Boolean {
        buffer += ch
        if (nativePtr != 0L) {
            try {
                val cp = ch.code
                val modifier = if (isShift || ch.isUpperCase()) 1.toByte() else 0.toByte()
                val suggPtr = BongoNative.engineFeedChar(nativePtr, cp, modifier, 0)
                if (suggPtr != 0L) {
                    updateNativeSuggestions(suggPtr)
                    BongoNative.suggestionFree(suggPtr)
                    return true
                }
            } catch (e: Exception) {
                Log.w(TAG, "Error in native feedChar: ${e.message}")
            }
        }

        // Built-in Kotlin fallback
        candidates = fallbackEngine.getCandidates(buffer)
        preedit = candidates.firstOrNull() ?: buffer
        return true
    }

    private fun updateNativeSuggestions(suggPtr: Long) {
        val count = BongoNative.suggestionCount(suggPtr).toInt()
        val cands = mutableListOf<String>()
        for (i in 0 until count) {
            val cand = BongoNative.suggestionGetCandidate(suggPtr, i.toLong())
            if (!cand.isNullOrEmpty()) {
                cands.add(cand)
            }
        }
        candidates = cands
        preedit = BongoNative.suggestionGetPreview(suggPtr) ?: candidates.firstOrNull() ?: ""
    }

    fun handleBackspace(): Boolean {
        if (nativePtr != 0L) {
            try {
                val suggPtr = BongoNative.engineBackspace(nativePtr, false)
                if (suggPtr != 0L) {
                    updateNativeSuggestions(suggPtr)
                    BongoNative.suggestionFree(suggPtr)
                    if (buffer.isNotEmpty()) buffer = buffer.dropLast(1)
                    return true
                } else {
                    resetSession()
                    return false
                }
            } catch (e: Exception) {
                Log.w(TAG, "Error in native backspace: ${e.message}")
            }
        }

        if (buffer.isNotEmpty()) {
            buffer = buffer.dropLast(1)
            if (buffer.isEmpty()) {
                resetSession()
                return false
            } else {
                candidates = fallbackEngine.getCandidates(buffer)
                preedit = candidates.firstOrNull() ?: buffer
                return true
            }
        }
        return false
    }

    fun commitCandidate(index: Int = 0): String {
        val committedText = if (index in candidates.indices) {
            candidates[index]
        } else {
            preedit.ifEmpty { buffer }
        }

        if (nativePtr != 0L) {
            try {
                BongoNative.engineCommit(nativePtr, index.toLong())
            } catch (e: Exception) {
                Log.w(TAG, "Error in native commit: ${e.message}")
            }
        }

        buffer = ""
        candidates = emptyList()
        preedit = ""
        return committedText
    }

    fun resetSession() {
        if (nativePtr != 0L) {
            try {
                BongoNative.engineReset(nativePtr)
            } catch (e: Exception) {
                Log.w(TAG, "Error in native reset: ${e.message}")
            }
        }
        buffer = ""
        candidates = emptyList()
        preedit = ""
    }

    fun destroy() {
        if (nativePtr != 0L) {
            try {
                BongoNative.engineFree(nativePtr)
                nativePtr = 0
            } catch (e: Exception) {
                Log.w(TAG, "Error freeing native engine: ${e.message}")
            }
        }
    }
}
