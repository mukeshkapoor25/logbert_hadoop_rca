# LogBERT Hadoop RCA - AI Agents Container
# =========================================
# Multi-stage Docker build for LogBERT AI Agents system
# Optimized for production deployment with security and performance

# ============================================================================
# Stage 1: Base Image with System Dependencies
# ============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Stage 2: Python Dependencies Installation
# ============================================================================
FROM base as dependencies

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt /tmp/requirements.txt
COPY requirements/test_requirements.txt /tmp/test_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install test dependencies (optional for development)
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
    pip install --no-cache-dir -r /tmp/test_requirements.txt; \
    fi

# ============================================================================
# Stage 3: Application Setup
# ============================================================================
FROM dependencies as application

# Create non-root user for security
RUN groupadd -r logbert && useradd -r -g logbert -s /bin/bash logbert

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=logbert:logbert . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/AI_MODELS/trained_models /app/AI_MODELS/datasets && \
    chown -R logbert:logbert /app

# Install the package in development mode
RUN pip install -e .

# ============================================================================
# Stage 4: Production Image
# ============================================================================
FROM application as production

# Switch to non-root user
USER logbert

# Set environment variables for the application
ENV LOGBERT_ENV=production \
    LOGBERT_LOG_LEVEL=INFO \
    LOGBERT_HOST=0.0.0.0 \
    LOGBERT_PORT=8000 \
    LOGBERT_WORKERS=4

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run the AI agents API
CMD ["python", "start_ai_agents.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ============================================================================
# Stage 5: Development Image (optional)
# ============================================================================
FROM application as development

# Install development dependencies
RUN pip install --no-cache-dir -r /tmp/test_requirements.txt

# Switch to non-root user
USER logbert

# Set environment variables for development
ENV LOGBERT_ENV=development \
    LOGBERT_LOG_LEVEL=DEBUG \
    LOGBERT_HOST=0.0.0.0 \
    LOGBERT_PORT=8000

# Expose the application port
EXPOSE 8000

# Development command with auto-reload
CMD ["python", "start_ai_agents.py", "--dev", "--host", "0.0.0.0", "--port", "8000"]
