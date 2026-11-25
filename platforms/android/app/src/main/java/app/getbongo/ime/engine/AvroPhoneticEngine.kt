package app.getbongo.ime.engine

import org.json.JSONArray
import org.json.JSONObject

/**
 * Pure Kotlin Avro phonetic engine.
 * Provides on-device zero-latency transliteration and dictionary lookups,
 * serving as an offline engine and seamless fallback.
 */
class AvroPhoneticEngine {

    var customShortcuts: Map<String, String> = emptyMap()
    var learnedSelections: MutableMap<String, String> = mutableMapOf()

    private val dictionary: Map<String, List<String>> by lazy {
        loadDictionary()
    }

    private val patterns: List<PatternRule> by lazy {
        loadPatterns()
    }

    data class Condition(val type: String, val scope: String, val value: String? = null)
    data class Rule(val matches: List<Condition>, val replace: String)
    data class PatternRule(val find: String, val default: String, val rules: List<Rule>)

    private fun isVowel(c: Char): Boolean = c in "aeiouAEIOU"
    private fun isConsonant(c: Char): Boolean = !isVowel(c) && (c in 'a'..'z' || c in 'A'..'Z')
    private fun isPunctuation(c: Char): Boolean = !(c in 'a'..'z' || c in 'A'..'Z')
    private fun isDigit(c: Char): Boolean = c in '0'..'9'

    private fun matchCondition(cond: Condition, prefix: String, suffix: String): Boolean {
        val isPrefix = cond.type.startsWith("Prefix")
        val isPositive = cond.type in listOf("PrefixIs", "SuffixIs")
        val ch = if (isPrefix) prefix.firstOrNull() ?: ' ' else suffix.firstOrNull() ?: ' '

        val ok = when (cond.scope) {
            "Vowel" -> isVowel(ch)
            "Consonant" -> isConsonant(ch)
            "Punctuation" -> isPunctuation(ch)
            "Number" -> isDigit(ch)
            "Char" -> ch.toString() == (cond.value ?: "")
            else -> false
        }
        return if (isPositive) ok else !ok
    }

    private fun getReplacement(pat: PatternRule, prefix: String, suffix: String): String {
        for (rule in pat.rules) {
            if (rule.matches.all { matchCondition(it, prefix, suffix) }) {
                return rule.replace
            }
        }
        return pat.default
    }

    private val autocorrectLoanwords: Map<String, List<String>> = mapOf(
        "1st" to listOf("১ম"), "2nd" to listOf("২য়"), "3rd" to listOf("৩য়"), "4th" to listOf("৪র্থ"), "5th" to listOf("৫ম"),
        "6th" to listOf("৬ষ্ঠ"), "7th" to listOf("৭ম"), "8th" to listOf("৮ম"), "9th" to listOf("৯ম"), "10th" to listOf("১০ম"),
        "class" to listOf("ক্লাস"), "click" to listOf("ক্লিক"), "chittagong" to listOf("চট্টগ্রাম"), "cinema" to listOf("সিনেমা"),
        "chemistry" to listOf("কেমিস্ট্রি"), "school" to listOf("স্কুল"), "college" to listOf("কলেজ"), "university" to listOf("বিশ্ববিদ্যালয়"),
        "police" to listOf("পুলিশ"), "bank" to listOf("ব্যাংক"), "card" to listOf("কার্ড"), "doctor" to listOf("ডাক্তার"),
        "hospital" to listOf("হাসপাতাল"), "station" to listOf("স্টেশন"), "ticket" to listOf("টিকিট"), "bus" to listOf("বাস"),
        "train" to listOf("ট্রেন"), "phone" to listOf("ফোন"), "mobile" to listOf("মোবাইল"), "internet" to listOf("ইন্টারনেট"),
        "email" to listOf("ইমেইল"), "facebook" to listOf("ফেসবুক"), "google" to listOf("গুগল"), "youtube" to listOf("ইউটিউব"),
        "windows" to listOf("উইন্ডোজ"), "office" to listOf("অফিস"), "video" to listOf("ভিডিও"), "audio" to listOf("অডিও"),
        "photo" to listOf("ছবি"), "camera" to listOf("ক্যামেরা"), "radio" to listOf("রেডিও"), "television" to listOf("টেলিভিশন"),
        "problem" to listOf("সমস্যা"), "program" to listOf("প্রোগ্রাম"), "project" to listOf("প্রজেক্ট"), "file" to listOf("ফাইল"),
        "folder" to listOf("ফোল্ডার"), "system" to listOf("সিস্টেম"), "service" to listOf("সার্ভিস"), "update" to listOf("আপডেট"),
        "version" to listOf("ভার্সন"), "page" to listOf("পেজ"), "site" to listOf("সাইট"), "link" to listOf("লিঙ্ক"),
        "post" to listOf("পোস্ট"), "comment" to listOf("কমেন্ট"), "message" to listOf("মেসেজ"), "chat" to listOf("চ্যাট"),
        "group" to listOf("গ্রুপ"), "member" to listOf("মেম্বার"), "admin" to listOf("অ্যাডমিন"), "login" to listOf("লগইন"),
        "password" to listOf("পাসওয়ার্ড"), "account" to listOf("অ্যাকাউন্ট"), "profile" to listOf("প্রোফাইল"),
        "status" to listOf("স্ট্যাটাস"), "story" to listOf("স্টোরি"), "share" to listOf("শেয়ার"), "like" to listOf("লাইক"),
        "subscribe" to listOf("সাবস্ক্রাইব"), "channel" to listOf("চ্যানেল"), "bongo" to listOf("বঙ্গ")
    )

    private val emojiKeywords: Map<String, String> = mapOf(
        "has" to "😄", "hasi" to "😂", "hashi" to "😂", "lol" to "😂", "smile" to "😊", "happy" to "😊",
        "love" to "❤️", "valobasha" to "❤️", "bhalobasha" to "❤️", "prem" to "💖", "heart" to "❤️",
        "kiss" to "😘", "chumo" to "😘", "sad" to "😢", "kanna" to "😭", "dukkho" to "😢", "dukho" to "😢",
        "rag" to "😡", "angry" to "😡", "shanto" to "😌", "thik" to "👍", "bhalo" to "👍", "ok" to "👌",
        "agun" to "🔥", "fire" to "🔥", "josh" to "🔥", "taka" to "💰", "money" to "💰",
        "bd" to "🇧🇩", "bangladesh" to "🇧🇩", "bongo" to "🇧🇩",
        "phul" to "🌸", "ful" to "🌸", "golap" to "🌹", "surjo" to "☀️", "sun" to "☀️",
        "chad" to "🌙", "chand" to "🌙", "moon" to "🌙", "tara" to "⭐", "star" to "⭐",
        "brishti" to "🌧️", "rain" to "🌧️", "megh" to "☁️",
        "cha" to "☕", "tea" to "☕", "coffee" to "☕", "aam" to "🥭", "mango" to "🥭",
        "clap" to "👏", "taali" to "👏", "namaste" to "🙏", "dua" to "🙏", "dowa" to "🙏",
        "salam" to "🤝", "eid" to "🌙", "party" to "🎉", "shuveccha" to "🎉", "birthday" to "🎂",
        "victory" to "✌️", "joy" to "✌️", "cricket" to "🏏", "football" to "⚽", "gaan" to "🎵",
        "ghum" to "😴", "sleep" to "😴", "kaj" to "💻", "work" to "💻", "boi" to "📚"
    )

