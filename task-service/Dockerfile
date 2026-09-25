FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY alembic.ini .
COPY alembic ./alembic
COPY src ./src

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Делаем start.sh исполняемым
RUN chmod 755 /app/src/start.sh
CMD ["bash", "/app/src/start.sh"]



