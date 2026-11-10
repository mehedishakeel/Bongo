package app.getbongo.ime.engine

import org.json.JSONArray
import org.json.JSONObject

/**
 * Pure Kotlin Avro phonetic engine.
 * Provides on-device zero-latency transliteration and dictionary lookups,
 * serving as an offline engine and seamless fallback.
 */
class AvroPhoneticEngine {

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
        const val PATTERNS_JSON = """[{"find":"NgkSh","default":"ঙ্ক্ষ","rules":[]},{"find":"Ngkkh","default":"ঙ্ক্ষ","rules":[]},{"find":"kkhN","default":"ক্ষ্ণ","rules":[]},{"find":"kShN","default":"ক্ষ্ণ","rules":[]},{"find":"kkhm","default":"ক্ষ্ম","rules":[]},{"find":"kShm","default":"ক্ষ্ম","rules":[]},{"find":"NGch","default":"ঞ্ছ","rules":[]},{"find":"Nggh","default":"ঙ্ঘ","rules":[]},{"find":"Ngkh","default":"ঙ্খ","rules":[]},{"find":"NGjh","default":"ঞ্ঝ","rules":[]},{"find":"ngOU","default":"ঙ্গৌ","rules":[]},{"find":"ngOI","default":"ঙ্গৈ","rules":[]},{"find":"Ngkx","default":"ঙ্ক্ষ","rules":[]},{"find":"rri`","default":"ৃ","rules":[]},{"find":"shch","default":"শ্ছ","rules":[]},{"find":"ShTh","default":"ষ্ঠ","rules":[]},{"find":"Shph","default":"ষ্ফ","rules":[]},{"find":"psh","default":"পশ","rules":[]},{"find":"bhl","default":"ভ্ল","rules":[]},{"find":"bdh","default":"ব্ধ","rules":[]},{"find":"cNG","default":"চ্ঞ","rules":[]},{"find":"cch","default":"চ্ছ","rules":[]},{"find":"dhn","default":"ধ্ন","rules":[]},{"find":"dhm","default":"ধ্ম","rules":[]},{"find":"dgh","default":"দ্ঘ","rules":[]},{"find":"ddh","default":"দ্ধ","rules":[]},{"find":"dbh","default":"দ্ভ","rules":[]},{"find":"...","default":"...","rules":[]},{"find":"ghn","default":"ঘ্ন","rules":[]},{"find":"Ghn","default":"ঘ্ন","rules":[]},{"find":"gdh","default":"গ্ধ","rules":[]},{"find":"Gdh","default":"গ্ধ","rules":[]},{"find":"jjh","default":"জ্ঝ","rules":[]},{"find":"jNG","default":"জ্ঞ","rules":[]},{"find":"kxN","default":"ক্ষ্ণ","rules":[]},{"find":"kxm","default":"ক্ষ্ম","rules":[]},{"find":"kkh","default":"ক্ষ","rules":[]},{"find":"kSh","default":"ক্ষ","rules":[]},{"find":"ksh","default":"কশ","rules":[]},{"find":"lbh","default":"ল্ভ","rules":[]},{"find":"ldh","default":"ল্ধ","rules":[]},{"find":"lkh","default":"লখ","rules":[]},{"find":"lgh","default":"লঘ","rules":[]},{"find":"lph","default":"লফ","rules":[]},{"find":"mth","default":"ম্থ","rules":[]},{"find":"mph","default":"ম্ফ","rules":[]},{"find":"mbh","default":"ম্ভ","rules":[]},{"find":"mpl","default":"মপ্ল","rules":[]},{"find":"NGc","default":"ঞ্চ","rules":[]},{"find":"nch","default":"ঞ্ছ","rules":[]},{"find":"njh","default":"ঞ্ঝ","rules":[]},{"find":"ngh","default":"ঙ্ঘ","rules":[]},{"find":"Ngk","default":"ঙ্ক","rules":[]},{"find":"Ngx","default":"ঙ্ষ","rules":[]},{"find":"Ngg","default":"ঙ্গ","rules":[]},{"find":"Ngm","default":"ঙ্ম","rules":[]},{"find":"NGj","default":"ঞ্জ","rules":[]},{"find":"ndh","default":"ন্ধ","rules":[]},{"find":"nTh","default":"ন্ঠ","rules":[]},{"find":"NTh","default":"ণ্ঠ","rules":[]},{"find":"nth","default":"ন্থ","rules":[]},{"find":"nkh","default":"ঙ্খ","rules":[]},{"find":"ngo","default":"ঙ্গ","rules":[]},{"find":"nga","default":"ঙ্গা","rules":[]},{"find":"ngi","default":"ঙ্গি","rules":[]},{"find":"ngI","default":"ঙ্গী","rules":[]},{"find":"ngu","default":"ঙ্গু","rules":[]},{"find":"ngU","default":"ঙ্গূ","rules":[]},{"find":"nge","default":"ঙ্গে","rules":[]},{"find":"ngO","default":"ঙ্গো","rules":[]},{"find":"NDh","default":"ণ্ঢ","rules":[]},{"find":"nsh","default":"নশ","rules":[]},{"find":"Ngr","default":"ঙর","rules":[]},{"find":"NGr","default":"ঞর","rules":[]},{"find":"ngr","default":"ংর","rules":[]},{"find":"OI`","default":"ৈ","rules":[]},{"find":"OU`","default":"ৌ","rules":[]},{"find":"phl","default":"ফ্ল","rules":[]},{"find":"rri","default":"ৃ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঋ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঋ"}]},{"find":"rrZ","default":"রর\u200d্য","rules":[]},{"find":"rry","default":"রর\u200d্য","rules":[]},{"find":"Sch","default":"শ্ছ","rules":[]},{"find":"skl","default":"স্ক্ল","rules":[]},{"find":"skh","default":"স্খ","rules":[]},{"find":"sth","default":"স্থ","rules":[]},{"find":"sph","default":"স্ফ","rules":[]},{"find":"shc","default":"শ্চ","rules":[]},{"find":"sht","default":"শ্ত","rules":[]},{"find":"shn","default":"শ্ন","rules":[]},{"find":"shm","default":"শ্ম","rules":[]},{"find":"shl","default":"শ্ল","rules":[]},{"find":"Shk","default":"ষ্ক","rules":[]},{"find":"ShT","default":"ষ্ট","rules":[]},{"find":"ShN","default":"ষ্ণ","rules":[]},{"find":"Shp","default":"ষ্প","rules":[]},{"find":"Shf","default":"ষ্ফ","rules":[]},{"find":"Shm","default":"ষ্ম","rules":[]},{"find":"spl","default":"স্প্ল","rules":[]},{"find":"oo`","default":"ু","rules":[]},{"find":"tth","default":"ত্থ","rules":[]},{"find":"t``","default":"ৎ","rules":[]},{"find":"ee`","default":"ী","rules":[]},{"find":"bj","default":"ব্জ","rules":[]},{"find":"bd","default":"ব্দ","rules":[]},{"find":"bb","default":"ব্ব","rules":[]},{"find":"bl","default":"ব্ল","rules":[]},{"find":"bh","default":"ভ","rules":[]},{"find":"vl","default":"ভ্ল","rules":[]},{"find":"cc","default":"চ্চ","rules":[]},{"find":"ch","default":"ছ","rules":[]},{"find":"dv","default":"দ্ভ","rules":[]},{"find":"dm","default":"দ্ম","rules":[]},{"find":"DD","default":"ড্ড","rules":[]},{"find":"Dh","default":"ঢ","rules":[]},{"find":"dh","default":"ধ","rules":[]},{"find":"dg","default":"দ্গ","rules":[]},{"find":"dd","default":"দ্দ","rules":[]},{"find":".`","default":".","rules":[]},{"find":"..","default":"।।","rules":[]},{"find":"gN","default":"গ্ণ","rules":[]},{"find":"GN","default":"গ্ণ","rules":[]},{"find":"gn","default":"গ্ন","rules":[]},{"find":"Gn","default":"গ্ন","rules":[]},{"find":"gm","default":"গ্ম","rules":[]},{"find":"Gm","default":"গ্ম","rules":[]},{"find":"gl","default":"গ্ল","rules":[]},{"find":"Gl","default":"গ্ল","rules":[]},{"find":"gg","default":"জ্ঞ","rules":[]},{"find":"GG","default":"জ্ঞ","rules":[]},{"find":"Gg","default":"জ্ঞ","rules":[]},{"find":"gG","default":"জ্ঞ","rules":[]},{"find":"gh","default":"ঘ","rules":[]},{"find":"Gh","default":"ঘ","rules":[]},{"find":"hN","default":"হ্ণ","rules":[]},{"find":"hn","default":"হ্ন","rules":[]},{"find":"hm","default":"হ্ম","rules":[]},{"find":"hl","default":"হ্ল","rules":[]},{"find":"jh","default":"ঝ","rules":[]},{"find":"jj","default":"জ্জ","rules":[]},{"find":"kx","default":"ক্ষ","rules":[]},{"find":"kk","default":"ক্ক","rules":[]},{"find":"kT","default":"ক্ট","rules":[]},{"find":"kt","default":"ক্ত","rules":[]},{"find":"kl","default":"ক্ল","rules":[]},{"find":"ks","default":"ক্স","rules":[]},{"find":"kh","default":"খ","rules":[]},{"find":"lk","default":"ল্ক","rules":[]},{"find":"lg","default":"ল্গ","rules":[]},{"find":"lT","default":"ল্ট","rules":[]},{"find":"lD","default":"ল্ড","rules":[]},{"find":"lp","default":"ল্প","rules":[]},{"find":"lv","default":"ল্ভ","rules":[]},{"find":"lm","default":"ল্ম","rules":[]},{"find":"ll","default":"ল্ল","rules":[]},{"find":"lb","default":"ল্ব","rules":[]},{"find":"mn","default":"ম্ন","rules":[]},{"find":"mp","default":"ম্প","rules":[]},{"find":"mv","default":"ম্ভ","rules":[]},{"find":"mm","default":"ম্ম","rules":[]},{"find":"ml","default":"ম্ল","rules":[]},{"find":"mb","default":"ম্ব","rules":[]},{"find":"mf","default":"ম্ফ","rules":[]},{"find":"nj","default":"ঞ্জ","rules":[]},{"find":"Ng","default":"ঙ","rules":[]},{"find":"NG","default":"ঞ","rules":[]},{"find":"nk","default":"ঙ্ক","rules":[]},{"find":"ng","default":"ং","rules":[]},{"find":"nn","default":"ন্ন","rules":[]},{"find":"NN","default":"ণ্ণ","rules":[]},{"find":"Nn","default":"ণ্ন","rules":[]},{"find":"nm","default":"ন্ম","rules":[]},{"find":"Nm","default":"ণ্ম","rules":[]},{"find":"nd","default":"ন্দ","rules":[]},{"find":"nT","default":"ন্ট","rules":[]},{"find":"NT","default":"ণ্ট","rules":[]},{"find":"nD","default":"ন্ড","rules":[]},{"find":"ND","default":"ণ্ড","rules":[]},{"find":"nt","default":"ন্ত","rules":[]},{"find":"ns","default":"ন্স","rules":[]},{"find":"nc","default":"ঞ্চ","rules":[]},{"find":"O`","default":"ো","rules":[]},{"find":"OI","default":"ৈ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঐ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঐ"}]},{"find":"OU","default":"ৌ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ঔ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ঔ"}]},{"find":"pT","default":"প্ট","rules":[]},{"find":"pt","default":"প্ত","rules":[]},{"find":"pn","default":"প্ন","rules":[]},{"find":"pp","default":"প্প","rules":[]},{"find":"pl","default":"প্ল","rules":[]},{"find":"ps","default":"প্স","rules":[]},{"find":"ph","default":"ফ","rules":[]},{"find":"fl","default":"ফ্ল","rules":[]},{"find":"rZ","default":"র\u200d্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"ry","default":"র\u200d্য","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"}],"replace":"্র্য"}]},{"find":"rr","default":"রর","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Vowel"},{"type":"SuffixIsNot","scope":"Char","val":"r"},{"type":"SuffixIsNot","scope":"Punctuation"}],"replace":"র্"},{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"}],"replace":"্রর"}]},{"find":"Rg","default":"ড়্গ","rules":[]},{"find":"Rh","default":"ঢ়","rules":[]},{"find":"sk","default":"স্ক","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"sT","default":"স্ট","rules":[]},{"find":"st","default":"স্ত","rules":[]},{"find":"sn","default":"স্ন","rules":[]},{"find":"sp","default":"স্প","rules":[]},{"find":"sf","default":"স্ফ","rules":[]},{"find":"sm","default":"স্ম","rules":[]},{"find":"sl","default":"স্ল","rules":[]},{"find":"sh","default":"শ","rules":[]},{"find":"Sc","default":"শ্চ","rules":[]},{"find":"St","default":"শ্ত","rules":[]},{"find":"Sn","default":"শ্ন","rules":[]},{"find":"Sm","default":"শ্ম","rules":[]},{"find":"Sl","default":"শ্ল","rules":[]},{"find":"Sh","default":"ষ","rules":[]},{"find":"oo","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"o`","default":"","rules":[]},{"find":"oZ","default":"অ্য","rules":[]},{"find":"TT","default":"ট্ট","rules":[]},{"find":"Tm","default":"ট্ম","rules":[]},{"find":"Th","default":"ঠ","rules":[]},{"find":"tn","default":"ত্ন","rules":[]},{"find":"tm","default":"ত্ম","rules":[]},{"find":"th","default":"থ","rules":[]},{"find":"tt","default":"ত্ত","rules":[]},{"find":"aZ","default":"অ্যা","rules":[]},{"find":"AZ","default":"অ্যা","rules":[]},{"find":"a`","default":"া","rules":[]},{"find":"A`","default":"া","rules":[]},{"find":"i`","default":"ি","rules":[]},{"find":"I`","default":"ী","rules":[]},{"find":"u`","default":"ু","rules":[]},{"find":"U`","default":"ূ","rules":[]},{"find":"ee","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"e`","default":"ে","rules":[]},{"find":":`","default":":","rules":[]},{"find":"^`","default":"^","rules":[]},{"find":",,","default":"্\u200c","rules":[]},{"find":"b","default":"ব","rules":[]},{"find":"v","default":"ভ","rules":[]},{"find":"c","default":"চ","rules":[]},{"find":"D","default":"ড","rules":[]},{"find":"d","default":"দ","rules":[]},{"find":".","default":"।","rules":[{"matches":[{"type":"SuffixIs","scope":"Number"}],"replace":"."}]},{"find":"g","default":"গ","rules":[]},{"find":"G","default":"গ","rules":[]},{"find":"h","default":"হ","rules":[]},{"find":"j","default":"জ","rules":[]},{"find":"J","default":"জ","rules":[]},{"find":"k","default":"ক","rules":[]},{"find":"l","default":"ল","rules":[]},{"find":"m","default":"ম","rules":[]},{"find":"0","default":"০","rules":[]},{"find":"1","default":"১","rules":[]},{"find":"2","default":"২","rules":[]},{"find":"3","default":"৩","rules":[]},{"find":"4","default":"৪","rules":[]},{"find":"5","default":"৫","rules":[]},{"find":"6","default":"৬","rules":[]},{"find":"7","default":"৭","rules":[]},{"find":"8","default":"৮","rules":[]},{"find":"9","default":"৯","rules":[]},{"find":"n","default":"ন","rules":[]},{"find":"N","default":"ণ","rules":[]},{"find":"O","default":"ো","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ও"}]},{"find":"f","default":"ফ","rules":[]},{"find":"p","default":"প","rules":[]},{"find":"R","default":"ড়","rules":[]},{"find":"r","default":"র","rules":[{"matches":[{"type":"PrefixIs","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"r"},{"type":"PrefixIsNot","scope":"Char","val":"y"},{"type":"PrefixIsNot","scope":"Char","val":"w"},{"type":"PrefixIsNot","scope":"Char","val":"x"},{"type":"PrefixIsNot","scope":"Char","val":"Z"}],"replace":"্র"}]},{"find":"s","default":"স","rules":[]},{"find":"S","default":"শ","rules":[]},{"find":"o","default":"","rules":[{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIsNot","scope":"Char","val":"o"}],"replace":"ও"},{"matches":[{"type":"PrefixIs","scope":"Vowel"},{"type":"PrefixIs","scope":"Char","val":"o"}],"replace":"অ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"অ"}]},{"find":"T","default":"ট","rules":[]},{"find":"t","default":"ত","rules":[]},{"find":"a","default":"া","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"},{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"য়া"},{"matches":[{"type":"PrefixIs","scope":"Char","val":"a"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"আ"}]},{"find":"i","default":"ি","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ই"}]},{"find":"I","default":"ী","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঈ"}]},{"find":"u","default":"ু","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"উ"}]},{"find":"U","default":"ূ","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"ঊ"}]},{"find":"e","default":"ে","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIsNot","scope":"Char","val":"`"}],"replace":"এ"}]},{"find":"z","default":"য","rules":[]},{"find":"Z","default":"্য","rules":[]},{"find":"y","default":"্য","rules":[{"matches":[{"type":"PrefixIsNot","scope":"Consonant"},{"type":"PrefixIsNot","scope":"Punctuation"}],"replace":"য়"},{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"ইয়"}]},{"find":"Y","default":"য়","rules":[]},{"find":"q","default":"ক","rules":[]},{"find":"w","default":"ও","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"},{"type":"SuffixIs","scope":"Vowel"}],"replace":"ওয়"},{"matches":[{"type":"PrefixIs","scope":"Consonant"}],"replace":"্ব"}]},{"find":"x","default":"ক্স","rules":[{"matches":[{"type":"PrefixIs","scope":"Punctuation"}],"replace":"এক্স"}]},{"find":":","default":"ঃ","rules":[]},{"find":"^","default":"ঁ","rules":[]},{"find":",","default":",","rules":[]},{"find":"$","default":"৳","rules":[]},{"find":"`","default":"","rules":[]}]"""