    val commonBigrams: Map<String, List<String>> = mapOf(
        // Greetings & social
        "আমার" to listOf("সোনার", "দেশ", "নাম", "মন", "বাংলাদেশ", "ভাই", "পরিবার", "জীবন"),
        "সোনার" to listOf("বাংলা", "বাংলাদেশ", "মেয়ে", "হরিণ", "স্বপ্ন"),
        "বাংলা" to listOf("ভাষা", "সাহিত্য", "একাডেমী", "দেশ", "গান", "নববর্ষ", "সংস্কৃতি"),
        "বাংলাদেশ" to listOf("একটি", "সরকার", "জাতীয়", "রেলওয়ে", "ক্রিকেট", "আমার", "পুলিশ", "সেনাবাহিনী"),
        "শুভ" to listOf("সকাল", "রাত্রি", "সন্ধ্যা", "জন্মদিন", "কামনা", "নববর্ষ", "বিকেল", "দুপুর"),
        "কেমন" to listOf("আছো", "আছেন", "হবে", "লাগল", "আছিস", "লাগছে"),
        "অনেক" to listOf("ধন্যবাদ", "ভালো", "সুন্দর", "কষ্ট", "ভালোবাসা", "দিন", "সময়", "কিছু"),
        "খুব" to listOf("ভালো", "সুন্দর", "বেশি", "সহজ", "খারাপ", "দ্রুত", "কঠিন", "মিষ্টি"),
        "ধন্যবাদ" to listOf("আপনাকে", "তোমাকে", "ভাই", "সবাইকে", "অনেক", "জানাই"),
        "আমি" to listOf("তোমাকে", "ভালো", "এখন", "যাব", "আছি", "বলছি", "জানি", "মনে", "চাই", "ভাবছি"),
        "তুমি" to listOf("কেমন", "কোথায়", "কি", "যাবে", "আসবে", "আছো", "কী", "বলো", "জানো"),
        "আপনি" to listOf("কেমন", "কোথায়", "কি", "বলুন", "আসবেন", "আছেন", "জানেন", "দেখুন", "করুন"),
        "সালাম" to listOf("জানাই", "দেবেন", "নিবেন", "আলাইকুম", "জানাচ্ছি"),
        "ইনশাআল্লাহ" to listOf("ভালো", "হবে", "দেখা", "জিতব", "শেষ"),
        "মাশাল্লাহ" to listOf("অনেক", "সুন্দর", "ভালো"),
        "আলহামদুলিল্লাহ" to listOf("ভালো", "আছি", "সুস্থ"),
        "আসসালামুআলাইকুম" to listOf("ওয়ারাহমাতুল্লাহ", "ভাই", "সবাইকে"),
        "দোয়া" to listOf("করবেন", "চাই", "করেন", "রইল", "করুন"),
        "মোবারক" to listOf("হোক", "জানাই", "বাদ"),

        // Questions & conversation
        "কি" to listOf("খবর", "অবস্থা", "করছেন", "করছো", "হবে", "বলেন", "মনে", "লাগছে"),
        "কী" to listOf("খবর", "অবস্থা", "করছেন", "করছো", "হবে", "করবেন", "ভাবছেন"),
        "কোথায়" to listOf("যাবেন", "আছেন", "যাচ্ছেন", "থাকেন", "যাবে"),
        "কখন" to listOf("আসবেন", "যাবেন", "হবে", "আসবে", "শুরু"),
        "কীভাবে" to listOf("করবেন", "যাবেন", "হবে", "করলেন", "করছেন"),
        "কেন" to listOf("করছেন", "বলছেন", "যাচ্ছেন", "হলো", "করলে"),
        "কতটা" to listOf("সময়", "দূর", "ভালো", "কঠিন"),
        "কতক্ষণ" to listOf("লাগবে", "থাকবেন", "হবে", "ধরবে"),
        "কতদিন" to listOf("লাগবে", "থাকবেন", "আগে", "পরে"),

        // Time & daily life
        "আজ" to listOf("বৃষ্টি", "ছুটি", "সকালে", "রাতে", "শুক্রবার", "মেঘলা", "গরম", "ঠান্ডা"),
        "কাল" to listOf("দেখা", "সকালে", "যাব", "হবে", "আসবেন", "থেকে"),
        "এখন" to listOf("কয়টা", "সময়", "যাই", "কী", "ঘুমাব", "খাব", "বের"),
        "আজকে" to listOf("কী", "কোথায়", "খাবো", "যাচ্ছি", "করলাম"),
        "সন্ধ্যায়" to listOf("দেখা", "আসবেন", "খাবো", "বেড়াতে"),
        "রাতে" to listOf("খাবো", "ঘুমাব", "কথা", "দেখা", "আসবেন"),
        "সকালে" to listOf("উঠেছি", "নাস্তা", "দেখা", "আসুন", "যাব"),
        "দুপুরে" to listOf("খাবো", "ঘুমাব", "দেখা", "আসবেন"),
        "পরে" to listOf("দেখা", "কথা", "যাব", "আসবেন", "জানাব"),
        "আগামীকাল" to listOf("দেখা", "যাব", "আসবেন", "কথা", "হবে"),
        "এইবার" to listOf("হবে", "করব", "যাব", "দেখা"),
        "এবার" to listOf("হবে", "করব", "যাব", "দেখা", "শুরু"),

        // Feelings & emotions
        "ভালো" to listOf("আছি", "থাকবেন", "থেকো", "লাগে", "বাসি", "হবে", "লাগছে", "থাকুন"),
        "ভালোবাসি" to listOf("তোমাকে", "আপনাকে", "অনেক"),
        "ভালোবাসা" to listOf("তোমার", "আমার", "দিয়ে", "করি"),
        "মিস" to listOf("করছি", "করি", "করছো"),
        "কষ্ট" to listOf("পাচ্ছি", "হচ্ছে", "লাগছে", "দিও না"),
        "দুঃখিত" to listOf("ভাই", "আপু", "বলার", "যে"),
        "মাফ" to listOf("করবেন", "করো", "করুন", "চাইছি"),
        "খুশি" to listOf("হয়েছি", "আছি", "হলে", "হবে"),
        "বিরক্ত" to listOf("লাগছে", "হচ্ছি", "লাগে"),
        "চিন্তা" to listOf("করো না", "করবেন না", "নেই", "হচ্ছে", "করছি"),

        // Places & geography
        "ঢাকা" to listOf("শহর", "বিশ্ববিদ্যালয়", "মেডিকেল", "উত্তর", "দক্ষিণ", "থেকে", "যাচ্ছি"),
        "চট্টগ্রাম" to listOf("শহর", "বিশ্ববিদ্যালয়", "বন্দর", "থেকে"),
        "সিলেট" to listOf("শহর", "বিভাগ", "থেকে"),
        "রাজশাহী" to listOf("বিশ্ববিদ্যালয়", "শহর", "থেকে"),
        "খুলনা" to listOf("শহর", "বিভাগ", "থেকে"),
        "বরিশাল" to listOf("শহর", "বিভাগ", "থেকে"),
        "ময়মনসিংহ" to listOf("শহর", "বিভাগ"),
        "রংপুর" to listOf("শহর", "বিভাগ"),
        "কুমিল্লা" to listOf("শহর", "জেলা"),
        "গাজীপুর" to listOf("জেলা", "শহর"),

        // National & civic
        "জাতীয়" to listOf("সংসদ", "পতাকা", "সঙ্গীত", "দিবস", "স্মৃতিসৌধ", "বিশ্ববিদ্যালয়", "পরিচয়পত্র"),
        "আন্তর্জাতিক" to listOf("মাতৃভাষা", "সম্পর্ক", "বিমানবন্দর", "মানদণ্ড", "সংস্থা"),
        "মাতৃভাষা" to listOf("দিবস", "আন্দোলন", "ইনস্টিটিউট"),
        "একুশে" to listOf("ফেব্রুয়ারি", "বইমেলা", "পদক"),
        "স্বাধীনতা" to listOf("দিবস", "যুদ্ধ", "সংগ্রাম", "সংগ্রামী"),
        "মুক্তিযুদ্ধ" to listOf("বিষয়ক", "যাদুঘর", "মন্ত্রণালয়", "স্মৃতি"),
        "সরকারি" to listOf("চাকরি", "কর্মকর্তা", "বিদ্যালয়", "হাসপাতাল", "পর্যায়ে"),
        "বেসরকারি" to listOf("প্রতিষ্ঠান", "সংস্থা", "বিশ্ববিদ্যালয়", "ব্যাংক"),

        // Education
        "বিশ্ববিদ্যালয়" to listOf("ভর্তি", "পড়াশোনা", "শিক্ষক", "থেকে", "জীবন"),
        "স্কুল" to listOf("জীবন", "থেকে", "পরীক্ষা", "ছুটি", "বন্ধু"),
        "কলেজ" to listOf("জীবন", "থেকে", "পরীক্ষা", "ছুটি"),
        "পরীক্ষা" to listOf("দিচ্ছি", "হবে", "শেষ", "ভালো", "কঠিন"),
        "পড়াশোনা" to listOf("করছি", "করতে", "শেষ", "ভালো"),
        "রেজাল্ট" to listOf("ভালো", "হয়েছে", "আসবে", "দেখেছো"),
        "ক্লাস" to listOf("আছে", "করছি", "শুরু", "শেষ", "নেই"),
        "শিক্ষক" to listOf("বললেন", "ভালো", "কঠোর", "মহোদয়"),

        // Work & professional
        "কাজ" to listOf("করছি", "শেষ", "করতে", "হচ্ছে", "আছে", "নেই", "দিন"),
        "অফিস" to listOf("যাচ্ছি", "থেকে", "আসছি", "কাজ", "বন্ধ"),
        "মিটিং" to listOf("আছে", "শেষ", "হবে", "করছি"),
        "প্রজেক্ট" to listOf("শেষ", "করছি", "হবে", "জমা"),
        "ডেডলাইন" to listOf("আজকে", "কাল", "আছে", "মিস"),
        "রিপোর্ট" to listOf("জমা", "লিখছি", "দিতে", "তৈরি"),
        "বস" to listOf("বললেন", "আছেন", "ডাকছেন"),
        "বেতন" to listOf("পেয়েছি", "হয়নি", "কম", "বেশি"),

        // Food & daily
        "খাবার" to listOf("খেয়েছো", "তৈরি", "আনো", "কী"),
        "ভাত" to listOf("খেয়েছো", "রান্না", "দাও", "খাব"),
        "রুটি" to listOf("খাব", "দাও", "রান্না"),
        "মাছ" to listOf("ভাজা", "রান্না", "কিনে", "খাব"),
        "মাংস" to listOf("রান্না", "কিনে", "খাব", "ভালো"),
        "চা" to listOf("খাব", "দাও", "বানাও", "আনো", "পান"),
        "নাস্তা" to listOf("খেয়েছো", "করেছো", "তৈরি", "দাও"),
        "রান্না" to listOf("করছি", "হয়েছে", "করো", "শিখছি"),

        // Health
        "অসুস্থ" to listOf("আছি", "হয়েছি", "লাগছে"),
        "জ্বর" to listOf("আছে", "হয়েছে", "কমছে", "বেশি"),
        "ডাক্তার" to listOf("দেখিয়েছো", "গেছো", "বললেন", "দরকার"),
        "ওষুধ" to listOf("খেয়েছো", "দরকার", "কিনে", "নাও"),
        "হাসপাতাল" to listOf("গেছো", "থেকে", "যেতে", "ভর্তি"),
        "সুস্থ" to listOf("হয়েছো", "আছো", "থেকো", "হও"),

        // Technology & social media
        "ফোন" to listOf("দাও", "করো", "করুন", "করব", "বন্ধ", "চার্জ"),
        "মোবাইল" to listOf("দাও", "করো", "করুন", "চার্জ", "বন্ধ"),
        "ইন্টারনেট" to listOf("নেই", "আছে", "স্লো", "চলছে"),
        "ফেসবুক" to listOf("দেখছি", "দিয়েছি", "পোস্ট", "আইডি"),
        "মেসেজ" to listOf("দিয়েছি", "করুন", "পাঠাব", "পেয়েছেন"),
        "ভিডিও" to listOf("কল", "দেখছি", "পাঠাও", "করো"),
        "লাইভ" to listOf("করছি", "দেখছি", "আসুন"),
        "ডাউনলোড" to listOf("করছি", "হচ্ছে", "শেষ", "দিন"),

        // Religion & culture
        "আল্লাহ" to listOf("ভরসা", "হাফেজ", "রহমত", "ইচ্ছা", "করুন"),
        "খোদা" to listOf("হাফেজ", "করুন"),
        "নামাজ" to listOf("পড়েছেন", "পড়বেন", "শেষ", "আদায়"),
        "রোজা" to listOf("রেখেছেন", "রাখবেন", "ভাঙা", "শেষ"),
        "ঈদ" to listOf("মোবারক", "কেমন", "কাটলো", "আনন্দ"),
        "পূজা" to listOf("মণ্ডপ", "শুভ", "কাটলো"),

        // Misc common phrases
        "সবাইকে" to listOf("ধন্যবাদ", "শুভ", "স্বাগতম", "জানাই", "আমন্ত্রণ"),
        "স্বাগতম" to listOf("জানাই", "আমাদের"),
        "কি" to listOf("খবর", "অবস্থা", "করছেন", "করছো", "হবে", "বলেন"),
        "সমস্যা" to listOf("নেই", "হবে", "আছে", "কী", "কোন"),
        "মনে" to listOf("হয়", "রাখবেন", "পড়ে", "আছে", "করো"),
        "কথা" to listOf("বলুন", "বলো", "বলতে", "হলো", "আছে"),
        "সব" to listOf("কিছু", "সময়", "ঠিক", "হবে", "জায়গায়"),
        "কোন" to listOf("সমস্যা", "কথা", "সন্দেহ", "না", "দরকার"),
        "আসো" to listOf("একসাথে", "দেখা", "কথা"),
        "যাও" to listOf("ভালো", "থেকো", "দেখে"),
        "দেখো" to listOf("ভালো", "আমি", "কী", "হচ্ছে"),
        "জানাও" to listOf("কবে", "কখন", "কী", "হলে"),
        "জানাবেন" to listOf("কবে", "কখন", "কী", "যদি"),
        "বলো" to listOf("কী", "কেন", "কীভাবে", "আমাকে"),
        "শুনো" to listOf("একটু", "কথা", "আমার"),
        "দেখি" to listOf("কী", "হয়", "পাচ্ছি", "করতে"),
        "হয়তো" to listOf("হবে", "আসবে", "যাব", "পারব"),
        "আসলে" to listOf("কী", "বলতে", "হয়নি", "ঠিকই"),
        "তবে" to listOf("হবে", "করব", "যাব", "ঠিক"),
        "কিন্তু" to listOf("সমস্যা", "আমি", "বলা", "করা"),
        "যদি" to listOf("হয়", "আসো", "পারো", "করো", "থাকো"),
        "তাহলে" to listOf("হবে", "করব", "যাব", "ঠিক"),
        "তবুও" to listOf("ভালো", "করব", "থাকব", "যাব"),
        "আর" to listOf("কী", "কতক্ষণ", "কখন", "নেই", "যাবে"),
        "না" to listOf("হয়", "থাকলে", "করলে", "বললে"),
        "হ্যাঁ" to listOf("ঠিকই", "বলেছেন", "আছি", "করব", "জানি"),
        "ঠিক" to listOf("আছে", "হবে", "বলেছেন", "করব"),
        "ঠিকআছে" to listOf("ভাই", "বুঝেছি", "করব"),
        "ওকে" to listOf("ভাই", "বুঝেছি", "করব", "দেখছি"),
        "বাই" to listOf("ভাই", "আপু", "দেখা"),
        "টাকা" to listOf("নেই", "লাগবে", "দাও", "পাঠাও", "কম", "বেশি"),
        "খরচ" to listOf("কত", "বেশি", "কম", "লাগবে"),
        "দাম" to listOf("কত", "বেশি", "কম", "কমাও"),
        "বাজার" to listOf("করতে", "যাব", "থেকে", "দাম"),
        "ট্রান্সপোর্ট" to listOf("ভাড়া", "পাওয়া", "নেই"),
        "রিকশা" to listOf("ভাড়া", "পাওয়া", "নেই", "করব"),
        "বাস" to listOf("আসছে", "নেই", "ধরব", "ভাড়া"),
        "ট্রেন" to listOf("সময়", "মিস", "ধরব", "ভাড়া"),
        "ফ্লাইট" to listOf("সময়", "মিস", "কাল", "আগামীকাল")
    )

