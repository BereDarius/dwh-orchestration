FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY orchestration/ ./orchestration/
COPY config/ ./config/
COPY pyproject.toml ./

# Install package in development mode
RUN pip install -e .

# Create logs directory
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PREFECT_API_URL=http://prefect-server:4200/api

# Default command (can be overridden)
CMD ["python", "-m", "orchestration.deploy", "--serve", "--environment", "dev"]
