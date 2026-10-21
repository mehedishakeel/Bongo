#!/usr/bin/env python3
"""
Bongo Welcome & Settings Application for Windows
Replicates the native macOS and Linux Bongo interface on Windows desktops.
Provides 4 main sections:
1. Getting Started: Setup guide, language switching shortcuts, phonetic typing guide, and interactive playground.
2. Bongo Layout: Complete searchable Avro phonetic keymap cheatsheet (Consonants, Vowels, Modifiers, Numbers).
3. Settings: Typing modes (Phonetic first, Smart, Phonetic only), emoji suggestions, startup configuration, hotkey.
4. Fonts & Typography: Bengali font selector, candidate size, and live candidate HUD preview.
"""

import os
import sys
import json
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk, font as tkfont
from pathlib import Path

# Configuration path (Windows APPDATA compliant)
def get_config_dir():
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Bongo"
    return Path.home() / ".config" / "bongo"

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "keyboard_layout": 0,     # 0: Avro Phonetic, 1: National (Bijoy)
    "typing_mode": 0,         # 0: PhoneticFirst, 1: Smart, 2: PhoneticOnly
    "suggest_emoji": True,
    "candidate_font": "Noto Sans Bengali",
    "candidate_font_size": 16,
    "toggle_key": "F12",
    "autostart": True,
}

# Dark theme palette matching macOS and Linux GTK4 Bongo styling
BG_DARK = "#18181b"
BG_SIDEBAR = "#111113"
BG_CARD = "#202024"
BG_CARD_BORDER = "#2e2e33"
BG_CARD_ACTIVE_BORDER = "#6366f1"
BG_HOVER = "#27272a"
ACCENT_COLOR = "#6366f1"
ACCENT_LIGHT = "#818cf8"
ACCENT_BG = "#232338"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a1a1aa"
TEXT_MUTED = "#71717a"
KEY_CHIP_BG = "#2a2a30"
KEY_CHIP_BORDER = "#3f3f46"

def load_settings():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    settings = dict(DEFAULT_SETTINGS)
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                settings.update(saved)
        except Exception as e:
            sys.stderr.write(f"Warning: Could not read settings: {e}\n")
    return settings