    fun predictNextWords(word: String): List<String> {
        if (word.isEmpty()) return emptyList()
        val clean = word.trim { it in " .,!?।:;'\"_-\t\n" }
        return commonBigrams[clean] ?: emptyList()
    }

    /**
     * Resolves a swipe-to-type (glide) key trajectory string into ranked word candidates.
     * Supports both Bangla phonetic vocabulary and common English words offline.
     */
    fun matchGlidePath(rawKeySeq: String, isBangla: Boolean): List<String> {
        val cleaned = rawKeySeq.lowercase().filter { it in 'a'..'z' }
        if (cleaned.length < 2) return emptyList()

        // Collapse consecutive repeated keys caused by dwelling on a key
        val path = buildString {
            for (c in cleaned) {
                if (isEmpty() || last() != c) append(c)
            }
        }
        if (path.length < 2) return emptyList()

        val vocabKeys: Collection<String> = if (isBangla) {
            (dictionary.keys + autocorrectLoanwords.keys + customShortcuts.keys + learnedSelections.keys).distinct()
        } else {
            (ENGLISH_GLIDE_VOCAB + customShortcuts.keys).distinct()
        }

        val scored = mutableListOf<Pair<String, Double>>()
        for (word in vocabKeys) {
            val w = word.lowercase().filter { it in 'a'..'z' }
            if (w.length < 2) continue
            val dedupWord = buildString {
                for (c in w) {
                    if (isEmpty() || last() != c) append(c)
                }
            }
            val score = scoreGlideMatch(path, dedupWord)
            if (score > 0.0) {
                scored.add(word to score)
            }
        }
        scored.sortByDescending { it.second }

        val results = linkedSetOf<String>()
        for ((matchedKey, _) in scored.take(6)) {
            if (isBangla) {
                getCandidates(matchedKey).firstOrNull()?.let { results.add(it) }
            } else {
                results.add(matchedKey)
            }
        }
        if (results.isEmpty()) {
            if (isBangla) {
                getCandidates(path).firstOrNull()?.let { results.add(it) }
            } else {
                results.add(path)
            }
        }
        return results.toList()
    }

