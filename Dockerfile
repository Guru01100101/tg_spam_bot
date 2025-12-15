FROM python:3.11-slim

# Встановити build-залежності (опціонально)
# RUN apt-get update && apt-get install -y build-essential gcc && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
COPY core/ core/
COPY models/ models/
COPY utils/ utils/
COPY main.py .
COPY filters.json .

RUN uv sync

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "-u", "main.py"]