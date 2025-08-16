#!/bin/bash
# Скрипт для локального тестування Docker-образу

# Кольори для виводу
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔨 Збираємо Docker-образ локально...${NC}"
docker build -t local-tg-spam-bot:test .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Помилка при збиранні образу!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Образ успішно зібрано.${NC}"

# Перевіряємо наявність .env файлу
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️ Файл .env не знайдено. Створюємо тестовий...${NC}"
    echo "BOT_TOKEN=test_token" > .env
    echo "ADMIN_IDS=123456789" >> .env
    echo "MUTE_DURATION_DAYS=2" >> .env
    echo "BAN_DURATION_DAYS=30" >> .env
fi

echo -e "${GREEN}🚀 Запускаємо контейнер для тестування...${NC}"
docker run --rm -it \
    --name test_spam_bot \
    -v "$(pwd)/.env:/app/.env" \
    -v "$(pwd)/filters.json:/app/filters.json" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    local-tg-spam-bot:test

echo -e "${GREEN}✅ Тестування завершено.${NC}"