    private fun scoreGlideMatch(path: String, word: String): Double {
        if (path == word) return 100.0
        if (!isNearKey(path.first(), word.first())) return -1.0
        if (!isNearKey(path.last(), word.last())) return -1.0

        // Ordered subsequence match across the glide path
        var pIdx = 0
        var matched = 0
        var exactHit = 0
        for (wc in word) {
            var found = false
            while (pIdx < path.length) {
                val pc = path[pIdx]
                pIdx++
                if (pc == wc) {
                    exactHit++
                    matched++
                    found = true
                    break
                } else if (isNearKey(pc, wc)) {
                    matched++
                    found = true
                    break
                }
            }
            if (!found) return -1.0
        }

        val firstExactBonus = if (path.first() == word.first()) 15.0 else 0.0
        val lastExactBonus = if (path.last() == word.last()) 15.0 else 0.0
        val lenPenalty = kotlin.math.abs(path.length - word.length) * 2.5
        return 40.0 + firstExactBonus + lastExactBonus + (exactHit * 4.0) - lenPenalty
    }

    private fun isNearKey(a: Char, b: Char): Boolean {
        if (a == b) return true
        val posA = QWERTY_COORDS[a] ?: return false
        val posB = QWERTY_COORDS[b] ?: return false
        val dr = kotlin.math.abs(posA.first - posB.first)
        val dc = kotlin.math.abs(posA.second - posB.second)
        return dr <= 1 && dc <= 1.2f
    }

    fun separatePadding(word: String): Triple<String, String, String> {
        if (word.isEmpty()) return Triple("", "", "")
        return try {
            val prefixMatch = PREFIX_PUNCT_REGEX.find(word)
            val prefix = prefixMatch?.value ?: ""
            val rest = word.substring(prefix.length)
            val suffixMatch = SUFFIX_PUNCT_REGEX.find(rest)
            val suffix = suffixMatch?.value ?: ""
            val stem = if (suffix.isNotEmpty()) rest.substring(0, rest.length - suffix.length) else rest
            Triple(prefix, stem, suffix)
        } catch (_: Exception) {
            Triple("", word, "")
        }
    }

    fun fixStringCase(word: String): String {
        if (word.isEmpty()) return ""
        val caseSensitive = "OIUDGJNRSTYZ"
        return word.map { c ->
            if (c in caseSensitive || !c.isLetter()) c else c.lowercaseChar()
        }.joinToString("")
    }

    fun convertWord(raw: String): String {
        if (raw.isEmpty()) return ""
        val inp = raw.map { c ->
            val lc = c.lowercaseChar()
            if (lc in listOf('o', 'i', 'u', 'd', 'g', 'j', 'n', 'r', 's', 't', 'y', 'z')) c else lc
        }.joinToString("")

        var prefix = " "
        val out = StringBuilder()
        var i = 0
        val n = inp.length

        while (i < n) {
            val sub = inp.substring(i)
            var matched: PatternRule? = null
            for (p in patterns) {
                if (sub.startsWith(p.find)) {
                    matched = p
                    break
                }
            }

            if (matched != null) {
                val flen = matched.find.length
                val suffix = if (i + flen < n) inp[i + flen].toString() else " "
                out.append(getReplacement(matched, prefix, suffix))
                prefix = matched.find.last().toString()
                i += flen
            } else {
                prefix = inp[i].toString()
                out.append(prefix)
                i += 1
            }
        }
        return out.toString()
    }

    fun getCandidates(word: String): List<String> {
        val cleaned = word.trim()
        if (cleaned.isEmpty()) return emptyList()

        val (punctPrefix, stem, punctSuffix) = separatePadding(cleaned)
        if (stem.isEmpty()) return listOf(cleaned)

        val casedStem = fixStringCase(stem)
        val lower = stem.lowercase()
        val cands = mutableListOf<String>()
        val seen = mutableSetOf<String>()

        fun add(c: String?) {
            if (!c.isNullOrEmpty() && seen.add(c)) {
                cands.add(c)
            }
        }

        // Custom Shortcuts & Text Expansion (highest priority)
        customShortcuts[lower]?.let { add(it) }

        // Adaptive Learned Selection (user's personal top choice)
        learnedSelections[lower]?.let { add(it) }

        // Inline Emoji Keywords
        val cleanKeyword = lower.trim(':')
        emojiKeywords[cleanKeyword]?.let { add(it) }

        dictionary[lower]?.forEach { add(it) }
        autocorrectLoanwords[lower]?.forEach { add(it) }

        val ruleBased = convertWord(casedStem)
        add(ruleBased)

        if (cands.size < 5) {
            add(convertWord(stem.replaceFirstChar { it.uppercase() }))
        }
        if (cands.size < 5) {
            if ("sh" in lower) {
                add(convertWord(stem.replace("sh", "s", ignoreCase = true)))
            } else if ("s" in lower) {
                add(convertWord(stem.replace("s", "sh", ignoreCase = true)))
            }
        }
        add(stem)

        return cands.take(5).map { "$punctPrefix$it$punctSuffix" }
    }

