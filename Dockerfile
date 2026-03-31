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

# Ensure Python output isn't buffered (so logs appear immediately)
ENV PYTHONUNBUFFERED=1

# ── Start the server ─────────────────────────────────────────────
# We run from the /app/backend directory so relative imports & paths work.
WORKDIR /app/backend

# Railway injects the $PORT variable securely at runtime.
# IMPORTANT: Use '::' instead of '0.0.0.0' for the host! 
# Railway's internal proxy routes healthchecks over IPv6. 
# Uvicorn on 0.0.0.0 only listens to IPv4, causing 502 Connection Refused.
CMD sh -c "uvicorn main:app --host :: --port $PORT --workers 1"


