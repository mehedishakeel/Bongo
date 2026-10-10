# Design Direction: Bongo (getbongo.app)

**Product Kind**: Native macOS software utility landing page and documentation.
**Target Audience**: Bengali-speaking Mac users (writers, students, software engineers, designers) running Apple Silicon (M1/M2/M3/M4+).
**Visual Language**: macOS Native Precision with Bengali Typographic Heritage. Clean hairline borders, authentic Apple-grade translucent surfaces, high contrast, tactile keyboard controls, and warm crimson-vermilion accents (`#c2410c` / `#e11d48`) honoring traditional Bengali print.

## Dials (Mandatory)
- **ENERGY**: 2 (Balanced. Professional Mac utility, clear focal points, confident hierarchy)
- **RHYTHM**: 2 (Consistent structure with purposeful compositional shifts between interactive simulator, preview panes, and reference tables)
- **MOTION**: 1 (Calm. Hover states, active keyboard state indicators, zero looping animations or floating decorative orbs)

## Palette
- **Light Theme**:
  - Background Canvas: `#f8fafc` (Slate 50)
  - Surface Card: `#ffffff`
  - Subtle Surface: `#f1f5f9` (Slate 100)
  - Border Hairline: `rgba(15, 23, 42, 0.08)`
  - Text Primary: `#0f172a` (Slate 900)
  - Text Secondary: `#475569` (Slate 600)
  - Accent Primary: `#c2410c` (Terracotta 700)
  - Accent Muted: `rgba(194, 65, 12, 0.08)`
- **Dark Theme**:
  - Background Canvas: `#0b0f17` (Deep Obsidian Slate)
  - Surface Card: `#131b26` (Slate 900)
  - Subtle Surface: `#1a2433` (Slate 800)
  - Border Hairline: `rgba(255, 255, 255, 0.08)`
  - Text Primary: `#f8fafc` (Slate 50)
  - Text Secondary: `#94a3b8` (Slate 400)
  - Accent Primary: `#fb923c` (Warm Amber-Orange 400)
  - Accent Muted: `rgba(251, 146, 60, 0.12)`

## Typography
- Latin: `-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif`
- Bengali: `"Kohinoor Bangla", "Bangla Sangam MN", "Noto Sans Bengali", "Kalpurush", sans-serif`
- Code / Keystrokes: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`

## Copywriting Constraints (R-02)
- Zero em dashes (`—`) in any user-facing text. Use commas, colons, periods, or parentheses.
- Concrete, verifiable facts only (M1-M4 Apple Silicon, macOS 13 Ventura through macOS 15 Sequoia, on-device `InputMethodKit`, 150,000+ dictionary entries).
- Zero AI marketing buzzwords (no "revolutionary", "seamless", "transformative").
