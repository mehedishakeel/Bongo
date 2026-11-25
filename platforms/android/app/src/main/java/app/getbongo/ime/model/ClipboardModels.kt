package app.getbongo.ime.model

import org.json.JSONArray
import org.json.JSONObject

/**
 * Structured clipboard item supporting pinning, privacy tagging, and automatic expiration.
 */
data class ClipboardEntry(
    val id: String,
    val text: String,
    val timestampMs: Long,
    val isPinned: Boolean = false,
    val isSensitive: Boolean = false
)

/**
 * Pure, testable clipboard history operations (JSON serialization, pinning,
 * deduplication, search, and sensitive-item expiration).
 */
object ClipboardStoreLogic {
    const val MAX_ITEMS = 30
    const val SENSITIVE_TTL_MS = 60L * 60L * 1000L // 1 hour

    fun parseJson(raw: String, nowMs: Long = System.currentTimeMillis()): MutableList<ClipboardEntry> {
        val result = mutableListOf<ClipboardEntry>()
        if (raw.isBlank()) return result
        try {
            val arr = JSONArray(raw)
            for (i in 0 until arr.length()) {
                val item = arr.opt(i)
                when (item) {
                    is JSONObject -> {
                        val text = item.optString("text", "")
                        if (text.isNotEmpty()) {
                            result.add(
                                ClipboardEntry(
                                    id = item.optString("id", "${i}_${text.hashCode()}"),
                                    text = text,
                                    timestampMs = item.optLong("ts", nowMs),
                                    isPinned = item.optBoolean("pinned", false),
                                    isSensitive = item.optBoolean("sensitive", false)
                                )
                            )
                        }
                    }
                    is String -> {
                        // Migrate legacy plain-string clipboard items seamlessly
                        if (item.isNotEmpty()) {
                            result.add(
                                ClipboardEntry(
                                    id = "legacy_${i}_${item.hashCode()}",
                                    text = item,
                                    timestampMs = nowMs,
                                    isPinned = false,
                                    isSensitive = false
                                )
                            )
                        }
                    }
                }
            }
        } catch (_: Exception) {}
        return sortAndPrune(result, nowMs)
    }

    fun toJson(entries: List<ClipboardEntry>): String {
        val arr = JSONArray()
        for (entry in entries.take(MAX_ITEMS)) {
            val obj = JSONObject()
            obj.put("id", entry.id)
            obj.put("text", entry.text)
            obj.put("ts", entry.timestampMs)
            obj.put("pinned", entry.isPinned)
            obj.put("sensitive", entry.isSensitive)
            arr.put(obj)
        }
        return arr.toString()
    }

    fun addText(
        entries: List<ClipboardEntry>,
        text: String,
        nowMs: Long = System.currentTimeMillis(),
        isSensitive: Boolean = false
    ): MutableList<ClipboardEntry> {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return sortAndPrune(entries, nowMs)

        val existing = entries.firstOrNull { it.text == trimmed }
        val wasPinned = existing?.isPinned ?: false
        val id = existing?.id ?: "${nowMs}_${trimmed.hashCode()}"

        val next = entries.filterNot { it.text == trimmed }.toMutableList()
        next.add(
            0,
            ClipboardEntry(
                id = id,
                text = trimmed,
                timestampMs = nowMs,
                isPinned = wasPinned,
                isSensitive = isSensitive
            )
        )
        return sortAndPrune(next, nowMs)
    }

    fun togglePin(entries: List<ClipboardEntry>, id: String, nowMs: Long = System.currentTimeMillis()): MutableList<ClipboardEntry> {
        val updated = entries.map { entry ->
            if (entry.id == id) entry.copy(isPinned = !entry.isPinned) else entry
        }
        return sortAndPrune(updated, nowMs)
    }

    fun deleteById(entries: List<ClipboardEntry>, id: String): MutableList<ClipboardEntry> =
        entries.filterNot { it.id == id }.toMutableList()

    fun clearUnpinned(entries: List<ClipboardEntry>): MutableList<ClipboardEntry> =
        entries.filter { it.isPinned }.toMutableList()

    fun search(entries: List<ClipboardEntry>, query: String): List<ClipboardEntry> {
        val q = query.trim().lowercase()
        if (q.isEmpty()) return entries
        return entries.filter { it.text.lowercase().contains(q) }
    }

    fun sortAndPrune(entries: List<ClipboardEntry>, nowMs: Long = System.currentTimeMillis()): MutableList<ClipboardEntry> {
        val valid = entries.filter { entry ->
            entry.isPinned || !entry.isSensitive || (nowMs - entry.timestampMs) < SENSITIVE_TTL_MS
        }
        val pinned = valid.filter { it.isPinned }.sortedByDescending { it.timestampMs }
        val unpinned = valid.filterNot { it.isPinned }.sortedByDescending { it.timestampMs }
        return (pinned + unpinned).take(MAX_ITEMS).toMutableList()
    }
}
