package app.getbongo.ime.model

import android.graphics.Color

/**
 * Color palette configurations for Bongo IME themes.
 */
data class ThemePalette(
    val name: String,
    val surfaceColor: Int,
    val keyNormalColor: Int,
    val keySpecialColor: Int,
    val keyReturnColor: Int,
    val keyPressedColor: Int,
    val keyTextColor: Int,
    val keySpecialTextColor: Int,
    val keyHintColor: Int,
    val keyBorderColor: Int,
    val stripPrimaryBg: Int,
    val stripPrimaryText: Int,
    val stripPrimaryBorder: Int,
    val stripSecondaryBg: Int,
    val stripSecondaryText: Int,
    val dividerColor: Int
) {
    companion object {
        fun getPalette(themeName: String): ThemePalette = when (themeName.lowercase()) {
            "custom" -> ThemePalette(
                name = "custom",
                surfaceColor = Color.TRANSPARENT,
                keyNormalColor = Color.argb(140, 24, 25, 28),
                keySpecialColor = Color.argb(175, 14, 15, 18),
                keyReturnColor = Color.argb(230, 79, 70, 229),
                keyPressedColor = Color.argb(220, 60, 60, 70),
                keyTextColor = Color.WHITE,
                keySpecialTextColor = Color.WHITE,
                keyHintColor = Color.argb(190, 210, 210, 220),
                keyBorderColor = Color.argb(70, 255, 255, 255),
                stripPrimaryBg = Color.argb(210, 79, 70, 229),
                stripPrimaryText = Color.WHITE,
                stripPrimaryBorder = Color.parseColor("#818cf8"),
                stripSecondaryBg = Color.argb(150, 20, 20, 25),
                stripSecondaryText = Color.argb(230, 240, 240, 245),
                dividerColor = Color.argb(50, 255, 255, 255)
            )
            "oled" -> ThemePalette(
                name = "oled",
                surfaceColor = Color.parseColor("#000000"),
                keyNormalColor = Color.parseColor("#121214"),
                keySpecialColor = Color.parseColor("#08080a"),
                keyReturnColor = Color.parseColor("#6366f1"),
                keyPressedColor = Color.parseColor("#27272a"),
                keyTextColor = Color.WHITE,
                keySpecialTextColor = Color.parseColor("#e4e4e7"),
                keyHintColor = Color.parseColor("#52525b"),
                keyBorderColor = Color.parseColor("#1e1e24"),
                stripPrimaryBg = Color.parseColor("#1e1b4b"),
                stripPrimaryText = Color.WHITE,
                stripPrimaryBorder = Color.parseColor("#6366f1"),
                stripSecondaryBg = Color.parseColor("#121214"),
                stripSecondaryText = Color.parseColor("#d4d4d8"),
                dividerColor = Color.parseColor("#1c1c20")
            )
            "light" -> ThemePalette(
                name = "light",
                surfaceColor = Color.parseColor("#f4f4f5"),
                keyNormalColor = Color.parseColor("#ffffff"),
                keySpecialColor = Color.parseColor("#e4e4e7"),
                keyReturnColor = Color.parseColor("#4f46e5"),
                keyPressedColor = Color.parseColor("#d4d4d8"),
                keyTextColor = Color.parseColor("#18181b"),
                keySpecialTextColor = Color.parseColor("#27272a"),
                keyHintColor = Color.parseColor("#a1a1aa"),
                keyBorderColor = Color.parseColor("#d4d4d8"),
                stripPrimaryBg = Color.parseColor("#e0e7ff"),
                stripPrimaryText = Color.parseColor("#312e81"),
                stripPrimaryBorder = Color.parseColor("#818cf8"),
                stripSecondaryBg = Color.parseColor("#ffffff"),
                stripSecondaryText = Color.parseColor("#3f3f46"),
                dividerColor = Color.parseColor("#e4e4e7")
            )
            "emerald" -> ThemePalette(
                name = "emerald",
                surfaceColor = Color.parseColor("#0c131f"),
                keyNormalColor = Color.parseColor("#182234"),
                keySpecialColor = Color.parseColor("#0f172a"),
                keyReturnColor = Color.parseColor("#059669"),
                keyPressedColor = Color.parseColor("#334155"),
                keyTextColor = Color.WHITE,
                keySpecialTextColor = Color.parseColor("#e2e8f0"),
                keyHintColor = Color.parseColor("#64748b"),
                keyBorderColor = Color.parseColor("#1e293b"),
                stripPrimaryBg = Color.parseColor("#064e3b"),
                stripPrimaryText = Color.parseColor("#a7f3d0"),
                stripPrimaryBorder = Color.parseColor("#10b981"),
                stripSecondaryBg = Color.parseColor("#1e293b"),
                stripSecondaryText = Color.parseColor("#cbd5e1"),
                dividerColor = Color.parseColor("#1e293b")
            )
            "crimson" -> ThemePalette(
                name = "crimson",
                surfaceColor = Color.parseColor("#1a0f12"),
                keyNormalColor = Color.parseColor("#2b191e"),
                keySpecialColor = Color.parseColor("#1f1216"),
                keyReturnColor = Color.parseColor("#e11d48"),
                keyPressedColor = Color.parseColor("#4c2832"),
                keyTextColor = Color.WHITE,
                keySpecialTextColor = Color.parseColor("#ffe4e6"),
                keyHintColor = Color.parseColor("#9f1239"),
                keyBorderColor = Color.parseColor("#3f1d26"),
                stripPrimaryBg = Color.parseColor("#881337"),
                stripPrimaryText = Color.parseColor("#fecdd3"),
                stripPrimaryBorder = Color.parseColor("#f43f5e"),
                stripSecondaryBg = Color.parseColor("#2b191e"),
                stripSecondaryText = Color.parseColor("#fda4af"),
                dividerColor = Color.parseColor("#2b191e")
            )
            "nord" -> ThemePalette(
                name = "nord",
                surfaceColor = Color.parseColor("#242933"),
                keyNormalColor = Color.parseColor("#2e3440"),
                keySpecialColor = Color.parseColor("#242933"),
                keyReturnColor = Color.parseColor("#88c0d0"),
                keyPressedColor = Color.parseColor("#434c5e"),
                keyTextColor = Color.parseColor("#eceff4"),
                keySpecialTextColor = Color.parseColor("#e5e9f0"),
                keyHintColor = Color.parseColor("#4c566a"),
                keyBorderColor = Color.parseColor("#3b4252"),
                stripPrimaryBg = Color.parseColor("#3b4252"),
                stripPrimaryText = Color.parseColor("#88c0d0"),
                stripPrimaryBorder = Color.parseColor("#81a1c1"),
                stripSecondaryBg = Color.parseColor("#2e3440"),
                stripSecondaryText = Color.parseColor("#d8dee9"),
                dividerColor = Color.parseColor("#2e3440")
            )
            else -> ThemePalette( // "midnight" (default, replicates classic Ridmik dark theme)
                name = "midnight",
                surfaceColor = Color.parseColor("#18191b"),
                keyNormalColor = Color.parseColor("#3c3d40"),
                keySpecialColor = Color.parseColor("#222325"),
                keyReturnColor = Color.parseColor("#222325"),
                keyPressedColor = Color.parseColor("#595a5f"),
                keyTextColor = Color.WHITE,
                keySpecialTextColor = Color.WHITE,
                keyHintColor = Color.parseColor("#8c8d93"),
                keyBorderColor = Color.parseColor("#252629"),
                stripPrimaryBg = Color.parseColor("#292a2d"),
                stripPrimaryText = Color.WHITE,
                stripPrimaryBorder = Color.parseColor("#6366f1"),
                stripSecondaryBg = Color.parseColor("#1c1d20"),
                stripSecondaryText = Color.parseColor("#d4d4d8"),
                dividerColor = Color.parseColor("#202123")
            )
        }
    }
}
