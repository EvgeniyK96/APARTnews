#!/usr/bin/env sh
# Точка входа контейнера: перед запуском приложения накатываем миграции
# и собираем статику (env-переменные, включая DATABASE_URL, уже доступны).
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input

# Запускаем то, что передано в CMD (по умолчанию — gunicorn).
exec "$@"
