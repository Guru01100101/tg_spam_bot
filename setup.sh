#!/bin/bash

# Кольорові повідомлення для кращої читабельності
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE} Ініціалізація Telegram Spam Bot    ${NC}"
echo -e "${BLUE}=====================================${NC}"

# Створення необхідних директорій
echo -e "${GREEN}[1/5]${NC} Створення директорій..."
mkdir -p ./data
mkdir -p ./logs
echo -e "${GREEN}✓${NC} Директорії створено"

# Перевірка наявності .env файлу
echo -e "${GREEN}[2/5]${NC} Перевірка конфігурації .env..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠${NC} .env файл не знайдено"
    echo -e "${GREEN}→${NC} Створюємо .env файл з шаблону..."
    cp env.example .env
    echo -e "${YELLOW}⚠${NC} ВАЖЛИВО: Відредагуйте файл .env, додавши необхідні налаштування!"
else
    echo -e "${GREEN}✓${NC} .env файл вже існує"
fi

# Перевірка наявності filters.json
echo -e "${GREEN}[3/5]${NC} Перевірка базових фільтрів..."
if [ ! -f filters.json ]; then
    echo -e "${YELLOW}⚠${NC} filters.json не знайдено"
    echo -e "${GREEN}→${NC} Створюємо базовий filters.json..."
    echo '[
  "([рp][уy]бл(и|ей|ий|ями|я)?)",
  "([уy]д[аa]л[еe]нн[оo])",
  "(₽)",
  "(\\$)"
]' > filters.json
    echo -e "${GREEN}✓${NC} Базові фільтри створено"
else
    echo -e "${GREEN}✓${NC} Файл filters.json вже існує"
fi

# Перевірка наявності patterns.json в директорії data
echo -e "${GREEN}[4/5]${NC} Перевірка файлів конфігурації..."
if [ ! -f ./data/patterns.json ]; then
    echo -e "${GREEN}→${NC} Створюємо patterns.json..."
    echo '[]' > ./data/patterns.json
fi

# Перевірка наявності admins.json в директорії data
if [ ! -f ./data/admins.json ]; then
    echo -e "${GREEN}→${NC} Створюємо admins.json..."
    echo '[]' > ./data/admins.json
fi

# Перевірка наявності char_map.json в директорії data
if [ ! -f ./data/char_map.json ]; then
    echo -e "${GREEN}→${NC} Створюємо char_map.json..."
    echo '{
  "а": ["a", "@"],
  "б": ["b", "6"],
  "в": ["v", "b"],
  "г": ["g"],
  "е": ["e"],
  "з": ["3", "z"],
  "и": ["i", "u"],
  "к": ["k"],
  "л": ["l"],
  "м": ["m"],
  "н": ["n"],
  "о": ["o", "0"],
  "п": ["p"],
  "р": ["p", "r"],
  "с": ["c", "s"],
  "т": ["t"],
  "у": ["y"],
  "х": ["x", "h"],
  "ч": ["4"],
  "ш": ["sh"],
  "щ": ["sh"],
  "ы": ["bi"],
  "ь": ["b"],
  "э": ["e"],
  "ю": ["io"],
  "я": ["ya"]
}' > ./data/char_map.json
fi
echo -e "${GREEN}✓${NC} Всі конфігураційні файли перевірено або створено"

# Перевірка наявності Docker та Docker Compose
echo -e "${GREEN}[5/5]${NC} Перевірка залежностей..."
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Docker не встановлено. Встановіть Docker для запуску в контейнері."
else
    echo -e "${GREEN}✓${NC} Docker встановлено"
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} Docker Compose не встановлено. Встановіть Docker Compose для запуску за допомогою docker-compose.yml."
    else
        echo -e "${GREEN}✓${NC} Docker Compose встановлено"
    fi
fi

echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}✓ Підготовка до запуску завершена!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "Для запуску бота виконайте: ${YELLOW}docker-compose up -d${NC}"
echo -e "Для перегляду логів: ${YELLOW}docker-compose logs -f${NC}"