    private fun loadPatterns(): List<PatternRule> {
        val result = mutableListOf<PatternRule>()
        val jsonArray = JSONArray(PATTERNS_JSON)
        for (i in 0 until jsonArray.length()) {
            val obj = jsonArray.getJSONObject(i)
            val find = obj.getString("find")
            val defaultStr = obj.getString("default")
            val rulesArray = obj.optJSONArray("rules") ?: JSONArray()
            val rules = mutableListOf<Rule>()
            for (j in 0 until rulesArray.length()) {
                val rObj = rulesArray.getJSONObject(j)
                val replace = rObj.getString("replace")
                val mArray = rObj.optJSONArray("matches") ?: JSONArray()
                val matches = mutableListOf<Condition>()
                for (k in 0 until mArray.length()) {
                    val mObj = mArray.getJSONObject(k)
                    matches.add(
                        Condition(
                            type = mObj.getString("type"),
                            scope = mObj.getString("scope"),
                            value = if (mObj.has("val")) mObj.getString("val") else null
                        )
                    )
                }
                rules.add(Rule(matches, replace))
            }
            result.add(PatternRule(find, defaultStr, rules))
        }
        return result
    }

    private fun loadDictionary(): Map<String, List<String>> {
        val map = mutableMapOf<String, List<String>>()
        val json = JSONObject(DICTIONARY_JSON)
        val keys = json.keys()
        while (keys.hasNext()) {
            val k = keys.next()
            val arr = json.getJSONArray(k)
            val list = mutableListOf<String>()
            for (i in 0 until arr.length()) {
                list.add(arr.getString(i))
            }
            map[k] = list
        }
        return map
    }

