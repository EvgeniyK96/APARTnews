#!/usr/bin/env bash
# Скрипт сборки для Render (buildCommand в render.yaml).
# Останавливаемся при первой же ошибке.
set -o errexit

pip install -r requirements.txt

# Собрать статику (WhiteNoise раздаст её из gunicorn).
python manage.py collectstatic --no-input

# Миграции НЕ здесь: во время сборки база из блупринта ещё может быть
# недоступна, из-за чего билд падает. Их выполняет startCommand при
# старте контейнера (см. render.yaml), когда БД уже готова.
