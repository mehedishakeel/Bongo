#!/usr/bin/env python3
"""
Bongo Welcome & Settings Application for Linux
Replicates the native macOS Bongo interface on Linux desktops using GTK.
Provides 4 main sections:
1. Getting Started: Setup guide, language switching shortcuts, and interactive playground.
2. Bongo Layout: Complete searchable Avro phonetic keymap cheatsheet.
3. Settings: Typing modes (Phonetic first, Smart, Phonetic only), emoji suggestions, system status.
4. Fonts & Typography: Bengali font selector, candidate size, and live candidate HUD preview.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Setup GObject Introspection for GTK
import gi

gtk_version = None
for v in ['4.0', '3.0']:
    try:
        gi.require_version('Gtk', v)
        gtk_version = v
        break
    except (ValueError, AttributeError):
        continue

if not gtk_version:
    sys.stderr.write("Error: GTK (4.0 or 3.0) GObject libraries are not installed.\n")
    sys.exit(1)

from gi.repository import Gtk, Gdk, GLib, Pango
try:
    from gi.repository import GdkPixbuf
except ImportError:
    GdkPixbuf = None

# Set application ID and name early for desktop environment integration and dock icon matching
GLib.set_prgname("app.getbongo.Bongo")
GLib.set_application_name("Bongo")

# Configuration path (XDG Base Directory compliant)
CONFIG_DIR = Path.home() / ".config" / "bongo"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "keyboard_layout": 0,     # 0: Avro Phonetic, 1: National (Bijoy)
    "typing_mode": 0,         # 0: PhoneticFirst, 1: Smart, 2: PhoneticOnly
    "suggest_emoji": True,
    "candidate_font": "Noto Sans Bengali",
    "candidate_font_size": 16,
}


def find_app_icon():
    """Finds the Bongo application icon from source or standard system paths."""
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "icons" / "hicolor" / "32x32" / "apps" / "bongo.png",
        Path(__file__).resolve().parent.parent / "data" / "icons" / "bongo.png",
        Path.home() / ".local" / "share" / "icons" / "hicolor" / "32x32" / "apps" / "bongo.png",
        Path.home() / ".local" / "share" / "icons" / "hicolor" / "64x64" / "apps" / "bongo.png",
        Path("/usr/local/share/icons/hicolor/32x32/apps/bongo.png"),
        Path("/usr/share/icons/hicolor/32x32/apps/bongo.png"),
        Path("/usr/share/icons/hicolor/64x64/apps/bongo.png"),
    ]
    for p in candidates:
        if p.is_file():
            return str(p)
    return None


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
    """Scans system for available Bengali fonts via fontconfig or common fallbacks."""
    fonts = set()
    common_bengali_fonts = [
        "Noto Sans Bengali",
        "Noto Serif Bengali",
        "Kalpurush",
        "Siyam Rupali",
        "SolaimanLipi",
        "Mukti",
        "Lohit Bengali",
        "Vrinda",
        "Bangla Sangam MN",
        "Akaash",
        "Mitra Mono",
        "Sagar",
    ]
    try:
        res = subprocess.run(
            ["fc-list", ":lang=bn", "family"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                for f in line.split(","):
                    name = f.strip()
                    if name:
                        fonts.add(name)
    except Exception:
        pass

    # Ensure popular fonts are included if found in fontconfig or present
    for font_name in common_bengali_fonts:
        fonts.add(font_name)

    # Convert to sorted list
    font_list = sorted(list(fonts))
    return font_list


# CSS Styling matching modern Bongo design language
BONGO_CSS = """
/* Bongo Global Application Theme */
window, .bongo-window {
    background-color: #18181b;
    color: #f4f4f5;
}

/* Integrated Dark Titlebar / Headerbar */
headerbar, .bongo-headerbar, .titlebar, window decoration {
    background-color: #111113;
    background-image: none;
    color: #ffffff;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: none;
}

headerbar .title, .bongo-headerbar .title, .titlebar .title {
    color: #ffffff;
    font-weight: 700;
    font-size: 13.5px;
}

headerbar .subtitle, .bongo-headerbar .subtitle {
    color: #a1a1aa;
    font-size: 11px;
}

headerbar button, .bongo-headerbar button {
    color: #f4f4f5;
    background: transparent;
    border: none;
    box-shadow: none;
}

headerbar button:hover, .bongo-headerbar button:hover {
    background-color: rgba(255, 255, 255, 0.08);
}

.bongo-sidebar {
    background-color: #111113;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    padding: 24px 16px 20px 16px;
}

.bongo-brand-title {
    font-size: 22px;
    font-weight: 800;
    color: #6366f1;
}

.bongo-nav-btn {
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13.5px;
    font-weight: 500;
    background-color: transparent;
    background-image: none;
    color: #a1a1aa;
    border: none;
    outline: none;
    box-shadow: none;
}

.bongo-nav-btn:focus,
.bongo-nav-btn:active,
.bongo-nav-btn:checked {
    outline: none;
    box-shadow: none;
    border: none;
    background-image: none;
}

.bongo-nav-btn label {
    color: inherit;
    font-weight: inherit;
}

.bongo-nav-btn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #f4f4f5;
}

.bongo-nav-btn.active {
    background-color: rgba(99, 102, 241, 0.18);
    color: #818cf8;
    font-weight: 700;
}

.bongo-nav-btn.active:hover {
    background-color: rgba(99, 102, 241, 0.22);
    color: #818cf8;
}

.bongo-content-area {
    background-color: #18181b;
    padding: 28px 32px;
}

.bongo-heading {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 4px;
}

.bongo-subtitle {
    font-size: 13px;
    color: #a1a1aa;
    margin-bottom: 20px;
}

.bongo-section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #71717a;
    margin-top: 14px;
    margin-bottom: 6px;
}

