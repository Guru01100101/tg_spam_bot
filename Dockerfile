FROM python:3.11-slim AS builder

# Метадані для образу
LABEL org.opencontainers.image.title="Telegram Spam Bot"
LABEL org.opencontainers.image.description="Bot for telegram chats or groups for deleting spam messages"
LABEL org.opencontainers.image.url="https://github.com/Guru01100101/tg_spam_bot"
LABEL org.opencontainers.image.source="https://github.com/Guru01100101/tg_spam_bot"
LABEL org.opencontainers.image.version="0.2.1"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install uv using official method
RUN apt-get update && \
    apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/ && \
    mv /root/.local/bin/uvx /usr/local/bin/

# Copy dependencies specification
COPY pyproject.toml uv.lock* ./

# Copy only necessary files for the application
COPY core/ core/
COPY models/ models/
COPY utils/ utils/
COPY main.py .
COPY filters.json .
# patterns.json and admins.json are created at runtime

# Create virtual environment and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv sync

# Second stage for smaller image
FROM python:3.11-slim

WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files and virtual environment from builder
COPY --from=builder /app /app
COPY --from=builder /app/.venv /app/.venv

# Create logs and data directories
RUN mkdir -p /app/logs /app/data

# Default environment variables
ENV BOT_TOKEN=""
ENV ADMIN_IDS=""
ENV MUTE_DURATION_DAYS=2
ENV BAN_DURATION_DAYS=30

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os, sys; sys.exit(0 if os.path.exists('/app/main.py') else 1)"

ENV PYTHONUNBUFFERED=1

# Run the bot with Python directly (dependencies already in site-packages)
CMD ["python", "-u", "main.py"]
