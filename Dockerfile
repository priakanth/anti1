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
# IMPORTANT: Railway's proxy determines where to route traffic by
# reading the EXPOSE instruction. It must be a hardcoded integer.
EXPOSE 8000

# Set explicitly for safety
ENV PORT=8000

# Ensure Python output isn't buffered (so logs appear immediately)
ENV PYTHONUNBUFFERED=1

# ── Start the server ─────────────────────────────────────────────
# We run from the /app/backend directory so relative imports & paths work.
WORKDIR /app/backend

# Run uvicorn strictly bound to 0.0.0.0:8000 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

