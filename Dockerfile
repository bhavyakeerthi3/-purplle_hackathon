# ============================================================
# Stage 1: Builder — install dependencies & generate demo data
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Layer-cache: install OS build deps first (rarely changes)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Layer-cache: install Python deps before copying app code
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy application source
COPY *.py .
COPY dashboard.html .

# Create runtime directories and generate demo data
RUN mkdir -p output data && \
    PYTHONPATH=/install/lib/python3.11/site-packages \
    python generate_demo_data.py

# ============================================================
# Stage 2: Runtime — lean production image
# ============================================================
FROM python:3.11-slim AS runtime

LABEL maintainer="purplle-intelligence" \
      description="Purplle Intelligence FastAPI application"

# Minimal runtime libs for OpenCV / ultralytics
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Bring over installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy application code and pre-generated data
COPY --from=builder /build/*.py ./
COPY --from=builder /build/dashboard.html ./
COPY --from=builder /build/requirements.txt ./
COPY --from=builder /build/output/ ./output/
COPY --from=builder /build/data/ ./data/

# Ensure the non-root user owns the app directory
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
