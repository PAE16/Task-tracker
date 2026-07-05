#!/bin/bash
# Скрипт для запуска Task Tracker на macOS

# Проверить что приложение собрано
if [ ! -d "dist/TaskTracker.app" ]; then
    echo "❌ Приложение не найдено!"
    echo "Собери его с помощью: python3 build.py"
    exit 1
fi

# Запустить приложение
echo "🚀 Запускаю Task Tracker..."
open dist/TaskTracker.app

echo "✅ Приложение запущено!"
