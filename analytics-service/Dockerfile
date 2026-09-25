FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy alembic files
COPY alembic.ini .
COPY alembic ./alembic

# Copy application
COPY src/ ./src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Run migrations and start app
CMD alembic upgrade head && python -m analytics_service.main
