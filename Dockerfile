FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Зависимости ставятся отдельным слоем — кешируется, если requirements не менялись.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

# Миграции + сборка статики при старте контейнера, затем gunicorn.
ENTRYPOINT ["./docker-entrypoint.sh"]
# Render передаёт порт в $PORT; локально по умолчанию 8000.
CMD ["sh", "-c", "gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
