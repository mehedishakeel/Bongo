package app.getbongo.ime.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FixedLayoutEngineTest {

    @Test
    fun nationalLayoutTypesBasicConsonantsPreBaseKarsAndConjuncts() {
        val engine = FixedLayoutEngine()
        engine.setLayout(FixedLayoutEngine.LAYOUT_NATIONAL)

        // j -> ক, J -> খ
        assertEquals("ক", engine.feedChar('j'))
        assertEquals("কখ", engine.feedChar('J'))
        assertEquals("কখ", engine.commitText())

        // Pre-base kar reordering: d (ি) + j (ক) -> কি
        assertEquals("ি", engine.feedChar('d'))
        assertEquals("কি", engine.feedChar('j'))
        assertEquals("কি", engine.commitText())

        // Conjunct with pre-base kar: d (ি) + j (ক) + g (্) + k (ত) -> ক্তি
        engine.feedChar('d')
        engine.feedChar('j')
        engine.feedChar('g')
        assertEquals("ক্তি", engine.feedChar('k'))
        assertEquals("ক্তি", engine.commitText())

        // Hasanta + Aa-kar -> আ
        engine.feedChar('g')
        assertEquals("আ", engine.feedChar('f'))
        assertEquals("আ", engine.commitText())

        // Ro-fola after pre-base kar: d (ি) + j (ক) + z (্র) -> ক্রি
        engine.feedChar('d')
        engine.feedChar('j')
        assertEquals("ক্রি", engine.feedChar('z'))
        assertEquals("ক্রি", engine.commitText())

        // Backslash maps to ৎ in National
        assertEquals("ৎ", engine.feedChar('\\'))
        assertEquals("ৎ", engine.commitText())
    }

    @Test
    fun bornoLayoutTypesExpectedCharactersAndPreBaseKars() {
        val engine = FixedLayoutEngine()
        engine.setLayout(FixedLayoutEngine.LAYOUT_BORNO)

        assertEquals("ক", engine.feedChar('k'))
        assertEquals("কা", engine.feedChar('a'))
        assertEquals("কা", engine.commitText())

        assertEquals("খ", engine.feedChar('K'))
        assertEquals("খঅ", engine.feedChar('A'))
        assertEquals("খঅ", engine.commitText())

        // Pre-base kar i (ি) + k (ক) -> কি, then P (্র) -> ক্রি
        assertEquals("ি", engine.feedChar('i'))
        assertEquals("কি", engine.feedChar('k'))
        assertEquals("ক্রি", engine.feedChar('P'))
        assertEquals("ক্রি", engine.commitText())

        // Backslash maps to ৱ in Borno
        assertEquals("ৱ", engine.feedChar('\\'))
        assertEquals("ৱ", engine.commitText())
    }

    @Test
    fun backspaceAndDisplayLabelsWorkCleanly() {
        val engine = FixedLayoutEngine()
        engine.setLayout(FixedLayoutEngine.LAYOUT_NATIONAL)

        // Pending kar cancelled cleanly on backspace
        engine.feedChar('d')
        assertTrue(engine.hasSession())
        assertFalse(engine.handleBackspace())
        assertEquals("", engine.preedit())

        assertEquals("ক", FixedLayoutEngine.getDisplayLabel('j', FixedLayoutEngine.LAYOUT_NATIONAL, shifted = false))
        assertEquals("খ", FixedLayoutEngine.getDisplayLabel('j', FixedLayoutEngine.LAYOUT_NATIONAL, shifted = true))
        assertEquals("ক", FixedLayoutEngine.getDisplayLabel('k', FixedLayoutEngine.LAYOUT_BORNO, shifted = false))
        assertEquals("খ", FixedLayoutEngine.getDisplayLabel('k', FixedLayoutEngine.LAYOUT_BORNO, shifted = true))
    }
}
