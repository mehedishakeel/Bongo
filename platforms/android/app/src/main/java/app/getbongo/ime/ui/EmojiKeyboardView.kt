package app.getbongo.ime.ui

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.StateListDrawable
import android.util.AttributeSet
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import app.getbongo.ime.model.ThemePalette
import org.json.JSONArray

/**
 * Modern, smooth, categorized Emoji and Kaomoji Sticker picker panel for Bongo IME.
 * Features built-in categories: Recent, Smileys, Gestures, Symbols, Nature, Food, and Stickers (Kaomoji),
 * with persistent on-device recent emoji memory.
 */
class EmojiKeyboardView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : LinearLayout(context, attrs, defStyleAttr) {

    var onEmojiSelected: ((String) -> Unit)? = null
    var onBackToKeyboard: (() -> Unit)? = null
    var onBackspace: (() -> Unit)? = null
    var onStartTypeSearch: (() -> Unit)? = null

    private var selectedCategoryIndex = 0
    private var activeSearchTag: String = ""
    private val categoryBar = LinearLayout(context)
    private val emojiContainer = LinearLayout(context)
    private val scrollView = ScrollView(context)
    private var currentPalette: ThemePalette = ThemePalette.getPalette("midnight")

    private val emojiPrefs = context.getSharedPreferences("bongo_emoji_prefs", Context.MODE_PRIVATE)

