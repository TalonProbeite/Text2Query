# ---------- STAGE 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml .

RUN uv pip install --system --no-cache-dir -r pyproject.toml


# ---------- STAGE 2: runtime ----------
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY backend/ .
COPY frontend/ /frontend

# папка под логи (важно чтобы существовала)
RUN mkdir -p /app/logs

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]