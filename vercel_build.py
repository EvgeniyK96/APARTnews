"""Шаг сборки на Vercel (`[tool.vercel.scripts] build` в pyproject.toml).

Запускается после установки зависимостей. collectstatic здесь не нужен —
Vercel выполняет его сам и раздаёт STATIC_ROOT со своего CDN.

Миграции гоняем на сборке: у функции нет отдельного шага «release», а база
внешняя (Neon / любой Postgres) и доступна уже во время билда.
"""

import os
import sys

import django
from django.core.management import call_command


def main():
    if not os.environ.get("DATABASE_URL"):
        # Без внешней БД Django откатится на SQLite внутри read-only бандла,
        # поэтому миграции бессмысленны, а сайт не сможет писать в базу.
        print("vercel_build: DATABASE_URL не задан — пропускаю migrate. Подключи Postgres к проекту.")
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()
    call_command("migrate", interactive=False)
    # Таблица для dbcache (кэш GNews на Vercel); для других бэкендов — no-op.
    call_command("createcachetable")


if __name__ == "__main__":
    sys.exit(main())