    companion object {
        private const val KEY_RECENTS = "recent_emojis"
        private val DEFAULT_RECENTS = listOf(
            "❤️", "😂", "👍", "😊", "🔥", "✨", "🙏", "😍", "🎉", "👏",
            "🇧🇩", "🥰", "🥺", "🤣", "🙌", "💯", "💖", "😎", "🤝", "☕", "✌️"
        )

        /**
         * Bilingual (Bengali script, phonetic Bangla, and English) emoji keyword index.
         */
        private val EMOJI_KEYWORDS: List<Pair<List<String>, List<String>>> = listOf(
            listOf("ভালোবাসা", "প্রেম", "ভালোবাসি", "মন", "হৃদয়", "love", "valobasha", "bhalobasha", "heart", "prem", "mon", "crush") to
                listOf("❤️", "💖", "💕", "😍", "🥰", "😘", "💘", "💝", "💓", "💗", "🫶", "💞"),
            listOf("হাসি", "খুশি", "মজা", "আনন্দ", "হাহা", "laugh", "hasi", "hashi", "smile", "happy", "khushi", "haha", "lol", "fun") to
                listOf("😂", "🤣", "😄", "😁", "😊", "😆", "🥳", "😎", "😃", "🤩", "😇"),
            listOf("দুঃখ", "কান্না", "কষ্ট", "মন খারাপ", "sad", "dukkho", "kanna", "cry", "kosto", "broken", "tear") to
                listOf("😢", "😭", "😔", "😞", "🥺", "💔", "😓", "😩", "😫", "😿"),
            listOf("রাগ", "বিরক্ত", "গুসসা", "angry", "rag", "raog", "mad", "birokto", "annoyed") to
                listOf("😡", "😠", "🤬", "😤", "💢", "🙄", "😒"),
            listOf("বাংলাদেশ", "বঙ্গ", "দেশ", "পতাকা", "ঢাকা", "টাকা", "bangladesh", "bongo", "bd", "desh", "dhaka", "taka", "flag") to
                listOf("🇧🇩", "🕌", "🌾", "🐯", "🌺", "৳", "🏏", "🏆", "✨"),
            listOf("দোয়া", "নামাজ", "ঈদ", "আল্লাহ", "মসজিদ", "সালাম", "ধন্যবাদ", "dua", "dowa", "namaz", "eid", "allah", "mosque", "salam", "pray", "thanks", "dhonnobad") to
                listOf("🙏", "🤲", "🕌", "🌙", "✨", "🤝", "💖", "🌟"),
            listOf("আগুন", "জোশ", "সেরা", "অসাধারণ", "দারুণ", "fire", "agun", "lit", "josh", "sera", "awesome", "darun", "100") to
                listOf("🔥", "💯", "⚡", "💥", "🚀", "🌟", "👑", "🤩"),
            listOf("শুভেচ্ছা", "উৎসব", "জন্মদিন", "অভিনন্দন", "পার্টি", "জয়", "congrats", "shuveccha", "birthday", "jonmodin", "party", "celebrate", "win") to
                listOf("🎉", "🎊", "🎂", "🎁", "🎈", "👏", "🙌", "🏆", "🥇", "✌️"),
            listOf("চা", "কফি", "খাবার", "ভাত", "আম", "মিষ্টি", "বিরিয়ানি", "ক্ষুধা", "tea", "cha", "coffee", "food", "khabar", "mango", "aam", "pizza", "burger", "cake", "hungry") to
                listOf("☕", "🍵", "🧋", "🍔", "🍕", "🥭", "🎂", "🍦", "🍩", "🍫", "🥪"),
            listOf("বৃষ্টি", "মেঘ", "আকাশ", "রোদ", "সূর্য", "চাঁদ", "শীত", "rain", "brishti", "cloud", "megh", "sun", "surjo", "moon", "chand", "weather", "cold") to
                listOf("🌧️", "☁️", "🌈", "☀️", "🌙", "⭐", "❄️", "⚡", "☂️"),
            listOf("ফুল", "গাছ", "প্রকৃতি", "বাগান", "পাখি", "বিড়াল", "বাঘ", "flower", "ful", "phul", "rose", "golap", "nature", "cat", "biral", "tiger", "bagh", "bird", "pakhi") to
                listOf("🌹", "🌺", "🌸", "🌻", "🌷", "🌿", "🍀", "🦋", "🐱", "🐯", "🐦"),
            listOf("কাজ", "অফিস", "কম্পিউটার", "ফোন", "বই", "পড়া", "টাকা", "work", "kaj", "office", "laptop", "code", "phone", "book", "boi", "study", "money", "taka") to
                listOf("💻", "📱", "📚", "✏️", "💡", "৳", "💲", "⏰", "🔔"),
            listOf("গান", "সঙ্গীত", "খেলা", "ক্রিকেট", "ফুটবল", "সিনেমা", "music", "gaan", "gan", "song", "cricket", "football", "game", "movie") to
                listOf("🎵", "🎶", "🎧", "🎤", "🏏", "⚽", "🎮", "🎬"),
            listOf("হাত", "ঠিক", "হ্যাঁ", "না", "ভালো", "ওকে", "তালি", "hand", "ok", "yes", "no", "bhalo", "good", "thumbs", "clap", "taali", "bye") to
                listOf("👍", "👌", "👏", "🙌", "👋", "🤝", "✌️", "🤞", "👎", "❌", "✅"),
            listOf("ঘুম", "রাত", "ক্লান্ত", "অসুস্থ", "জ্বর", "sleep", "ghum", "night", "rat", "tired", "sick", "osustho", "fever", "jor") to
                listOf("😴", "🥱", "💤", "🌙", "🤒", "😷", "🤧", "🏥"),
            listOf("ভ্রমণ", "গাড়ি", "ট্রেন", "বিমান", "রাস্তা", "travel", "car", "gari", "train", "bus", "flight", "plane") to
                listOf("🚗", "🚌", "🚆", "✈️", "🚀", "🗺️")
        )

        private val QUICK_SEARCH_CHIPS: List<Pair<String, String>> = listOf(
            "সব" to "",
            "❤️ ভালোবাসা" to "ভালোবাসা",
            "😂 হাসি" to "হাসি",
            "😢 দুঃখ" to "দুঃখ",
            "🙏 দোয়া" to "দোয়া",
            "🇧🇩 বাংলাদেশ" to "বাংলাদেশ",
            "🔥 আগুন" to "আগুন",
            "🎉 শুভেচ্ছা" to "শুভেচ্ছা",
            "☕ চা" to "চা",
            "🌧️ বৃষ্টি" to "বৃষ্টি",
            "🌸 ফুল" to "ফুল",
            "💻 কাজ" to "কাজ"
        )

        /**
         * Searches emojis matching [query] or [banglaQuery] across Bengali, phonetic, and English tags.
         * Returns popular defaults when both queries are blank.
         */
        fun searchEmojis(query: String, banglaQuery: String = ""): List<String> {
            val q1 = query.trim().lowercase()
            val q2 = banglaQuery.trim().lowercase()
            if (q1.isEmpty() && q2.isEmpty()) {
                return DEFAULT_RECENTS
            }
            val results = linkedSetOf<String>()
            // Exact or prefix matches first, then substring matches
            for ((keywords, emojis) in EMOJI_KEYWORDS) {
                val exactOrPrefix = keywords.any { kw ->
                    (q1.isNotEmpty() && kw.startsWith(q1)) || (q2.isNotEmpty() && kw.startsWith(q2))
                }
                if (exactOrPrefix) results.addAll(emojis)
            }
            for ((keywords, emojis) in EMOJI_KEYWORDS) {
                val contains = keywords.any { kw ->
                    (q1.isNotEmpty() && (kw.contains(q1) || q1.contains(kw))) ||
                    (q2.isNotEmpty() && (kw.contains(q2) || q2.contains(kw)))
                }
                if (contains) results.addAll(emojis)
            }
            return results.toList()
        }

        val CATEGORIES = listOf(
            Category("Recent", "🕒", emptyList(), isRecent = true),
            Category("Search", "🔍", emptyList(), isSearch = true),
            Category("Smileys", "😀", listOf(
                "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🥲", "☺️",
                "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗",
                "😙", "😚", "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓",
                "😎", "🥸", "🤩", "🥳", "😏", "😒", "😞", "😔", "😟", "😕",
                "🙁", "😣", "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠",
                "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥",
                "😓", "🤗", "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬",
                "🙄", "😯", "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪",
                "😵", "🤐", "🥴", "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑",
                "🤠", "😈", "👿", "👻", "💀", "👽", "🤖", "💩"
            )),
            Category("Gestures", "👍", listOf(
                "👍", "👎", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💅",
                "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞",
                "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "✊",
                "👊", "🤛", "🤜", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "👃",
                "👀", "👁️", "👅", "👄", "🧠", "🫀", "🫁", "🦴", "🦷", "🫂",
                "🏃", "🚶", "💃", "🕺", "🙇", "🤦", "🤷"
            )),
            Category("Symbols", "🔣", listOf(
                "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
                "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "✨",
                "⭐", "🌟", "💫", "🔥", "💥", "💯", "💢", "🎉", "🎊", "🎈",
                "✔️", "✅", "❌", "❎", "⚠️", "⛔", "🚫", "❓", "❗", "💤",
                "➕", "➖", "✖️", "➗", "💲", "৳", "₹", "€", "£", "¥",
                "©️", "®️", "™️", "🆗", "🆙", "🆒", "🆕", "🆓",
                "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
                "#️⃣", "*️⃣", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪",
                "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "⬛", "⬜",
                "🔻", "🔺", "🔹", "🔸", "🔷", "🔶"
            )),
            Category("Nature", "🌸", listOf(
                "🌺", "🌸", "🌹", "🌷", "🌼", "🌻", "🌾", "🌿", "🍀", "🍁",
                "🍂", "🍃", "☀️", "🌙", "☁️", "🌧️", "❄️", "⚡", "🌈", "⭐",
                "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
                "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🦅", "🦉",
                "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🐞",
                "🐢", "🐍", "🐬", "🐳", "🐟"
            )),
            Category("Food", "🍔", listOf(
                "🇧🇩", "☕", "🍵", "🧃", "🥤", "🧋", "🍕", "🍔", "🍟", "🍎",
                "🥭", "🍌", "🍉", "🍇", "🍓", "🏏", "⚽", "🏀", "🏆", "🥇",
                "🎯", "🎲", "🎮", "🚗", "🚌", "🚆", "✈️", "🚀", "💡", "📱",
                "💻", "📚", "✏️", "🔔", "🎵", "🎶", "🎤", "🎧", "🎬", "🕌",
                "🥪", "🌭", "🍿", "🍩", "🍦", "🎂", "🍫"
            )),
            Category("Stickers", "🎭", listOf(
                "(✿◠‿◠)", "( ͡° ͜ʖ ͡°)", "¯\\_(ツ)_/¯", "(╯°□°)╯︵ ┻━┻",
                "(づ｡◕‿‿◕｡)づ", "ʕ•ᴥ•ʔ", "(>_<)", "(^_^)/",
                "(T_T)", "(♥_♥)", "(•‿•)", "(¬_¬)",
                "(ง'̀-'́)ง", "(｡♥‿♥｡)", "＼(＾O＾)／", "(°o°)",
                "(¬‿¬)", "(ó_ò)", "(•_•)", "(•_•)ゝ",
                "(ง ͠° ͟ل͜ ͡°)ง", "ಠ_ಠ", "(ര_ര)", "(ಥ﹏ಥ)",
                "(づ￣ ³￣)づ", "ヘ( ^o^)ノ", "(づ｡◕‿◕｡)づ", "(っ˘з(˘⌣˘ )",
                "(•ω•)", "(｡◕‿◕｡)", "(~˘▾˘)~", "(づ◡﹏◡)づ",
                "(^з^)-☆", "(*^▽^*)", "(=^･^=)", "(•̀ᴗ•́)و ̑̑",
                "٩(◕‿◕｡)۶", "(⁄ ⁄•⁄ω⁄•⁄ ⁄)", "(◡‿◡✿)", "(◕‿◕✿)"
            ), isSticker = true)
        )
    }

