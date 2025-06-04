# Multi-stage build for security and size optimization
FROM python:3.12-slim as builder

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --only=main --no-root

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Production stage
FROM python:3.12-slim as production

ENV DEBIAN_FRONTEND=noninteractive

# Create non-root user for security
RUN groupadd -r firewall && useradd -r -g firewall firewall

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Ollama from builder
COPY --from=builder /usr/local/bin/ollama /usr/local/bin/ollama

# Create app directories and set permissions
RUN mkdir -p /app/logs /app/config /home/firewall/.ollama && \
    chown -R firewall:firewall /app /home/firewall

WORKDIR /app

# Copy application code
COPY --chown=firewall:firewall . .

# Create default config if not provided
RUN if [ ! -f config.json ]; then cp config.json /app/config/config.json; fi

# Switch to non-root user
USER firewall

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV LLM_FIREWALL_CONFIG=/app/config.json
ENV LLM_FIREWALL_LICENSE=/app/license.key
ENV LLM_FIREWALL_HOST=0.0.0.0
ENV LLM_FIREWALL_PORT=5001

# Expose firewall API port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Default command
CMD ["python3", "firewall_service.py"]