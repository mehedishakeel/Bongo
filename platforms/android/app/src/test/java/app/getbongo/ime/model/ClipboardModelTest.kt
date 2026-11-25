package app.getbongo.ime.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ClipboardModelTest {

    @Test
    fun addPinDeleteSearchAndJsonRoundTripWork() {
        val t0 = 1_000_000L
        var list = mutableListOf<ClipboardEntry>()
        list = ClipboardStoreLogic.addText(list, "আমার সোনার বাংলা", t0, isSensitive = false)
        list = ClipboardStoreLogic.addText(list, "Hello Bongo", t0 + 1000L, isSensitive = false)

        assertEquals(2, list.size)
        assertEquals("Hello Bongo", list[0].text)

        val secondId = list[1].id
        list = ClipboardStoreLogic.togglePin(list, secondId, t0 + 2000L)
        assertTrue(list.first { it.id == secondId }.isPinned)

        // Pinned items survive clearUnpinned
        val afterClear = ClipboardStoreLogic.clearUnpinned(list)
        assertEquals(1, afterClear.size)
        assertEquals("আমার সোনার বাংলা", afterClear[0].text)

        // Search filters case-insensitively
        assertEquals(1, ClipboardStoreLogic.search(list, "bongo").size)

        // JSON persistence round trip
        val json = ClipboardStoreLogic.toJson(list)
        val restored = ClipboardStoreLogic.parseJson(json, t0 + 3000L)
        assertEquals(2, restored.size)

        val afterDelete = ClipboardStoreLogic.deleteById(restored, secondId)
        assertFalse(afterDelete.any { it.id == secondId })
    }

    @Test
    fun sensitiveClipboardEntriesExpireAfterOneHour() {
        val t0 = 1_000_000L
        var list = mutableListOf<ClipboardEntry>()
        list = ClipboardStoreLogic.addText(list, "OTP 948201", t0, isSensitive = true)
        list = ClipboardStoreLogic.addText(list, "Persistent note", t0, isSensitive = false)

        val serialized = ClipboardStoreLogic.toJson(list)
        // Before 1h TTL: both remain
        val beforeExpiry = ClipboardStoreLogic.parseJson(serialized, t0 + 30 * 60 * 1000L)
        assertEquals(2, beforeExpiry.size)

        // After 1h TTL: sensitive entry expires, regular note remains
        val afterExpiry = ClipboardStoreLogic.parseJson(serialized, t0 + 61 * 60 * 1000L)
        assertEquals(1, afterExpiry.size)
        assertEquals("Persistent note", afterExpiry[0].text)
    }
}
