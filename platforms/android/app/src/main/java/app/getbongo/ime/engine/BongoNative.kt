package app.getbongo.ime.engine

import android.util.Log

/**
 * JNI bindings for the high-performance Rust core (libbongo_engine.so).
 */
object BongoNative {
    private const val TAG = "BongoNative"
    var isLoaded = false
        private set

    init {
        try {
            System.loadLibrary("bongo_engine")
            isLoaded = true
            Log.i(TAG, "Native bongo_engine library loaded successfully.")
        } catch (e: UnsatisfiedLinkError) {
            Log.w(TAG, "libbongo_engine.so not available, falling back to pure Kotlin engine: ${e.message}")
            isLoaded = false
        } catch (e: Exception) {
            Log.e(TAG, "Unexpected error loading bongo_engine: ${e.message}")
            isLoaded = false
        }
    }

    external fun engineNew(): Long
    external fun engineFree(ptr: Long)
    external fun engineSetMode(ptr: Long, mode: Int)
    external fun engineSetEmoji(ptr: Long, enabled: Boolean)
    external fun engineHasSession(ptr: Long): Boolean
    external fun setLayout(ptr: Long, layout: Int)
    external fun getLayout(ptr: Long): Int
    external fun engineFeedChar(ptr: Long, ch: Int, modifier: Byte, selection: Byte): Long
    external fun engineBackspace(ptr: Long, wholeWord: Boolean): Long
    external fun engineCommit(ptr: Long, index: Long)
    external fun engineReset(ptr: Long)

    external fun suggestionCount(suggPtr: Long): Long
    external fun suggestionGetCandidate(suggPtr: Long, index: Long): String?
    external fun suggestionGetPreview(suggPtr: Long): String?
    external fun suggestionFree(suggPtr: Long)
}