    data class Category(
        val name: String,
        val icon: String,
        val emojis: List<String>,
        val isRecent: Boolean = false,
        val isSearch: Boolean = false,
        val isSticker: Boolean = false
    )

    init {
        orientation = VERTICAL
        setBackgroundColor(currentPalette.surfaceColor)

        setupCategoryBar()
        setupScrollView()
        setupBottomBar()

        loadCategory(0)
    }

    fun applyTheme(palette: ThemePalette) {
        currentPalette = palette
        setBackgroundColor(palette.surfaceColor)
        loadCategory(selectedCategoryIndex)
    }

    private fun getRecentEmojis(): List<String> {
        val jsonStr = emojiPrefs.getString(KEY_RECENTS, null) ?: return DEFAULT_RECENTS
        return try {
            val jsonArray = JSONArray(jsonStr)
            val list = mutableListOf<String>()
            for (i in 0 until jsonArray.length()) {
                list.add(jsonArray.getString(i))
            }
            if (list.isEmpty()) DEFAULT_RECENTS else list
        } catch (_: Exception) {
            DEFAULT_RECENTS
        }
    }

    fun recordEmojiUsed(emoji: String) {
        recordRecentEmoji(emoji)
    }

    private fun recordRecentEmoji(emoji: String) {
        val current = getRecentEmojis().toMutableList()
        current.remove(emoji)
        current.add(0, emoji)
        val capped = current.take(35)
        val jsonArray = JSONArray()
        capped.forEach { jsonArray.put(it) }
        emojiPrefs.edit().putString(KEY_RECENTS, jsonArray.toString()).apply()

        if (selectedCategoryIndex == 0) {
            loadCategory(0)
        }
    }

