"""Catppuccin Mocha-inspired interface colors and stylesheet."""

BACKGROUND = "#1e1e2e"
SURFACE = "#313244"
SURFACE_ALT = "#45475a"
TEXT = "#cdd6f4"
MUTED = "#a6adc8"
BLUE = "#89b4fa"
GREEN = "#a6e3a1"
MAUVE = "#cba6f7"
TEAL = "#94e2d5"

STYLESHEET = f"""
QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 10pt;
}}
QMainWindow {{ background-color: {BACKGROUND}; }}
QLabel#pageTitle {{
    color: {TEXT};
    font-size: 22pt;
    font-weight: 700;
}}
QLabel#subtitle, QLabel[class="muted"] {{ color: {MUTED}; }}
QFrame#card {{
    background-color: {SURFACE};
    border: 1px solid {SURFACE_ALT};
    border-radius: 14px;
}}
QLabel[class="metricTitle"] {{
    color: {MUTED};
    font-size: 9pt;
    font-weight: 600;
}}
QLabel[class="metricValue"] {{
    color: {TEXT};
    font-size: 23pt;
    font-weight: 700;
}}
QProgressBar {{
    background-color: {SURFACE_ALT};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{ background-color: {BLUE}; border-radius: 4px; }}
QProgressBar#memoryBar::chunk {{ background-color: {MAUVE}; }}
QProgressBar#storageBar::chunk {{ background-color: {TEAL}; }}
QComboBox, QPushButton {{
    background-color: {SURFACE};
    border: 1px solid {SURFACE_ALT};
    border-radius: 8px;
    padding: 7px 10px;
}}
QComboBox:hover, QPushButton:hover {{ border-color: {BLUE}; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    selection-background-color: {SURFACE_ALT};
    border: 1px solid {SURFACE_ALT};
}}
QLabel#uptime {{ color: {GREEN}; font-weight: 600; }}
"""
