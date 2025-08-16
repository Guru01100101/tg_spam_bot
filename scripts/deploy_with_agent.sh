#!/bin/bash
# Скрипт для розгортання на Hetzner з використанням SSH конфігурації

# Налаштування
SSH_HOST_ALIAS="hetzner"  # Аліас хоста з вашого ~/.ssh/config
REMOTE_DIR="/home/guru101/tg_spam_bot"  # Повний шлях до директорії проекту на сервері

# Кольори для виводу
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Перевірка аргументів для опції перезапуску
if [ "$#" -gt 0 ]; then
    SKIP_RESTART=$1
fi

echo -e "${GREEN}� Починаємо розгортання на Hetzner...${NC}"
echo -e "${GREEN}� Використовуємо SSH конфіг з аліасом: ${SSH_HOST_ALIAS}${NC}"

# Перевірка з'єднання з сервером
echo -e "${GREEN}🔍 Перевірка з'єднання з сервером...${NC}"
if ! ssh -o ConnectTimeout=10 $SSH_HOST_ALIAS "echo \"З'єднання встановлено!\""; then
    echo -e "${RED}❌ Не вдалося підключитися до сервера. Перевірте SSH конфігурацію.${NC}"
    echo -e "${YELLOW}⚠️ Переконайтеся, що у вас правильно налаштований файл ~/.ssh/config:${NC}"
    echo -e "Host $SSH_HOST_ALIAS"
    echo -e "    HostName ваш.хост.або.ip"
    echo -e "    User ваш_користувач"
    echo -e "    Port ваш_порт"
    echo -e "    IdentityFile ~/.ssh/ваш_ключ"
    exit 1
fi

# Перевірка наявності Docker
echo -e "${GREEN}🔍 Перевірка наявності Docker на сервері...${NC}"
if ! ssh $SSH_HOST_ALIAS "which docker docker-compose > /dev/null 2>&1"; then
    echo -e "${RED}❌ Docker або docker-compose не знайдено на сервері.${NC}"
    echo -e "${YELLOW}⚠️ Потрібно встановити Docker і Docker Compose:${NC}"
    echo -e "sudo apt update && sudo apt install -y docker.io docker-compose"
    exit 1
fi

# Створення директорії проекту на сервері, якщо вона не існує
echo -e "${GREEN}📁 Створення директорії проекту...${NC}"
ssh $SSH_HOST_ALIAS "mkdir -p $REMOTE_DIR"

# Копіювання файлів на сервер
echo -e "${GREEN}📤 Копіювання docker-compose.yml...${NC}"
scp docker-compose.yml $SSH_HOST_ALIAS:$REMOTE_DIR/

echo -e "${GREEN}📤 Копіювання filters.json...${NC}"
scp filters.json $SSH_HOST_ALIAS:$REMOTE_DIR/

# Створення додаткових директорій для даних та логів
echo -e "${GREEN}📁 Створення директорій для даних та логів...${NC}"
ssh $SSH_HOST_ALIAS "mkdir -p $REMOTE_DIR/data $REMOTE_DIR/logs"

# Оновлення образу Docker та перезапуск контейнера
if [ "$SKIP_RESTART" != "norestart" ]; then
    echo -e "${GREEN}🔄 Оновлення образу та перезапуск контейнера...${NC}"
    ssh $SSH_HOST_ALIAS "cd $REMOTE_DIR && docker compose pull && docker compose down telegram_spam_bot && docker compose up -d"
    
    # Даємо контейнеру трохи часу на запуск
    echo -e "${GREEN}⏳ Чекаємо запуску контейнера...${NC}"
    sleep 5
    
    # Перевіряємо логи та шукаємо помилки
    echo -e "${GREEN}📋 Перевірка логів контейнера...${NC}"
    ssh $SSH_HOST_ALIAS "cd $REMOTE_DIR && docker compose logs --tail 20 bot"
    
    echo -e "${GREEN}🔍 Перевірка наявності помилок...${NC}"
    ERROR_CHECK=$(ssh $SSH_HOST_ALIAS "cd $REMOTE_DIR && docker compose logs bot | grep -i 'error\|exception\|traceback' | tail -10")
    
    if [ ! -z "$ERROR_CHECK" ]; then
        echo -e "${RED}❌ Знайдено помилки в логах:${NC}"
        echo -e "$ERROR_CHECK"
        echo -e "${YELLOW}⚠️ Рекомендується перевірити конфігурацію та залежності.${NC}"
    fi
    
    echo -e "${GREEN}✅ Розгортання завершено успішно!${NC}"
else
    echo -e "${YELLOW}⚠️ Пропускаємо перезапуск контейнера за запитом.${NC}"
    echo -e "${GREEN}✅ Копіювання файлів завершено. Для запуску виконайте:${NC}"
    echo -e "${YELLOW}ssh $SSH_HOST_ALIAS \"cd $REMOTE_DIR && docker compose down && docker compose up -d\"${NC}"
fi
