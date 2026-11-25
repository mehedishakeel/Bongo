package app.getbongo.ime.util

import java.math.BigDecimal
import java.math.RoundingMode
import kotlin.math.pow

/**
 * Safe, zero-dependency recursive-descent arithmetic evaluator for inline IME math.
 * Supports ASCII (0-9) and Bengali (০-৯) numerals, decimals, parentheses,
 * and operators (+, -, *, ×, /, ÷, %, ^).
 */
object MathEvaluator {

    private const val BENGALI_DIGITS = "০১২৩৪৫৬৭৮৯"

    /**
     * Evaluates an expression ending with '=' (or raw expression) and returns formatted result,
     * or null if the input is not a valid multi-token arithmetic expression.
     */
    fun evaluateInline(rawInput: String, useBengaliDigits: Boolean = false): String? {
        val trimmed = rawInput.trim().removeSuffix("=").trim()
        if (trimmed.isEmpty()) return null

        val normalized = normalizeExpression(trimmed) ?: return null
        // Require at least one operator so plain numbers like "123=" don't trigger math evaluation
        if (!normalized.any { it in "+-*/%^" }) return null
        // Must have at least one digit
        if (!normalized.any { it in '0'..'9' }) return null

        val value = try {
            Parser(normalized).parse()
        } catch (_: Exception) {
            return null
        } ?: return null

        if (value.isNaN() || value.isInfinite()) return null

        val formatted = formatNumber(value)
        return if (useBengaliDigits) toBengaliDigits(formatted) else formatted
    }

    private fun normalizeExpression(input: String): String? {
        val sb = StringBuilder(input.length)
        for (ch in input) {
            when {
                ch.isWhitespace() -> continue
                ch in '0'..'9' || ch in "+-*/%^()." -> sb.append(ch)
                ch == '×' -> sb.append('*')
                ch == '÷' -> sb.append('/')
                ch in '০'..'৯' -> sb.append((ch - '০').digitToChar())
                else -> return null
            }
        }
        return sb.toString()
    }

    private fun formatNumber(value: Double): String {
        val bd = BigDecimal.valueOf(value).setScale(6, RoundingMode.HALF_UP).stripTrailingZeros()
        return bd.toPlainString()
    }

    fun toBengaliDigits(text: String): String {
        val sb = StringBuilder(text.length)
        for (c in text) {
            if (c in '0'..'9') {
                sb.append(BENGALI_DIGITS[c - '0'])
            } else {
                sb.append(c)
            }
        }
        return sb.toString()
    }

    private class Parser(private val s: String) {
        private var pos = 0

        fun parse(): Double? {
            val result = parseExpression() ?: return null
            return if (pos == s.length) result else null
        }

        private fun parseExpression(): Double? {
            var left = parseTerm() ?: return null
            while (pos < s.length) {
                when (s[pos]) {
                    '+' -> {
                        pos++
                        val right = parseTerm() ?: return null
                        left += right
                    }
                    '-' -> {
                        pos++
                        val right = parseTerm() ?: return null
                        left -= right
                    }
                    else -> break
                }
            }
            return left
        }

        private fun parseTerm(): Double? {
            var left = parsePower() ?: return null
            while (pos < s.length) {
                when (s[pos]) {
                    '*' -> {
                        pos++
                        val right = parsePower() ?: return null
                        left *= right
                    }
                    '/' -> {
                        pos++
                        val right = parsePower() ?: return null
                        if (right == 0.0) return null
                        left /= right
                    }
                    '%' -> {
                        pos++
                        val right = parsePower() ?: return null
                        if (right == 0.0) return null
                        left %= right
                    }
                    else -> break
                }
            }
            return left
        }

        private fun parsePower(): Double? {
            val base = parseUnary() ?: return null
            if (pos < s.length && s[pos] == '^') {
                pos++
                val exp = parsePower() ?: return null
                return base.pow(exp)
            }
            return base
        }

        private fun parseUnary(): Double? {
            if (pos < s.length) {
                if (s[pos] == '+') {
                    pos++
                    return parseUnary()
                }
                if (s[pos] == '-') {
                    pos++
                    val v = parseUnary() ?: return null
                    return -v
                }
            }
            return parsePrimary()
        }

        private fun parsePrimary(): Double? {
            if (pos >= s.length) return null
            if (s[pos] == '(') {
                pos++
                val inner = parseExpression() ?: return null
                if (pos >= s.length || s[pos] != ')') return null
                pos++
                return inner
            }
            val start = pos
            var hasDot = false
            var hasDigit = false
            while (pos < s.length) {
                val c = s[pos]
                if (c in '0'..'9') {
                    hasDigit = true
                    pos++
                } else if (c == '.' && !hasDot) {
                    hasDot = true
                    pos++
                } else {
                    break
                }
            }
            if (!hasDigit) return null
            return s.substring(start, pos).toDoubleOrNull()
        }
    }
}
