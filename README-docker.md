# 🐳 Запуск через Docker

Бот може бути запущений у Docker контейнері, що забезпечує ізольоване середовище та спрощену розгортання.

## 🛠️ Підготовка до запуску

Перед запуском бота рекомендується виконати скрипт ініціалізації, який створить необхідні директорії та файли:

```bash
# Зробити скрипт виконуваним
chmod +x setup.sh

# Запустити скрипт ініціалізації
./setup.sh
```

Скрипт створить необхідну структуру каталогів і файлів:

- Директорії `data/` та `logs/`
- Файл `.env` з шаблону `env.example`
- Базовий `filters.json` (якщо його немає)
- Пусті файли `patterns.json` та `admins.json` в директорії `data/`
- Файл `char_map.json` з картою заміни символів

## 🚀 Запуск контейнера

### Використання Docker Compose (рекомендовано)

Після виконання скрипту `setup.sh` та налаштування файлу `.env` запустіть бота:

```bash
# Запуск бота у фоновому режимі
docker-compose up -d

# Перегляд логів
docker-compose logs -f
```

### Ручний запуск з Docker

Якщо ви не хочете використовувати Docker Compose, можна запустити контейнер напряму:

```bash
docker run -d \
  --name telegram_spam_bot \
  -e BOT_TOKEN="your_bot_token_here" \
  -e ADMIN_IDS="123456789,987654321" \
  -e MUTE_DURATION_DAYS=2 \
  -e BAN_DURATION_DAYS=30 \
  -v $(pwd)/filters.json:/app/filters.json \
  -v $(pwd)/data/patterns.json:/app/patterns.json \
  -v $(pwd)/data/admins.json:/app/admins.json \
  -v $(pwd)/data/char_map.json:/app/char_map.json \
  -v $(pwd)/logs:/app/logs \
  guru01100101/tg-spam-bot:latest
```

## 📄 Конфігураційні файли

### .env

Містить основні налаштування бота:

```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here
 
# Admin Configuration
# Add your Telegram ID(s) here
# Single admin: ADMIN_IDS=123456789
# Multiple admins: ADMIN_IDS=123456789,987654321,555666777
ADMIN_IDS=123456789,987654321 

# Configuration for mute and ban timers in days
MUTE_DURATION_DAYS=2
BAN_DURATION_DAYS=30
```

### filters.json

Містить базові регулярні вирази для фільтрації спаму:

```json
[
  "([рp][уy]бл(и|ей|ий|ями|я)?)",
  "([уy]д[аa]л[еe]нн[оo])",
  "(₽)",
  "(\\$)"
]
```

### data/patterns.json

Створюється автоматично та містить динамічні патерни, додані через адмін-панель:

```json
[
  "крипто",
  "заработок",
  "инвестиции"
]
```

### data/admins.json

Створюється автоматично та містить динамічно додані ID адміністраторів:

```json
[
  123456789,
  987654321
]
```

### data/char_map.json

Містить карту заміни символів для нормалізації повідомлень:

```json
{
  "а": ["a", "@"],
  "б": ["b", "6"],
  "в": ["v", "b"],
  ...
}
```

## 🔄 Оновлення контейнера

Для оновлення бота до нової версії без втрати конфігурації:

```bash
# Зупинити і видалити старий контейнер
docker-compose down

# Отримати нову версію образу
docker pull guru01100101/tg-spam-bot:latest

# Запустити оновлений контейнер
docker-compose up -d
```

## 📊 Моніторинг та обслуговування

### Перегляд логів

```bash
# Через Docker Compose
docker-compose logs -f

# Або безпосередньо через Docker
docker logs -f telegram_spam_bot
```

### Перевірка стану

```bash
# Через Docker Compose
docker-compose ps

# Або безпосередньо через Docker
docker ps -a | grep telegram_spam_bot
```

### Перезапуск бота

```bash
# Через Docker Compose
docker-compose restart

# Або безпосередньо через Docker
docker restart telegram_spam_bot
```

## 🛑 Зупинка бота

```bash
# Через Docker Compose
docker-compose stop

# Повне видалення контейнера (конфігурації збережуться у томах)
docker-compose down
```
