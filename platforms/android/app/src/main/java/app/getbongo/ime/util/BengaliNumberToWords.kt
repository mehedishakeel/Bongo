package app.getbongo.ime.util

/**
 * High-performance Bengali Number-to-Words converter.
 * Converts numeric strings (in English 0-9 or Bengali ০-৯ digits) into full spoken Bengali words
 * using the traditional South Asian numbering system (কোটি, লক্ষ, হাজার, শত).
 */
object BengaliNumberToWords {

    private val DIGIT_MAP = mapOf(
        '০' to '0', '১' to '1', '২' to '2', '৩' to '3', '৪' to '4',
        '৫' to '5', '৬' to '6', '৭' to '7', '৮' to '8', '৯' to '9'
    )

    private val NUMBERS_0_TO_99 = arrayOf(
        "শূন্য", "এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়", "দশ",
        "এগারো", "বারো", "তেরো", "চৌদ্দ", "পনেরো", "ষোলো", "সতেরো", "আঠারো", "উনিশ", "বিশ",
        "একুশ", "বাইশ", "তেইশ", "চব্বিশ", "পঁচিশ", "ছাব্বিশ", "সাতাশ", "আঠাশ", "উনত্রিশ", "ত্রিশ",
        "একত্রিশ", "বত্রিশ", "তেত্রিশ", "চৌত্রিশ", "পঁয়ত্রিশ", "ছত্রিশ", "সাঁয়ত্রিশ", "আটত্রিশ", "উনচল্লিশ", "চল্লিশ",
        "একচল্লিশ", "বিয়াল্লিশ", "তেতাল্লিশ", "চুয়াল্লিশ", "পঁয়তাল্লিশ", "ছেচল্লিশ", "সাতচল্লিশ", "আটচল্লিশ", "উনপঞ্চাশ", "পঞ্চাশ",
        "একান্ন", "বায়ান্ন", "তিপ্পান্ন", "চুয়ান্ন", "পঞ্চান্ন", "ছাপ্পান্ন", "সাতান্ন", "আটান্ন", "উনষাট", "ষাট",
        "একষট্টি", "বাষট্টি", "তেষট্টি", "চৌষট্টি", "পঁয়ষট্টি", "ছেষট্টি", "সাতষট্টি", "আটষট্টি", "উনসত্তর", "সত্তর",
        "একাত্তর", "বাহাত্তর", "তিয়াত্তর", "চুয়াত্তর", "পঁচাত্তর", "ছিয়াত্তর", "সাতাত্তর", "আটাত্তর", "উনআশি", "আশি",
        "একাশি", "বিরাশি", "তিরাশি", "চুরাশি", "পঁচাশি", "ছিয়াশি", "সাতাশি", "আটাশি", "ঊননব্বই", "নব্বই",
        "একানব্বই", "বিরানব্বই", "তিরানব্বই", "চুরানব্বই", "পঁচানব্বই", "ছিয়ানব্বই", "সাতানব্বই", "আটানব্বই", "নিরানব্বই"
    )

    fun normalizeDigits(input: String): String {
        val sb = StringBuilder()
        for (c in input) {
            if (c in '0'..'9') {
                sb.append(c)
            } else if (c in DIGIT_MAP) {
                sb.append(DIGIT_MAP[c])
            }
        }
        return sb.toString()
    }

    fun convert(input: String, asCurrency: Boolean = false): String {
        val normalized = normalizeDigits(input).trimStart('0')
        if (normalized.isEmpty()) {
            return if (asCurrency) "শূন্য টাকা মাত্র" else "শূন্য"
        }

        val num = try {
            normalized.toLong()
        } catch (_: Exception) {
            return "অত্যধিক বড় সংখ্যা"
        }

        val words = convertToWords(num)
        return if (asCurrency) "$words টাকা মাত্র" else words
    }

    private fun convertToWords(n: Long): String {
        if (n == 0L) return NUMBERS_0_TO_99[0]
        if (n < 100L) return NUMBERS_0_TO_99[n.toInt()]

        val parts = mutableListOf<String>()

        var rem = n

        // কোটি (Crore: 10,000,000)
        val crore = rem / 10000000L
        if (crore > 0L) {
            parts.add("${convertToWords(crore)} কোটি")
            rem %= 10000000L
        }

        // লক্ষ (Lakh: 100,000)
        val lakh = rem / 100000L
        if (lakh > 0L) {
            parts.add("${NUMBERS_0_TO_99[lakh.toInt()]} লক্ষ")
            rem %= 100000L
        }

        // হাজার (Thousand: 1,000)
        val thousand = rem / 1000L
        if (thousand > 0L) {
            parts.add("${NUMBERS_0_TO_99[thousand.toInt()]} হাজার")
            rem %= 1000L
        }

        // শত (Hundred: 100)
        val hundred = rem / 100L
        if (hundred > 0L) {
            parts.add("${NUMBERS_0_TO_99[hundred.toInt()]} শত")
            rem %= 100L
        }

        // Remainder 1-99
        if (rem > 0L) {
            parts.add(NUMBERS_0_TO_99[rem.toInt()])
        }

        return parts.joinToString(" ")
    }
}
