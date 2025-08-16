FROM python:3.11-slim AS builder

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

# Install dependencies
RUN uv sync

# Second stage for smaller image
FROM python:3.11-slim

WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files from builder
COPY --from=builder /app /app

# Default environment variables
ENV BOT_TOKEN=""
ENV ADMIN_IDS=""
ENV MUTE_DURATION_DAYS=2
ENV BAN_DURATION_DAYS=30

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os, sys; sys.exit(0 if os.path.exists('/app/main.py') else 1)"

ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["uv", "run", "python", "-u", "main.py"]
