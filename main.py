
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
# Точка входа: поднимаем БД, тему и главное окно.
import sys
import os

# На случай запуска из другой директории — добавляем путь проекта в импорт.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont
from database import init_database, seed_data
from gui import TaskTrackerApp
from theme import apply_theme


def main():
    """Главная точка входа в приложение."""
    # База должна быть готова до старта UI.
    init_database()
    seed_data()

    # Важно выставить до QApplication, иначе часть настроек игнорируется.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Создаём приложение и базовые метаданные.
    app = QApplication(sys.argv)
    # Единый шрифт = стабильный рендер и меньше шумных предупреждений по семействам.
    app.setFont(QFont("Helvetica Neue", 11))
    app.setOrganizationName("TaskTracker")
    app.setApplicationName("Task Tracker")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    settings = QSettings("TaskTracker", "Task Tracker")
    theme_mode = str(settings.value("appearance/theme", "system"))
    apply_theme(app, theme_mode)

    # Поднимаем основное окно после темы и настроек.
    window = TaskTrackerApp(app, settings)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
