# Налаштування Docker і CI/CD

## 🐳 Налаштування DockerHub для автоматичних публікацій

Щоб CI/CD правильно публікував Docker-образи у DockerHub, необхідно налаштувати секрети GitHub:

1. Перейдіть до свого репозиторію на GitHub
2. Відкрийте вкладку `Settings`
3. У лівому меню виберіть `Secrets and variables` → `Actions`
4. Натисніть `New repository secret` і додайте два секрети:
   - Назва: `DOCKERHUB_USERNAME` - ваш логін DockerHub
   - Назва: `DOCKERHUB_TOKEN` - токен доступу DockerHub (НЕ пароль)

## 🔑 Створення токена DockerHub

1. Увійдіть у свій акаунт [DockerHub](https://hub.docker.com)
2. Натисніть на свій аватар у правому верхньому куті і виберіть `Account Settings`
3. У меню зліва виберіть `Security`
4. Натисніть `New Access Token`
5. Введіть опис токена (наприклад, "GitHub Actions")
6. Виберіть `Read & Write` для доступу
7. Скопіюйте створений токен і збережіть його як `DOCKERHUB_TOKEN` в секретах GitHub

## 📦 Docker-теги

Workflow налаштований на автоматичне створення тегів:

- `latest` - для гілки `dev`
- `stable` - для гілки `main`
- Версія з Git-тега - якщо зроблено реліз з тегом

## 🔍 Перевірка публікації

Після налаштування секретів і виконання workflow, перевірте наявність образів:

1. Перейдіть на свою сторінку DockerHub: `https://hub.docker.com/r/YOUR_USERNAME/tg_spam_bot`
2. Переконайтеся, що є образи з правильними тегами

## 🧪 Локальне тестування Docker образу

```bash
# Зібрати образ локально
docker build -t tg_spam_bot .

# Запустити контейнер з підстановкою змінних
docker run -d --name tg_spam_bot \
  -e BOT_TOKEN="ваш_токен" \
  -e ADMIN_IDS="12345,67890" \
  tg_spam_bot
```
