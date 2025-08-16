#!/bin/bash
# Скрипт для перевірки статусу анотацій типів у проекті

echo "Перевірка поточного стану анотацій типів"
echo "----------------------------------------"

# Активація віртуального середовища
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Запуск mypy з різними рівнями перевірки
echo "1. Базова перевірка (поточні налаштування):"
mypy --ignore-missing-imports --implicit-optional --no-strict-optional --follow-imports=skip core/ models/ utils/ main.py

echo -e "\n2. Строгіша перевірка (для майбутнього розвитку):"
mypy --ignore-missing-imports core/ models/ utils/ main.py

echo -e "\n3. Статистика типів у проекті:"
echo "Кількість файлів Python: $(find core models utils -name "*.py" | wc -l)"
echo "Кількість типізованих функцій (з анотаціями): $(grep -r "def.*-> " core models utils | wc -l)"
echo "Кількість нетипізованих функцій: $(grep -r "def " core models utils | grep -v "def.*-> " | wc -l)"

echo -e "\nПорада: Поступово додавайте анотації типів до проекту, починаючи з нових функцій."
