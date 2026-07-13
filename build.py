#!/usr/bin/env python3
"""Скрипт для сборки приложения Task Tracker для Windows и macOS."""

import PyInstaller.__main__
import sys
import os
from pathlib import Path

# Базовые пути проекта держим рядом, чтобы сборка была предсказуемой.
ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

def build_app():
    """Собрать приложение в standalone executable."""
    
    # Минимальный набор параметров для one-file сборки.
    args = [
        str(ROOT_DIR / "main.py"),
        f"--name=TaskTracker",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--onefile",  # Один исполняемый файл
        "--windowed",  # Без консольного окна
        "--add-data=theme.py:.",
        "--add-data=gui.py:.",
        "--add-data=database.py:.",
        "--add-data=charts.py:.",
        "--hidden-import=PyQt5.QtSql",
        "--hidden-import=matplotlib.backends.backend_qt5agg",
    ]
    
    print(f"🔨 Начинаю сборку приложения...")
    print(f"📁 Рабочая директория: {ROOT_DIR}")
    print(f"📦 Выходная директория: {DIST_DIR}")
    
    # Запускаем сборку строго из корня репы.
    os.chdir(ROOT_DIR)
    
    # Основной шаг сборки.
    PyInstaller.__main__.run(args)
    
    print(f"\n✅ Сборка завершена!")
    print(f"📦 Исполняемый файл находится в: {DIST_DIR}")
    
    # Просто выводим, под какую систему собрали бинарь.
    platform_name = "macOS" if sys.platform == "darwin" else "Windows" if sys.platform == "win32" else "Linux"
    print(f"🖥️  Собрано для: {platform_name}")

if __name__ == "__main__":
    try:
        build_app()
    except Exception as e:
        print(f"❌ Ошибка при сборке: {e}")
        sys.exit(1)
