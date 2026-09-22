# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install dependencies into it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime C-libraries for Postgres
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

# Create a non-root user and home directory
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy virtualenv from builder stage to /opt/venv (accessible by appuser)
COPY --from=builder /opt/venv /opt/venv

# Set environment variables for virtualenv execution
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Copy application code with non-root user ownership
COPY --chown=appuser:appuser . .

# Fix line endings and execution permissions on entrypoint
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port and default entrypoint
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]