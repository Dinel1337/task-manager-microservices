#!/bin/bash
set -e

echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Starting Task Notification Service..."
python /app/src/main.py
