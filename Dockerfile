# ═══════════════════════════════════════════════════════════════
# Dockerfile — TaskFlow To-Do App
#
# Single-container strategy:
#   - FastAPI serves both the REST API (/tasks, /health, /docs)
#     AND the frontend static files (HTML, CSS, JS) from the same port.
#   - Railway auto-assigns a PORT environment variable; we read it here.
#   - Python 3.11-slim is used for stability and smaller image size.
# ═══════════════════════════════════════════════════════════════

# ── Stage: Runtime ───────────────────────────────────────────────
FROM python:3.11-slim

# Metadata labels (good practice)
LABEL maintainer="TaskFlow"
LABEL description="Full-stack To-Do app — FastAPI + SQLite + HTML/CSS/JS"

# Set working directory inside the container
WORKDIR /app

# ── Install Python dependencies ──────────────────────────────────
# Copy requirements first — Docker caches this layer separately.
# If only source code changes (not requirements), this layer is reused,
# making rebuilds much faster.
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy application source ──────────────────────────────────────
# Copy backend Python files
COPY backend/ ./backend/

# Copy frontend static files
# FastAPI will serve these via StaticFiles at "/"
COPY frontend/ ./frontend/

# ── Create data directory for SQLite persistence ─────────────────
# When using Railway Volumes, mount at /data. Set env var:
#   DATABASE_URL=sqlite:////data/todo.db
RUN mkdir -p /data

# ── Environment defaults ─────────────────────────────────────────
# PORT: Railway sets this automatically. Default to 8000 locally.
ENV PORT=8000

# Ensure Python output isn't buffered (so logs appear immediately)
ENV PYTHONUNBUFFERED=1

# ── Expose the port ──────────────────────────────────────────────
EXPOSE ${PORT}

# ── Start the server ─────────────────────────────────────────────
# We run from the /app/backend directory so relative imports & paths work.
# --workers 1: SQLite doesn't support multiple writers safely.
# --no-access-log: Railway shows its own logs; keeps output clean.
WORKDIR /app/backend

CMD uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1
