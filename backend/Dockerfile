# T4-02: Backend Dockerfile
# Spec Reference: spec.md FR-1.1, FR-1.3, FR-1.6
# Plan Reference: plan.md Section 4.1, 1.3

# ============================================
# Stage 1: Build - Install Python dependencies
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/

# Set up environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Health check for Kubernetes probes
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run as non-root user for security
USER appuser

# Start FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
