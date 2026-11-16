"""Modern, user-selectable QuickStats palettes.

The palette is deliberately token-based: widgets consume semantic roles rather
than hard-coded hex values, so theme changes stay consistent across the app.
"""

from __future__ import annotations

import re

THEMES: dict[str, dict[str, str]] = {
    "graphite": {
        "background": "#101318",
        "surface": "#171c23",
        "surface_alt": "#202833",
        "border": "#2b3542",
        "text": "#edf2f7",
        "muted": "#9aa8b8",
        "grid": "#303b49",
        "success": "#53d6a1",
    },
    "midnight": {
        "background": "#11111b",
        "surface": "#1a1a2a",
        "surface_alt": "#25253a",
        "border": "#38384f",
        "text": "#e6e9f5",
        "muted": "#a4a9c2",
        "grid": "#38384f",
        "success": "#8be0bd",
    },
    "light": {
        "background": "#f3f5f8",
        "surface": "#ffffff",
        "surface_alt": "#e9edf3",
        "border": "#d5dce6",
        "text": "#202938",
        "muted": "#657386",
        "grid": "#dce3eb",
        "success": "#16845c",
    },
}

ACCENTS: dict[str, str] = {
    "blue": "#68a9ff",
    "violet": "#a78bfa",
    "teal": "#45c6b0",
    "emerald": "#35c98f",
    "amber": "#f2b866",
    "rose": "#f18ca8",
}

_ACTIVE_THEME = "graphite"
_ACTIVE_ACCENT = "blue"


def configure(theme_name: str = "graphite", accent_name: str = "blue") -> None:
    """Set the active semantic palette, falling back safely for unknown values."""
    global _ACTIVE_THEME, _ACTIVE_ACCENT
    _ACTIVE_THEME = theme_name if theme_name in THEMES else "graphite"
    if accent_name in ACCENTS:
        _ACTIVE_ACCENT = accent_name
    elif re.fullmatch(r"#[0-9a-fA-F]{6}", accent_name):
        _ACTIVE_ACCENT = accent_name.lower()
    else:
        _ACTIVE_ACCENT = "blue"


def current_palette() -> dict[str, str]:
    """Return a fresh palette with the selected accent merged in."""
    palette = dict(THEMES[_ACTIVE_THEME])
    palette["accent"] = ACCENTS.get(_ACTIVE_ACCENT, _ACTIVE_ACCENT)
    palette["accent_soft"] = palette["accent"] + "33"
    palette["memory"] = "#b59cff" if _ACTIVE_THEME != "light" else "#7654c5"
    palette["storage"] = "#45c6b0" if _ACTIVE_THEME != "light" else "#168a83"
    return palette


def build_stylesheet(theme_name: str = "graphite", accent_name: str = "blue") -> str:
    """Build a compact Qt stylesheet from the selected palette."""
    configure(theme_name, accent_name)
    p = current_palette()
    return f"""
QWidget {{
    background-color: {p['background']};
    color: {p['text']};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}}
QMainWindow {{ background-color: {p['background']}; }}
QLabel#pageTitle {{ color: {p['text']}; font-size: 22pt; font-weight: 700; }}
QLabel#subtitle, QLabel[class="muted"] {{ color: {p['muted']}; }}
QLabel#uptime {{ color: {p['success']}; font-weight: 600; }}
QFrame#card {{
    background-color: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 16px;
}}
QLabel[class="metricTitle"] {{
    color: {p['muted']}; font-size: 9pt; font-weight: 600;
}}
QLabel[class="metricValue"] {{
    color: {p['text']}; font-size: 23pt; font-weight: 700;
}}
QProgressBar {{
    background-color: {p['surface_alt']}; border: none;
    border-radius: 4px; height: 7px; text-align: center;
}}
QProgressBar::chunk {{ background-color: {p['accent']}; border-radius: 4px; }}
QProgressBar#memoryBar::chunk {{ background-color: {p['memory']}; }}
QProgressBar#storageBar::chunk {{ background-color: {p['storage']}; }}
QComboBox, QPushButton {{
    background-color: {p['surface_alt']}; color: {p['text']};
    border: 1px solid {p['border']}; border-radius: 9px; padding: 7px 10px;
}}
QComboBox:hover, QPushButton:hover {{ border-color: {p['accent']}; }}
QComboBox QAbstractItemView {{
    background-color: {p['surface']}; color: {p['text']};
    selection-background-color: {p['accent_soft']};
    border: 1px solid {p['border']};
}}
QToolTip {{
    background: {p['surface']}; color: {p['text']};
    border: 1px solid {p['border']}; padding: 5px;
}}
"""


# Backwards-compatible default for code importing the old constant.
STYLESHEET = build_stylesheet()
