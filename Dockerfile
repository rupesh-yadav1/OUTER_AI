# ---------- STAGE 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Cleanup build tools
RUN apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy project code
COPY backend/ ./backend/

# ---------- STAGE 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Avoid writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install Python dependencies again
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files from builder
COPY --from=builder /app /app

# Set up a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1

# Start the app
ENTRYPOINT ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