def save_settings(settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write settings: {e}\n")

def scan_bengali_fonts():
    """Scans system for available Bengali fonts on Windows and common fallbacks."""
    fonts = set()
    common_bengali_fonts = [
        "System Font (Default)",
        "Noto Sans Bengali",
        "Noto Serif Bengali",
        "Kalpurush",
        "Siyam Rupali",
        "SolaimanLipi",
        "Vrinda",
        "Nirmala UI",
        "Shonar Bangla",
        "Akaash",
        "Mitra Mono",
        "Bangla",
        "Arial Unicode MS",
        "Segoe UI",
    ]
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
            for i in range(winreg.QueryInfoKey(key)[1]):
                val_name, _, _ = winreg.EnumValue(key, i)
                clean_name = val_name.split(" (")[0].strip()
                for c in common_bengali_fonts:
                    if c != "System Font (Default)" and c.lower() in clean_name.lower():
                        fonts.add(clean_name)
            winreg.CloseKey(key)
        except Exception:
            pass

    for f in common_bengali_fonts:
        fonts.add(f)
    return sorted(list(fonts))

def enable_windows_dark_titlebar(hwnd):
    """Enables Windows 10/11 dark title bar via DWM API."""
    if sys.platform == "win32":
        try:
            import ctypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            user32 = ctypes.windll.user32
            dwmapi = ctypes.windll.dwmapi
            target_hwnd = user32.GetParent(hwnd)
            if not target_hwnd:
                target_hwnd = hwnd
            value = ctypes.c_int(1)
            res = dwmapi.DwmSetWindowAttribute(
                target_hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
            if res != 0:
                dwmapi.DwmSetWindowAttribute(
                    target_hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
        except Exception:
            pass

def set_windows_autostart(enabled: bool):
    """Configures Windows Run registry key for automatic startup."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            # Find bongo.exe (background input service) rather than settings GUI
            bongo_exe = Path(sys.executable).parent / "bongo.exe"
            if not bongo_exe.is_file():
                bongo_exe = Path(__file__).resolve().parent.parent / "service" / "bongo_service.py"
            if bongo_exe.is_file():
                if bongo_exe.suffix == ".py":
                    cmd = f'"{sys.executable}" "{bongo_exe}" --daemon'
                else:
                    cmd = f'"{bongo_exe}" --daemon'
            else:
                cmd = f'"{sys.executable}" --daemon'

            if enabled:
                winreg.SetValueEx(key, "Bongo", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "Bongo")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            sys.stderr.write(f"Warning: Could not update Windows startup registry: {e}\n")

def ensure_background_service():
    """Ensures the Bongo background input service is running."""
    if sys.platform == "win32":
        try:
            import subprocess
            proc = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq bongo.exe", "/NH"],
                capture_output=True,
                text=True
            )
            if "bongo.exe" not in proc.stdout.lower():
                svc_candidates = [
                    Path(sys.executable).parent / "bongo.exe",
                    Path(__file__).resolve().parent.parent / "service" / "bongo_service.py",
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Bongo" / "bongo.exe",
                    Path(r"C:\Program Files\Bongo\bongo.exe"),
                ]
                for sc in svc_candidates:
                    if sc.is_file():
                        creation_flag = 0x08000000  # CREATE_NO_WINDOW
                        if sc.suffix == ".py":
                            subprocess.Popen([sys.executable, str(sc), "--daemon"], creationflags=creation_flag)
                        else:
                            subprocess.Popen([str(sc), "--daemon"], creationflags=creation_flag)
                        break
        except Exception:
            pass

# Built-in phonetic transliteration mapping for interactive playground
PLAYGROUND_SAMPLES = {
    "ami": "আমি",
    "amader": "আমাদের",
    "bangla": "বাংলা",
    "banglay": " বাংলায়",
    "gan": "গান",
    "gai": "গাই",
    "shonar": "সোনার",
    "dhonnobad": "ধন্যবাদ",
    "bongo": "বঙ্গ",
    "shadhinota": "স্বাধীনতা",
    "bhalobashi": "ভালোবাসি",
}

def quick_transliterate(text: str) -> str:
    """Translates sample words or applies simple Avro phonetic rules for typing preview."""
    words = text.split(" ")
    out_words = []
    for w in words:
        clean = w.lower().strip()
        if clean in PLAYGROUND_SAMPLES:
            out_words.append(PLAYGROUND_SAMPLES[clean])
        else:
            # Fallback simple replacement
            repl = w
            table = [
                ("kkh", "ক্ষ"), ("kh", "খ"), ("gh", "ঘ"), ("ch", "ছ"),
                ("jh", "ঝ"), ("Th", "ঠ"), ("Dh", "ঢ"), ("th", "থ"),
                ("dh", "ধ"), ("ph", "ফ"), ("bh", "ভ"), ("sh", "শ"),
                ("Sh", "ষ"), ("ng", "ং"), ("k", "ক"), ("g", "গ"),
                ("c", "চ"), ("j", "জ"), ("T", "ট"), ("D", "ড"),
                ("N", "ণ"), ("t", "ত"), ("d", "দ"), ("n", "ন"),
                ("p", "প"), ("f", "ফ"), ("b", "ব"), ("v", "ভ"),
                ("m", "ম"), ("z", "য"), ("r", "র"), ("l", "ল"),
                ("s", "স"), ("h", "হ"), ("R", "ড়"), ("y", "য়"),
                ("o", "অ"), ("a", "আ"), ("i", "ই"), ("I", "ঈ"),
                ("u", "উ"), ("U", "ঊ"), ("e", "এ"), ("O", "ও"),
            ]
            for pat, val in table:
                repl = repl.replace(pat, val)
            out_words.append(repl)
    return " ".join(out_words)


class BongoSettingsApp:
    def __init__(self, root, initial_tab=0):
        self.root = root
        self.root.title("Bongo")
        self.root.geometry("920x640")
        self.root.minsize(860, 580)
        self.root.configure(bg=BG_DARK)

        self.settings = load_settings()
        self.bengali_fonts = scan_bengali_fonts()
        self.active_tab_index = initial_tab

        # Setup application window icon to replace Tkinter feather icon
        self.app_icon = None
        icon_png_candidates = [
            Path(__file__).resolve().parent.parent / "data" / "bongo_32.png",
            Path(__file__).resolve().parent.parent / "data" / "bongo.png",
            Path(sys.executable).parent / "data" / "bongo_32.png",
            Path(sys.executable).parent / "data" / "bongo.png",
            Path(sys.executable).parent / "bongo_32.png",
            Path(sys.executable).parent / "bongo.png",
        ]
        for p in icon_png_candidates:
            if p.is_file():
                try:
                    img = tk.PhotoImage(file=str(p))
                    if img.width() > 48:
                        factor = max(1, img.width() // 32)
                        self.app_icon = img.subsample(factor, factor)
                    else:
                        self.app_icon = img
                    break
                except Exception:
                    pass

        if self.app_icon:
            try:
                self.root.iconphoto(True, self.app_icon)
            except Exception:
                pass

        icon_ico_candidates = [
            Path(__file__).resolve().parent.parent / "data" / "bongo.ico",
            Path(sys.executable).parent / "data" / "bongo.ico",
            Path(sys.executable).parent / "bongo.ico",
        ]
        for p in icon_ico_candidates:
            if p.is_file():
                try:
                    self.root.iconbitmap(str(p))
                    break
                except Exception:
                    try:
                        self.root.iconbitmap(default=str(p))
                        break
                    except Exception:
                        pass

        # Windows titlebar dark styling
        self.root.update_idletasks()
        try:
            hwnd = self.root.winfo_id()
            enable_windows_dark_titlebar(hwnd)
        except Exception:
            pass

        self.setup_ui()
        ensure_background_service()

    def setup_ui(self):
        # Root layout: Sidebar (left) and Content Area (right)
        self.main_container = tk.Frame(self.root, bg=BG_DARK)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.setup_sidebar()
        self.setup_content_area()
        self.select_tab(self.active_tab_index)

    def setup_sidebar(self):
        self.sidebar = tk.Frame(self.main_container, bg=BG_SIDEBAR, width=216)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Brand header: Icon + Bongo text (no Windows badge)
        brand_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        brand_frame.pack(fill=tk.X, padx=20, pady=(28, 24))

        # Try loading app icon
        self.logo_img = None
        candidates = [
            Path(__file__).resolve().parent.parent / "data" / "bongo_32.png",
            Path(__file__).resolve().parent.parent / "data" / "bongo.png",
        ]
        for p in candidates:
            if p.is_file():
                try:
                    img = tk.PhotoImage(file=str(p))
                    if img.width() > 36:
                        factor = max(1, img.width() // 32)
                        self.logo_img = img.subsample(factor, factor)
                    else:
                        self.logo_img = img
                    break
                except Exception:
                    pass

        if self.logo_img:
            logo_lbl = tk.Label(
                brand_frame,
                image=self.logo_img,
                bg=BG_SIDEBAR,
                bd=0,
                highlightthickness=0
            )
            logo_lbl.pack(side=tk.LEFT, padx=(0, 10))

        brand_label = tk.Label(
            brand_frame,
            text="Bongo",
            font=("Segoe UI", 18, "bold"),
            fg=ACCENT_LIGHT,
            bg=BG_SIDEBAR
        )
        brand_label.pack(side=tk.LEFT)

        # Navigation items with icons matching macOS and Linux
        self.nav_widgets = []
        nav_items = [
            ("✦  Getting Started", 0),
            ("⌨  Bongo Layout", 1),
            ("⚙  Settings", 2),
            ("Aa  Fonts", 3),
        ]

        nav_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        nav_frame.pack(fill=tk.X, padx=12, pady=(4, 10))

        for label_text, idx in nav_items:
            # Container for each nav row
            row_frame = tk.Frame(nav_frame, bg=BG_SIDEBAR, cursor="hand2")
            row_frame.pack(fill=tk.X, pady=3)

            # Left indicator bar (pill highlight)
            ind = tk.Frame(row_frame, bg=BG_SIDEBAR, width=3)
            ind.pack(side=tk.LEFT, fill=tk.Y)

            # Label button
            lbl = tk.Label(
                row_frame,
                text=f"  {label_text}",
                font=("Segoe UI", 10, "normal"),
                fg=TEXT_SECONDARY,
                bg=BG_SIDEBAR,
                anchor="w",
                padx=12,
                pady=9,
                cursor="hand2"
            )
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Bind clicks
            row_frame.bind("<Button-1>", lambda e, i=idx: self.select_tab(i))
            lbl.bind("<Button-1>", lambda e, i=idx: self.select_tab(i))
            ind.bind("<Button-1>", lambda e, i=idx: self.select_tab(i))

            # Bind hover
            def make_hover(rf, l, i, index=idx):
                def on_enter(e):
                    if self.active_tab_index != index:
                        rf.configure(bg=BG_HOVER)
                        l.configure(bg=BG_HOVER)
                def on_leave(e):
                    if self.active_tab_index != index:
                        rf.configure(bg=BG_SIDEBAR)
                        l.configure(bg=BG_SIDEBAR)
                rf.bind("<Enter>", on_enter)
                rf.bind("<Leave>", on_leave)
                l.bind("<Enter>", on_enter)
                l.bind("<Leave>", on_leave)

            make_hover(row_frame, lbl, ind, idx)
            self.nav_widgets.append((row_frame, ind, lbl))

        # Bottom footer matching macOS (v1.0.0 · windows / Developed by Mehedi Shakeel)
        footer_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))

        ver_label = tk.Label(
            footer_frame,
            text="v1.0.1 · windows",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_SIDEBAR
        )
        ver_label.pack(anchor="w", pady=(0, 2))

        author_label = tk.Label(
            footer_frame,
            text="Developed by Mehedi Shakeel",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_SIDEBAR
        )
        author_label.pack(anchor="w")

    def setup_content_area(self):
        self.content_frame = tk.Frame(self.main_container, bg=BG_DARK)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Unified Header fixed at top of content area (matches macOS & Linux)
        header_container = tk.Frame(self.content_frame, bg=BG_DARK)
        header_container.pack(fill=tk.X, padx=32, pady=(28, 14))

        self.heading_label = tk.Label(
            header_container,
            text="Getting Started",
            font=("Segoe UI", 20, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_DARK
        )
        self.heading_label.pack(anchor="w", pady=(0, 4))

        self.subtitle_label = tk.Label(
            header_container,
            text="Everything you need to begin typing in Bangla.",
            font=("Segoe UI", 10),
            fg=TEXT_SECONDARY,
            bg=BG_DARK
        )
        self.subtitle_label.pack(anchor="w")

        # Scrollable Canvas below header
        body_container = tk.Frame(self.content_frame, bg=BG_DARK)
        body_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(body_container, bg=BG_DARK, bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(body_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_DARK)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Keep frame width tied to canvas width
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)

        # Mousewheel scrolling
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(32, 4), pady=(0, 20))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 20))

        # Create the 4 views
        self.pages = [
            self.create_getting_started_view(self.scrollable_frame),
            self.create_layout_view(self.scrollable_frame),
            self.create_settings_view(self.scrollable_frame),
            self.create_fonts_view(self.scrollable_frame),
        ]

    def select_tab(self, idx):
        self.active_tab_index = idx

        tab_headers = [
            ("Getting Started", "Everything you need to begin typing in Bangla."),
            ("Bongo Layout", "The complete phonetic key map at a glance."),
            ("Settings", "Choose how Bongo behaves while you type."),
            ("Fonts", "Make the suggestion popup comfortable to read."),
        ]

        title, subtitle = tab_headers[idx]
        self.heading_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)

        # Update sidebar active styling
        for i, (rf, ind, lbl) in enumerate(self.nav_widgets):
            if i == idx:
                rf.configure(bg=ACCENT_BG)
                ind.configure(bg=ACCENT_COLOR)
                lbl.configure(
                    bg=ACCENT_BG,
                    fg=ACCENT_LIGHT,
                    font=("Segoe UI", 10, "bold")
                )
            else:
                rf.configure(bg=BG_SIDEBAR)
                ind.configure(bg=BG_SIDEBAR)
                lbl.configure(
                    bg=BG_SIDEBAR,
                    fg=TEXT_SECONDARY,
                    font=("Segoe UI", 10, "normal")
                )

        # Show active page, hide others
        for i, page in enumerate(self.pages):
            if i == idx:
                page.pack(fill=tk.BOTH, expand=True)
            else:
                page.pack_forget()

        # Reset scroll to top
        self.canvas.yview_moveto(0.0)

    # -------------------------------------------------------------
    # UI Component Helpers
    # -------------------------------------------------------------
    def make_card(self, parent, active=False):
        """Creates a styled card container matching macOS and Linux styling."""
        border_col = BG_CARD_ACTIVE_BORDER if active else BG_CARD_BORDER
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            highlightbackground=border_col,
            highlightcolor=border_col,
            highlightthickness=1,
            padx=18,
            pady=16
        )
        card.pack(fill=tk.X, pady=(0, 14))
        return card

    def make_section_label(self, parent, text):
        lbl = tk.Label(
            parent,
            text=text.upper(),
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_MUTED,
            bg=BG_DARK
        )
        lbl.pack(anchor="w", pady=(18, 8))
        return lbl

    def make_key_chip(self, parent, text):
        chip = tk.Label(
            parent,
            text=text,
            font=("Consolas", 10, "bold"),
            fg=TEXT_PRIMARY,
            bg=KEY_CHIP_BG,
            highlightbackground=KEY_CHIP_BORDER,
            highlightcolor=KEY_CHIP_BORDER,
            highlightthickness=1,
            padx=8,
            pady=4
        )
        return chip

    def make_button(self, parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_HOVER,
            activebackground=ACCENT_COLOR,
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=command
        )
        return btn

    # -------------------------------------------------------------
    # 1. Getting Started Tab
    # -------------------------------------------------------------
    def create_getting_started_view(self, parent):
        container = tk.Frame(parent, bg=BG_DARK)

        # Card 1: 1. Enable Bongo in Windows Settings
        c1 = self.make_card(container)
        c1_title = tk.Label(
            c1,
            text="1. Enable Bongo in Windows Settings",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        c1_title.pack(anchor="w", pady=(0, 6))

        c1_desc = tk.Label(
            c1,
            text="Bongo runs automatically in the background. Press F12 anytime to toggle between English and Bangla across any app (Notepad, Word, browsers, IDEs).",
            font=("Segoe UI", 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            wraplength=560,
            justify=tk.LEFT,
            anchor="w"
        )
        c1_desc.pack(anchor="w", fill=tk.X, pady=(0, 10))

        c1_btn = self.make_button(c1, "Open Language Settings... ↗", self.open_language_settings)
        c1_btn.pack(anchor="w")

        # Card 2: 2. Switch Keyboards Quickly
        c2 = self.make_card(container)
        c2_title = tk.Label(
            c2,
            text="2. Switch Keyboards Quickly",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        c2_title.pack(anchor="w", pady=(0, 6))

        c2_desc = tk.Label(
            c2,
            text="Press F12 (or customizable shortcut) anytime to toggle between English and Bangla.",
            font=("Segoe UI", 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            wraplength=560,
            justify=tk.LEFT,
            anchor="w"
        )
        c2_desc.pack(anchor="w", fill=tk.X, pady=(0, 10))

        chips_row = tk.Frame(c2, bg=BG_CARD)
        chips_row.pack(anchor="w")

        chip_f12 = self.make_key_chip(chips_row, "F12")
        chip_f12.pack(side=tk.LEFT, padx=(0, 8))

        chip_win = self.make_key_chip(chips_row, "⊞ Win + Space")
        chip_win.pack(side=tk.LEFT, padx=(0, 8))

        chip_ctrl = self.make_key_chip(chips_row, "⌃ Control + Space")
        chip_ctrl.pack(side=tk.LEFT)

        # Card 3: 3. Type Natural Phonetic Bangla
        c3 = self.make_card(container)
        c3_title = tk.Label(
            c3,
            text="3. Type Natural Phonetic Bangla",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        c3_title.pack(anchor="w", pady=(0, 6))

        c3_desc = tk.Label(
            c3,
            text="Type English letters phonetically according to how words sound. For example, ami becomes আমি, bangla becomes বাংলা, and dhonnobad becomes ধন্যবাদ.",
            font=("Segoe UI", 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            wraplength=560,
            justify=tk.LEFT,
            anchor="w"
        )
        c3_desc.pack(anchor="w", fill=tk.X)

        # Card 4: Interactive Typing Playground
        c4 = self.make_card(container)
        c4_title = tk.Label(
            c4,
            text="Interactive Typing Playground",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        c4_title.pack(anchor="w", pady=(0, 6))

        c4_desc = tk.Label(
            c4,
            text="Select Bongo or press F12, and try typing right inside this field:",
            font=("Segoe UI", 10),
            fg=TEXT_SECONDARY,
            bg=BG_CARD
        )
        c4_desc.pack(anchor="w", pady=(0, 10))

        play_frame = tk.Frame(c4, bg=BG_DARK, highlightbackground=BG_CARD_BORDER, highlightthickness=1, padx=12, pady=10)
        play_frame.pack(fill=tk.X)

        self.play_var = tk.StringVar(value="")
        self.play_entry = tk.Entry(
            play_frame,
            textvariable=self.play_var,
            font=("Noto Sans Bengali", 12),
            bg=BG_DARK,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_LIGHT,
            relief=tk.FLAT,
            bd=0
        )
        self.play_entry.pack(fill=tk.X)

        # Placeholder label
        self.placeholder_text = "Switch to Bongo and type here (e.g. ami banglay gan gai)..."
        self.play_placeholder = tk.Label(
            play_frame,
            text=self.placeholder_text,
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=BG_DARK
        )
        self.play_placeholder.place(x=0, y=1)

        def on_entry_focus_in(e):
            self.play_placeholder.place_forget()
        def on_entry_focus_out(e):
            if not self.play_var.get():
                self.play_placeholder.place(x=0, y=1)

        self.play_entry.bind("<FocusIn>", on_entry_focus_in)
        self.play_entry.bind("<FocusOut>", on_entry_focus_out)
        self.play_placeholder.bind("<Button-1>", lambda e: self.play_entry.focus_set())

        # Live transliteration preview in playground
        self.preview_lbl = tk.Label(
            c4,
            text="Preview: আমি বাংলায় গান গাই (ami banglay gan gai)",
            font=("Noto Sans Bengali", 10),
            fg=ACCENT_LIGHT,
            bg=BG_CARD
        )
        self.preview_lbl.pack(anchor="w", pady=(8, 0))

        def on_text_change(*args):
            val = self.play_var.get()
            if val:
                self.play_placeholder.place_forget()
                converted = quick_transliterate(val)
                self.preview_lbl.configure(text=f"Phonetic: {converted}")
            else:
                self.preview_lbl.configure(text="Preview: আমি বাংলায় গান গাই (ami banglay gan gai)")

        self.play_var.trace_add("write", on_text_change)

        return container

    def open_language_settings(self):
        try:
            if sys.platform == "win32":
                os.system("start ms-settings:regionlanguage")
            else:
                webbrowser.open("https://getbongo.app")
        except Exception:
            pass

    # -------------------------------------------------------------
    # 2. Bongo Layout Tab (Full Phonetic Key Map)
    # -------------------------------------------------------------
    def create_layout_view(self, parent):
        container = tk.Frame(parent, bg=BG_DARK)

        # Search Bar
        search_frame = tk.Frame(container, bg=BG_CARD, highlightbackground=BG_CARD_BORDER, highlightthickness=1, padx=12, pady=8)
        search_frame.pack(fill=tk.X, pady=(0, 16))

        search_icon = tk.Label(search_frame, text="🔍", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_CARD)
        search_icon.pack(side=tk.LEFT, padx=(0, 8))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_LIGHT,
            relief=tk.FLAT,
            bd=0
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.layout_items = []

        # Section 1: Consonants
        self.make_section_label(container, "Consonants · ব্যঞ্জনবর্ণ")
        c_pairs = [
            ("ক", "k"), ("ট", "T"), ("প", "p"), ("স", "s"),
            ("খ", "kh"), ("ঠ", "Th"), ("ফ", "ph, f"), ("হ", "h"),
            ("গ", "g"), ("ড", "D"), ("ব", "b"), ("ড়", "R"),
            ("ঘ", "gh"), ("ঢ", "Dh"), ("ভ", "bh, v"), ("ঢ়", "Rh"),
            ("ঙ", "Ng"), ("ণ", "N"), ("ম", "m"), ("য়", "y, Y"),
            ("চ", "c"), ("ত", "t"), ("য", "z"), ("শ", "sh, S"),
            ("ছ", "ch"), ("থ", "th"), ("র", "r"), ("ষ", "Sh"),
            ("জ", "j"), ("দ", "d"), ("ল", "l"), ("ং", "ng"),
            ("ঝ", "jh"), ("ধ", "dh"), ("ঃ", ":"), ("ঁ", "^"),
            ("ঞ", "NG"), ("ন", "n"), ("ৎ", "t``"), ("ক্ষ", "kkh")
        ]
        self.create_key_grid(container, c_pairs, cols=4)

        # Section 2: Vowels
        self.make_section_label(container, "Vowels · স্বরবর্ণ")
        v_pairs = [
            ("অ", "o"), ("ই / কি", "i"), ("উ / কু", "u"),
            ("আ / কা", "a"), ("ঈ / কী", "I"), ("ঊ / কূ", "U"),
            ("ঋ / কৃ", "rri"), ("এ / কে", "e"), ("ও / কো", "O"),
            ("ঐ / কৈ", "OI"), ("ঔ / কৌ", "OU"), ("া ি ী", "kar")
        ]
        self.create_key_grid(container, v_pairs, cols=3)

        # Section 3: Special & Modifiers
        self.make_section_label(container, "Special & Modifiers · বিশেষ")
        s_pairs = [
            ("্ হসন্ত", ",,"), ("ব-ফলা", "w"), ("রেফ", "rr (v)"),
            ("় নুক্তা", ".."), ("য-ফলা", "y, Z"), ("। দাঁড়ি", "."),
            ("ZWJ", "`"), ("র-ফলা", "r"), ("৳ টাকা", "$"),
            ("ZWNJ", "~"), ("্য ্র", "conj"), ("্ হস", ",,")
        ]
        self.create_key_grid(container, s_pairs, cols=3)

        # Section 4: Numbers
        self.make_section_label(container, "Numbers · সংখ্যা")
        n_pairs = [
            ("০", "0"), ("১", "1"), ("২", "2"), ("৩", "3"), ("৪", "4"),
            ("৫", "5"), ("৬", "6"), ("৭", "7"), ("৮", "8"), ("৯", "9")
        ]
        self.create_key_grid(container, n_pairs, cols=5)

        # Hook search filtering
        self.search_var.trace_add("write", self.filter_layout)

        return container

    def create_key_grid(self, parent, pairs, cols=4):
        card = self.make_card(parent)
        grid_frame = tk.Frame(card, bg=BG_CARD)
        grid_frame.pack(fill=tk.X)

        for col_idx in range(cols):
            grid_frame.columnconfigure(col_idx, weight=1)

        row = 0
        col = 0
        for bn, en in pairs:
            cell = tk.Frame(grid_frame, bg=BG_CARD, padx=8, pady=6)
            cell.grid(row=row, column=col, sticky="w")

            bn_lbl = tk.Label(
                cell,
                text=bn,
                font=("Noto Sans Bengali", 13, "bold"),
                fg=TEXT_PRIMARY,
                bg=BG_CARD,
                width=6,
                anchor="w"
            )
            bn_lbl.pack(side=tk.LEFT)

            chip = self.make_key_chip(cell, en)
            chip.pack(side=tk.LEFT)

            self.layout_items.append((cell, f"{bn} {en}".lower()))

            col += 1
            if col >= cols:
                col = 0
                row += 1

    def filter_layout(self, *args):
        query = self.search_var.get().strip().lower()
        for cell, text in self.layout_items:
            if not query or query in text:
                cell.grid()
            else:
                cell.grid_remove()

    # -------------------------------------------------------------
    # 3. Settings Tab
    # -------------------------------------------------------------
    def create_settings_view(self, parent):
        container = tk.Frame(parent, bg=BG_DARK)

        # Section: KEYBOARD LAYOUT
        self.make_section_label(container, "Keyboard layout")

        self.layout_cards = []
        layouts = [
            (0, "Avro Phonetic",
             "Modern phonetic input: type as you speak in English letters (e.g. ami -> আমি, bangla -> বাংলা).", True),
            (1, "National / Bijoy (জাতীয়)",
             "Standard Bangladesh BDS 1738:2004 layout: fixed keymap (e.g. j -> ক, d+j -> কি, g -> ্).", False)
        ]

        current_layout = self.settings.get("keyboard_layout", 0)

        for layout_id, title, desc, recommended in layouts:
            card = self.make_layout_card(container, layout_id, title, desc, recommended, selected=(layout_id == current_layout))
            self.layout_cards.append((card, layout_id))

        # Section: TYPING MODE
        self.make_section_label(container, "Typing mode")

        self.mode_cards = []
        modes = [
            (0, "Phonetic first",
             "Types the exact phonetic spelling by default, showing suggestions underneath for alternatives you can select with arrows or numbers.", True),
            (1, "Smart suggestions",
             "Picks the top dictionary-ranked word automatically on Space. Best for fluid fast typing.", False),
            (2, "Phonetic only",
             "Direct inline phonetic output with no candidate popup or suggestions.", False)
        ]

        current_mode = self.settings.get("typing_mode", 0)

        for mode_id, title, desc, recommended in modes:
            card = self.make_mode_card(container, mode_id, title, desc, recommended, selected=(mode_id == current_mode))
            self.mode_cards.append((card, mode_id))

        # Section: PREFERENCES
        self.make_section_label(container, "Preferences")

        pref_card = self.make_card(container)
        p_row = tk.Frame(pref_card, bg=BG_CARD)
        p_row.pack(fill=tk.X)

        p_lbl = tk.Label(
            p_row,
            text="Show emoji in suggestions",
            font=("Segoe UI", 10),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        p_lbl.pack(side=tk.LEFT)

        self.emoji_var = tk.BooleanVar(value=self.settings.get("suggest_emoji", True))
        em_cb = tk.Checkbutton(
            p_row,
            variable=self.emoji_var,
            command=self.on_emoji_changed,
            bg=BG_CARD,
            selectcolor=BG_DARK,
            activebackground=BG_CARD,
            activeforeground=ACCENT_LIGHT
        )
        em_cb.pack(side=tk.RIGHT)

        # Section: UPDATES & SYSTEM
        self.make_section_label(container, "Updates & System")

        sys_card = self.make_card(container)
        s_row = tk.Frame(sys_card, bg=BG_CARD)
        s_row.pack(fill=tk.X)

        import platform
        arch = platform.machine()
        sys_lbl = tk.Label(
            s_row,
            text=f"Windows Native · {arch} · Win32 Hook Engine",
            font=("Segoe UI", 10),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        sys_lbl.pack(side=tk.LEFT)

        upd_btn = self.make_button(s_row, "Check for Updates... ↗", lambda: webbrowser.open("https://getbongo.app"))
        upd_btn.pack(side=tk.RIGHT)

        # Windows Integration Card: Autostart & Shortcut
        win_card = self.make_card(container)

        # Row 1: Autostart
        as_row = tk.Frame(win_card, bg=BG_CARD)
        as_row.pack(fill=tk.X, pady=(0, 12))

        as_lbl = tk.Label(
            as_row,
            text="Start Bongo automatically when Windows starts",
            font=("Segoe UI", 10),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        as_lbl.pack(side=tk.LEFT)

        self.autostart_var = tk.BooleanVar(value=self.settings.get("autostart", True))
        as_cb = tk.Checkbutton(
            as_row,
            variable=self.autostart_var,
            command=self.on_autostart_changed,
            bg=BG_CARD,
            selectcolor=BG_DARK,
            activebackground=BG_CARD,
            activeforeground=ACCENT_LIGHT
        )
        as_cb.pack(side=tk.RIGHT)

        # Row 2: Toggle Hotkey
        hk_row = tk.Frame(win_card, bg=BG_CARD)
        hk_row.pack(fill=tk.X)

        hk_lbl = tk.Label(
            hk_row,
            text="Toggle Shortcut Key:",
            font=("Segoe UI", 10),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        hk_lbl.pack(side=tk.LEFT, padx=(0, 10))

        self.hotkey_var = tk.StringVar(value=self.settings.get("toggle_key", "F12"))
        hk_combo = ttk.Combobox(
            hk_row,
            textvariable=self.hotkey_var,
            values=["F12", "Ctrl+Shift", "Win+Space"],
            state="readonly",
            width=14
        )
        hk_combo.pack(side=tk.LEFT)
        hk_combo.bind("<<ComboboxSelected>>", self.on_hotkey_changed)

        return container

    def make_mode_card(self, parent, mode_id, title, desc, recommended, selected=False):
        border_col = BG_CARD_ACTIVE_BORDER if selected else BG_CARD_BORDER
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            highlightbackground=border_col,
            highlightcolor=border_col,
            highlightthickness=1,
            padx=16,
            pady=14,
            cursor="hand2"
        )
        card.pack(fill=tk.X, pady=(0, 10))

        row = tk.Frame(card, bg=BG_CARD, cursor="hand2")
        row.pack(fill=tk.X)

        # Radio symbol
        radio_sym = "●" if selected else "○"
        radio_lbl = tk.Label(
            row,
            text=radio_sym,
            font=("Segoe UI", 12),
            fg=ACCENT_LIGHT if selected else TEXT_MUTED,
            bg=BG_CARD,
            cursor="hand2"
        )
        radio_lbl.pack(side=tk.LEFT, padx=(0, 10))
        card._radio_lbl = radio_lbl

        # Content box
        content = tk.Frame(row, bg=BG_CARD, cursor="hand2")
        content.pack(side=tk.LEFT, fill=tk.X, expand=True)

        header_row = tk.Frame(content, bg=BG_CARD, cursor="hand2")
        header_row.pack(anchor="w", pady=(0, 4))

        t_lbl = tk.Label(
            header_row,
            text=title,
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            cursor="hand2"
        )
        t_lbl.pack(side=tk.LEFT)

        if recommended:
            rec_badge = tk.Label(
                header_row,
                text="RECOMMENDED",
                font=("Segoe UI", 8, "bold"),
                fg=ACCENT_LIGHT,
                bg=ACCENT_BG,
                padx=6,
                pady=2,
                cursor="hand2"
            )
            rec_badge.pack(side=tk.LEFT, padx=(10, 0))

        d_lbl = tk.Label(
            content,
            text=desc,
            font=("Segoe UI", 9),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            wraplength=520,
            justify=tk.LEFT,
            anchor="w",
            cursor="hand2"
        )
        d_lbl.pack(anchor="w", fill=tk.X)

        # Click handler
        def on_click(e):
            self.select_mode(mode_id)

        for w in (card, row, radio_lbl, content, header_row, t_lbl, d_lbl):
            w.bind("<Button-1>", on_click)

        return card

    def make_layout_card(self, parent, layout_id, title, desc, recommended, selected=False):
        border_col = BG_CARD_ACTIVE_BORDER if selected else BG_CARD_BORDER
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            highlightbackground=border_col,
            highlightcolor=border_col,
            highlightthickness=1,
            padx=16,
            pady=14,
            cursor="hand2"
        )
        card.pack(fill=tk.X, pady=(0, 10))

        row = tk.Frame(card, bg=BG_CARD, cursor="hand2")
        row.pack(fill=tk.X)

        radio_sym = "●" if selected else "○"
        radio_lbl = tk.Label(
            row,
            text=radio_sym,
            font=("Segoe UI", 12),
            fg=ACCENT_LIGHT if selected else TEXT_MUTED,
            bg=BG_CARD,
            cursor="hand2"
        )
        radio_lbl.pack(side=tk.LEFT, padx=(0, 10))
        card._radio_lbl = radio_lbl

        content = tk.Frame(row, bg=BG_CARD, cursor="hand2")
        content.pack(side=tk.LEFT, fill=tk.X, expand=True)

        header_row = tk.Frame(content, bg=BG_CARD, cursor="hand2")
        header_row.pack(anchor="w", pady=(0, 4))

        t_lbl = tk.Label(
            header_row,
            text=title,
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
            cursor="hand2"
        )
        t_lbl.pack(side=tk.LEFT)

        if recommended:
            rec_badge = tk.Label(
                header_row,
                text="RECOMMENDED",
                font=("Segoe UI", 8, "bold"),
                fg=ACCENT_LIGHT,
                bg=ACCENT_BG,
                padx=6,
                pady=2,
                cursor="hand2"
            )
            rec_badge.pack(side=tk.LEFT, padx=(10, 0))

        d_lbl = tk.Label(
            content,
            text=desc,
            font=("Segoe UI", 9),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            wraplength=520,
            justify=tk.LEFT,
            anchor="w",
            cursor="hand2"
        )
        d_lbl.pack(anchor="w", fill=tk.X)

        def on_click(e):
            self.select_layout(layout_id)

        for w in (card, row, radio_lbl, content, header_row, t_lbl, d_lbl):
            w.bind("<Button-1>", on_click)

        return card

    def select_layout(self, layout_id):
        self.settings["keyboard_layout"] = layout_id
        save_settings(self.settings)

        for card, lid in self.layout_cards:
            is_cur = (lid == layout_id)
            border_col = BG_CARD_ACTIVE_BORDER if is_cur else BG_CARD_BORDER
            card.configure(
                highlightbackground=border_col,
                highlightcolor=border_col
            )
            card._radio_lbl.configure(
                text="●" if is_cur else "○",
                fg=ACCENT_LIGHT if is_cur else TEXT_MUTED
            )

    def select_mode(self, mode_id):
        self.settings["typing_mode"] = mode_id
        save_settings(self.settings)

        for card, mid in self.mode_cards:
            is_cur = (mid == mode_id)
            border_col = BG_CARD_ACTIVE_BORDER if is_cur else BG_CARD_BORDER
            card.configure(
                highlightbackground=border_col,
                highlightcolor=border_col
            )
            card._radio_lbl.configure(
                text="●" if is_cur else "○",
                fg=ACCENT_LIGHT if is_cur else TEXT_MUTED
            )

    def on_emoji_changed(self):
        self.settings["suggest_emoji"] = self.emoji_var.get()
        save_settings(self.settings)

    def on_autostart_changed(self):
        val = self.autostart_var.get()
        self.settings["autostart"] = val
        save_settings(self.settings)
        set_windows_autostart(val)

    def on_hotkey_changed(self, *args):
        self.settings["toggle_key"] = self.hotkey_var.get()
        save_settings(self.settings)

    # -------------------------------------------------------------
    # 4. Fonts Tab
    # -------------------------------------------------------------
    def create_fonts_view(self, parent):
        container = tk.Frame(parent, bg=BG_DARK)

        # Section: CANDIDATE POPUP TYPOGRAPHY
        self.make_section_label(container, "Candidate popup typography")

        font_card = self.make_card(container)
        f_box = tk.Frame(font_card, bg=BG_CARD)
        f_box.pack(fill=tk.X)

        # Column 1: Font Family
        font_col = tk.Frame(f_box, bg=BG_CARD)
        font_col.pack(side=tk.LEFT, padx=(0, 24))

        f_lbl = tk.Label(
            font_col,
            text="Font Family",
            font=("Segoe UI", 10),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        f_lbl.pack(anchor="w", pady=(0, 6))

        cur_font = self.settings.get("candidate_font", "Noto Sans Bengali")
        self.font_var = tk.StringVar(value=cur_font)
        self.font_combo = ttk.Combobox(
            font_col,
            textvariable=self.font_var,
            values=self.bengali_fonts,
            state="readonly",
            width=24
        )
        self.font_combo.pack(anchor="w")
        self.font_combo.bind("<<ComboboxSelected>>", self.on_font_changed)

        # Column 2: Size
        size_col = tk.Frame(f_box, bg=BG_CARD)
        size_col.pack(side=tk.LEFT)

        s_lbl = tk.Label(
            size_col,
            text="Size",
            font=("Segoe UI", 10),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        )
        s_lbl.pack(anchor="w", pady=(0, 6))

        self.size_options = [14, 16, 18, 20, 22, 24, 28]
        size_strings = [f"{s} pt" for s in self.size_options]
        cur_sz = self.settings.get("candidate_font_size", 16)
        sz_str = f"{cur_sz} pt" if cur_sz in self.size_options else "16 pt"

        self.size_var = tk.StringVar(value=sz_str)
        self.size_combo = ttk.Combobox(
            size_col,
            textvariable=self.size_var,
            values=size_strings,
            state="readonly",
            width=10
        )
        self.size_combo.pack(anchor="w")
        self.size_combo.bind("<<ComboboxSelected>>", self.on_size_changed)

        # Section: LIVE CANDIDATE PREVIEW
        self.make_section_label(container, "Live candidate preview")

        prev_card = self.make_card(container)

        # Inner HUD Dark Container matching macOS & Linux HUD Popup
        hud_box = tk.Frame(
            prev_card,
            bg="#111113",
            highlightbackground="#2e2e33",
            highlightcolor="#2e2e33",
            highlightthickness=1,
            padx=18,
            pady=16
        )
        hud_box.pack(fill=tk.X)

        self.aux_label = tk.Label(
            hud_box,
            text="ami  ·  বাংলা",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg="#111113"
        )
        self.aux_label.pack(anchor="w", pady=(0, 8))

        self.cand_labels = []
        cands = [("1", "আমি", True), ("2", "আমার", False), ("3", "আমরা", False)]
        for num, word, is_active in cands:
            row = tk.Frame(hud_box, bg="#111113")
            row.pack(anchor="w", pady=2)

            num_lbl = tk.Label(
                row,
                text=f"{num}  ",
                font=("Segoe UI", 11, "bold" if is_active else "normal"),
                fg=ACCENT_LIGHT if is_active else TEXT_MUTED,
                bg="#111113"
            )
            num_lbl.pack(side=tk.LEFT)

            w_lbl = tk.Label(
                row,
                text=word,
                font=(cur_font if cur_font != "System Font (Default)" else "Segoe UI", cur_sz, "bold" if is_active else "normal"),
                fg=TEXT_PRIMARY if is_active else TEXT_SECONDARY,
                bg="#111113"
            )
            w_lbl.pack(side=tk.LEFT)
            self.cand_labels.append((num_lbl, w_lbl, is_active))

        sep = tk.Frame(hud_box, bg=BG_CARD_BORDER, height=1)
        sep.pack(fill=tk.X, pady=(12, 10))

        self.sentence_label = tk.Label(
            hud_box,
            text="আমি বাংলায় গান গাই · বাংলা আমার অহংকার",
            font=(cur_font if cur_font != "System Font (Default)" else "Segoe UI", 12),
            fg=ACCENT_LIGHT,
            bg="#111113"
        )
        self.sentence_label.pack(anchor="w")

        # Action Buttons row (Refresh Fonts, Open Windows Fonts)
        act_row = tk.Frame(container, bg=BG_DARK)
        act_row.pack(fill=tk.X, pady=(6, 0))

        ref_btn = self.make_button(act_row, "Refresh Fonts", self.refresh_fonts)
        ref_btn.pack(side=tk.LEFT, padx=(0, 10))

        font_btn = self.make_button(act_row, "Open Windows Fonts ↗", self.open_system_fonts)
        font_btn.pack(side=tk.LEFT)

        return container

    def on_font_changed(self, *args):
        f = self.font_var.get()
        self.settings["candidate_font"] = f
        save_settings(self.settings)
        self.update_font_preview()

    def on_size_changed(self, *args):
        try:
            val_str = self.size_var.get().replace(" pt", "").strip()
            sz = int(val_str)
            self.settings["candidate_font_size"] = sz
            save_settings(self.settings)
            self.update_font_preview()
        except ValueError:
            pass

    def update_font_preview(self):
        f = self.settings.get("candidate_font", "Noto Sans Bengali")
        actual_font = "Segoe UI" if f == "System Font (Default)" else f
        s = self.settings.get("candidate_font_size", 16)

        for num_lbl, w_lbl, is_active in self.cand_labels:
            w_lbl.configure(font=(actual_font, s, "bold" if is_active else "normal"))

        self.sentence_label.configure(font=(actual_font, 12))

    def refresh_fonts(self):
        self.bengali_fonts = scan_bengali_fonts()
        self.font_combo["values"] = self.bengali_fonts

    def open_system_fonts(self):
        try:
            if sys.platform == "win32":
                os.system("start ms-settings:fonts")
            else:
                webbrowser.open("https://getbongo.app")
        except Exception:
            pass


def main():
    initial_tab = 0
    for arg in sys.argv[1:]:
        if arg.startswith("--tab="):
            try:
                initial_tab = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg == "--playground":
            initial_tab = 0

    root = tk.Tk()
    app = BongoSettingsApp(root, initial_tab=initial_tab)
    root.mainloop()


if __name__ == "__main__":
    main()
