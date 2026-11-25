package app.getbongo.ime.util

import org.junit.Assert.assertEquals
import org.junit.Test

class BengaliNumberToWordsTest {

    @Test
    fun convertsZeroAndTwoDigitNumbers() {
        assertEquals("শূন্য", BengaliNumberToWords.convert("0"))
        assertEquals("শূন্য টাকা মাত্র", BengaliNumberToWords.convert("0", asCurrency = true))
        assertEquals("পঁচাত্তর", BengaliNumberToWords.convert("75"))
    }

    @Test
    fun convertsSouthAsianUnitsAndBengaliDigits() {
        assertEquals("এক লক্ষ পঁচিশ হাজার", BengaliNumberToWords.convert("125000"))
        assertEquals("এক কোটি", BengaliNumberToWords.convert("১০০০০০০০"))
        assertEquals("এক হাজার দুই শত ত্রিশ টাকা মাত্র", BengaliNumberToWords.convert("১২৩০", asCurrency = true))
    }
}