    companion object {
        private val PREFIX_PUNCT_REGEX = Regex("""^([-~!@#%&*()_=+{}\[\]'";<>/?|.,:\\]+)""")
        private val SUFFIX_PUNCT_REGEX = Regex("""([-~!@#%&*()_=+{}\[\]'";<>/?|.,:\\]+)$""")
        private val QWERTY_COORDS: Map<Char, Pair<Int, Float>> = mapOf(
            'q' to (0 to 0f), 'w' to (0 to 1f), 'e' to (0 to 2f), 'r' to (0 to 3f), 't' to (0 to 4f),
            'y' to (0 to 5f), 'u' to (0 to 6f), 'i' to (0 to 7f), 'o' to (0 to 8f), 'p' to (0 to 9f),
            'a' to (1 to 0.5f), 's' to (1 to 1.5f), 'd' to (1 to 2.5f), 'f' to (1 to 3.5f), 'g' to (1 to 4.5f),
            'h' to (1 to 5.5f), 'j' to (1 to 6.5f), 'k' to (1 to 7.5f), 'l' to (1 to 8.5f),
            'z' to (2 to 1.5f), 'x' to (2 to 2.5f), 'c' to (2 to 3.5f), 'v' to (2 to 4.5f),
            'b' to (2 to 5.5f), 'n' to (2 to 6.5f), 'm' to (2 to 7.5f)
        )
        private val ENGLISH_GLIDE_VOCAB = listOf(
            "the", "be", "to", "of", "and", "in", "that", "have", "it", "for", "not", "on", "with",
            "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say",
            "her", "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when", "make",
            "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year",
            "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look",
            "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how",
            "our", "work", "first", "well", "way", "even", "new", "want", "because", "any", "these",
            "give", "day", "most", "us", "hello", "hi", "hey", "thanks", "thank", "please", "sorry",
            "yes", "yeah", "okay", "sure", "great", "awesome", "love", "miss", "need", "help",
            "today", "tomorrow", "tonight", "morning", "night", "home", "office", "meeting", "call",
            "message", "send", "wait", "soon", "done", "ready", "happy", "birthday", "friend", "family",
            "phone", "email", "password", "search", "open", "close", "save", "delete", "update", "code",
            "bongo", "bangla", "bangladesh", "dhaka", "android", "keyboard", "typing", "fast", "clean",
            "where", "why", "how", "what", "when", "here", "right", "left", "very", "much", "more", "best"
        )
        const val PATTERNS_JSON = """[{"find":"NgkSh","default":"ঙ্ক্ষ","rules":[]},{"find":"Ngkkh","default":"ঙ্ক্ষ","rules":[]},{"find":"kkhN","default":"ক্ষ্ণ","rules":[]},{"find":"kShN","default":"ক্ষ্ণ","rules":[]},{"find":"kkhm","default":"ক্ষ্ম","rules":[]},{"find":"kShm","default":"ক্ষ্ম","rules":[]},{"find":"NGch","default":"ঞ্ছ","rules":[]},{"find":"Nggh","default":"ঙ্ঘ","rules":[]},{"find":"Ngkh","default":"ঙ্খ","rules":[]},{"find":"NGjh","default":"ঞ্ঝ","rules":[]},{"find":"ngOU","default":"ঙ্গৌ","rules":[]},{"find":"ngOI","default":"ঙ্গৈ","rules":[]},{"find":"Ngkx","default":"ঙ্ক্ষ","rules":[]},{"find":"rri`","default":"ৃ","rules":[]},{"find":"shch","default":"শ্ছ","rules":[]},{"find":"ShTh","default":"ষ্ঠ","rules":[]},{"find":"Shph","default":"ষ্ফ","rules":[]},{"find":"psh","default":"পশ","rules":[]},{"find":"bhl","default":"ভ্ল","rules":[]},{"find":"bdh","default":"ব্ধ","rules":[]},{"find":"cNG","default":"চ্ঞ","rules":[]},{"find":"cch","default":"চ্ছ","rules":[]},{"find":"dhn","default":"ধ্ন","rules":[]},{"find":"dhm","default":"ধ্ম","rules":[]},{"find":"dgh","default":"দ্ঘ","rules":[]},{"find":"ddh","default":"দ্ধ","rules":[]},{"find":"dbh","default":"দ্ভ","rules":[]},{"find":"...","default":"...","rules":[]},{"find":"ghn","default":"ঘ্ন","rules":[]},{"find":"Ghn","default":"ঘ্ন","rules":[]},{"find":"gdh","default":"গ্ধ","rules":[]},{"find":"Gdh","default":"গ্ধ","rules":[]},{"find":"jjh","default":"জ্ঝ","rules":[]},{"find":"jNG","default":"জ্ঞ","rules":[]},{"find":"kxN","default":"ক্ষ্ণ","rules":[]},{"find":"kxm","default":"ক্ষ্ম","rules":[]},{"find":"kkh","default":"ক্ষ","rules":[]},{"find":"kSh","default":"ক্ষ","rules":[]},{"find":"ksh","default":"কশ","rules":[]},{"find":"lbh","default":"ল্ভ","rules":[]},{"find":"ldh","default":"ল্ধ","rules":[]},{"find":"lkh","default":"লখ","rules":[]},{"find":"lgh","default":"লঘ","rules":[]},{"find":"lph","default":"লফ","rules":[]},{"find":"mth","default":"ম্থ","rules":[]},{"find":"mph","default":"ম্ফ","rules":[]},{"find":"mbh","default":"ম্ভ","rules":[]},{"find":"mpl","default":"মপ্ল","rules":[]},{"find":"NGc","default":"ঞ্চ","rules":[]},{"find":"nch","default":"ঞ্ছ","rules":[]},{"find":"njh","default":"ঞ্ঝ","rules":[]},{"find":"ngh","default":"ঙ্ঘ","rules":[]},{"find":"Ngk","default":"ঙ্ক","rules":[]},{"find":"Ngx","default":"ঙ্ষ","rules":[]},{"find":"Ngg","default":"ঙ্গ","rules":[]},{"find":"Ngm","default":"ঙ্ম","rules":[]},{"find":"NGj","default":"ঞ্জ","rules":[]},{"find":"ndh","default":"ন্ধ","rules":[]},{"find":"nTh","default":"ন্ঠ","rules":[]},{"find":"NTh","default":"ণ্ঠ","rules":[]},{"find":"nth","default":"ন্থ","rules":[]},{"find":"nkh","default":"ঙ্খ","rules":[]},{"find":"ngo","default":"ঙ্গ","rules":[]},{"find":"nga","default":"ঙ্গা","rules":[]},{"find":"ngi","default":"ঙ্গি","rules":[]},{"find":"ngI","default":"ঙ্গী","rules":[]},{"find":"ngu","default":"ঙ্গু","rules":[]},{"find":"ngU","default":"ঙ্গূ","rules":[]},{"find":"nge","default":"ঙ্গে","rules":[]},{"find":"ngO","default":"ঙ্গো","rules":[]},{"find":"NDh","default":"ণ্ঢ","rules":[]},{"find":"nsh","default":"নশ","rules":[]},{"find":"Ngr","default":"ঙর","rules":[]},{"find":"NGr","default":"ঞর","rules":[]},{"find":"ngr","default":"ংর","rules":[]},{"find":"OI`","default":"ৈ","rules":[]},{"find":"OU`","default":"ৌ","rules":[]},{"find":"phl","default":"ফ্ল","rules":[]},{"find":"rri","default":"ৃ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঋ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঋ"}]},{"find":"rrZ","default":"রর\u200d্য","rules":[]},{"find":"rry","default":"রর\u200d্য","rules":[]},{"find":"Sch","default":"শ্ছ","rules":[]},{"find":"skl","default":"স্ক্ল","rules":[]},{"find":"skh","default":"স্খ","rules":[]},{"find":"sth","default":"স্থ","rules":[]},{"find":"sph","default":"স্ফ","rules":[]},{"find":"shc","default":"শ্চ","rules":[]},{"find":"sht","default":"শ্ত","rules":[]},{"find":"shn","default":"শ্ন","rules":[]},{"find":"shm","default":"শ্ম","rules":[]},{"find":"shl","default":"শ্ল","rules":[]},{"find":"Shk","default":"ষ্ক","rules":[]},{"find":"ShT","default":"ষ্ট","rules":[]},{"find":"ShN","default":"ষ্ণ","rules":[]},{"find":"Shp","default":"ষ্প","rules":[]},{"find":"Shf","default":"ষ্ফ","rules":[]},{"find":"Shm","default":"ষ্ম","rules":[]},{"find":"spl","default":"স্প্ল","rules":[]},{"find":"oo`","default":"ু","rules":[]},{"find":"tth","default":"ত্থ","rules":[]},{"find":"t``","default":"ৎ","rules":[]},{"find":"ee`","default":"ী","rules":[]},{"find":"bj","default":"ব্জ","rules":[]},{"find":"bd","default":"ব্দ","rules":[]},{"find":"bb","default":"ব্ব","rules":[]},{"find":"bl","default":"ব্ল","rules":[]},{"find":"bh","default":"ভ","rules":[]},{"find":"vl","default":"ভ্ল","rules":[]},{"find":"cc","default":"চ্চ","rules":[]},{"find":"ch","default":"ছ","rules":[]},{"find":"dv","default":"দ্ভ","rules":[]},{"find":"dm","default":"দ্ম","rules":[]},{"find":"DD","default":"ড্ড","rules":[]},{"find":"Dh","default":"ঢ","rules":[]},{"find":"dh","default":"ধ","rules":[]},{"find":"dg","default":"দ্গ","rules":[]},{"find":"dd","default":"দ্দ","rules":[]},{"find":".`","default":".","rules":[]},{"find":"..","default":"।।","rules":[]},{"find":"gN","default":"গ্ণ","rules":[]},{"find":"GN","default":"গ্ণ","rules":[]},{"find":"gn","default":"গ্ন","rules":[]},{"find":"Gn","default":"গ্ন","rules":[]},{"find":"gm","default":"গ্ম","rules":[]},{"find":"Gm","default":"গ্ম","rules":[]},{"find":"gl","default":"গ্ল","rules":[]},{"find":"Gl","default":"গ্ল","rules":[]},{"find":"gg","default":"জ্ঞ","rules":[]},{"find":"GG","default":"জ্ঞ","rules":[]},{"find":"Gg","default":"জ্ঞ","rules":[]},{"find":"gG","default":"জ্ঞ","rules":[]},{"find":"gh","default":"ঘ","rules":[]},{"find":"Gh","default":"ঘ","rules":[]},{"find":"hN","default":"হ্ণ","rules":[]},{"find":"hn","default":"হ্ন","rules":[]},{"find":"hm","default":"হ্ম","rules":[]},{"find":"hl","default":"হ্ল","rules":[]},{"find":"jh","default":"ঝ","rules":[]},{"find":"jj","default":"জ্জ","rules":[]},{"find":"kx","default":"ক্ষ","rules":[]},{"find":"kk","default":"ক্ক","rules":[]},{"find":"kT","default":"ক্ট","rules":[]},{"find":"kt","default":"ক্ত","rules":[]},{"find":"kl","default":"ক্ল","rules":[]},{"find":"ks","default":"ক্স","rules":[]},{"find":"kh","default":"খ","rules":[]},{"find":"lk","default":"ল্ক","rules":[]},{"find":"lg","default":"ল্গ","rules":[]},{"find":"lT","default":"ল্ট","rules":[]},{"find":"lD","default":"ল্ড","rules":[]},{"find":"lp","default":"ল্প","rules":[]},{"find":"lv","default":"ল্ভ","rules":[]},{"find":"lm","default":"ল্ম","rules":[]},{"find":"ll","default":"ল্ল","rules":[]},{"find":"lb","default":"ল্ব","rules":[]},{"find":"mn","default":"ম্ন","rules":[]},{"find":"mp","default":"ম্প","rules":[]},{"find":"mv","default":"ম্ভ","rules":[]},{"find":"mm","default":"ম্ম","rules":[]},{"find":"ml","default":"ম্ল","rules":[]},{"find":"mb","default":"ম্ব","rules":[]},{"find":"mf","default":"ম্ফ","rules":[]},{"find":"nj","default":"ঞ্জ","rules":[]},{"find":"Ng","default":"ঙ","rules":[]},{"find":"NG","default":"ঞ","rules":[]},{"find":"nk","default":"ঙ্ক","rules":[]},{"find":"ng","default":"ং","rules":[]},{"find":"nn","default":"ন্ন","rules":[]},{"find":"NN","default":"ণ্ণ","rules":[]},{"find":"Nn","default":"ণ্ন","rules":[]},{"find":"nm","default":"ন্ম","rules":[]},{"find":"Nm","default":"ণ্ম","rules":[]},{"find":"nd","default":"ন্দ","rules":[]},{"find":"nT","default":"ন্ট","rules":[]},{"find":"NT","default":"ণ্ট","rules":[]},{"find":"nD","default":"ন্ড","rules":[]},{"find":"ND","default":"ণ্ড","rules":[]},{"find":"nt","default":"ন্ত","rules":[]},{"find":"ns","default":"ন্স","rules":[]},{"find":"nc","default":"ঞ্চ","rules":[]},{"find":"O`","default":"ো","rules":[]},{"find":"OI","default":"ৈ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঐ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঐ"}]},{"find":"OU","default":"ৌ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঔ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঔ"}]},{"find":"pT","default":"প্ট","rules":[]},{"find":"pt","default":"প্ত","rules":[]},{"find":"pn","default":"প্ন","rules":[]},{"find":"pp","default":"প্প","rules":[]},{"find":"pl","default":"প্ল","rules":[]},{"find":"ps","default":"প্স","rules":[]},{"find":"ph","default":"ফ","rules":[]},{"find":"fl","default":"ফ্ল","rules":[]},{"find":"rZ","default":"র\u200d্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"ry","default":"র\u200d্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"rr","default":"রর","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Vowel"},{"type":"SuffixIsNot","scope":"Char","val":"r"},{"type":"SuffixIsNot","scope":"Punctuation"}],"replace":"র্"},{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"}],"replace":"্রর"}]},{"find":"Rg","default":"ড়্গ","rules":[]},{"find":"Rh","default":"ঢ়","rules":[]},{"find":"sk","default":"স্ক","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"sT","default":"স্ট","rules":[]},{"find":"st","default":"স্ত","rules":[]},{"find":"sn","default":"স্ন","rules":[]},{"find":"sp","default":"স্প","rules":[]},{"find":"sf","default":"স্ফ","rules":[]},{"find":"sm","default":"স্ম","rules":[]},{"find":"sl","default":"স্ল","rules":[]},{"find":"sh","default":"শ","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"St","default":"শ্ত","rules":[]},{"find":"Sn","default":"শ্ন","rules":[]},{"find":"Sm","default":"শ্ম","rules":[]},{"find":"Sl","default":"শ্ল","rules":[]},{"find":"Sh","default":"ষ","rules":[]},{"find":"oo","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"o`","default":"","rules":[]},{"find":"oZ","default":"অ্য","rules":[]},{"find":"TT","default":"ট্ট","rules":[]},{"find":"Tm","default":"ট্ম","rules":[]},{"find":"Th","default":"ঠ","rules":[]},{"find":"tn","default":"ত্ন","rules":[]},{"find":"tm","default":"ত্ম","rules":[]},{"find":"th","default":"থ","rules":[]},{"find":"tt","default":"ত্ত","rules":[]},{"find":"aZ","default":"অ্যা","rules":[]},{"find":"AZ","default":"অ্যা","rules":[]},{"find":"a`","default":"া","rules":[]},{"find":"A`","default":"া","rules":[]},{"find":"i`","default":"ি","rules":[]},{"find":"I`","default":"ী","rules":[]},{"find":"u`","default":"ু","rules":[]},{"find":"U`","default":"ূ","rules":[]},{"find":"ee","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"e`","default":"ে","rules":[]},{"find":":`","default":":","rules":[]},{"find":"^`","default":"^","rules":[]},{"find":",,","default":"্\u200c","rules":[]},{"find":"b","default":"ব","rules":[]},{"find":"v","default":"ভ","rules":[]},{"find":"c","default":"চ","rules":[]},{"find":"D","default":"ড","rules":[]},{"find":"d","default":"দ","rules":[]},{"find":".","default":"।","rules":[{"matches":[{"type":"SuffixIs","scope":"Number"}],"replace":"."}]},{"find":"g","default":"গ","rules":[]},{"find":"G","default":"গ","rules":[]},{"find":"h","default":"হ","rules":[]},{"find":"j","default":"জ","rules":[]},{"find":"J","default":"জ","rules":[]},{"find":"k","default":"ক","rules":[]},{"find":"l","default":"ল","rules":[]},{"find":"m","default":"ম","rules":[]},{"find":"0","default":"০","rules":[]},{"find":"1","default":"১","rules":[]},{"find":"2","default":"২","rules":[]},{"find":"3","default":"৩","rules":[]},{"find":"4","default":"৪","rules":[]},{"find":"5","default":"৫","rules":[]},{"find":"6","default":"৬","rules":[]},{"find":"7","default":"৭","rules":[]},{"find":"8","default":"৮","rules":[]},{"find":"9","default":"৯","rules":[]},{"find":"n","default":"ন","rules":[]},{"find":"N","default":"ণ","rules":[]},{"find":"O","default":"ো","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ও"}]},{"find":"f","default":"ফ","rules":[]},{"find":"p","default":"প","rules":[]},{"find":"R","default":"ড়","rules":[]},{"find":"r","default":"র","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"},{"type":"PrefixIsNot","scope":"Char","val":"Z"}],"replace":"্র"}]},{"find":"s","default":"স","rules":[]},{"find":"S","default":"শ","rules":[]},{"find":"o","default":"","rules":[{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIsNot","scope":"Char","val":"o"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIs","scope":"Char","val":"o"}],"replace":"অ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"অ"}]},{"find":"T","default":"ট","rules":[]},{"find":"t","default":"ত","rules":[]},{"find":"a","default":"া","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"},{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"য়া"},{"matches":[{"type":"PrefixIs","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"}]},{"find":"i","default":"ি","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"}]},{"find":"I","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"u","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"U","default":"ূ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"}]},{"find":"e","default":"ে","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"}]},{"find":"z","default":"য","rules":[]},{"find":"Z","default":"্য","rules":[]},{"find":"y","default":"্য","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Punctuation"}],"replace":"য়"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ইয়"}]},{"find":"Y","default":"য়","rules":[]},{"find":"q","default":"ক","rules":[]},{"find":"w","default":"ও","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIs","scope":"Vowel"}],"replace":"ওয়"},{"matches":[{"type":"PrefixIs","scope":"Consonant"}],"replace":"্ব"}]},{"find":"x","default":"ক্স","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"এক্স"}]},{"find":":","default":"ঃ","rules":[]},{"find":"^","default":"ঁ","rules":[]},{"find":",","default":",","rules":[]},{"find":"$","default":"৳","rules":[]},{"find":"`","default":"","rules":[]}]"""

        const val DICTIONARY_JSON = """{"ami":["আমি","আম","আমায়","আমেরিকায়","আমার"],"amader":["আমাদের","আমোদ","আমড়া"],"amar":["আমার","আমরা","অমর"],"amra":["আমরা"],"amake":["আমাকে"],"tumi":["তুমি","তোমরা","তোমার"],"tomader":["তোমাদের"],"tomar":["তোমার"],"tomake":["তোমাকে"],"tomay":["তোমায়","তোমাকে"],"apni":["আপনি","আপনে","আপ্নি"],"apnader":["আপনাদের"],"apnar":["আপনার"],"apnake":["আপনাকে"],"she":["সে","শে"],"tini":["তিনি"],"tara":["তারা"],"tader":["তাদের"],"taderke":["তাদেরকে"],"ora":["ওরা"],"oder":["ওদের"],"era":["এরা"],"eder":["এদের"],"kemon":["কেমন","কেমনে"],"achen":["আছেন","আছি","আছে"],"achi":["আছি"],"ache":["আছে"],"achilo":["ছিল","আছিল"],"chilo":["ছিল"],"chilam":["ছিলাম"],"chile":["ছিলে"],"chilen":["ছিলেন"],"bhalo":["ভালো","ভাল","ভালা"],"valo":["ভালো","ভাল"],"bhalobashi":["ভালোবাসি","ভালোবাসা"],"valobashi":["ভালোবাসি"],"bhalobasha":["ভালোবাসা","ভালোবাসায়"],"valobasha":["ভালোবাসা"],"dhonnobad":["ধন্যবাদ","ধন্য","ধন"],"bangla":["বাংলা","বাঙলা","বাঙালি","বাংলাদেশ"],"bangladesh":["বাংলাদেশ","বাংলাদেশী"],"banglay":["বাংলায়","বাংলায়","বাঙলায়"],"shonar":["সোনার","শোনার","সুন্দর"],"sonar":["সোনার"],"gan":["গান","গণ","জ্ঞান"],"gai":["গাই","গায়ে"],"bongo":["বঙ্গ","বঙ্গবন্ধু","বঙ্গোপসাগর"],"lekho":["লেখো","লেখা","লেখক"],"likhi":["লিখি"],"likhte":["লিখতে"],"lekha":["লেখা"],"onek":["অনেক","অনেকে","অনুপ"],"shob":["সব","শব","সবাই"],"sob":["সব","সবাই"],"shobai":["সবাই"],"sobai":["সবাই"],"shobar":["সবার","শোবার"],"sobar":["সবার"],"shobaike":["সবাইকে"],"shanti":["শান্তি","শান্ত"],"kolkata":["কলকাতা","কলিকাতা"],"dhaka":["ঢাকা","ঢাকাই","ঢাক"],"robindronath":["রবীন্দ্রনাথ","রবি","রব"],"kazi":["কাজী","কাজি"],"nazrul":["নজরুল"],"koto":["কত","কতো"],"kichu":["কিছু","কিছুই"],"desh":["দেশ","দেশে","দেশের"],"deshe":["দেশে"],"desher":["দেশের"],"manush":["মানুষ","মানুষের","মানুষকে"],"manushe":["মানুষে"],"manusher":["মানুষের"],"bondhu":["বন্ধু","বন্ধুরা","বন্ধুর"],"bondhura":["বন্ধুরা"],"khabar":["খাবার","খবর"],"khobor":["খবর","খবরে"],"shundor":["সুন্দর","সুন্দরী"],"sundor":["সুন্দর"],"ranna":["রান্না","রান্নাঘর"],"kothay":["কোথায়","কথায়"],"shomoy":["সময়","সাময়িক"],"somoy":["সময়"],"protidin":["প্রতিদিন"],"notun":["নতুন","নূতন"],"purono":["পুরোনো","পুরনো"],"shobdo":["শব্দ","শব্দকোষ"],"sobdo":["শব্দ"],"ki":["কি","কী"],"keno":["কেন","কেনো"],"kobe":["কবে"],"kothao":["কোথাও"],"kokhon":["কখন","কখনো"],"ekhon":["এখন","এখনো"],"tokhon":["তখন","তখনো"],"jokhon":["যখন","যখনই"],"ei":["এই"],"oi":["ওই","ঐ"],"shei":["সেই"],"je":["যে","যেসব"],"o":["ও"],"ebong":["এবং"],"ar":["আর","আরও"],"kintu":["কিন্তু"],"ba":["বা"],"othoba":["অথবা"],"na":["না","নাই"],"hacche":["হচ্ছে"],"hocche":["হচ্ছে"],"hobe":["হবে","হবেন"],"hobar":["হবার"],"hoyeche":["হয়েছে"],"kaj":["কাজ","কাজে"],"kaje":["কাজে"],"basha":["বাসা","ভাষা"],"bhasha":["ভাষা","ভাষায়"],"bari":["বাড়ি","বারি"],"ghor":["ঘর","ঘরে"],"boi":["বই","বইয়ের"],"kotha":["কথা","কথায়"],"shune":["শুনে","শুনেছি"],"shunbo":["শুনব","শুনবো"],"shunte":["শুনতে"],"shuni":["শুনি"],"dekhe":["দেখে","দেখেছি"],"dekha":["দেখা","দেখার"],"dekho":["দেখো","দেখ"],"dekhi":["দেখি"],"dekhte":["দেখতে"],"ashun":["আসুন"],"ashbo":["আসব","আসবো"],"ashchi":["আসছি"],"aschi":["আসছি"],"ashlam":["আসলাম"],"jao":["যাও"],"jai":["যাই"],"jacchi":["যাচ্ছি"],"jabo":["যাব","যাবো"],"gelam":["গেলাম"],"geche":["গেছে","গিয়েছে"],"korbo":["করব","করবো"],"korchi":["করছি"],"kori":["করি"],"koro":["করো","কর"],"korben":["করবেন"],"kore":["করে","করেছি"],"korechi":["করেছি"],"shokal":["সকাল","সকালে"],"sokal":["সকাল"],"dupur":["দুপুর","দুপুরে"],"shondha":["সন্ধ্যা","সন্ধ্যায়"],"sondha":["সন্ধ্যা"],"rat":["রাত","রাতে"],"din":["দিন","দিনে"],"mash":["মাস","মাসে"],"bochor":["বছর","বছরে"],"mon":["মন","মনে"],"mone":["মনে","মনেও"],"janina":["জানিনা","জানি না"],"parina":["পারিনা","পারি না"],"pari":["পারি"],"parbo":["পারব","পারবো"],"parbe":["পারবে"],"bhabchi":["ভাবছি"],"bhabi":["ভাবি"],"bhabo":["ভাবো","ভাব"],"bhabte":["ভাবতে"],"khub":["খুব","খুবি"],"shotti":["সত্যি","সত্য"],"sotti":["সত্যি"],"shothik":["সঠিক"],"sothik":["সঠিক"],"bhul":["ভুল","ভুলে"],"thik":["ঠিক","ঠিকই"],"shohoj":["সহজ","সহজে"],"sohoj":["সহজ"],"kothin":["কঠিন"],"shobcheye":["সবচেয়ে","সবচাইতে"],"sobcheye":["সবচেয়ে"],"prothom":["প্রথম","প্রথমে"],"shesh":["শেষ","শেষে"],"shuru":["শুরু","শুরুতে"],"suru":["শুরু"],"subheccha":["শুভেচ্ছা"],"shubheccha":["শুভেচ্ছা"],"shuvo":["শুভ"],"shubh":["শুভ"],"computer":["কম্পিউটার"],"keyboard":["কীবোর্ড","কিবোর্ড"],"software":["সফটওয়্যার","সফটওয়্যার"],"native":["নেটিভ"],"apple":["অ্যাপল","আপেল"],"silicon":["সিলিকন"],"mac":["ম্যাক"],"macos":["ম্যাকওএস"],"macbook":["ম্যাকবুক"],"font":["ফন্ট"],"download":["ডাউনলোড"],"install":["ইনস্টল"],"free":["ফ্রি"],"typing":["টাইপিং"],"bengali":["বাঙালি","বেঙ্গলি"],"mehedi":["মেহেদি","মেহেদী"],"shakeel":["শাকিল","শাকীল"],"hya":["হ্যাঁ","হইয়া","হ্যা"],"hea":["হ্যাঁ","হেয়া"],"cad":["চাঁদ"],"chad":["চাঁদ","ছাদ"],"chada":["চাঁদা","ছাদা"],"pac":["পাঁচ"],"pach":["পাঁচ","পাছ"],"hata":["হাঁটা","হাতা","হাটা"],"hatchi":["হাঁটছি"],"hatte":["হাঁটতে"],"hatahati":["হাঁটাহাটি"],"khuj":["খুঁজ"],"khuja":["খোঁজা","খুঁজা"],"khoja":["খোঁজা"],"khuje":["খুঁজে","খুজে"],"khuji":["খুঁজি"],"khujchi":["খুঁজছি"],"khujcho":["খুঁজছো"],"khujchen":["খুঁজছেন"],"khujte":["খুঁজতে","খুজতে"],"khujbo":["খুঁজব","খুঁজবো"],"dhadha":["ধাঁধা","ধাধা"],"aka":["আঁকা","আকা"],"aki":["আঁকি"],"ake":["আঁকে"],"akchi":["আঁকছি"],"akte":["আঁকতে"],"akbo":["আঁকব","আঁকবো"],"bash":["বাঁশ","বাস","বাশ"],"has":["হাঁস","হাস"],"hash":["হাঁস","হাশ"],"hasi":["হাসি","হাঁসি"],"fapa":["ফাঁপা"],"fad":["ফাঁদ"],"fak":["ফাঁক"],"fashi":["ফাঁসি","ফাসি"],"jhap":["ঝাঁপ"],"chapa":["চাঁপা","চাপা"],"dhoya":["ধোঁয়া","ধোয়া"],"jhok":["ঝোঁক"],"bothe":["বঁটি"],"boti":["বঁটি","বটি"],"kacha":["কাঁচা","কাচা"],"shakha":["শাঁখা","শাখা"],"ghata":["ঘাঁটা","ঘাটা"],"chata":["ছাঁটা","ছাটা"],"gaye":["গাঁয়ে","গায়ে"],"badha":["বাধা","বাঁধা"],"dat":["দাঁত"],"idur":["ইঁদুর"],"katha":["কাঁথা","কথা"],"kathal":["কাঁঠাল"],"baka":["বাঁকা","বাকা"],"khocha":["খোঁচা"],"radha":["রাঁধা","রাধা"],"tak":["টাক","টাঁক"],"chuch":["ছুঁচ","ছুচ"],"jak":["ঝাঁক","যাক"],"taka":["টাকা"],"paka":["পাকা"]}"""
    }
}
