# ── Stage 1: build Python dependencies ──────────────────────
FROM python:3.12-slim AS py-builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: build React SPA ────────────────────────────────
FROM node:22-slim AS fe-builder

WORKDIR /web

COPY web/package.json web/package-lock.json ./
RUN npm ci
RUN npm rebuild lightningcss

COPY web/ ./
RUN npm run build

# ── Stage 3: production image ───────────────────────────────
FROM python:3.12-slim

# Security: non-root user
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

# Copy only installed packages from builder
COPY --from=py-builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY schema.sql seed.py ./

# Copy built frontend
COPY --from=fe-builder /web/dist ./static/

# Own everything by app user
RUN chown -R app:app /app

USER app

ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
