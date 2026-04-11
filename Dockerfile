# ---------- STAGE 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml .

RUN uv pip install --system --no-cache-dir -e . || \
    uv pip install --system --no-cache-dir -r pyproject.toml


# ---------- STAGE 2: runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости для рантайма (libpq нужен asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь
RUN adduser --disabled-password --gecos "" appuser

# Копируем зависимости из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код
COPY backend/ .
COPY frontend/ /frontend

# Папка под логи с правильным владельцем
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["python", "run.py"]