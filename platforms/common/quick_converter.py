#!/usr/bin/env python3
"""
Bongo Quick Converter - Fast, floating linguistic utility for Desktop (Windows, Linux, macOS)
Provides instant:
  1. Bijoy (ANSI / SutonnyMJ) ⇄ Unicode bidirectional text conversion
  2. Bengali Number-to-Words conversion with currency mode (টাকা মাত্র)
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add repo root to import path if needed
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from platforms.common.converter import (
        unicode_to_bijoy,
        bijoy_to_unicode,
        bengali_number_to_words,
    )
except ImportError:
    # Local fallback
    try:
        from converter import unicode_to_bijoy, bijoy_to_unicode, bengali_number_to_words
    except ImportError:
        def unicode_to_bijoy(t): return t
        def bijoy_to_unicode(t): return t
        def bengali_number_to_words(n, as_currency=False): return str(n)


class QuickConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bongo Quick Converter")
        self.root.geometry("640x520")
        self.root.minsize(560, 440)

        # Style palette (matching Bongo dark design)
        self.bg_color = "#18191b"
        self.card_bg = "#222326"
        self.input_bg = "#121315"
        self.fg_color = "#f4f4f5"
        self.accent_color = "#4f46e5"
        self.accent_hover = "#6366f1"
        self.text_muted = "#a1a1aa"

        self.root.configure(bg=self.bg_color)

        self.create_widgets()
        self.check_initial_clipboard()

        # Keyboard shortcuts
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Control-Return>", lambda e: self.convert_to_unicode())
        self.root.bind("<Command-Return>", lambda e: self.convert_to_unicode())

    def create_widgets(self):
        # Header Frame
        header = tk.Frame(self.root, bg=self.bg_color, pady=10, padx=16)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="Bongo Linguistic Converter",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 15, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        title.pack(side=tk.LEFT)

        subtitle = tk.Label(
            header,
            text="Bijoy ⇄ Unicode & Number Words",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10),
            bg=self.bg_color,
            fg=self.text_muted,
        )
        subtitle.pack(side=tk.LEFT, padx=10, pady=2)

        # Notebook (Tabs)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=self.card_bg,
            foreground=self.fg_color,
            padding=[16, 6],
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.accent_color)],
            foreground=[("selected", "#ffffff")],
        )

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=6)

        # Tab 1: Text Converter
        text_tab = tk.Frame(notebook, bg=self.bg_color, padx=10, pady=10)
        notebook.add(text_tab, text="Bijoy ⇄ Unicode")
        self.build_text_converter_tab(text_tab)

        # Tab 2: Number to Words
        num_tab = tk.Frame(notebook, bg=self.bg_color, padx=10, pady=10)
        notebook.add(num_tab, text="Number to Words")
        self.build_number_tab(num_tab)

    def build_text_converter_tab(self, parent):
        # Input Label
        lbl_in = tk.Label(
            parent,
            text="Input Text (Paste or Type):",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        lbl_in.pack(anchor=tk.W, pady=(0, 4))

        self.txt_input = tk.Text(
            parent,
            height=6,
            bg=self.input_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            font=("Noto Sans Bengali" if sys.platform != "darwin" else "Bangla Sangam MN", 12),
            padx=8,
            pady=8,
        )
        self.txt_input.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Action Buttons Row
        btn_bar = tk.Frame(parent, bg=self.bg_color)
        btn_bar.pack(fill=tk.X, pady=4)

        btn_u2b = tk.Button(
            btn_bar,
            text="Unicode ➔ Bijoy (ANSI)",
            bg=self.accent_color,
            fg="#ffffff",
            activebackground=self.accent_hover,
            activeforeground="#ffffff",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.convert_to_bijoy,
        )
        btn_u2b.pack(side=tk.LEFT, padx=(0, 6))

        btn_b2u = tk.Button(
            btn_bar,
            text="Bijoy (ANSI) ➔ Unicode",
            bg=self.accent_color,
            fg="#ffffff",
            activebackground=self.accent_hover,
            activeforeground="#ffffff",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.convert_to_unicode,
        )
        btn_b2u.pack(side=tk.LEFT, padx=6)

        btn_swap = tk.Button(
            btn_bar,
            text="⇄ Swap",
            bg=self.card_bg,
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.swap_text,
        )
        btn_swap.pack(side=tk.LEFT, padx=6)

        btn_clear = tk.Button(
            btn_bar,
            text="Clear",
            bg=self.card_bg,
            fg=self.text_muted,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.clear_text,
        )
        btn_clear.pack(side=tk.RIGHT)

        # Output Label + Copy
        lbl_out_row = tk.Frame(parent, bg=self.bg_color)
        lbl_out_row.pack(fill=tk.X, pady=(10, 4))

        lbl_out = tk.Label(
            lbl_out_row,
            text="Converted Output:",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        lbl_out.pack(side=tk.LEFT)

        self.btn_copy = tk.Button(
            lbl_out_row,
            text="📋 Copy Output",
            bg=self.card_bg,
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.copy_output,
        )
        self.btn_copy.pack(side=tk.RIGHT)

        self.txt_output = tk.Text(
            parent,
            height=6,
            bg=self.input_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            font=("Noto Sans Bengali" if sys.platform != "darwin" else "Bangla Sangam MN", 12),
            padx=8,
            pady=8,
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True)

    def build_number_tab(self, parent):
        lbl = tk.Label(
            parent,
            text="Enter Number (English digits 0-9 or Bengali ০-৯):",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        lbl.pack(anchor=tk.W, pady=(8, 6))

        self.num_entry = tk.Entry(
            parent,
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 14),
            bg=self.input_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT,
        )
        self.num_entry.pack(fill=tk.X, ipady=6, pady=(0, 10))
        self.num_entry.insert(0, "12500")
        self.num_entry.bind("<KeyRelease>", lambda e: self.update_number_words())

        self.var_currency = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            parent,
            text="Currency mode (append 'টাকা মাত্র')",
            variable=self.var_currency,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.card_bg,
            activebackground=self.bg_color,
            activeforeground=self.fg_color,
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10),
            command=self.update_number_words,
        )
        chk.pack(anchor=tk.W, pady=(0, 14))

        # Result Card
        res_card = tk.Frame(parent, bg=self.card_bg, padx=16, pady=16)
        res_card.pack(fill=tk.X, pady=8)

        lbl_res_title = tk.Label(
            res_card,
            text="Bengali Spoken Words:",
            font=("Segoe UI" if sys.platform == "win32" else "Helvetica", 10),
            bg=self.card_bg,
            fg=self.text_muted,
        )
        lbl_res_title.pack(anchor=tk.W)

        self.lbl_num_result = tk.Label(
            res_card,
            text="",
            font=("Noto Sans Bengali" if sys.platform != "darwin" else "Bangla Sangam MN", 15, "bold"),
            bg=self.card_bg,
            fg="#34d399",
            wraplength=520,
            justify=tk.LEFT,
        )
        self.lbl_num_result.pack(anchor=tk.W, pady=(6, 12))

        btn_copy_num = tk.Button(
            res_card,
            text="📋 Copy Result",
            bg=self.accent_color,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.copy_num_result,
        )
        btn_copy_num.pack(anchor=tk.W)

        self.update_number_words()

    def check_initial_clipboard(self):
        try:
            clip = self.root.clipboard_get()
            if clip and len(clip.strip()) > 0:
                self.txt_input.insert("1.0", clip)
        except Exception:
            pass

    def convert_to_unicode(self):
        src = self.txt_input.get("1.0", tk.END).strip()
        if not src:
            return
        out = bijoy_to_unicode(src)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert("1.0", out)

    def convert_to_bijoy(self):
        src = self.txt_input.get("1.0", tk.END).strip()
        if not src:
            return
        out = unicode_to_bijoy(src)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert("1.0", out)

    def swap_text(self):
        in_text = self.txt_input.get("1.0", tk.END).strip()
        out_text = self.txt_output.get("1.0", tk.END).strip()
        self.txt_input.delete("1.0", tk.END)
        self.txt_output.delete("1.0", tk.END)
        self.txt_input.insert("1.0", out_text)
        self.txt_output.insert("1.0", in_text)

    def clear_text(self):
        self.txt_input.delete("1.0", tk.END)
        self.txt_output.delete("1.0", tk.END)

    def copy_output(self):
        out = self.txt_output.get("1.0", tk.END).strip()
        if out:
            self.root.clipboard_clear()
            self.root.clipboard_append(out)
            orig_text = self.btn_copy.cget("text")
            self.btn_copy.config(text="✓ Copied!")
            self.root.after(1500, lambda: self.btn_copy.config(text=orig_text))

    def update_number_words(self):
        raw = self.num_entry.get().strip()
        if not raw:
            self.lbl_num_result.config(text="")
            return
        words = bengali_number_to_words(raw, as_currency=self.var_currency.get())
        self.lbl_num_result.config(text=words)

    def copy_num_result(self):
        res = self.lbl_num_result.cget("text")
        if res:
            self.root.clipboard_clear()
            self.root.clipboard_append(res)
            messagebox.showinfo("Bongo", "Bengali words copied to clipboard!")


def main():
    root = tk.Tk()
    app = QuickConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
