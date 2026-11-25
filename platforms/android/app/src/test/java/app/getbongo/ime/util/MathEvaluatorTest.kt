package app.getbongo.ime.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MathEvaluatorTest {

    @Test
    fun evaluatesBasicArithmeticAndPrecedence() {
        assertEquals("100", MathEvaluator.evaluateInline("25*4="))
        assertEquals("14", MathEvaluator.evaluateInline("2+3*4="))
        assertEquals("20", MathEvaluator.evaluateInline("(2+3)*4="))
        assertEquals("2.5", MathEvaluator.evaluateInline("5/2="))
    }

    @Test
    fun evaluatesBengaliDigitsAndUnicodeOperators() {
        assertEquals("১৫", MathEvaluator.evaluateInline("১২+৩=", useBengaliDigits = true))
        assertEquals("15", MathEvaluator.evaluateInline("12+3=", useBengaliDigits = false))
        assertEquals("12", MathEvaluator.evaluateInline("৩×৪=", useBengaliDigits = false))
        assertEquals("4", MathEvaluator.evaluateInline("8÷2=", useBengaliDigits = false))
    }

    @Test
    fun ignoresPlainProseAndDivisionByZero() {
        assertNull(MathEvaluator.evaluateInline("hello="))
        assertNull(MathEvaluator.evaluateInline("x ="))
        assertNull(MathEvaluator.evaluateInline("10/0="))
        assertNull(MathEvaluator.evaluateInline("42"))
    }
}
