#!/usr/bin/env bash
# Скрипт сборки для Render (buildCommand в render.yaml).
# Останавливаемся при первой же ошибке.
set -o errexit

pip install -r requirements.txt

# Собрать статику (WhiteNoise раздаст её из gunicorn).
python manage.py collectstatic --no-input

# Накатить миграции. На платных планах Render это лучше вынести
# в preDeployCommand, но на free-плане держим здесь.
python manage.py migrate
