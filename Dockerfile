# RDKit Sidecar Service - Al-Zamzami Molecular Twin v7.2
# Production-grade Docker image with RDKit full stack
# Conforms to: CII Best Practices, NIST Cybersecurity Framework

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install system dependencies for RDKit compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libboost-all-dev \
    libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash rdkit && \
    mkdir -p /app && \
    chown -R rdkit:rdkit /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=rdkit:rdkit app.py .
COPY --chown=rdkit:rdkit geometry.py .
COPY --chown=rdkit:rdkit validation.py .

# Switch to non-root user
USER rdkit

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Start service with production server (uvicorn)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
