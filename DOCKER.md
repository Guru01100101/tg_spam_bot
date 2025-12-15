# Docker репозиторій для tg_spam_bot

Цей файл містить інформацію про Docker-репозиторій для проєкту tg_spam_bot.

## Репозиторій на DockerHub

URL: https://hub.docker.com/r/guru01100101/tg_spam_bot

## Теги образів

- `latest` - останння версія з гілки `dev`
- `stable` - стабільна версія з гілки `main`
- Семантичні версії - відповідають Git-тегам (наприклад, `v1.0.0`)

## Перевірка наявності образів

Якщо ви внесли зміни та виконали push, перевірте наявність оновлених образів на DockerHub:

```bash
# Перевірка останньої версії
docker pull guru01100101/tg_spam_bot:latest

# Перевірка стабільної версії
docker pull guru01100101/tg_spam_bot:stable
```

## Використання образу

```bash
docker run -d --name tg_spam_bot \
  -e BOT_TOKEN="ваш_токен" \
  -e ADMIN_IDS="12345,67890" \
  guru01100101/tg_spam_bot:latest
```

## Запуск без Docker

Якщо ви не хочете використовувати Docker, ви можете запустити бота безпосередньо:

```bash
# Встановлення залежностей
uv venv
source .venv/bin/activate
uv sync

# Запуск бота
python main.py
```