.bongo-card {
    background-color: #202024;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}

.bongo-card-active {
    background-color: rgba(99, 102, 241, 0.10);
    border: 1.5px solid #6366f1;
}

.bongo-key-chip {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: monospace;
    font-weight: 600;
    font-size: 12px;
    color: #f4f4f5;
}

.bongo-badge-recommended {
    background-color: rgba(99, 102, 241, 0.20);
    color: #818cf8;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10.5px;
    font-weight: 700;
}

.bongo-table {
    background-color: #202024;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
}

.bongo-hud-preview {
    background: #202024;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 14px 18px;
}

.bongo-toggle-container {
    background-color: #202024;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 6px;
}

.bongo-toggle-btn {
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    background-color: transparent;
    color: #a1a1aa;
    border: none;
    outline: none;
    box-shadow: none;
}

.bongo-toggle-btn:hover {
    color: #f4f4f5;
    background-color: rgba(255, 255, 255, 0.06);
}

.bongo-toggle-btn.active {
    background-color: #6366f1;
    color: #ffffff;
    font-weight: 700;
}
"""


class BongoSettingsApp:
    def __init__(self, initial_tab=0):
        self.settings = load_settings()
        self.bengali_fonts = scan_bengali_fonts()
        self.active_tab_index = initial_tab
        self.setup_ui()

    def setup_ui(self):
        # Prefer dark theme for window decorations and titlebar
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings:
            gtk_settings.set_property("gtk-application-prefer-dark-theme", True)

        # Create Main Window with dark HeaderBar
        if gtk_version == '4.0':
            self.window = Gtk.Window(title="Bongo")
            self.window.set_default_size(920, 640)
            self.window.add_css_class("bongo-window")

            headerbar = Gtk.HeaderBar()
            headerbar.set_show_title_buttons(True)
            headerbar.add_css_class("bongo-headerbar")
            self.window.set_titlebar(headerbar)
        else:
            self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            self.window.set_title("Bongo")
            self.window.set_default_size(920, 640)
            self.window.get_style_context().add_class("bongo-window")
            self.window.set_position(Gtk.WindowPosition.CENTER)
            self.window.set_wmclass("app.getbongo.Bongo", "app.getbongo.Bongo")
            self.window.set_role("app.getbongo.Bongo")
            self.window.connect("destroy", Gtk.main_quit)

            headerbar = Gtk.HeaderBar()
            headerbar.set_show_close_button(True)
            headerbar.set_title("Bongo")
            headerbar.get_style_context().add_class("bongo-headerbar")
            self.window.set_titlebar(headerbar)

        Gtk.Window.set_default_icon_name("bongo")
        self.window.set_icon_name("bongo")

        icon_path = find_app_icon()
        if icon_path and os.path.exists(icon_path):
            try:
                if gtk_version != '4.0':
                    self.window.set_icon_from_file(icon_path)
                    Gtk.Window.set_default_icon_from_file(icon_path)
            except Exception:
                pass

        # Apply CSS
        css_provider = Gtk.CssProvider()
        if gtk_version == '4.0':
            css_provider.load_from_data(BONGO_CSS.encode('utf-8'))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        else:
            css_provider.load_from_data(BONGO_CSS.encode('utf-8'))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        # Root Split Box (Sidebar on left, Content on right)
        if gtk_version == '4.0':
            self.root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            self.window.set_child(self.root_box)
        else:
            self.root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            self.window.add(self.root_box)

        # Sidebar
        self.setup_sidebar()

        # Content Area Stack
        self.setup_content_area()

        # Connect initial selection
        self.select_tab(self.active_tab_index)

    def setup_sidebar(self):
        if gtk_version == '4.0':
            self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            self.sidebar_box.set_size_request(220, -1)
            self.sidebar_box.add_css_class("bongo-sidebar")
            self.root_box.append(self.sidebar_box)
        else:
            self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            self.sidebar_box.set_size_request(220, -1)
            self.sidebar_box.get_style_context().add_class("bongo-sidebar")
            self.root_box.pack_start(self.sidebar_box, False, False, 0)

        # Brand Header Box
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand_box.set_valign(Gtk.Align.CENTER)

        icon_path = find_app_icon()
        logo_image = None
        if icon_path and os.path.exists(icon_path):
            try:
                if gtk_version == '4.0':
                    logo_image = Gtk.Image.new_from_file(icon_path)
                    logo_image.set_pixel_size(32)
                else:
                    if GdkPixbuf:
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_path, 32, 32, True)
                        logo_image = Gtk.Image.new_from_pixbuf(pixbuf)
                    else:
                        logo_image = Gtk.Image.new_from_file(icon_path)
                        logo_image.set_pixel_size(32)
            except Exception:
                logo_image = None

        if not logo_image:
            try:
                if gtk_version == '4.0':
                    logo_image = Gtk.Image.new_from_icon_name("bongo")
                    logo_image.set_pixel_size(32)
                else:
                    logo_image = Gtk.Image.new_from_icon_name("bongo", Gtk.IconSize.DND)
            except Exception:
                logo_image = None

        if logo_image:
            if gtk_version == '4.0':
                brand_box.append(logo_image)
            else:
                brand_box.pack_start(logo_image, False, False, 0)

        brand_label = Gtk.Label(label="Bongo")
        if gtk_version == '4.0':
            brand_label.add_css_class("bongo-brand-title")
            brand_box.append(brand_label)
            self.sidebar_box.append(brand_box)
        else:
            brand_label.get_style_context().add_class("bongo-brand-title")
            brand_box.pack_start(brand_label, False, False, 0)
            self.sidebar_box.pack_start(brand_box, False, False, 0)

        # Separator spacing
        space = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        space.set_size_request(-1, 12)
        if gtk_version == '4.0':
            self.sidebar_box.append(space)
        else:
            self.sidebar_box.pack_start(space, False, False, 0)

        # Nav Buttons
        self.nav_buttons = []
        tab_names = [
            ("⭐  Getting Started", 0),
            ("⌨️  Bongo Layout", 1),
            ("⚙️  Settings", 2),
            ("🔤  Fonts", 3),
        ]
        for label_text, index in tab_names:
            btn = Gtk.Button()
            if gtk_version == '4.0':
                btn.set_focusable(False)
            else:
                btn.set_can_focus(False)
            btn_label = Gtk.Label(label=label_text)
            btn_label.set_xalign(0.0)
            btn_label.set_hexpand(True)
            if gtk_version == '4.0':
                btn.set_child(btn_label)
                btn.add_css_class("bongo-nav-btn")
                btn.connect("clicked", lambda b, idx=index: self.select_tab(idx))
                self.sidebar_box.append(btn)
            else:
                btn.add(btn_label)
                btn.get_style_context().add_class("bongo-nav-btn")
                btn.connect("clicked", lambda b, idx=index: self.select_tab(idx))
                self.sidebar_box.pack_start(btn, False, False, 0)
            self.nav_buttons.append(btn)

        # Bottom Version & Author Box
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        bottom_box.set_valign(Gtk.Align.END)
        bottom_box.set_vexpand(True)

        ver_label = Gtk.Label(label="v1.0.1 · linux")
        ver_label.set_xalign(0)
        ver_label.get_style_context().add_class("dim-label") if gtk_version != '4.0' else None

        author_label = Gtk.Label(label="Developed by Mehedi Shakeel")
        author_label.set_xalign(0)
        author_label.get_style_context().add_class("dim-label") if gtk_version != '4.0' else None

        if gtk_version == '4.0':
            bottom_box.append(ver_label)
            bottom_box.append(author_label)
            self.sidebar_box.append(bottom_box)
        else:
            bottom_box.pack_start(ver_label, False, False, 0)
            bottom_box.pack_start(author_label, False, False, 0)
            self.sidebar_box.pack_end(bottom_box, False, False, 0)

    def setup_content_area(self):
        # Content box
        if gtk_version == '4.0':
            self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.content_container.set_hexpand(True)
            self.content_container.set_vexpand(True)
            self.content_container.add_css_class("bongo-content-area")
            self.root_box.append(self.content_container)
        else:
            self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.content_container.get_style_context().add_class("bongo-content-area")
            self.root_box.pack_start(self.content_container, True, True, 0)

        # Header Titles
        self.heading_label = Gtk.Label()
        self.heading_label.set_xalign(0)
        if gtk_version == '4.0':
            self.heading_label.add_css_class("bongo-heading")
            self.content_container.append(self.heading_label)
        else:
            self.heading_label.get_style_context().add_class("bongo-heading")
            self.content_container.pack_start(self.heading_label, False, False, 0)

        self.subtitle_label = Gtk.Label()
        self.subtitle_label.set_xalign(0)
        if gtk_version == '4.0':
            self.subtitle_label.add_css_class("bongo-subtitle")
            self.content_container.append(self.subtitle_label)
        else:
            self.subtitle_label.get_style_context().add_class("bongo-subtitle")
            self.content_container.pack_start(self.subtitle_label, False, False, 0)

        # Scrolled View for main pages
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)

        if gtk_version == '4.0':
            self.content_container.append(self.scrolled_window)
        else:
            self.content_container.pack_start(self.scrolled_window, True, True, 0)

        # Stack holding the 4 views
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.view_getting_started = self.create_getting_started_view()
        self.view_cheatsheet = self.create_cheatsheet_view()
        self.view_settings = self.create_settings_view()
        self.view_fonts = self.create_fonts_view()

        self.stack.add_named(self.view_getting_started, "getting_started")
        self.stack.add_named(self.view_cheatsheet, "cheatsheet")
        self.stack.add_named(self.view_settings, "settings")
        self.stack.add_named(self.view_fonts, "fonts")

        if gtk_version == '4.0':
            self.scrolled_window.set_child(self.stack)
        else:
            self.scrolled_window.add(self.stack)

    def select_tab(self, index):
        self.active_tab_index = index
        titles = [
            ("Getting Started", "Everything you need to begin typing in Bangla."),
            ("Bongo Layout", "The complete phonetic key map at a glance."),
            ("Settings", "Choose how Bongo behaves while you type."),
            ("Fonts", "Make the suggestion popup comfortable to read.")
        ]
        page_names = ["getting_started", "cheatsheet", "settings", "fonts"]

        title, subtitle = titles[index]
        self.heading_label.set_text(title)
        self.subtitle_label.set_text(subtitle)
        self.stack.set_visible_child_name(page_names[index])

        for i, btn in enumerate(self.nav_buttons):
            if gtk_version == '4.0':
                if i == index:
                    btn.add_css_class("active")
                else:
                    btn.remove_css_class("active")
            else:
                ctx = btn.get_style_context()
                if i == index:
                    ctx.add_class("active")
                else:
                    ctx.remove_class("active")

    # -------------------------------------------------------------
    # 1. Getting Started Tab
    # -------------------------------------------------------------
    def create_getting_started_view(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Step 1 Card: Enable in Settings
        card1 = self.make_card()
        c1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c1_title = Gtk.Label(label="1. Enable Bongo in Your Input Method")
        c1_title.set_xalign(0)
        c1_title.set_markup("<b>1. Enable Bongo in Your Input Method</b>")
        c1_desc = Gtk.Label(
            label=(
                "GNOME / IBus: Settings -> Keyboard -> Input Sources -> Add, "
                "then choose Bengali (Bongo).\n"
                "KDE / Hyprland / Omarchy / fcitx5: run fcitx5-configtool and "
                "add Bongo under Input Method."
            )
        )
        c1_desc.set_xalign(0)
        c1_desc.set_wrap(True)

        c1_btn = Gtk.Button(label="Open Input Settings...")
        c1_btn.set_halign(Gtk.Align.START)
        c1_btn.connect("clicked", self.open_system_keyboard_settings)

        self.append_widget(c1_box, c1_title)
        self.append_widget(c1_box, c1_desc)
        self.append_widget(c1_box, c1_btn)
        self.set_card_content(card1, c1_box)
        self.append_widget(box, card1)

        # Step 2 Card: Switch Languages
        card2 = self.make_card()
        c2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c2_title = Gtk.Label()
        c2_title.set_xalign(0)
        c2_title.set_markup("<b>2. Switch Keyboards Quickly</b>")
        c2_desc = Gtk.Label(
            label="Press Super + Space or Control + Space anytime to toggle between English and Bongo."
        )
        c2_desc.set_xalign(0)
        c2_desc.set_wrap(True)

        chips_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        chip1 = self.make_key_chip("❖ Super + Space")
        chip2 = self.make_key_chip("⌃ Control + Space")
        self.append_widget(chips_row, chip1)
        self.append_widget(chips_row, chip2)

        self.append_widget(c2_box, c2_title)
        self.append_widget(c2_box, c2_desc)
        self.append_widget(c2_box, chips_row)
        self.set_card_content(card2, c2_box)
        self.append_widget(box, card2)

        # Step 3 Card: Phonetic Typing
        card3 = self.make_card()
        c3_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        c3_title = Gtk.Label()
        c3_title.set_xalign(0)
        c3_title.set_markup("<b>3. Type Natural Phonetic Bangla</b>")
        c3_desc = Gtk.Label(
            label="Type English letters phonetically according to how words sound. For example, ami becomes আমি, bangla becomes বাংলা, and dhonnobad becomes ধন্যবাদ."
        )
        c3_desc.set_xalign(0)
        c3_desc.set_wrap(True)

        self.append_widget(c3_box, c3_title)
        self.append_widget(c3_box, c3_desc)
        self.set_card_content(card3, c3_box)
        self.append_widget(box, card3)

        # Step 4: Interactive Playground
        card4 = self.make_card()
        c4_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        c4_title = Gtk.Label()
        c4_title.set_xalign(0)
        c4_title.set_markup("<b>Interactive Typing Playground</b>")
        c4_desc = Gtk.Label(
            label="Select Bongo from the top bar or switch shortcut, and try typing right inside this field:"
        )
        c4_desc.set_xalign(0)
        c4_desc.set_wrap(True)

        self.playground_entry = Gtk.Entry()
        self.playground_entry.set_placeholder_text("Switch to Bongo and type here (e.g. ami banglay gan gai)...")

        self.append_widget(c4_box, c4_title)
        self.append_widget(c4_box, c4_desc)
        self.append_widget(c4_box, self.playground_entry)
        self.set_card_content(card4, c4_box)
        self.append_widget(box, card4)

        return box

    def open_system_keyboard_settings(self, _btn):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        gnome_like = any(
            name in desktop for name in ("gnome", "unity", "pantheon")
        )
        if gnome_like:
            commands = [
                ["gnome-control-center", "keyboard"],
                ["ibus-setup"],
                ["fcitx5-configtool"],
            ]
        else:
            commands = [
                ["fcitx5-configtool"],
                ["kcmshell6", "kcm_keyboard"],
                ["kcmshell5", "kcm_keyboard"],
                ["gnome-control-center", "keyboard"],
                ["ibus-setup"],
            ]
        for cmd in commands:
            if not shutil.which(cmd[0]):
                continue
            try:
                subprocess.Popen(cmd)
                return
            except OSError:
                continue

    # -------------------------------------------------------------
    # 2. Cheatsheet / Layout Tab
    # -------------------------------------------------------------
    def create_cheatsheet_view(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        # 1. Dual Layout Switcher Bar
        toggle_wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        if gtk_version == '4.0':
            toggle_wrapper.add_css_class("bongo-toggle-container")
        else:
            toggle_wrapper.get_style_context().add_class("bongo-toggle-container")

        toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toggle_box.set_homogeneous(True)
        toggle_box.set_hexpand(True)

        self.btn_avro_cheatsheet = Gtk.Button(label="Avro Phonetic Layout")
        self.btn_national_cheatsheet = Gtk.Button(label="National / Bijoy (জাতীয়)")

        for btn in (self.btn_avro_cheatsheet, self.btn_national_cheatsheet):
            if gtk_version == '4.0':
                btn.add_css_class("bongo-toggle-btn")
            else:
                btn.get_style_context().add_class("bongo-toggle-btn")

        self.btn_avro_cheatsheet.connect("clicked", lambda b: self.switch_cheatsheet_mode("avro"))
        self.btn_national_cheatsheet.connect("clicked", lambda b: self.switch_cheatsheet_mode("national"))

        self.append_widget(toggle_box, self.btn_avro_cheatsheet)
        self.append_widget(toggle_box, self.btn_national_cheatsheet)
        self.append_widget(toggle_wrapper, toggle_box)
        self.append_widget(box, toggle_wrapper)

        # 2. Search filter box
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Quick filter keys (e.g. k, sh, a, Z, ক, য)...")
        self.search_entry.connect("search-changed", self.filter_cheatsheet)
        self.append_widget(box, self.search_entry)

        # Cheatsheet Data
        self.cheatsheet_rows = []

        # 3. Avro Layout Container
        self.avro_cheatsheet_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Section 1: Consonants
        self.append_widget(self.avro_cheatsheet_container, self.make_section_label("Consonants · ব্যঞ্জনবর্ণ"))
        c_table = self.build_key_grid([
            ("ক", "k"), ("ট", "T"), ("প", "p"), ("স", "s"),
            ("খ", "kh"), ("ঠ", "Th"), ("ফ", "ph, f"), ("হ", "h"),
            ("গ", "g"), ("ড", "D"), ("ব", "b"), ("ড়", "R"),
            ("ঘ", "gh"), ("ঢ", "Dh"), ("ভ", "bh, v"), ("ঢ়", "Rh"),
            ("ঙ", "Ng"), ("ণ", "N"), ("ম", "m"), ("য়", "y, Y"),
            ("চ", "c"), ("ত", "t"), ("য", "z"), ("শ", "sh, S"),
            ("ছ", "ch"), ("থ", "th"), ("র", "r"), ("ষ", "Sh"),
            ("জ", "j"), ("দ", "d"), ("ল", "l"), ("ং", "ng"),
            ("ঝ", "jh"), ("ধ", "dh"), ("ঃ", ":"), ("ঁ", "^"),
            ("ঞ", "NG"), ("ন", "n"), ("ৎ", "t``"), ("", "")
        ], cols=4, container_id="avro")
        self.append_widget(self.avro_cheatsheet_container, c_table)

        # Section 2: Vowels
        self.append_widget(self.avro_cheatsheet_container, self.make_section_label("Vowels · স্বরবর্ণ"))
        v_table = self.build_key_grid([
            ("অ", "o"), ("ই / কি", "i"), ("উ / কু", "u"),
            ("আ / কা", "a"), ("ঈ / কী", "I"), ("ঊ / কূ", "U"),
            ("ঋ / কৃ", "rri"), ("এ / কে", "e"), ("ও / কো", "O"),
            ("ঐ / কৈ", "OI"), ("ঔ / কৌ", "OU"), ("", "")
        ], cols=3, container_id="avro")
        self.append_widget(self.avro_cheatsheet_container, v_table)

        # Section 3: Special & Modifiers
        self.append_widget(self.avro_cheatsheet_container, self.make_section_label("Special & Modifiers · বিশেষ"))
        s_table = self.build_key_grid([
            ("্ হসন্ত", ",,"), ("ব-ফলা", "w"), ("রেফ", "rr (v)"),
            ("় নুক্তা", ".."), ("য-ফলা", "y, Z"), ("। দাঁড়ি", "."),
            ("ZWJ", "`"), ("র-ফলা", "r"), ("৳ টাকা", "$"),
            ("ZWNJ", "~"), ("", ""), ("", "")
        ], cols=3, container_id="avro")
        self.append_widget(self.avro_cheatsheet_container, s_table)

        # Section 4: Numbers
        self.append_widget(self.avro_cheatsheet_container, self.make_section_label("Numbers · সংখ্যা"))
        n_table = self.build_key_grid([
            ("০", "0"), ("১", "1"), ("২", "2"), ("৩", "3"), ("৪", "4"),
            ("৫", "5"), ("৬", "6"), ("৭", "7"), ("৮", "8"), ("৯", "9")
        ], cols=5, container_id="avro")
        self.append_widget(self.avro_cheatsheet_container, n_table)

        self.append_widget(box, self.avro_cheatsheet_container)

        # 4. National / Bijoy Layout Container
        self.national_cheatsheet_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Section 1: Consonants (BDS 1738:2004)
        self.append_widget(self.national_cheatsheet_container, self.make_section_label("Consonants · ব্যঞ্জনবর্ণ (BDS 1738:2004)"))
        nat_c_table = self.build_key_grid([
            ("ক", "j"), ("ট", "t"), ("প", "r"), ("স", "s"),
            ("খ", "J (Shift+j)"), ("ঠ", "T (Shift+t)"), ("ফ", "R (Shift+r)"), ("হ", "i"),
            ("গ", "o"), ("ড", "b"), ("ব", "h"), ("ড়", "P (Shift+p)"),
            ("ঘ", "O (Shift+o)"), ("ঢ", "B (Shift+b)"), ("ভ", "H (Shift+h)"), ("ঢ়", "V (Shift+v)"),
            ("ঙ", "q"), ("ণ", "p"), ("ম", "m"), ("য়", "W (Shift+w)"),
            ("চ", "y"), ("ত", "k"), ("য", "w"), ("ৎ", "` (Grave)"),
            ("ছ", "Y (Shift+y)"), ("থ", "K (Shift+k)"), ("র", "v"), ("ং", "Q (Shift+q)"),
            ("জ", "u"), ("দ", "l"), ("ল", "n"), ("ঃ", "X (Shift+x)"),
            ("ঝ", "U (Shift+u)"), ("ধ", "L (Shift+l)"), ("শ", "M (Shift+m)"), ("ঁ", "x"),
            ("ঞ", "e"), ("ন", "b"), ("ষ", "N (Shift+n)"), ("", "")
        ], cols=4, container_id="national")
        self.append_widget(self.national_cheatsheet_container, nat_c_table)

        # Section 2: Vowels & Kars
        self.append_widget(self.national_cheatsheet_container, self.make_section_label("Vowels & Kars · স্বরবর্ণ ও কার"))
        nat_v_table = self.build_key_grid([
            ("অ", "F (Shift+f)"), ("আ / া", "g+f / f"), ("ই / ি", "g+d / d"),
            ("ঈ / ী", "g+D / D"), ("উ / ু", "g+s / s"), ("ঊ / ূ", "g+S / S"),
            ("ঋ / ৃ", "A / a"), ("এ / ে", "g+c / c"), ("ঐ / ৈ", "g+C / C"),
            ("ও / ো", "g+1 / c+f"), ("ঔ / ৌ", "g+X / X"), ("", "")
        ], cols=3, container_id="national")
        self.append_widget(self.national_cheatsheet_container, nat_v_table)

        # Section 3: Conjuncts & Special Rules
        self.append_widget(self.national_cheatsheet_container, self.make_section_label("Conjuncts & Special Rules · যুক্তবর্ণ ও নিয়ম"))
        nat_s_table = self.build_key_grid([
            ("্ হসন্ত (Link Key)", "g (যেমন: j+g+k → ক্ত)"),
            ("্ র-ফলা", "z (যেমন: j+z → ক্র)"),
            ("্ য-ফলা", "Z (Shift+z)"),
            ("রেফ", "A (Shift+a) (যেমন: A+j → র্ক)"),
            ("কার আগে টাইপ (Pre-base)", "d + j → কি (যেমন বিজয়ে)"),
            ("দাঁড়ি / টাকা", "G (Shift+g) → । | $ → ৳")
        ], cols=2, container_id="national")
        self.append_widget(self.national_cheatsheet_container, nat_s_table)

        # Section 4: Numbers
        self.append_widget(self.national_cheatsheet_container, self.make_section_label("Numbers · সংখ্যা"))
        nat_n_table = self.build_key_grid([
            ("০", "0"), ("১", "1"), ("২", "2"), ("৩", "3"), ("৪", "4"),
            ("৫", "5"), ("৬", "6"), ("৭", "7"), ("৮", "8"), ("৯", "9")
        ], cols=5, container_id="national")
        self.append_widget(self.national_cheatsheet_container, nat_n_table)

        self.append_widget(box, self.national_cheatsheet_container)

        # Set default active mode to match current layout setting
        initial_mode = "national" if self.settings.get("keyboard_layout", 0) == 1 else "avro"
        self.switch_cheatsheet_mode(initial_mode)

        return box

    def build_key_grid(self, pairs, cols=4, container_id="avro"):
        card = self.make_card()
        grid = Gtk.Grid()
        grid.set_column_spacing(18)
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(True)

        r = 0
        c = 0
        for bn, en in pairs:
            if not bn and not en:
                c += 1
                if c >= cols:
                    c = 0
                    r += 1
                continue

            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            bn_label = Gtk.Label(label=bn)
            bn_label.set_markup(f"<span font='14'><b>{bn}</b></span>")
            bn_label.set_xalign(0)

            chip = self.make_key_chip(en)
            self.append_widget(item_box, bn_label)
            self.append_widget(item_box, chip)

            grid.attach(item_box, c, r, 1, 1)
            self.cheatsheet_rows.append((item_box, f"{bn} {en}".lower(), container_id))

            c += 1
            if c >= cols:
                c = 0
                r += 1

        self.set_card_content(card, grid)
        return card

    def switch_cheatsheet_mode(self, mode):
        self.cheatsheet_mode = mode
        is_avro = (mode == "avro")
        self.avro_cheatsheet_container.set_visible(is_avro)
        self.national_cheatsheet_container.set_visible(not is_avro)

        if gtk_version == '4.0':
            if is_avro:
                self.btn_avro_cheatsheet.add_css_class("active")
                self.btn_national_cheatsheet.remove_css_class("active")
            else:
                self.btn_national_cheatsheet.add_css_class("active")
                self.btn_avro_cheatsheet.remove_css_class("active")
        else:
            ctx_a = self.btn_avro_cheatsheet.get_style_context()
            ctx_n = self.btn_national_cheatsheet.get_style_context()
            if is_avro:
                ctx_a.add_class("active")
                ctx_n.remove_class("active")
            else:
                ctx_n.add_class("active")
                ctx_a.remove_class("active")

        if hasattr(self, 'search_entry'):
            self.filter_cheatsheet(self.search_entry)

    def filter_cheatsheet(self, entry):
        query = entry.get_text().lower().strip()
        for widget, text, container_id in self.cheatsheet_rows:
            if container_id == getattr(self, 'cheatsheet_mode', 'avro'):
                if not query or query in text:
                    widget.set_visible(True)
                else:
                    widget.set_visible(False)

    # -------------------------------------------------------------
    # 3. Settings Tab
    # -------------------------------------------------------------
    def create_settings_view(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Layout Section
        self.append_widget(box, self.make_section_label("Keyboard layout"))

        self.layout_cards = []
        layouts = [
            (0, "Avro Phonetic",
             "Modern phonetic input: type as you speak in English letters (e.g. ami -> আমি, bangla -> বাংলা).", True),
            (1, "National / Bijoy (জাতীয়)",
             "Standard Bangladesh BDS 1738:2004 layout: fixed keymap (e.g. j -> ক, d+j -> কি, g -> ্).", False)
        ]

        current_layout = self.settings.get("keyboard_layout", 0)

        for layout_id, title, desc, recommended in layouts:
            card = self.make_layout_card(layout_id, title, desc, recommended, selected=(layout_id == current_layout))
            self.layout_cards.append((card, layout_id))
            self.append_widget(box, card)

        # Mode Section
        self.append_widget(box, self.make_section_label("Typing mode"))

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
            card = self.make_mode_card(mode_id, title, desc, recommended, selected=(mode_id == current_mode))
            self.mode_cards.append((card, mode_id))
            self.append_widget(box, card)

        # Preferences Section
        self.append_widget(box, self.make_section_label("Preferences"))

        pref_card = self.make_card()
        pref_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        pref_label = Gtk.Label(label="Show emoji in suggestions")
        pref_label.set_xalign(0)
        pref_label.set_hexpand(True)

        self.emoji_switch = Gtk.Switch()
        self.emoji_switch.set_active(self.settings.get("suggest_emoji", True))
        self.emoji_switch.connect("state-set", self.on_emoji_toggled)

        self.append_widget(pref_box, pref_label)
        self.append_widget(pref_box, self.emoji_switch)
        self.set_card_content(pref_card, pref_box)
        self.append_widget(box, pref_card)

        # Updates & System Section
        self.append_widget(box, self.make_section_label("Updates & System"))

        sys_card = self.make_card()
        sys_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)

        import platform
        arch = platform.machine()
        sys_label = Gtk.Label(
            label=f"Linux Native · {arch} · IBus + fcitx5"
        )
        sys_label.set_xalign(0)
        sys_label.set_hexpand(True)

        update_btn = Gtk.Button(label="Check for Updates...")
        update_btn.connect("clicked", self.open_website)

        self.append_widget(sys_box, sys_label)
        self.append_widget(sys_box, update_btn)
        self.set_card_content(sys_card, sys_box)
        self.append_widget(box, sys_card)

        return box

    def make_layout_card(self, layout_id, title, desc, recommended, selected=False):
        card = self.make_card()
        if selected:
            if gtk_version == '4.0':
                card.add_css_class("bongo-card-active")
            else:
                card.get_style_context().add_class("bongo-card-active")

        c_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        check_label = Gtk.Label()
        check_label.set_markup("<b>●</b>" if selected else "○")
        card._check_label = check_label

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)

        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        t_label = Gtk.Label()
        t_label.set_markup(f"<b>{title}</b>")
        t_label.set_xalign(0)
        self.append_widget(header_row, t_label)

        if recommended:
            rec_badge = Gtk.Label(label="Recommended")
            if gtk_version == '4.0':
                rec_badge.add_css_class("bongo-badge-recommended")
            else:
                rec_badge.get_style_context().add_class("bongo-badge-recommended")
            self.append_widget(header_row, rec_badge)

        d_label = Gtk.Label(label=desc)
        d_label.set_wrap(True)
        d_label.set_xalign(0)
        if gtk_version != '4.0':
            d_label.get_style_context().add_class("dim-label")

        self.append_widget(info_box, header_row)
        self.append_widget(info_box, d_label)

        self.append_widget(c_box, check_label)
        self.append_widget(c_box, info_box)
        self.set_card_content(card, c_box)

        gesture = None
        if gtk_version == '4.0':
            gesture = Gtk.GestureClick()
            gesture.connect("released", lambda *args: self.select_layout(layout_id))
            card.add_controller(gesture)
        else:
            card.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            card.connect("button-press-event", lambda *args: self.select_layout(layout_id))

        return card

    def select_layout(self, layout_id):
        self.settings["keyboard_layout"] = layout_id
        save_settings(self.settings)

        for card, lid in self.layout_cards:
            is_cur = (lid == layout_id)
            if gtk_version == '4.0':
                if is_cur:
                    card.add_css_class("bongo-card-active")
                else:
                    card.remove_css_class("bongo-card-active")
            else:
                ctx = card.get_style_context()
                if is_cur:
                    ctx.add_class("bongo-card-active")
                else:
                    ctx.remove_class("bongo-card-active")
            if hasattr(card, '_check_label'):
                card._check_label.set_markup("<b>●</b>" if is_cur else "○")

        if hasattr(self, 'cheatsheet_mode') and hasattr(self, 'switch_cheatsheet_mode'):
            mode = "national" if layout_id == 1 else "avro"
            self.switch_cheatsheet_mode(mode)

    def make_mode_card(self, mode_id, title, desc, recommended, selected=False):
        card = self.make_card()
        if selected:
            if gtk_version == '4.0':
                card.add_css_class("bongo-card-active")
            else:
                card.get_style_context().add_class("bongo-card-active")

        c_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        # Radio check icon / marker
        check_label = Gtk.Label()
        check_label.set_markup("<b>●</b>" if selected else "○")
        card._check_label = check_label

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)

        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        t_label = Gtk.Label()
        t_label.set_markup(f"<b>{title}</b>")
        t_label.set_xalign(0)
        self.append_widget(header_row, t_label)

        if recommended:
            rec_badge = Gtk.Label(label="Recommended")
            if gtk_version == '4.0':
                rec_badge.add_css_class("bongo-badge-recommended")
            else:
                rec_badge.get_style_context().add_class("bongo-badge-recommended")
            self.append_widget(header_row, rec_badge)

        d_label = Gtk.Label(label=desc)
        d_label.set_wrap(True)
        d_label.set_xalign(0)
        if gtk_version != '4.0':
            d_label.get_style_context().add_class("dim-label")

        self.append_widget(info_box, header_row)
        self.append_widget(info_box, d_label)

        self.append_widget(c_box, check_label)
        self.append_widget(c_box, info_box)
        self.set_card_content(card, c_box)

        # Click event
        gesture = None
        if gtk_version == '4.0':
            gesture = Gtk.GestureClick()
            gesture.connect("released", lambda *args: self.select_mode(mode_id))
            card.add_controller(gesture)
        else:
            card.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            card.connect("button-press-event", lambda *args: self.select_mode(mode_id))

        return card

    def select_mode(self, mode_id):
        self.settings["typing_mode"] = mode_id
        save_settings(self.settings)

        for card, mid in self.mode_cards:
            is_cur = (mid == mode_id)
            if gtk_version == '4.0':
                if is_cur:
                    card.add_css_class("bongo-card-active")
                else:
                    card.remove_css_class("bongo-card-active")
            else:
                ctx = card.get_style_context()
                if is_cur:
                    ctx.add_class("bongo-card-active")
                else:
                    ctx.remove_class("bongo-card-active")
            if hasattr(card, '_check_label'):
                card._check_label.set_markup("<b>●</b>" if is_cur else "○")

    def on_emoji_toggled(self, switch, state):
        self.settings["suggest_emoji"] = state
        save_settings(self.settings)

    def open_website(self, _btn):
        import webbrowser
        webbrowser.open("https://getbongo.app")

    # -------------------------------------------------------------
    # 4. Fonts Tab
    # -------------------------------------------------------------
    def create_fonts_view(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        self.append_widget(box, self.make_section_label("Candidate popup typography"))

        font_card = self.make_card()
        f_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)

        # Font family dropdown
        font_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        font_lbl = Gtk.Label(label="Font Family")
        font_lbl.set_xalign(0)
        self.append_widget(font_col, font_lbl)

        if gtk_version == '4.0':
            self.font_combo = Gtk.DropDown.new_from_strings(self.bengali_fonts)
            cur_font = self.settings.get("candidate_font", "Noto Sans Bengali")
            if cur_font in self.bengali_fonts:
                self.font_combo.set_selected(self.bengali_fonts.index(cur_font))
            self.font_combo.connect("notify::selected", self.on_font_changed)
            self.append_widget(font_col, self.font_combo)
        else:
            self.font_combo = Gtk.ComboBoxText()
            cur_font = self.settings.get("candidate_font", "Noto Sans Bengali")
            cur_idx = 0
            for i, f in enumerate(self.bengali_fonts):
                self.font_combo.append_text(f)
                if f == cur_font:
                    cur_idx = i
            self.font_combo.set_active(cur_idx)
            self.font_combo.connect("changed", self.on_font_changed)
            self.append_widget(font_col, self.font_combo)

        # Size dropdown
        size_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        size_lbl = Gtk.Label(label="Size")
        size_lbl.set_xalign(0)
        self.append_widget(size_col, size_lbl)

        size_strings = ["14 pt", "16 pt", "18 pt", "20 pt", "22 pt", "24 pt", "28 pt"]
        self.sizes = [14, 16, 18, 20, 22, 24, 28]
        cur_size = self.settings.get("candidate_font_size", 16)
        size_idx = self.sizes.index(cur_size) if cur_size in self.sizes else 1

        if gtk_version == '4.0':
            self.size_combo = Gtk.DropDown.new_from_strings(size_strings)
            self.size_combo.set_selected(size_idx)
            self.size_combo.connect("notify::selected", self.on_size_changed)
            self.append_widget(size_col, self.size_combo)
        else:
            self.size_combo = Gtk.ComboBoxText()
            for s in size_strings:
                self.size_combo.append_text(s)
            self.size_combo.set_active(size_idx)
            self.size_combo.connect("changed", self.on_size_changed)
            self.append_widget(size_col, self.size_combo)

        self.append_widget(f_box, font_col)
        self.append_widget(f_box, size_col)
        self.set_card_content(font_card, f_box)
        self.append_widget(box, font_card)

        # Live candidate HUD preview
        self.append_widget(box, self.make_section_label("Live candidate preview"))

        prev_card = self.make_card()
        prev_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        if gtk_version == '4.0':
            prev_box.add_css_class("bongo-hud-preview")
        else:
            prev_box.get_style_context().add_class("bongo-hud-preview")

        aux_label = Gtk.Label(label="ami · বাংলা")
        aux_label.set_xalign(0)

        self.cand1 = Gtk.Label(label="1   আমি")
        self.cand1.set_xalign(0)

        self.cand2 = Gtk.Label(label="2   আমার")
        self.cand2.set_xalign(0)

        self.cand3 = Gtk.Label(label="3   আমরা")
        self.cand3.set_xalign(0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)

        self.sentence_label = Gtk.Label(label="আমি বাংলায় গান গাই · বাংলা আমার অহংকার")
        self.sentence_label.set_xalign(0)

        self.append_widget(prev_box, aux_label)
        self.append_widget(prev_box, self.cand1)
        self.append_widget(prev_box, self.cand2)
        self.append_widget(prev_box, self.cand3)
        self.append_widget(prev_box, sep)
        self.append_widget(prev_box, self.sentence_label)

        self.set_card_content(prev_card, prev_box)
        self.append_widget(box, prev_card)

        # Actions row (Refresh fonts, System Font Manager)
        actions_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        refresh_btn = Gtk.Button(label="Refresh Fonts")
        refresh_btn.connect("clicked", self.refresh_fonts)

        font_mgr_btn = Gtk.Button(label="Open Font Manager")
        font_mgr_btn.connect("clicked", self.open_font_manager)

        self.append_widget(actions_row, refresh_btn)
        self.append_widget(actions_row, font_mgr_btn)
        self.append_widget(box, actions_row)

        self.update_font_preview()
        return box

    def on_font_changed(self, *_args):
        if gtk_version == '4.0':
            idx = self.font_combo.get_selected()
            font_name = self.bengali_fonts[idx]
        else:
            font_name = self.font_combo.get_active_text()
        if font_name:
            self.settings["candidate_font"] = font_name
            save_settings(self.settings)
            self.update_font_preview()

    def on_size_changed(self, *_args):
        if gtk_version == '4.0':
            idx = self.size_combo.get_selected()
            sz = self.sizes[idx]
        else:
            idx = self.size_combo.get_active()
            sz = self.sizes[idx] if idx >= 0 and idx < len(self.sizes) else 16
        self.settings["candidate_font_size"] = sz
        save_settings(self.settings)
        self.update_font_preview()

    def update_font_preview(self):
        font_name = self.settings.get("candidate_font", "Noto Sans Bengali")
        font_size = self.settings.get("candidate_font_size", 16)
        markup_tmpl = "<span font_desc='{} {}'>{}</span>"

        self.cand1.set_markup(markup_tmpl.format(font_name, font_size, "<b>1   আমি</b>"))
        self.cand2.set_markup(markup_tmpl.format(font_name, font_size, "2   আমার"))
        self.cand3.set_markup(markup_tmpl.format(font_name, font_size, "3   আমরা"))
        self.sentence_label.set_markup(markup_tmpl.format(font_name, font_size, "আমি বাংলায় গান গাই · বাংলা আমার অহংকার"))

    def refresh_fonts(self, _btn):
        self.bengali_fonts = scan_bengali_fonts()
        cur_font = self.settings.get("candidate_font", "Noto Sans Bengali")
        if gtk_version == '4.0':
            self.font_combo.set_model(Gtk.StringList.new(self.bengali_fonts))
            if cur_font in self.bengali_fonts:
                self.font_combo.set_selected(self.bengali_fonts.index(cur_font))
        else:
            self.font_combo.remove_all()
            cur_idx = 0
            for i, f in enumerate(self.bengali_fonts):
                self.font_combo.append_text(f)
                if f == cur_font:
                    cur_idx = i
            self.font_combo.set_active(cur_idx)
        self.update_font_preview()

    def open_font_manager(self, _btn):
        for cmd in [["gnome-font-viewer"], ["font-manager"], ["kfontview"]]:
            try:
                subprocess.Popen(cmd)
                return
            except FileNotFoundError:
                continue

    # -------------------------------------------------------------
    # Shared UI Helpers
    # -------------------------------------------------------------
    def make_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        if gtk_version == '4.0':
            card.add_css_class("bongo-card")
        else:
            card.get_style_context().add_class("bongo-card")
        return card

    def set_card_content(self, card, child):
        if gtk_version == '4.0':
            card.append(child)
        else:
            card.pack_start(child, True, True, 0)

    def append_widget(self, parent, child):
        if gtk_version == '4.0':
            parent.append(child)
        else:
            parent.pack_start(child, False, False, 0)

    def make_section_label(self, text):
        lbl = Gtk.Label(label=text)
        lbl.set_xalign(0)
        if gtk_version == '4.0':
            lbl.add_css_class("bongo-section-label")
        else:
            lbl.get_style_context().add_class("bongo-section-label")
        return lbl

    def make_key_chip(self, text):
        chip = Gtk.Label(label=text)
        if gtk_version == '4.0':
            chip.add_css_class("bongo-key-chip")
        else:
            chip.get_style_context().add_class("bongo-key-chip")
        return chip

    def run(self):
        if gtk_version == '4.0':
            self.window.present()
            # Gtk4 loop via Application or simple activate
            app = Gtk.Application(application_id="app.getbongo.Bongo")
            def on_activate(application):
                self.window.set_application(application)
                self.window.present()
            app.connect("activate", on_activate)
            app.run(sys.argv)
        else:
            self.window.show_all()
            Gtk.main()


def main():
    initial_tab = 0
    if "--tab" in sys.argv:
        try:
            idx = sys.argv.index("--tab")
            if idx + 1 < len(sys.argv):
                initial_tab = int(sys.argv[idx + 1])
                # Remove --tab args so GTK Application doesn't complain
                sys.argv.pop(idx + 1)
                sys.argv.pop(idx)
        except (ValueError, IndexError):
            pass
    app = BongoSettingsApp(initial_tab=initial_tab)
    app.run()


if __name__ == "__main__":
    main()
