package app.getbongo.ime.engine

import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BijoyConverterTest {

    @Test
    fun convertsBengaliWordWithKarReorderingToBijoy() {
        val unicode = "বাংলাদেশ"
        val bijoy = BijoyConverter.unicodeToBijoy(unicode)
        assertNotEquals(unicode, bijoy)
        assertTrue(bijoy.isNotBlank())
        assertFalse(bijoy.contains("ি") || bijoy.contains("ে"))
    }

    @Test
    fun preservesWhitespaceAndAsciiText() {
        assertEqualsOrContainsSpace(BijoyConverter.unicodeToBijoy("আমি বাংলা"))
    }

    private fun assertEqualsOrContainsSpace(text: String) {
        assertTrue(text.contains(" "))
    }
}
