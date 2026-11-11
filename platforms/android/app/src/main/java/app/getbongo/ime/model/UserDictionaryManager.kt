package app.getbongo.ime.model

import android.content.Context
import org.json.JSONObject
import java.io.File

/**
 * Manages custom user text shortcuts and expansion dictionary for Bongo IME.
 * Stored in `autocorrect.json` in the app's files directory for seamless cross-platform parity.
 */
class UserDictionaryManager(private val context: Context) {

    private val file: File
        get() = File(context.filesDir, "autocorrect.json")

    fun getShortcuts(): Map<String, String> {
        val map = mutableMapOf<String, String>()
        try {
            if (file.exists()) {
                val content = file.readText(Charsets.UTF_8)
                val json = JSONObject(content)
                val keys = json.keys()
                while (keys.hasNext()) {
                    val k = keys.next()
                    val v = json.optString(k, "")
                    if (k.isNotEmpty() && v.isNotEmpty()) {
                        map[k.lowercase()] = v
                    }
                }
            }
        } catch (_: Exception) {}
        return map
    }

    fun saveShortcuts(shortcuts: Map<String, String>) {
        try {
            val json = JSONObject()
            for ((k, v) in shortcuts) {
                json.put(k.lowercase().trim(), v.trim())
            }
            file.writeText(json.toString(2), Charsets.UTF_8)
        } catch (_: Exception) {}
    }

    fun addShortcut(shortcut: String, expansion: String): Boolean {
        val k = shortcut.lowercase().trim()
        val v = expansion.trim()
        if (k.isEmpty() || v.isEmpty()) return false

        val current = getShortcuts().toMutableMap()
        current[k] = v
        saveShortcuts(current)
        return true
    }

    fun deleteShortcut(shortcut: String): Boolean {
        val k = shortcut.lowercase().trim()
        val current = getShortcuts().toMutableMap()
        if (current.remove(k) != null) {
            saveShortcuts(current)
            return true
        }
        return false
    }

    fun loadPresets(): Map<String, String> {
        val presets = mapOf(
            "fb" to "ফেসবুক",
            "gm" to "শুভ সকাল",
            "gn" to "শুভ রাত্রি",
            "yt" to "ইউটিউব",
            "thx" to "ধন্যবাদ",
            "bd" to "বাংলাদেশ",
            "dhaka" to "ঢাকা"
        )
        val current = getShortcuts().toMutableMap()
        for ((k, v) in presets) {
            current[k] = v
        }
        saveShortcuts(current)
        return current
    }

    fun exportToJson(): String {
        val current = getShortcuts()
        val json = JSONObject()
        for ((k, v) in current) {
            json.put(k, v)
        }
        return json.toString(2)
    }

    fun importFromJson(jsonString: String): Int {
        try {
            val json = JSONObject(jsonString)
            val current = getShortcuts().toMutableMap()
            val keys = json.keys()
            var count = 0
            while (keys.hasNext()) {
                val k = keys.next().lowercase().trim()
                val v = json.optString(k, "").trim()
                if (k.isNotEmpty() && v.isNotEmpty()) {
                    current[k] = v
                    count++
                }
            }
            if (count > 0) {
                saveShortcuts(current)
            }
            return count
        } catch (_: Exception) {
            return 0
        }
    }
}
