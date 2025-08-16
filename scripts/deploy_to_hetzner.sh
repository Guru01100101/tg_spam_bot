#!/bin/bash
# Скрипт для розгортання на Hetzner

# Налаштування
HETZNER_SSH_USER=""  # Замініть на свій логін на сервері
HETZNER_SSH_HOST=""  # Замініть на IP або хост вашого сервера
HETZNER_SSH_PORT=""  # Замініть на ваш кастомний SSH порт
REMOTE_DIR=""  # Замініть на шлях до директорії проекту на сервері

# Кольори для виводу
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Перевірка аргументів
if [ "$#" -lt 1 ]; then
    echo -e "${YELLOW}Використання: $0 <шлях до приватного ключа> [порт SSH] [без перезапуску]${NC}"
    echo "Приклад 1: $0 ~/.ssh/id_rsa"
    echo "Приклад 2: $0 ~/.ssh/id_rsa 22222"
    echo "Приклад 3: $0 ~/.ssh/id_rsa 22222 norestart"
    exit 1
fi

SSH_KEY=$1

# Перевіряємо, чи вказано кастомний порт
if [ "$#" -gt 1 ] && [[ "$2" =~ ^[0-9]+$ ]]; then
    HETZNER_SSH_PORT=$2
    SKIP_RESTART=$3
else
    SKIP_RESTART=$2
fi

echo -e "${GREEN}🔍 Використовуємо SSH порт: ${HETZNER_SSH_PORT}${NC}"

echo -e "${GREEN}🚀 Починаємо розгортання на Hetzner...${NC}"

# Перевірка з'єднання з сервером
echo -e "${GREEN}🔍 Перевірка з'єднання з сервером...${NC}"
if ! ssh -i $SSH_KEY -p $HETZNER_SSH_PORT -o ConnectTimeout=10 $HETZNER_SSH_USER@$HETZNER_SSH_HOST "echo 'З'єднання встановлено!'"; then
    echo -e "${RED}❌ Не вдалося підключитися до сервера. Перевірте налаштування та спробуйте знову.${NC}"
    exit 1
fi

# Перевірка наявності Docker
echo -e "${GREEN}🔍 Перевірка наявності Docker на сервері...${NC}"
if ! ssh -i $SSH_KEY -p $HETZNER_SSH_PORT $HETZNER_SSH_USER@$HETZNER_SSH_HOST "which docker docker-compose > /dev/null 2>&1"; then
    echo -e "${RED}❌ Docker або docker-compose не знайдено на сервері.${NC}"
    echo -e "${YELLOW}⚠️ Потрібно встановити Docker і Docker Compose:${NC}"
    echo -e "sudo apt update && sudo apt install -y docker.io docker-compose"
    exit 1
fi

# Копіювання файлів на сервер
echo -e "${GREEN}📤 Копіювання docker-compose.yml...${NC}"
scp -i $SSH_KEY -P $HETZNER_SSH_PORT docker-compose.yml $HETZNER_SSH_USER@$HETZNER_SSH_HOST:$REMOTE_DIR/

echo -e "${GREEN}📤 Копіювання .env файлу (якщо він локально оновлений)...${NC}"
scp -i $SSH_KEY -P $HETZNER_SSH_PORT .env $HETZNER_SSH_USER@$HETZNER_SSH_HOST:$REMOTE_DIR/ || echo -e "${YELLOW}⚠️ .env не знайдено локально. Використовуємо існуючий на сервері.${NC}"

echo -e "${GREEN}📤 Копіювання filters.json...${NC}"
scp -i $SSH_KEY -P $HETZNER_SSH_PORT filters.json $HETZNER_SSH_USER@$HETZNER_SSH_HOST:$REMOTE_DIR/

# Перевірка та створення директорій для даних
echo -e "${GREEN}📁 Перевірка директорій на сервері...${NC}"
ssh -i $SSH_KEY -p $HETZNER_SSH_PORT $HETZNER_SSH_USER@$HETZNER_SSH_HOST "mkdir -p $REMOTE_DIR/data $REMOTE_DIR/logs"

# Оновлення образу Docker та перезапуск контейнера
if [ "$SKIP_RESTART" != "norestart" ]; then
    echo -e "${GREEN}🔄 Оновлення образу та перезапуск контейнера...${NC}"
    ssh -i $SSH_KEY -p $HETZNER_SSH_PORT $HETZNER_SSH_USER@$HETZNER_SSH_HOST "cd $REMOTE_DIR && docker-compose pull && docker-compose down && docker-compose up -d"
    
    echo -e "${GREEN}📋 Перевірка логів контейнера...${NC}"
    ssh -i $SSH_KEY -p $HETZNER_SSH_PORT $HETZNER_SSH_USER@$HETZNER_SSH_HOST "cd $REMOTE_DIR && docker-compose logs --tail 20"
    
    echo -e "${GREEN}✅ Розгортання завершено успішно!${NC}"
else
    echo -e "${YELLOW}⚠️ Пропускаємо перезапуск контейнера за запитом.${NC}"
    echo -e "${GREEN}✅ Копіювання файлів завершено. Для запуску виконайте:${NC}"
    echo -e "${YELLOW}ssh -i $SSH_KEY -p $HETZNER_SSH_PORT $HETZNER_SSH_USER@$HETZNER_SSH_HOST \"cd $REMOTE_DIR && docker-compose down && docker-compose up -d\"${NC}"
fi
