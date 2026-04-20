# ---------- STAGE 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml .
# Устанавливаем зависимости
RUN uv pip install --system --no-cache-dir -e . || \
    uv pip install --system --no-cache-dir -r pyproject.toml


# ---------- STAGE 2: runtime ----------
FROM python:3.11-slim

WORKDIR /app

# КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Добавляем ca-certificates для работы почты через TLS
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    redis-server \
    supervisor \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" appuser

# Копируем Python зависимости из билдера
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код проекта
COPY backend/ .
# Если фронтенд реально нужен внутри этого же образа:
COPY frontend/ /frontend 

# Настройка прав
RUN mkdir -p /app/logs /var/log/supervisor /var/run/redis /var/lib/redis && \
    chown -R appuser:appuser /app /var/log/supervisor /var/run/redis /var/lib/redis

# Конфиг супервизора
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REDIS_HOST=127.0.0.1

EXPOSE 8000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]