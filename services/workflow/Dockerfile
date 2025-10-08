# Multi-stage build for optimized Python service
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first for better caching
COPY services/workflow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy packages and modules for building CORTX packages
COPY packages/ /app/packages/
COPY modules/ /app/modules/

# Install CORTX packages to user site-packages
RUN pip install -e packages/cortx_core/ && \
    pip install -e packages/cortx_rulepack_sdk/ && \
    pip install -e packages/cortx_backend/ && \
    pip install -e modules/reconciliation/

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the editable-installed packages (needed for cortx_core, etc.)
COPY --from=builder /app/packages /app/packages
COPY --from=builder /app/modules /app/modules

# Update PATH to include user packages

# Copy only application code (respects .dockerignore)
COPY services/workflow/ /app/

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash cortx
RUN chown -R cortx:cortx /app
USER cortx

EXPOSE 8130

# Use more efficient startup
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8130", "--workers", "1"]
