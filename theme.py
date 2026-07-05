"""Хелперы темы приложения для Task Tracker.

Модуль содержит палитры, генератор QPalette и глобальный stylesheet.
Остальной код запрашивает цвета и стили отсюда для согласованности UI.
"""
from __future__ import annotations

import subprocess
import sys

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

THEME_MODES = ("system", "light", "dark")

_LIGHT = {
    "window": "#f5f2eb",
    "surface": "#ffffff",
    "surface_alt": "#f7f4ef",
    "text": "#111111",
    "muted": "#6b6b6b",
    "border": "#ede8df",
    "accent": "#ff6900",
    "accent_hover": "#e25a00",
    "accent_soft": "#ffe7dc",
    "selection": "#ffede2",
    "selection_text": "#111111",
    "header": "#ffffff",
    "header_text": "#111111",
    "chart_bg": "#ffffff",
    "chart_axes": "#ffffff",
    "chart_grid": "#ece7df",
    "chart_text": "#1c1c1c",
    "chart_muted": "#6b6b6b",
    "chart_blue": "#1d4ed8",
    "chart_red": "#ef4444",
    "chart_green": "#10b981",
    "chart_orange": "#f59e0b",
    "chart_purple": "#8b5cf6",
        "group_bg": "rgba(255,255,255,0.94)",
}

_DARK = {
    "window": "#050505",
    "surface": "#0d0d0f",
    "surface_alt": "#1a1a1f",
    "text": "#f5f5f5",
    "muted": "#8b8b8b",
    "border": "#3a3a3f",
    "accent": "#ff6900",
    "accent_hover": "#ff7a1f",
    "accent_soft": "#3d2818",
    "selection": "#ff6900",
    "selection_text": "#111111",
    "header": "#0d0d0f",
    "header_text": "#f8f8f8",
    "chart_bg": "#050505",
    "chart_axes": "#0d0d0f",
    "chart_grid": "#232327",
    "chart_text": "#f5f5f5",
    "chart_muted": "#c2c2c2",
    "chart_blue": "#60a5fa",
    "chart_red": "#fb7185",
    "chart_green": "#4ade80",
    "chart_orange": "#fbbf24",
    "chart_purple": "#c084fc",
        "group_bg": "rgba(15,15,17,0.48)",
}


def detect_system_theme() -> str:
    """Определяет системную тему (macOS/Windows) с лучшей попыткой.

    Возвращает 'light' или 'dark' согласно настройкам ОС или по палитре Qt.
    """
    # Returns 'light' or 'dark' depending on OS settings or Qt palette.
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and "Dark" in result.stdout:
                return "dark"
        except OSError:
            pass
        return "light"

    if sys.platform.startswith("win"):
        try:
            import winreg  # type: ignore

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
        except Exception:
            pass

    app = QApplication.instance()
    if app is not None:
        window_color = app.palette().color(QPalette.Window)
        return "dark" if window_color.lightness() < 128 else "light"

    return "light"


def resolve_theme(mode: str) -> str:
    """Разрешает фактическую тему по значению режима пользователя."""
    # mode: 'system'|'light'|'dark' -> returns resolved 'light' or 'dark'
    return detect_system_theme() if mode == "system" else mode


def theme_data(mode: str) -> dict:
    """Возвращает словарь цветов для заданного (разрешённого) режима."""
    # Small helper mapping to the _LIGHT/_DARK dicts used throughout UI.
    resolved = resolve_theme(mode) if mode in THEME_MODES else "light"
    return _DARK if resolved == "dark" else _LIGHT


def palette_for(mode: str) -> QPalette:
    """Строит Qt-палитру для переданного режима."""
    # Construct a QPalette that Qt widgets will consume for native colors.
    colors = theme_data(mode)
    palette = QPalette()

    window = QColor(colors["window"])
    surface = QColor(colors["surface"])
    text = QColor(colors["text"])
    muted = QColor(colors["muted"])
    accent = QColor(colors["accent"])
    selection = QColor(colors["selection"])

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, surface)
    palette.setColor(QPalette.AlternateBase, QColor(colors["surface_alt"]))
    palette.setColor(QPalette.ToolTipBase, surface)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, surface)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, accent)
    palette.setColor(QPalette.HighlightedText, QColor(colors["selection_text"]))
    palette.setColor(QPalette.Link, accent)
    palette.setColor(QPalette.LinkVisited, accent)
    palette.setColor(QPalette.PlaceholderText, muted)
    palette.setColor(QPalette.Light, QColor(colors["surface_alt"]))
    palette.setColor(QPalette.Mid, QColor(colors["border"]))
    palette.setColor(QPalette.Midlight, QColor(colors["surface_alt"]))
    palette.setColor(QPalette.Dark, QColor(colors["border"]))

    inactive = QPalette.Inactive
    palette.setColor(inactive, QPalette.WindowText, text)
    palette.setColor(inactive, QPalette.Text, text)
    palette.setColor(inactive, QPalette.ButtonText, text)
    palette.setColor(inactive, QPalette.Highlight, selection)
    palette.setColor(inactive, QPalette.HighlightedText, QColor(colors["selection_text"]))

    return palette


