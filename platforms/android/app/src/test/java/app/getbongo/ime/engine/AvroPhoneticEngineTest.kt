package app.getbongo.ime.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AvroPhoneticEngineTest {

    private val engine = AvroPhoneticEngine()

    @Test
    fun convertsCorePhoneticWordsAndLoanwords() {
        assertEquals("আমি", engine.convertWord("ami"))
        assertEquals("বাংলা", engine.convertWord("bangla"))
        assertTrue(engine.getCandidates("bangladesh").contains("বাংলাদেশ"))
        assertTrue(engine.getCandidates("school").contains("স্কুল"))
    }

    @Test
    fun handlesPaddingAndBigramPredictions() {
        val (prefix, core, suffix) = engine.separatePadding("...ami!")
        assertEquals("...", prefix)
        assertEquals("ami", core)
        assertEquals("!", suffix)

        val nexts = engine.predictNextWords("আমি")
        assertTrue(nexts.isNotEmpty())
        assertTrue(nexts.contains("তোমাকে") || nexts.contains("ভালো"))
    }
}
