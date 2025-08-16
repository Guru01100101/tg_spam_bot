# Етап збірки
FROM python:3.11-slim AS builder

# Встановлення базових інструментів
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Встановлення uv з фіксованою версією
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uvx /usr/local/bin/uvx

WORKDIR /app

# Копіювання всіх необхідних файлів для збірки
COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md ./
COPY core/ core/
COPY models/ models/
COPY utils/ utils/

# Створення віртуального середовища та встановлення залежностей
RUN uv venv && \
    uv sync --no-editable

# Другий етап - фінальний образ
FROM python:3.11-slim

# Метадані для образу
LABEL org.opencontainers.image.title="Telegram Spam Bot"
LABEL org.opencontainers.image.description="Bot for telegram chats or groups for deleting spam messages"
LABEL org.opencontainers.image.url="https://github.com/Guru01100101/tg_spam_bot"
LABEL org.opencontainers.image.source="https://github.com/Guru01100101/tg_spam_bot"
LABEL org.opencontainers.image.version="0.2.1"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Копіювання віртуального середовища з етапу збірки
COPY --from=builder /app/.venv /app/.venv

# Копіювання файлів додатку
COPY core/ core/
COPY models/ models/
COPY utils/ utils/
COPY main.py .
COPY filters.json .
# patterns.json та admins.json створюються під час виконання

# Створення директорій для логів і даних
RUN mkdir -p /app/logs /app/data

# Налаштування шляху до біну віртуального середовища
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Перевірка здоров'я
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os, sys; sys.exit(0 if os.path.exists('/app/main.py') else 1)"

# Запуск бота з активованим віртуальним середовищем
CMD ["python", "-u", "main.py"]