def stylesheet_for(mode: str) -> str:
    """Генерирует глобальный Qt-стили для переданного режима."""
    # Returns a Qt stylesheet string used by QApplication.setStyleSheet().
    colors = theme_data(mode)
    return f"""
        QMainWindow, QDialog {{
            background-color: {colors['window']};
            color: {colors['text']};
        }}
        QWidget {{
            color: {colors['text']};
            font-family: 'Helvetica Neue';
            font-size: 13px;
        }}
        QLabel {{
            color: {colors['text']};
        }}
        QLabel#heroTitle {{
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: {colors['header_text']};
        }}
        QLabel#themeBadge {{
            background-color: {colors['accent_soft']};
            color: {colors['accent']};
            border: 1px solid {colors['border']};
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 700;
        }}
        QFrame#headerCard {{
            background-color: {colors['header']};
            border: 1px solid {colors['border']};
            border-radius: 24px;
        }}
        QFrame#dashboardCard {{
            background-color: transparent;
        }}
        QGroupBox {{
            background-color: {colors['group_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 18px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: {colors['accent']};
        }}
        QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 8px 12px;
            selection-background-color: {colors['selection']};
            selection-color: {colors['selection_text']};
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {colors['accent']};
        }}
        QDialog {{
            background-color: {colors['window']};
            color: {colors['text']};
        }}
        QDialog QLabel {{
            color: {colors['text']};
        }}
        QPushButton {{
            background-color: transparent;
            color: {colors['text']};
            border: 1px solid transparent;
            border-radius: 999px;
            padding: 7px 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {colors['surface_alt']};
            border-color: {colors['border']};
        }}
        QPushButton:pressed {{
            background-color: {colors['accent_soft']};
        }}
        QPushButton[variant="primary"] {{
            background-color: {colors['accent']};
            color: #ffffff;
            border: 1px solid {colors['accent']};
        }}
        QPushButton[variant="secondary"] {{
            background-color: transparent;
            border: 1px solid {colors['border']};
        }}
        QPushButton[variant="ghost"] {{
            background-color: transparent;
            border: 1px solid transparent;
            padding: 6px 10px;
        }}
        QMenuBar {{
            background-color: {colors['window']};
            color: {colors['text']};
        }}
        QMenuBar::item:selected {{
            background-color: {colors['accent_soft']};
        }}
        QMenu {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        QMenu::item:selected {{
            background-color: {colors['accent_soft']};
        }}
        QStatusBar {{
            background-color: {colors['window']};
            color: {colors['muted']};
        }}
        QTableWidget {{
            background-color: {colors['surface']};
            alternate-background-color: {colors['surface_alt']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            gridline-color: {colors['border']};
            selection-background-color: {colors['selection']};
            selection-color: {colors['selection_text']};
        }}
        QTableWidget::item {{
            padding: 6px 8px;
        }}
        QHeaderView::section {{
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {colors['border']};
            font-weight: 700;
        }}
        QAbstractItemView {{
            background-color: {colors['surface']};
            color: {colors['text']};
            selection-background-color: {colors['selection']};
            selection-color: {colors['selection_text']};
        }}
        QToolTip {{
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        QCheckBox, QRadioButton {{
            color: {colors['text']};
            spacing: 6px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            background-color: {colors['surface']};
            border: 2px solid {colors['border']};
            border-radius: 3px;
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {colors['accent']};
            border: 2px solid {colors['accent']};
        }}
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border: 2px solid {colors['accent_hover']};
        }}
        QMessageBox {{
            background-color: {colors['window']};
            color: {colors['text']};
        }}
        QMessageBox QLabel {{
            color: {colors['text']};
        }}
        QMessageBox QAbstractButton {{
            min-width: 70px;
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QMessageBox QAbstractButton:hover {{
            background-color: {colors['accent_soft']};
        }}
        QAbstractButton {{
            color: {colors['text']};
        }}
        QDialogButtonBox QPushButton {{
            min-width: 92px;
        }}
    """


def apply_theme(app: QApplication, mode: str) -> str:
    """Применяет указанную тему к QApplication.

    Возвращает разрешённую тему ("light" или "dark").
    """
    resolved = resolve_theme(mode)
    app.setProperty("themeMode", mode)
    app.setProperty("resolvedTheme", resolved)
    app.setPalette(palette_for(resolved))
    app.setStyleSheet(stylesheet_for(resolved))
    return resolved


def get_active_theme_mode() -> str:
    """Возвращает текущую применённую тему, хранящуюся в приложении."""
    app = QApplication.instance()
    if app is None:
        return "light"
    return str(app.property("resolvedTheme") or "light")
