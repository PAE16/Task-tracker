
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Tracker — Система управления проектами
Кроссплатформенное приложение на PyQt5 с SQLite

Запуск:
    python main.py

Сборка:
    Windows: pyinstaller --onefile --windowed --name "TaskTracker" main.py
    macOS:   pyinstaller --onefile --windowed --name "TaskTracker" main.py
"""
# Entrypoint: инициализирует БД, применяет тему и запускает главное окно.
import sys
import os

# Добавляем путь к текущей директории для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont
from database import init_database, seed_data
from gui import TaskTrackerApp
from theme import apply_theme


def main():
    """Главная точка входа в приложение."""
    # Инициализация базы данных
    init_database()
    seed_data()

    # Эти атрибуты должны быть выставлены до создания QApplication.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Создание приложения
    app = QApplication(sys.argv)
    # Устанавливаем системный шрифт приложения, чтобы снизить предупреждения
    # о недостающих семействах и сделать рендер стабильным на macOS/Windows.
    app.setFont(QFont("Helvetica Neue", 11))
    app.setOrganizationName("TaskTracker")
    app.setApplicationName("Task Tracker")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    settings = QSettings("TaskTracker", "Task Tracker")
    theme_mode = str(settings.value("appearance/theme", "system"))
    apply_theme(app, theme_mode)

    # Создание и показ главного окна
    window = TaskTrackerApp(app, settings)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