        const val DICTIONARY_JSON = """{"ami":["আমি","আম","আমায়","আমেরিকায়","আমার"],"amader":["আমাদের","আমোদ","আমড়া"],"amar":["আমার","আমরা","অমর"],"amra":["আমরা"],"amake":["আমাকে"],"tumi":["তুমি","তোমরা","তোমার"],"tomader":["তোমাদের"],"tomar":["তোমার"],"tomake":["তোমাকে"],"tomay":["তোমায়","তোমাকে"],"apni":["আপনি","আপনে","আপ্নি"],"apnader":["আপনাদের"],"apnar":["আপনার"],"apnake":["আপনাকে"],"she":["সে","শে"],"tini":["তিনি"],"tara":["তারা"],"tader":["তাদের"],"taderke":["তাদেরকে"],"ora":["ওরা"],"oder":["ওদের"],"era":["এরা"],"eder":["এদের"],"kemon":["কেমন","কেমনে"],"achen":["আছেন","আছি","আছে"],"achi":["আছি"],"ache":["আছে"],"achilo":["ছিল","আছিল"],"chilo":["ছিল"],"chilam":["ছিলাম"],"chile":["ছিলে"],"chilen":["ছিলেন"],"bhalo":["ভালো","ভাল","ভালা"],"valo":["ভালো","ভাল"],"bhalobashi":["ভালোবাসি","ভালোবাসা"],"valobashi":["ভালোবাসি"],"bhalobasha":["ভালোবাসা","ভালোবাসায়"],"valobasha":["ভালোবাসা"],"dhonnobad":["ধন্যবাদ","ধন্য","ধন"],"bangla":["বাংলা","বাঙলা","বাঙালি","বাংলাদেশ"],"bangladesh":["বাংলাদেশ","বাংলাদেশী"],"banglay":["বাংলায়","বাংলায়","বাঙলায়"],"shonar":["সোনার","শোনার","সুন্দর"],"sonar":["সোনার"],"gan":["গান","গণ","জ্ঞান"],"gai":["গাই","গায়ে"],"bongo":["বঙ্গ","বঙ্গবন্ধু","বঙ্গোপসাগর"],"lekho":["লেখো","লেখা","লেখক"],"likhi":["লিখি"],"likhte":["লিখতে"],"lekha":["লেখা"],"onek":["অনেক","অনেকে","অনুপ"],"shob":["সব","শব","সবাই"],"sob":["সব","সবাই"],"shobai":["সবাই"],"sobai":["সবাই"],"shobar":["সবার","শোবার"],"sobar":["সবার"],"shobaike":["সবাইকে"],"shanti":["শান্তি","শান্ত"],"kolkata":["কলকাতা","কলিকাতা"],"dhaka":["ঢাকা","ঢাকাই","ঢাক"],"robindronath":["রবীন্দ্রনাথ","রবি","রব"],"kazi":["কাজী","কাজি"],"nazrul":["নজরুল"],"koto":["কত","কতো"],"kichu":["কিছু","কিছুই"],"desh":["দেশ","দেশে","দেশের"],"deshe":["দেশে"],"desher":["দেশের"],"manush":["মানুষ","মানুষের","মানুষকে"],"manushe":["মানুষে"],"manusher":["মানুষের"],"bondhu":["বন্ধু","বন্ধুরা","বন্ধুর"],"bondhura":["বন্ধুরা"],"khabar":["খাবার","খবর"],"khobor":["খবর","খবরে"],"shundor":["সুন্দর","সুন্দরী"],"sundor":["সুন্দর"],"ranna":["রান্না","রান্নাঘর"],"kothay":["কোথায়","কথায়"],"shomoy":["সময়","সাময়িক"],"somoy":["সময়"],"protidin":["প্রতিদিন"],"notun":["নতুন","নূতন"],"purono":["পুরোনো","পুরনো"],"shobdo":["শব্দ","শব্দকোষ"],"sobdo":["শব্দ"],"ki":["কি","কী"],"keno":["কেন","কেনো"],"kobe":["কবে"],"kothao":["কোথাও"],"kokhon":["কখন","কখনো"],"ekhon":["এখন","এখনো"],"tokhon":["তখন","তখনো"],"jokhon":["যখন","যখনই"],"ei":["এই"],"oi":["ওই","ঐ"],"shei":["সেই"],"je":["যে","যেসব"],"o":["ও"],"ebong":["এবং"],"ar":["আর","আরও"],"kintu":["কিন্তু"],"ba":["বা"],"othoba":["অথবা"],"na":["না","নাই"],"hacche":["হচ্ছে"],"hocche":["হচ্ছে"],"hobe":["হবে","হবেন"],"hobar":["হবার"],"hoyeche":["হয়েছে"],"kaj":["কাজ","কাজে"],"kaje":["কাজে"],"basha":["বাসা","ভাষা"],"bhasha":["ভাষা","ভাষায়"],"bari":["বাড়ি","বারি"],"ghor":["ঘর","ঘরে"],"boi":["বই","বইয়ের"],"kotha":["কথা","কথায়"],"shune":["শুনে","শুনেছি"],"shunbo":["শুনব","শুনবো"],"shunte":["শুনতে"],"shuni":["শুনি"],"dekhe":["দেখে","দেখেছি"],"dekha":["দেখা","দেখার"],"dekho":["দেখো","দেখ"],"dekhi":["দেখি"],"dekhte":["দেখতে"],"ashun":["আসুন"],"ashbo":["আসব","আসবো"],"ashchi":["আসছি"],"aschi":["আসছি"],"ashlam":["আসলাম"],"jao":["যাও"],"jai":["যাই"],"jacchi":["যাচ্ছি"],"jabo":["যাব","যাবো"],"gelam":["গেলাম"],"geche":["গেছে","গিয়েছে"],"korbo":["করব","করবো"],"korchi":["করছি"],"kori":["করি"],"koro":["করো","কর"],"korben":["করবেন"],"kore":["করে","করেছি"],"korechi":["করেছি"],"shokal":["সকাল","সকালে"],"sokal":["সকাল"],"dupur":["দুপুর","দুপুরে"],"shondha":["সন্ধ্যা","সন্ধ্যায়"],"sondha":["সন্ধ্যা"],"rat":["রাত","রাতে"],"din":["দিন","দিনে"],"mash":["মাস","মাসে"],"bochor":["বছর","বছরে"],"mon":["মন","মনে"],"mone":["মনে","মনেও"],"janina":["জানিনা","জানি না"],"parina":["পারিনা","পারি না"],"pari":["পারি"],"parbo":["পারব","পারবো"],"parbe":["পারবে"],"bhabchi":["ভাবছি"],"bhabi":["ভাবি"],"bhabo":["ভাবো","ভাব"],"bhabte":["ভাবতে"],"khub":["খুব","খুবি"],"shotti":["সত্যি","সত্য"],"sotti":["সত্যি"],"shothik":["সঠিক"],"sothik":["সঠিক"],"bhul":["ভুল","ভুলে"],"thik":["ঠিক","ঠিকই"],"shohoj":["সহজ","সহজে"],"sohoj":["সহজ"],"kothin":["কঠিন"],"shobcheye":["সবচেয়ে","সবচাইতে"],"sobcheye":["সবচেয়ে"],"prothom":["প্রথম","প্রথমে"],"shesh":["শেষ","শেষে"],"shuru":["শুরু","শুরুতে"],"suru":["শুরু"],"subheccha":["শুভেচ্ছা"],"shubheccha":["শুভেচ্ছা"],"shuvo":["শুভ"],"shubh":["শুভ"],"computer":["কম্পিউটার"],"keyboard":["কীবোর্ড","কিবোর্ড"],"software":["সফটওয়্যার","সফটওয়্যার"],"native":["নেটিভ"],"apple":["অ্যাপল","আপেল"],"silicon":["সিলিকন"],"mac":["ম্যাক"],"macos":["ম্যাকওএস"],"macbook":["ম্যাকবুক"],"font":["ফন্ট"],"download":["ডাউনলোড"],"install":["ইনস্টল"],"free":["ফ্রি"],"typing":["টাইপিং"],"bengali":["বাঙালি","বেঙ্গলি"],"mehedi":["মেহেদি","মেহেদী"],"shakeel":["শাকিল","শাকীল"],"hya":["হ্যাঁ","হইয়া","হ্যা"],"hea":["হ্যাঁ","হেয়া"],"cad":["চাঁদ"],"chad":["চাঁদ","ছাদ"],"chada":["চাঁদা","ছাদা"],"pac":["পাঁচ"],"pach":["পাঁচ","পাছ"],"hata":["হাঁটা","হাতা","হাটা"],"hatchi":["হাঁটছি"],"hatte":["হাঁটতে"],"hatahati":["হাঁটাহাটি"],"khuj":["খুঁজ"],"khuja":["খোঁজা","খুঁজা"],"khoja":["খোঁজা"],"khuje":["খুঁজে","খুজে"],"khuji":["খুঁজি"],"khujchi":["খুঁজছি"],"khujcho":["খুঁজছো"],"khujchen":["খুঁজছেন"],"khujte":["খুঁজতে","খুজতে"],"khujbo":["খুঁজব","খুঁজবো"],"dhadha":["ধাঁধা","ধাধা"],"aka":["আঁকা","আকা"],"aki":["আঁকি"],"ake":["আঁকে"],"akchi":["আঁকছি"],"akte":["আঁকতে"],"akbo":["আঁকব","আঁকবো"],"bash":["বাঁশ","বাস","বাশ"],"has":["হাঁস","হাস"],"hash":["হাঁস","হাশ"],"hasi":["হাসি","হাঁসি"],"fapa":["ফাঁপা"],"fad":["ফাঁদ"],"fak":["ফাঁক"],"fashi":["ফাঁসি","ফাসি"],"jhap":["ঝাঁপ"],"chapa":["চাঁপা","চাপা"],"dhoya":["ধোঁয়া","ধোয়া"],"jhok":["ঝোঁক"],"bothe":["বঁটি"],"boti":["বঁটি","বটি"],"kacha":["কাঁচা","কাচা"],"shakha":["শাঁখা","শাখা"],"ghata":["ঘাঁটা","ঘাটা"],"chata":["ছাঁটা","ছাটা"],"gaye":["গাঁয়ে","গায়ে"],"badha":["বাধা","বাঁধা"],"dat":["দাঁত"],"idur":["ইঁদুর"],"katha":["কাঁথা","কথা"],"kathal":["কাঁঠাল"]}"""
    }
}
