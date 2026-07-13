"""Система оформления приложения Task Tracker.

Фиксированная светлая тема для минималистичного интерфейса (Nothing-вдохновение).
Все цвета предопределены - нет переключения тем.
"""

from PyQt5.QtGui import QPalette, QColor

# Одна фиксированная палитра: светлая тема без переключения.
LIGHT_THEME = {
    "window": "#f5f2eb",           # Основной фон окна
    "surface": "#ffffff",          # Фон поверхности (таблица, диалоги)
    "surface_alt": "#f0ede5",      # Альтернативный фон
    "text": "#1a1a1a",             # Основной текст
    "text_muted": "#666666",       # Приглушённый текст
    "border": "#e0ddd5",           # Границы элементов
    "accent": "#ff6900",           # Оранжевый акцент (Nothing style)
    "accent_hover": "#e55a00",     # Акцент при наведении
    "accent_soft": "#ffe6d0",      # Мягкий акцент (фон)
    "selection": "#ff6900",        # Выделение
    "selection_text": "#ffffff",   # Текст выделения
    "chart_green": "#4caf50",      # Зелёный (графики)
    "chart_red": "#f44336",        # Красный (графики)
    "chart_blue": "#2196f3",       # Синий (графики)
    "chart_yellow": "#ffc107",     # Жёлтый (графики)
    "chart_purple": "#9c27b0",     # Фиолетовый (графики)
    "chart_orange": "#ff6900",     # Оранжевый (графики)
    "chart_bg": "#ffffff",         # Фон графика (белый)
    "chart_axes": "#f5f2eb",       # Фон осей графика
    "chart_text": "#1a1a1a",       # Текст на графике
    "chart_grid": "#e0ddd5",       # Сетка графика
    "muted": "#999999",            # Приглушённый цвет
    "group_bg": "#faf8f3",         # Фон групп
}


def theme_data(mode="light"):
    """Получить палитру цветов для темы.
    
    Args:
        mode (str): Режим темы. Всегда возвращает светлую тему.
    
    Returns:
        dict: Словарь цветов в формате hex.
    """
    return LIGHT_THEME


def palette_for(mode="light"):
    """Создать QPalette для native Qt виджетов (светлая тема).
    
    Args:
        mode (str): Режим темы. Всегда используется светлая.
    
    Returns:
        QPalette: Палитра для QApplication.
    """
    palette = QPalette()
    colors = LIGHT_THEME
    
    palette.setColor(QPalette.Window, QColor(colors["window"]))
    palette.setColor(QPalette.WindowText, QColor(colors["text"]))
    palette.setColor(QPalette.Base, QColor(colors["surface"]))
    palette.setColor(QPalette.AlternateBase, QColor(colors["surface_alt"]))
    palette.setColor(QPalette.ToolTipBase, QColor(colors["surface"]))
    palette.setColor(QPalette.ToolTipText, QColor(colors["text"]))
    palette.setColor(QPalette.Text, QColor(colors["text"]))
    palette.setColor(QPalette.Button, QColor(colors["surface_alt"]))
    palette.setColor(QPalette.ButtonText, QColor(colors["text"]))
    palette.setColor(QPalette.BrightText, QColor(colors["accent"]))
    palette.setColor(QPalette.Link, QColor(colors["accent"]))
    palette.setColor(QPalette.Highlight, QColor(colors["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor(colors["selection_text"]))
    
    return palette


def stylesheet_for(mode="light"):
    """Генерировать глобальный QSS для всех виджетов (светлая тема).
    
    Args:
        mode (str): Режим темы. Всегда используется светлая.
    
    Returns:
        str: QSS стили для QApplication.
    """
    colors = LIGHT_THEME
    
    return f"""
        /* База интерфейса */
        QMainWindow, QDialog {{
            background-color: {colors['window']};
            color: {colors['text']};
        }}
        
        /* Обычные виджеты */
        QWidget {{
            background-color: {colors['window']};
            color: {colors['text']};
        }}
        
        /* Кнопки */
        QPushButton {{
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 6px 12px;
            font-weight: 600;
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent_soft']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent']};
            color: {colors['selection_text']};
        }}
        
        /* Поля ввода */
        QLineEdit, QComboBox, QDateEdit {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 6px 8px;
            selection-background-color: {colors['accent']};
        }}
        
        /* Таблица задач */
        QTableWidget {{
            background-color: {colors['surface']};
            alternate-background-color: {colors['surface_alt']};
            gridline-color: {colors['border']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        
        QTableWidget::item {{
            padding: 6px 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors['accent']};
            color: {colors['selection_text']};
        }}
        
        QHeaderView::section {{
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            padding: 5px 8px;
            font-weight: 700;
            border: none;
            border-bottom: 1px solid {colors['border']};
        }}
        
        /* Диалоги */
        QDialog {{
            background-color: {colors['window']};
        }}
        
        QGroupBox {{
            background-color: {colors['group_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 12px;
            margin-top: 8px;
            color: {colors['text']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: {colors['accent']};
        }}
        
        /* Подписи */
        QLabel {{
            color: {colors['text']};
        }}
        
        /* Верхнее меню */
        QMenuBar {{
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            border-bottom: 1px solid {colors['border']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['accent']};
            color: {colors['selection_text']};
        }}
        
        /* Пункты меню */
        QMenu {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        
        QMenu::item:selected {{
            background-color: {colors['accent']};
            color: {colors['selection_text']};
        }}
        
        /* Чекбоксы и радиокнопки */
        QCheckBox, QRadioButton {{
            color: {colors['text']};
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            border: 1px solid {colors['border']};
            background-color: {colors['surface']};
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {colors['accent']};
        }}
        
        /* Скроллы */
        QScrollBar:vertical, QScrollBar:horizontal {{
            background-color: {colors['surface_alt']};
            border: none;
        }}
        
        QScrollBar::handle {{
            background-color: {colors['border']};
            border-radius: 4px;
        }}
        
        QScrollBar::handle:hover {{
            background-color: {colors['text_muted']};
        }}
        
        /* Окна сообщений */
        QMessageBox {{
            background-color: {colors['window']};
        }}
    """


def apply_theme(app, mode="light"):
    """Применить светлую тему к приложению.
    
    Args:
        app: QApplication объект.
        mode (str): Режим темы (всегда светлая).
    
    Returns:
        str: Разрешённая тема ("light").
    """
    app.setPalette(palette_for(mode))
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet_for(mode))
    return "light"


def resolve_theme(mode="light"):
    """Разрешить название темы (всегда возвращает "light").
    
    Args:
        mode (str): Запрошенный режим темы.
    
    Returns:
        str: "light" (единственная доступная тема).
    """
    return "light"


def detect_system_theme():
    """Определить системную тему (не используется, всегда светлая).
    
    Returns:
        str: "light" (всегда светлая тема).
    """
    return "light"


def get_active_theme_mode():
    """Получить активный режим темы.
    
    Returns:
        str: "light" (единственный режим).
    """
    return "light"


# Оставлено для обратной совместимости.
THEME_MODES = ["light"]
