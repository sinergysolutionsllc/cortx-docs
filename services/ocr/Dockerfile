# Multi-stage build for OCR service with Tesseract
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies and system libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first for better caching
COPY services/ocr/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only application code (respects .dockerignore)
COPY services/ocr/ /app/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash ocr && \
    chown -R ocr:ocr /app

USER ocr

# Expose service port
EXPOSE 8137

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8137/healthz || exit 1

# Use efficient startup with single worker (can scale with K8s replicas)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8137", "--workers", "1"]
