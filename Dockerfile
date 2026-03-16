# ── Stage 1: build dependencies ──────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: production image ────────────────────────────────
FROM python:3.12-slim

# Security: non-root user
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY schema.sql .

# Own everything by app user
RUN chown -R app:app /app

USER app

ENV PORT=8000
EXPOSE ${PORT}

# Healthcheck against the real endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{__import__(\"os\").environ.get(\"PORT\",8000)}/health')" || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
