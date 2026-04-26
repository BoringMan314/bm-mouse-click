import os
import sys
import time
import ctypes
import threading
import webbrowser
import subprocess
import json
from typing import List, Tuple
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, messagebox

try:
    import winsound
except Exception:
    winsound = None

from PIL import Image, ImageDraw, ImageTk
import pystray
import keyboard
from pynput.mouse import Controller, Button

import bm_single_instance


APP_TITLE_SUFFIX = "V1.0 By. [B.M] 圓周率 3.14"
ABOUT_URL = "http://exnormal.com:81/"
SINGLE_APP_ID = "bm-mouse-click"
WINDOW_POS_X = 100
WINDOW_POS_Y = 100
DEFAULT_TK_FONT_SIZE = 10
                                     
SETTINGS_FILE_BASENAME_MAIN = "bm-mouse-click"
DEFAULT_SETTINGS = {
    "languages": "zh_TW",
    "interval_ms": 50,
    "hotkey": {"ctrl": True, "alt": False, "win": False, "key": "F6"},
}


def apply_default_font_size(root):
    for name in (
        "TkDefaultFont",
        "TkTextFont",
        "TkFixedFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    ):
        try:
            tkfont.nametofont(name).configure(size=DEFAULT_TK_FONT_SIZE)
        except tk.TclError:
            pass


HOTKEY_ALIAS_MAP = {
    "PAGE UP": "PAGEUP",
    "PAGE DOWN": "PAGEDOWN",
    "PGUP": "PAGEUP",
    "PGDN": "PAGEDOWN",
    "PRTSC": "PRINTSCREEN",
    "PRINT": "PRINTSCREEN",
    "SCROLL LOCK": "SCROLLLOCK",
    "NUMPAD+": "NUMPADADD",
    "NUMPAD-": "NUMPADSUB",
    "NUMPAD/": "NUMPADDIV",
    "NUMPAD*": "NUMPADMUL",
    "KP_ADD": "NUMPADADD",
    "KP_SUBTRACT": "NUMPADSUB",
    "KP_DIVIDE": "NUMPADDIV",
    "KP_MULTIPLY": "NUMPADMUL",
}

HOTKEY_SPECIAL_KEYS = {
    ",",
    ".",
    "/",
    "-",
    "=",
    "+",
    "INSERT",
    "DELETE",
    "HOME",
    "END",
    "PAGEUP",
    "PAGEDOWN",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "PRINTSCREEN",
    "PAUSE",
    "SCROLLLOCK",
    "NUMPAD0",
    "NUMPAD1",
    "NUMPAD2",
    "NUMPAD3",
    "NUMPAD4",
    "NUMPAD5",
    "NUMPAD6",
    "NUMPAD7",
    "NUMPAD8",
    "NUMPAD9",
    "NUMPADADD",
    "NUMPADSUB",
    "NUMPADDIV",
    "NUMPADMUL",
}

HOTKEY_KEY_TO_KEYBOARD = {
    ",": ",",
    ".": ".",
    "/": "/",
    "-": "-",
    "=": "=",
    "+": "plus",
    "INSERT": "insert",
    "DELETE": "delete",
    "HOME": "home",
    "END": "end",
    "PAGEUP": "page up",
    "PAGEDOWN": "page down",
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
    "PRINTSCREEN": "print screen",
    "PAUSE": "pause",
    "SCROLLLOCK": "scroll lock",
    "NUMPAD0": "num 0",
    "NUMPAD1": "num 1",
    "NUMPAD2": "num 2",
    "NUMPAD3": "num 3",
    "NUMPAD4": "num 4",
    "NUMPAD5": "num 5",
    "NUMPAD6": "num 6",
    "NUMPAD7": "num 7",
    "NUMPAD8": "num 8",
    "NUMPAD9": "num 9",
    "NUMPADADD": "add",
    "NUMPADSUB": "subtract",
    "NUMPADDIV": "divide",
    "NUMPADMUL": "multiply",
}


def _primary_screen_origin() -> Tuple[int, int]:
    if sys.platform != "win32":
        return 0, 0
    try:
        MONITOR_DEFAULTTOPRIMARY = 1

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        user32 = ctypes.windll.user32
        m = user32.MonitorFromPoint(POINT(0, 0), MONITOR_DEFAULTTOPRIMARY)
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if m and user32.GetMonitorInfoW(m, ctypes.byref(mi)):
            return int(mi.rcMonitor.left), int(mi.rcMonitor.top)
    except Exception:
        pass
    return 0, 0
BUILTIN_LANG_ORDER = ["zh_TW", "zh_CN", "ja_JP", "en_US"]
BUILTIN_I18N = {
    "zh_TW": {
        "language_name": "繁體中文",
        "settings": "設定",
        "project_name": "滑鼠連點",
        "interval": "連點間隔 (ms)：",
        "hotkey": "啟動/停止熱鍵：",
        "save_settings": "儲存設定",
        "restore_default": "還原預設",
        "status_stop": "狀態：已停止",
        "status_run": "狀態：連點中",
        "status_hotkey": "狀態：熱鍵已套用 ({hotkey})",
        "hint": "",
        "error_interval": "連點間隔必須是大於 0 的整數毫秒。",
        "error_hotkey": "按鍵請填有效按鍵，例如 F6、Q。",
        "about": "關於",
        "exit": "離開",
        "input_error_title": "輸入錯誤",
        "hotkey_error_title": "熱鍵錯誤",
    },
    "zh_CN": {
        "language_name": "简体中文",
        "settings": "设置",
        "project_name": "鼠标连点",
        "interval": "连点间隔 (ms)：",
        "hotkey": "启动/停止热键：",
        "save_settings": "保存设置",
        "restore_default": "还原默认",
        "status_stop": "状态：已停止",
        "status_run": "状态：连点中",
        "status_hotkey": "状态：热键已套用 ({hotkey})",
        "hint": "",
        "error_interval": "连点间隔必须是大于 0 的整数毫秒。",
        "error_hotkey": "按键请填有效按键，例如 F6、Q。",
        "about": "关于",
        "exit": "离开",
        "input_error_title": "输入错误",
        "hotkey_error_title": "热键错误",
    },
    "ja_JP": {
        "language_name": "日本語",
        "settings": "設定",
        "project_name": "マウス連点",
        "interval": "連點間隔 (ms)：",
        "hotkey": "開始/停止ホットキー：",
        "save_settings": "設定を保存",
        "restore_default": "既定に戻す",
        "status_stop": "状態：停止",
        "status_run": "状態：連點中",
        "status_hotkey": "状態：ホットキー適用済み ({hotkey})",
        "hint": "",
        "error_interval": "連點間隔は 0 より大きい整数ミリ秒で入力してください。",
        "error_hotkey": "有効なキーを入力してください。例：F6、Q",
        "about": "バージョン情報",
        "exit": "終了",
        "input_error_title": "入力エラー",
        "hotkey_error_title": "ホットキーエラー",
    },
    "en_US": {
        "language_name": "English",
        "settings": "Settings",
        "project_name": "Mouse Clicker",
        "interval": "Click Interval (ms):",
        "hotkey": "Start/Stop Hotkey:",
        "save_settings": "Save Settings",
        "restore_default": "Restore Default",
        "status_stop": "Status: Stopped",
        "status_run": "Status: Clicking",
        "status_hotkey": "Status: Hotkey applied ({hotkey})",
        "hint": "",
        "error_interval": "Interval must be an integer milliseconds value greater than 0.",
        "error_hotkey": "Key must be valid (e.g. F6, Q).",
        "about": "About",
        "exit": "Exit",
        "input_error_title": "Input Error",
        "hotkey_error_title": "Hotkey Error",
    },
}

BUILTIN_I18N_REF_KEYS = frozenset(BUILTIN_I18N["zh_TW"].keys())


def _default_ui_language(lang_order: List[str]) -> str:
    if "zh_TW" in lang_order:
        return "zh_TW"
    return lang_order[0] if lang_order else "zh_TW"


def merged_lang_table(raw_languages) -> dict:
    base = json.loads(json.dumps(BUILTIN_I18N))
    if not isinstance(raw_languages, dict):
        return base
    fallback = BUILTIN_I18N["zh_TW"]
    for code, messages in raw_languages.items():
        if not isinstance(code, str) or not code.strip():
            continue
        if not isinstance(messages, dict):
            continue
        if "language_name" not in messages:
            continue
        norm_code = code.strip()
        if norm_code not in base:
            base[norm_code] = dict(fallback)
        for key, value in messages.items():
            if isinstance(value, str):
                base[norm_code][key] = value
    return base


def available_ui_languages(lang_map: dict) -> List[str]:
    ordered = [x for x in BUILTIN_LANG_ORDER if x in lang_map]
    extras = [k for k in lang_map.keys() if k not in BUILTIN_LANG_ORDER]
    ordered.extend(extras)
    if not ordered:
        return ["zh_TW"]
    return ordered


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_settings_file() -> str:
                                           
    base_name = SETTINGS_FILE_BASENAME_MAIN
    return os.path.join(get_app_dir(), f"{base_name}.json")


SETTINGS_FILE = get_settings_file()


def _is_valid_mouse_settings_raw(raw) -> bool:
    if not isinstance(raw, dict):
        return False
    if "settings" not in raw or "languages" not in raw:
        return False
    st = raw["settings"]
    if not isinstance(st, dict):
        return False
    code = st.get("languages")
    if not isinstance(code, str) or not str(code).strip():
        return False
    code = str(code).strip()
    lg = raw["languages"]
    if not isinstance(lg, dict) or not lg or code not in lg:
        return False
    for m in lg.values():
        if not isinstance(m, dict):
            return False
        if frozenset(m.keys()) != BUILTIN_I18N_REF_KEYS:
            return False
        for rk in BUILTIN_I18N_REF_KEYS:
            v = m.get(rk)
            if not isinstance(v, str):
                return False
            if rk in ("language_name", "project_name", "settings") and not v.strip():
                return False
    if "interval_ms" not in st or "hotkey" not in st:
        return False
    if not isinstance(st.get("hotkey"), dict):
        return False
    hk = st["hotkey"]
    for req in ("ctrl", "alt", "win", "key"):
        if req not in hk:
            return False
    try:
        if int(st.get("interval_ms", 0)) < 1:
            return False
    except (TypeError, ValueError):
        return False
    return True


def get_resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", get_app_dir())
    return os.path.join(base, name)


def create_icon_image(size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (20, 24, 34, 255))
    d = ImageDraw.Draw(img)
    pad = int(size * 0.08)
    d.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=int(size * 0.2),
        fill=(28, 36, 50, 255),
        outline=(86, 115, 255, 255),
        width=max(2, size // 64),
    )
    center = size // 2
    r = int(size * 0.28)
    d.ellipse(
        [center - r, center - r, center + r, center + r],
        fill=(64, 214, 255, 255),
        outline=(255, 255, 255, 220),
        width=max(2, size // 80),
    )
    d.text((center - int(size * 0.16), center - int(size * 0.11)), "BM", fill=(15, 24, 38, 255))
    dot_r = max(2, size // 24)
    d.ellipse(
        [center + int(size * 0.18) - dot_r, center + int(size * 0.18) - dot_r,
         center + int(size * 0.18) + dot_r, center + int(size * 0.18) + dot_r],
        fill=(255, 225, 67, 255),
    )
    return img


class MouseClickerApp:
    def __init__(self):
        self.i18n = merged_lang_table({})
        self.lang_order = available_ui_languages(self.i18n)
        self.custom_languages = {}
        self.settings = self.load_settings()
        self.language = self.settings["languages"]
        if self.language not in self.lang_order:
            self.language = _default_ui_language(self.lang_order)
        self.default_hotkey = DEFAULT_SETTINGS["hotkey"].copy()

        self.root = tk.Tk()
        apply_default_font_size(self.root)
        self.root.title(self.get_app_title())
        self._set_app_user_model_id()
        ox, oy = _primary_screen_origin()
        self.root.geometry(f"400x220+{ox + WINDOW_POS_X}+{oy + WINDOW_POS_Y}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.root.bind("<Unmap>", self.on_root_unmap)
        self.root.bind("<Activate>", self._on_root_activate, add="+")
        self.root.bind("<Deactivate>", self._on_root_deactivate, add="+")
        self.root.bind("<FocusIn>", self._on_root_focus_in, add="+")

        self.icon_img = create_icon_image(256)
        self.tk_icon = ImageTk.PhotoImage(self.icon_img.resize((64, 64), Image.LANCZOS))
        self.root.iconphoto(True, self.tk_icon)

        self.interval_var = tk.StringVar(value=str(self.settings["interval_ms"]))
        self.ctrl_var = tk.BooleanVar(value=self.settings["hotkey"]["ctrl"])
        self.alt_var = tk.BooleanVar(value=self.settings["hotkey"]["alt"])
        self.win_var = tk.BooleanVar(value=self.settings["hotkey"]["win"])
        self.key_var = tk.StringVar(value=self.settings["hotkey"]["key"])
        self.status_var = tk.StringVar(value=self.text("status_stop"))
        self.running = False
        self.click_thread = None
        self.stop_event = threading.Event()
        self.hotkey_registered = False
        self._last_hotkey_display = ""
        self.error_after_id = None
        self.mouse = Controller()

        self.tray_icon = None
        self.switch_sound = get_resource_path(os.path.join("wav", "switch.wav"))
        self.build_ui()
        self._install_ttk_focus_ring_mitigation()
                                                                               
        try:
            self.save_settings()
        except Exception:
            pass
        self.register_hotkey(play_sound=False)
        self.start_tray()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=14)
        frm.pack(fill="both", expand=True)

        row0 = ttk.Frame(frm)
        row0.pack(fill="x", pady=(0, 10))
        self.lbl_title = ttk.Label(row0, text=self.get_app_title())
        self.lbl_title.pack(side="left")
        self.lang_btn = ttk.Button(row0, command=self._on_lang_button_clicked)
        self.lang_btn.configure(takefocus=False)
        self.lang_btn.pack(side="left", padx=(6, 0))

        row1 = ttk.Frame(frm)
        row1.pack(fill="x", pady=4)
        self.lbl_interval = ttk.Label(row1, width=18)
        self.lbl_interval.pack(side="left")
        self._interval_vcmd = (self.root.register(self._validate_interval_input), "%P")
        self.ent_interval = ttk.Entry(
            row1,
            textvariable=self.interval_var,
            width=8,
            validate="key",
            validatecommand=self._interval_vcmd,
        )
        self.ent_interval.pack(side="left")
        self.ent_interval.bind("<KeyRelease>", self._normalize_interval_text, add="+")

        row2 = ttk.Frame(frm)
        row2.pack(fill="x", pady=4)
        self.lbl_hotkey = ttk.Label(row2, width=18)
        self.lbl_hotkey.pack(side="left")
        self.chk_ctrl = ttk.Checkbutton(row2, text="Ctrl", variable=self.ctrl_var)
        self.chk_ctrl.configure(takefocus=False)
        self.chk_ctrl.pack(side="left")
        self.chk_alt = ttk.Checkbutton(row2, text="Alt", variable=self.alt_var)
        self.chk_alt.configure(takefocus=False)
        self.chk_alt.pack(side="left", padx=(6, 0))
        self.chk_win = ttk.Checkbutton(row2, text="Win", variable=self.win_var)
        self.chk_win.configure(takefocus=False)
        self.chk_win.pack(side="left", padx=(6, 6))
        self.ent_hotkey = ttk.Entry(
            row2,
            textvariable=self.key_var,
            width=8,
            justify="center",
            state="readonly",
        )
        self.ent_hotkey.pack(side="left")
        self.ent_hotkey.bind("<KeyPress>", self.on_hotkey_entry_keypress, add="+")
        self.ent_hotkey.bind("<KeyRelease>", self.on_hotkey_entry_keyrelease, add="+")
        self.ent_hotkey.bind("<Button-1>", self.on_hotkey_entry_mouse_press, add="+")
        self.ent_hotkey.bind("<Double-Button-1>", self.on_hotkey_entry_mouse_press, add="+")
        self.ent_hotkey.bind("<Triple-Button-1>", self.on_hotkey_entry_mouse_press, add="+")
        self.ent_hotkey.bind("<B1-Motion>", self.on_hotkey_entry_mouse_drag, add="+")

        row3 = ttk.Frame(frm)
        row3.pack(fill="x", pady=(8, 4))
        self.btn_apply = ttk.Button(row3, command=self._on_apply_button_clicked)
        self.btn_apply.configure(takefocus=False)
        self.btn_apply.pack(side="left")
        self.btn_restore = ttk.Button(row3, command=self._on_restore_button_clicked)
        self.btn_restore.configure(takefocus=False)
        self.btn_restore.pack(side="left", padx=(8, 0))

        self._space_guard_widgets = [
            self.lang_btn,
            self.chk_ctrl,
            self.chk_alt,
            self.chk_win,
            self.ent_interval,
            self.ent_hotkey,
            self.btn_apply,
            self.btn_restore,
        ]
        self.root.bind_all("<KeyPress-space>", self.on_space_guard, add="+")
        self.root.bind_all("<KeyRelease-space>", self.on_space_guard, add="+")
        self._bind_space_block_for_widgets(
            [
                self.lang_btn,
                self.chk_ctrl,
                self.chk_alt,
                self.chk_win,
                self.ent_interval,
                self.btn_apply,
                self.btn_restore,
            ]
        )

        self.lbl_status = ttk.Label(frm, textvariable=self.status_var, foreground="#007acc")
        self.lbl_status.pack(anchor="w", pady=(10, 0))
        self.apply_language()

    def _defocus_toplevel_of(self, w):
        try:
            t = w.winfo_toplevel()
            if t and t.winfo_exists():
                t.focus_set()
        except Exception:
            pass

    def _on_ttk_buttonlike_release(self, event):
        self.root.after_idle(lambda: self._defocus_toplevel_of(event.widget))

    def _install_ttk_focus_ring_mitigation(self):
        style = ttk.Style(self.root)
        try:
            style.configure("TButton", focuscolor=style.lookup("TButton", "background"))
        except tk.TclError:
            pass
        try:
            bg = style.lookup("TCheckbutton", "background")
            style.configure("TCheckbutton", focuscolor=bg)
            style.map("TCheckbutton", focuscolor=[("focus", bg), ("!focus", bg)])
        except tk.TclError:
            pass
        if getattr(self, "_ttk_focus_release_bind_done", False):
            return
        self._ttk_focus_release_bind_done = True
        self.root.bind_class("TButton", "<ButtonRelease-1>", self._on_ttk_buttonlike_release, add="+")
        self.root.bind_class("TCheckbutton", "<ButtonRelease-1>", self._on_ttk_buttonlike_release, add="+")

    def load_settings(self):
        data = json.loads(json.dumps(DEFAULT_SETTINGS))
        data["languages"] = _default_ui_language(self.lang_order)
        if not os.path.exists(SETTINGS_FILE):
            return data
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if not _is_valid_mouse_settings_raw(raw):
                try:
                    os.remove(SETTINGS_FILE)
                except Exception:
                    pass
                return data
            settings_raw = raw.get("settings", raw)
            if not isinstance(settings_raw, dict):
                return data
            self.i18n = merged_lang_table(raw.get("languages", {}))
            self.lang_order = available_ui_languages(self.i18n)
            self.custom_languages = json.loads(json.dumps(self.i18n))
            language = settings_raw.get("languages")
            if language in self.lang_order:
                data["languages"] = language
            else:
                data["languages"] = _default_ui_language(self.lang_order)
            interval = int(settings_raw.get("interval_ms", data["interval_ms"]))
            data["interval_ms"] = max(1, interval)
            hotkey = settings_raw.get("hotkey", {})
            data["hotkey"]["ctrl"] = bool(hotkey.get("ctrl", data["hotkey"]["ctrl"]))
            data["hotkey"]["alt"] = bool(hotkey.get("alt", data["hotkey"]["alt"]))
            data["hotkey"]["win"] = bool(hotkey.get("win", data["hotkey"]["win"]))
            key = str(hotkey.get("key", data["hotkey"]["key"])).upper().strip()
            data["hotkey"]["key"] = key or data["hotkey"]["key"]
        except Exception:
            try:
                os.remove(SETTINGS_FILE)
            except Exception:
                pass
        return data

    def save_settings(self):
        languages_payload = json.loads(json.dumps(self.i18n))
        payload = {
            "settings": {
                "languages": self.language,
                "interval_ms": int(self.interval_var.get().strip()),
                "hotkey": {
                    "ctrl": self.ctrl_var.get(),
                    "alt": self.alt_var.get(),
                    "win": self.win_var.get(),
                    "key": self.key_var.get().strip().upper(),
                },
            },
            "languages": languages_payload,
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def text(self, key: str) -> str:
        langs = self.lang_order
        lang = self.language
        if lang not in langs:
            lang = _default_ui_language(langs)
        order = [lang] + [x for x in langs if x != lang]
        if "zh_TW" not in order:
            order.append("zh_TW")
        for L in order:
            m = self.i18n.get(L, {})
            v = m.get(key)
            if isinstance(v, str) and v:
                return v
        return BUILTIN_I18N["zh_TW"].get(key, key)

    def get_app_title(self) -> str:
        return f"[B.M] {self.text('project_name')} {APP_TITLE_SUFFIX}"

    def apply_language(self):
        self.root.title(self.get_app_title())
        self._set_app_user_model_id()
        self.lbl_title.configure(text=self.get_app_title())
        self.lang_btn.configure(text=self.text("language_name"))
        self.lbl_interval.configure(text=self.text("interval"))
        self.lbl_hotkey.configure(text=self.text("hotkey"))
        self.btn_apply.configure(text=self.text("save_settings"))
        self.btn_restore.configure(text=self.text("restore_default"))
        if self.running:
            self.status_var.set(self.text("status_run"))
        elif self.hotkey_registered and self._last_hotkey_display:
            self.status_var.set(
                self.text("status_hotkey").format(hotkey=self._last_hotkey_display)
            )
        else:
            self.status_var.set(self.text("status_stop"))
        if self.tray_icon is not None:
            try:
                self.tray_icon.menu = self._tray_build_menu()
                if hasattr(self.tray_icon, "update_menu"):
                    self.tray_icon.update_menu()
                self.tray_icon.title = self.get_app_title()
            except Exception:
                pass

    def show_status_error(self, text: str):
        if self.error_after_id is not None:
            self.root.after_cancel(self.error_after_id)
            self.error_after_id = None
        self.status_var.set(text)
        self.lbl_status.configure(foreground="#d02020")
        self.error_after_id = self.root.after(3000, self.restore_status_normal)

    def restore_status_normal(self):
        self.error_after_id = None
        self.lbl_status.configure(foreground="#007acc")
        if self.running:
            self.status_var.set(self.text("status_run"))
        else:
            self.status_var.set(self.text("status_stop"))

    def cycle_language(self):
        idx = self.lang_order.index(self.language)
        self.language = self.lang_order[(idx + 1) % len(self.lang_order)]
        self.apply_language()
        try:
            self.save_settings()
        except Exception:
            pass

    def validate_interval(self) -> float:
        try:
            ms = int(self.interval_var.get().strip())
            if ms < 1:
                raise ValueError
            return ms / 1000.0
        except ValueError:
            messagebox.showerror(self.text("input_error_title"), self.text("error_interval"))
            raise

    @staticmethod
    def _validate_interval_input(proposed: str) -> bool:
                                           
        return proposed == "" or proposed.isdigit()

    def _normalize_interval_text(self, _event=None) -> None:
        cur = (self.interval_var.get() or "").strip()
        if not cur:
            return
        digits_only = "".join(ch for ch in cur if ch.isdigit())
        if digits_only != cur:
            self.interval_var.set(digits_only)

    def validate_hotkey(self):
        key = self.normalize_hotkey_text(self.key_var.get())
        self.key_var.set(key)
        if not key:
            raise ValueError("key invalid")
        return key

    @staticmethod
    def normalize_hotkey_text(text: str) -> str:
        s = (text or "").strip().upper()
        if not s:
            return ""
        if len(s) >= 2 and s.startswith("F") and s[1:].isdigit():
            n = int(s[1:])
            if 1 <= n <= 12:
                return f"F{n}"
        if len(s) == 1 and s.isascii() and s.isalnum():
            return s
        if s in HOTKEY_SPECIAL_KEYS:
            return s
        if s in HOTKEY_ALIAS_MAP:
            return HOTKEY_ALIAS_MAP[s]
        return ""

    def on_hotkey_entry_keypress(self, event):
        ks = (event.keysym or "").upper()
        if ks in ("BACKSPACE", "DELETE"):
            self.key_var.set("")
            return "break"
        if ks == "ESCAPE":
            self.root.focus_set()
            return "break"
        if ks == "SPACE":
            return "break"
        if ks.startswith("F") and ks[1:].isdigit():
            n = int(ks[1:])
            if 1 <= n <= 12:
                self.key_var.set(f"F{n}")
                self.root.focus_set()
                return "break"
        if len(ks) == 1 and ks.isascii() and ks.isalnum():
            self.key_var.set(ks)
            self.root.focus_set()
            return "break"
        symbol_map = {
            "COMMA": ",",
            "PERIOD": ".",
            "SLASH": "/",
            "MINUS": "-",
            "EQUAL": "=",
            "PLUS": "+",
        }
        if ks in symbol_map:
            self.key_var.set(symbol_map[ks])
            self.root.focus_set()
            return "break"
        nav_map = {
            "INSERT": "INSERT",
            "DELETE": "DELETE",
            "HOME": "HOME",
            "END": "END",
            "PRIOR": "PAGEUP",
            "NEXT": "PAGEDOWN",
            "PAGE_UP": "PAGEUP",
            "PAGE_DOWN": "PAGEDOWN",
            "UP": "UP",
            "DOWN": "DOWN",
            "LEFT": "LEFT",
            "RIGHT": "RIGHT",
            "PRINT": "PRINTSCREEN",
            "SNAPSHOT": "PRINTSCREEN",
            "PAUSE": "PAUSE",
            "SCROLL_LOCK": "SCROLLLOCK",
        }
        if ks in nav_map:
            self.key_var.set(nav_map[ks])
            self.root.focus_set()
            return "break"
        if ks.startswith("KP_"):
            kp_map = {
                "KP_0": "NUMPAD0",
                "KP_1": "NUMPAD1",
                "KP_2": "NUMPAD2",
                "KP_3": "NUMPAD3",
                "KP_4": "NUMPAD4",
                "KP_5": "NUMPAD5",
                "KP_6": "NUMPAD6",
                "KP_7": "NUMPAD7",
                "KP_8": "NUMPAD8",
                "KP_9": "NUMPAD9",
                "KP_ADD": "NUMPADADD",
                "KP_SUBTRACT": "NUMPADSUB",
                "KP_DIVIDE": "NUMPADDIV",
                "KP_MULTIPLY": "NUMPADMUL",
            }
            mapped = kp_map.get(ks)
            if mapped:
                self.key_var.set(mapped)
                self.root.focus_set()
                return "break"
        return "break"

    def on_hotkey_entry_keyrelease(self, _event):
                             
        self.key_var.set(self.normalize_hotkey_text(self.key_var.get()))

    def on_hotkey_entry_mouse_press(self, _event):
                         
        self.ent_hotkey.focus_set()
        try:
            self.ent_hotkey.selection_clear()
        except Exception:
            pass
        self.ent_hotkey.icursor(tk.END)
        return "break"

    def on_hotkey_entry_mouse_drag(self, _event):
        try:
            self.ent_hotkey.selection_clear()
        except Exception:
            pass
        return "break"

    def _leave_hotkey_entry_focus(self) -> None:
        try:
            if self.root.focus_get() == self.ent_hotkey:
                self.root.focus_set()
        except Exception:
            pass

    def _on_root_activate(self, event):
        if event.widget is not self.root:
            return

        def _defer():
            self._leave_hotkey_entry_focus()

        try:
            self.root.after_idle(_defer)
        except Exception:
            _defer()

    def _on_root_deactivate(self, event):
        if event.widget is not self.root:
            return
        self._leave_hotkey_entry_focus()

    def _on_root_focus_in(self, event):
                                                                  
        if event.widget is not self.root:
            return

        def _defer():
            self._leave_hotkey_entry_focus()

        try:
            self.root.after_idle(_defer)
        except Exception:
            _defer()

    def _on_lang_button_clicked(self):
        self._leave_hotkey_entry_focus()
        self.cycle_language()

    def _on_apply_button_clicked(self):
        self._leave_hotkey_entry_focus()
        self.register_hotkey()

    def _on_restore_button_clicked(self):
        self._leave_hotkey_entry_focus()
        self.restore_default_hotkey()

    def on_space_guard(self, event):
        w = self.root.focus_get() or event.widget
        if w in self._space_guard_widgets:
            return "break"
        cls = str(getattr(w, "winfo_class", lambda: "")())
        if cls in ("TButton", "Button", "TCheckbutton", "Checkbutton"):
            return "break"
        return None

    @staticmethod
    def _bind_space_block_for_widgets(widgets):
        for w in widgets:
            w.bind("<KeyPress-space>", lambda _e: "break", add="+")
            w.bind("<KeyRelease-space>", lambda _e: "break", add="+")

    def build_hotkey_combo(self):
        key = self.validate_hotkey()
        parts = []
        display_parts = []
        if self.ctrl_var.get():
            parts.append("ctrl")
            display_parts.append("CTRL")
        if self.alt_var.get():
            parts.append("alt")
            display_parts.append("ALT")
        if self.win_var.get():
            parts.append("windows")
            display_parts.append("WIN")
        parts.append(HOTKEY_KEY_TO_KEYBOARD.get(key, key.lower()))
        return "+".join(parts), "+".join(display_parts + [key])

    def click_loop(self):
        while not self.stop_event.is_set():
            interval = 0.05
            try:
                interval = self.validate_interval()
            except Exception:
                self.stop_event.set()
                break
            self.mouse.click(Button.left)
            time.sleep(interval)

    def start_clicking(self):
        if self.running:
            return
        try:
            self.validate_interval()
        except Exception:
            return
        self.running = True
        self.play_switch_sound()
        self.stop_event.clear()
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
        self.status_var.set(self.text("status_run"))

    def stop_clicking(self):
        if not self.running:
            return
        self.running = False
        self.play_switch_sound()
        self.stop_event.set()
        self.status_var.set(self.text("status_stop"))

    def toggle_clicking(self):
        if self.running:
            self.stop_clicking()
        else:
            self.start_clicking()

    def on_hotkey_triggered(self):
        self.root.after(0, self.toggle_clicking)

    def play_switch_sound(self):
        try:
            if winsound is not None:
                winsound.PlaySound(
                    self.switch_sound,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                return
            if sys.platform == "darwin":
                subprocess.Popen(
                    ["afplay", self.switch_sound],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

    def register_hotkey(self, play_sound: bool = True):
        try:
            if self.hotkey_registered:
                keyboard.clear_all_hotkeys()
                self.hotkey_registered = False
            combo, combo_display = self.build_hotkey_combo()
            keyboard.add_hotkey(combo, self.on_hotkey_triggered, suppress=False)
            self.hotkey_registered = True
            self._last_hotkey_display = combo_display
            self.status_var.set(self.text("status_hotkey").format(hotkey=combo_display))
            self.lbl_status.configure(foreground="#007acc")
            self.save_settings()
            if play_sound:
                self.play_switch_sound()
        except Exception:
            self._last_hotkey_display = ""
            self.show_status_error(self.text("error_hotkey"))

    def restore_default_hotkey(self):
        self.ctrl_var.set(self.default_hotkey["ctrl"])
        self.alt_var.set(self.default_hotkey["alt"])
        self.win_var.set(self.default_hotkey["win"])
        self.key_var.set(self.default_hotkey["key"])
        self.interval_var.set(str(DEFAULT_SETTINGS["interval_ms"]))
        self.register_hotkey(play_sound=True)

    def _set_app_user_model_id(self) -> None:
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                self.get_app_title()
            )
        except Exception:
            pass

    def move_to_default_position(self):
        self.root.after(0, self._show_and_move)

    def _show_and_move(self):
        self.root.deiconify()
        self.root.lift()
        self.root.state("normal")
        ox, oy = _primary_screen_origin()
        self.root.geometry(f"+{ox + WINDOW_POS_X}+{oy + WINDOW_POS_Y}")
        self.root.focus_force()

    def hide_window(self):
        self.root.withdraw()

    def on_root_unmap(self, event):
        if self.root.state() == "iconic":
            self.root.after(10, self.hide_window)

    def show_about(self, icon=None, item=None):
        try:
            webbrowser.open(ABOUT_URL)
        except Exception:
            pass

    def exit_app(self, icon=None, item=None):
        self.stop_clicking()
        try:
            keyboard.clear_all_hotkeys()
        except Exception:
            pass
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _tray_build_menu(self):
        default_item = pystray.MenuItem(
            "還原",
            lambda icon, item: self.move_to_default_position(),
            default=True,
            visible=False,
        )
        return pystray.Menu(
            default_item,
            pystray.MenuItem(lambda item: self.text("about"), self.show_about),
            pystray.MenuItem(lambda item: self.text("exit"), self.exit_app),
        )

    def _create_tray(self):
        self.tray_icon = pystray.Icon(
            "bm-clicker", self.icon_img, self.get_app_title(), self._tray_build_menu()
        )
        self.tray_icon.run_detached()

    def start_tray(self):
        self._create_tray()

    def run(self):
        self.root.mainloop()


def main():
                                                                          
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    mh = bm_single_instance.acquire_or_handshake(SINGLE_APP_ID)
    if not mh:
        return
    app = MouseClickerApp()
    bm_single_instance.start_pipe_server(SINGLE_APP_ID, lambda: app.root.after(0, app.exit_app))
    app.run()
    bm_single_instance.release_mutex(mh)


if __name__ == "__main__":
    main()