    private fun setupCategoryBar() {
        val hScroll = HorizontalScrollView(context).apply {
            isHorizontalScrollBarEnabled = false
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(42))
        }

        categoryBar.apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(8), dp(2), dp(8), dp(2))
        }

        CATEGORIES.forEachIndexed { index, cat ->
            val tab = TextView(context).apply {
                text = "${cat.icon} ${cat.name}"
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(if (index == selectedCategoryIndex) Color.parseColor("#818cf8") else Color.parseColor("#71717a"))
                setPadding(dp(12), dp(8), dp(12), dp(8))
                gravity = Gravity.CENTER
                background = createTabBackground(index == selectedCategoryIndex)

                setOnClickListener {
                    loadCategory(index)
                }
            }
            categoryBar.addView(tab)
        }

        hScroll.addView(categoryBar)
        addView(hScroll)

        // Divider
        addView(View(context).apply {
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(1))
            setBackgroundColor(currentPalette.dividerColor)
        })
    }

    private fun setupScrollView() {
        scrollView.apply {
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f)
            isFillViewport = true
        }

        emojiContainer.apply {
            orientation = VERTICAL
            setPadding(dp(6), dp(8), dp(6), dp(8))
        }

        scrollView.addView(emojiContainer)
        addView(scrollView)
    }

    private fun setupBottomBar() {
        val bottomBar = LinearLayout(context).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(48))
            setBackgroundColor(currentPalette.keySpecialColor)
            setPadding(dp(8), dp(4), dp(8), dp(4))
        }

        // Return to keyboard button
        val abcBtn = TextView(context).apply {
            text = "ABC"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 15f)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(currentPalette.keyTextColor)
            gravity = Gravity.CENTER
            background = createKeyBackground(true)
            layoutParams = LayoutParams(dp(72), LayoutParams.MATCH_PARENT).apply {
                setMargins(dp(4), dp(2), dp(4), dp(2))
            }
            setOnClickListener {
                onBackToKeyboard?.invoke()
            }
        }

        // Center space bar
        val spaceBtn = TextView(context).apply {
            text = "Space"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            setTextColor(currentPalette.keySpecialTextColor)
            gravity = Gravity.CENTER
            background = createKeyBackground(false)
            layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, 1f).apply {
                setMargins(dp(4), dp(2), dp(4), dp(2))
            }
            setOnClickListener {
                onEmojiSelected?.invoke(" ")
            }
        }

        // Backspace button
        val backspaceBtn = TextView(context).apply {
            text = "⌫"
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
            setTextColor(currentPalette.keyTextColor)
            gravity = Gravity.CENTER
            background = createKeyBackground(true)
            layoutParams = LayoutParams(dp(64), LayoutParams.MATCH_PARENT).apply {
                setMargins(dp(4), dp(2), dp(4), dp(2))
            }
            setOnClickListener {
                onBackspace?.invoke()
            }
        }

        bottomBar.addView(abcBtn)
        bottomBar.addView(spaceBtn)
        bottomBar.addView(backspaceBtn)

        addView(bottomBar)
    }

    private fun loadCategory(categoryIndex: Int) {
        selectedCategoryIndex = categoryIndex

        // Update category tabs style
        for (i in 0 until categoryBar.childCount) {
            val child = categoryBar.getChildAt(i) as? TextView ?: continue
            val isSelected = (i == categoryIndex)
            val accentColor = if (currentPalette.name == "light") Color.parseColor("#4f46e5") else Color.parseColor("#818cf8")
            val inactiveColor = if (currentPalette.name == "light") Color.parseColor("#71717a") else Color.parseColor("#9ca3af")
            child.setTextColor(if (isSelected) accentColor else inactiveColor)
            child.background = createTabBackground(isSelected)
        }

        emojiContainer.removeAllViews()
        val category = CATEGORIES[categoryIndex]

        if (category.isSearch) {
            renderSearchPanel()
            scrollView.smoothScrollTo(0, 0)
            return
        }

        val items = if (category.isRecent) getRecentEmojis() else category.emojis

        if (category.isSticker) {
            // Render Kaomoji Text Stickers in responsive 2-column or 3-column pill chips
            val numColumns = 3
            var rowLayout: LinearLayout? = null

            items.forEachIndexed { idx, sticker ->
                if (idx % numColumns == 0) {
                    rowLayout = LinearLayout(context).apply {
                        orientation = HORIZONTAL
                        layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(44)).apply {
                            setMargins(0, dp(2), 0, dp(2))
                        }
                        weightSum = numColumns.toFloat()
                    }
                    emojiContainer.addView(rowLayout)
                }

                val tv = TextView(context).apply {
                    text = sticker
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
                    typeface = Typeface.DEFAULT_BOLD
                    setTextColor(currentPalette.keyTextColor)
                    gravity = Gravity.CENTER
                    background = createStickerChipBackground()
                    layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, 1f).apply {
                        setMargins(dp(3), dp(2), dp(3), dp(2))
                    }
                    setOnClickListener {
                        recordRecentEmoji(sticker)
                        onEmojiSelected?.invoke(sticker)
                    }
                }
                rowLayout?.addView(tv)
            }
        } else {
            renderEmojiGrid(items)
        }

        scrollView.smoothScrollTo(0, 0)
    }

    private fun renderSearchPanel() {
        // Clickable bar that switches to keyboard-backed live bilingual emoji search
        val typeSearchBtn = TextView(context).apply {
            text = "🔍 টাইপ করে ইমোজি খুঁজুন (যেমন: ভালোবাসা, hasi, cha)..."
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            setTextColor(currentPalette.stripSecondaryText)
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(14), dp(10), dp(14), dp(10))
            background = GradientDrawable().apply {
                cornerRadius = dp(10).toFloat()
                setColor(currentPalette.keyNormalColor)
                setStroke(dp(1), currentPalette.keyBorderColor)
            }
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT).apply {
                setMargins(dp(6), dp(2), dp(6), dp(8))
            }
            setOnClickListener {
                onStartTypeSearch?.invoke()
            }
        }
        emojiContainer.addView(typeSearchBtn)

        // One-tap Bengali mood & topic chips
        val chipScroll = HorizontalScrollView(context).apply {
            isHorizontalScrollBarEnabled = false
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, dp(6))
            }
        }
        val chipRow = LinearLayout(context).apply {
            orientation = HORIZONTAL
            setPadding(dp(4), dp(2), dp(4), dp(2))
        }
        for ((label, tag) in QUICK_SEARCH_CHIPS) {
            val isSelected = activeSearchTag == tag
            val chip = TextView(context).apply {
                text = label
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12.5f)
                typeface = if (isSelected) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                setTextColor(if (isSelected) currentPalette.stripPrimaryText else currentPalette.keyTextColor)
                setPadding(dp(11), dp(6), dp(11), dp(6))
                background = createTabBackground(isSelected)
                layoutParams = LayoutParams(LayoutParams.WRAP_CONTENT, LayoutParams.WRAP_CONTENT).apply {
                    setMargins(dp(3), 0, dp(3), 0)
                }
                setOnClickListener {
                    activeSearchTag = tag
                    loadCategory(selectedCategoryIndex)
                }
            }
            chipRow.addView(chip)
        }
        chipScroll.addView(chipRow)
        emojiContainer.addView(chipScroll)

        val matched = if (activeSearchTag.isEmpty()) {
            EMOJI_KEYWORDS.flatMap { it.second }.distinct()
        } else {
            searchEmojis(activeSearchTag)
        }
        renderEmojiGrid(matched)
    }

    private fun renderEmojiGrid(items: List<String>) {
        val numColumns = if (resources.configuration.smallestScreenWidthDp >= 600) 10 else 7
        var rowLayout: LinearLayout? = null

        items.forEachIndexed { idx, emoji ->
            if (idx % numColumns == 0) {
                rowLayout = LinearLayout(context).apply {
                    orientation = HORIZONTAL
                    layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, dp(44))
                    weightSum = numColumns.toFloat()
                }
                emojiContainer.addView(rowLayout)
            }

            val tv = TextView(context).apply {
                text = emoji
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 22f)
                gravity = Gravity.CENTER
                layoutParams = LayoutParams(0, LayoutParams.MATCH_PARENT, 1f)
                background = createRippleBackground()
                setOnClickListener {
                    recordRecentEmoji(emoji)
                    onEmojiSelected?.invoke(emoji)
                }
            }
            rowLayout?.addView(tv)
        }
    }

    private fun createTabBackground(isSelected: Boolean): GradientDrawable = GradientDrawable().apply {
        cornerRadius = dp(16).toFloat()
        if (isSelected) {
            val bg = if (currentPalette.name == "light") Color.parseColor("#e0e7ff") else Color.parseColor("#1f1f2e")
            val stroke = if (currentPalette.name == "light") Color.parseColor("#6366f1") else Color.parseColor("#4f46e5")
            setColor(bg)
            setStroke(dp(1), stroke)
        } else {
            setColor(Color.TRANSPARENT)
        }
    }

    private fun createStickerChipBackground(): StateListDrawable {
        val normal = GradientDrawable().apply {
            cornerRadius = dp(10).toFloat()
            setColor(currentPalette.keyNormalColor)
            setStroke(dp(1), currentPalette.keyBorderColor)
        }
        val pressed = GradientDrawable().apply {
            cornerRadius = dp(10).toFloat()
            setColor(currentPalette.keyPressedColor)
        }
        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun createKeyBackground(isSpecial: Boolean): StateListDrawable {
        val normal = GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(if (isSpecial) currentPalette.keySpecialColor else currentPalette.keyNormalColor)
            setStroke(dp(1), currentPalette.keyBorderColor)
        }
        val pressed = GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(currentPalette.keyPressedColor)
        }
        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun createRippleBackground(): StateListDrawable {
        val normal = GradientDrawable().apply {
            setColor(Color.TRANSPARENT)
        }
        val pressed = GradientDrawable().apply {
            cornerRadius = dp(8).toFloat()
            setColor(currentPalette.keyPressedColor)
        }
        return StateListDrawable().apply {
            addState(intArrayOf(android.R.attr.state_pressed), pressed)
            addState(intArrayOf(), normal)
        }
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()
}
