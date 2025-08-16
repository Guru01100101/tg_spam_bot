#!/bin/bash
# Цей скрипт створює базовий файл для mypy, який дозволяє ігнорувати поточні помилки
# але виявляти нові помилки у майбутньому

# Переконайтеся, що директорія scripts існує
mkdir -p $(dirname "$0")

# Активація віртуального середовища (якщо використовується)
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Створення директорії .mypy_cache, якщо вона не існує
mkdir -p .mypy_cache

# Генерація baseline з поточними помилками
mypy --ignore-missing-imports core/ models/ utils/ main.py --show-error-codes > .mypy_baseline.txt

echo "Базовий файл для mypy створено у .mypy_baseline.txt"
echo "Додайте цей файл до .gitignore, якщо не хочете його відстежувати"
echo "Використовуйте опцію --follow-imports=skip у mypy.ini для ігнорування проблем у сторонніх бібліотеках"
