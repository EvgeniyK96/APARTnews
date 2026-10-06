# APARTnews

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Новостной сайт на Django с серверным рендерингом. Новости берутся из [GNews](https://gnews.io) на **русском языке**, статья читается **целиком прямо на сайте** — без перехода на источник, а оформление сделано в стиле ленты [ТАСС](https://tass.ru/mezhdunarodnaya-panorama) в зелёной палитре и адаптировано под мобильные устройства.

Проект вырос из Django + DRF стартер-шаблона, поэтому REST-эндпоинты и Swagger остались на месте (см. [REST API](#rest-api-наследие-шаблона)), но основной сайт — это server-rendered страницы на Django-шаблонах с сессионной аутентификацией.

---

## Возможности

- 📰 **Лента новостей** из GNews с разбивкой по разделам (в мире, бизнес, технологии, спорт, наука и др.).
- 🇷🇺 **Русский язык** — запросы к GNews идут с `lang=ru`.
- 📖 **Полный текст на сайте** — страница-источник парсится через [trafilatura](https://trafilatura.readthedocs.io/), извлечённый текст показывается прямо в карточке новости. У GNews в ответе только обрезанный анонс, поэтому полный текст достаётся парсером и кэшируется на сутки.
- ⭐ **Избранное** — авторизованный пользователь добавляет в избранное отдельные новости и целые разделы; новости из избранных разделов поднимаются в начало ленты.
- 💬 **Комментарии** к новостям для авторизованных пользователей.
- 🔍 **Поиск** по новостям.
- 🎨 **Дизайн под ТАСС в зелёных тонах** + адаптивная вёрстка (планшеты и телефоны).
- 👤 **Регистрация и вход** через стандартную сессионную аутентификацию Django.

---

## Стек

| Пакет | Назначение |
|---|---|
| [Django](https://www.djangoproject.com/) | Основной фреймворк, server-rendered шаблоны |
| [trafilatura](https://trafilatura.readthedocs.io/) | Извлечение полного текста статьи со страницы-источника |
| [requests](https://requests.readthedocs.io/) | HTTP-клиент к GNews API |
| [django-environ](https://django-environ.readthedocs.io/) | Чтение настроек из `.env` |
| [django-jazzmin](https://django-jazzmin.readthedocs.io/) | Тема для Django Admin |
| [Django REST Framework](https://www.django-rest-framework.org/) + [djoser](https://djoser.readthedocs.io/) + [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/) | REST API (наследие шаблона) |
| [drf-yasg](https://drf-yasg.readthedocs.io/) | Swagger / ReDoc для REST API |
| [Pillow](https://pillow.readthedocs.io/) · [psycopg2-binary](https://www.psycopg.org/) | Изображения · драйвер PostgreSQL |

---

## Быстрый старт

### Локально (без Docker)

```bash
# 1. Виртуальное окружение
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

# 2. Зависимости
pip install -r requirements.txt

# 3. Переменные окружения
cp .env.example .env
# Открой .env и впиши свой GNEWS_API_KEY (см. раздел ниже)

# 4. Миграции
python manage.py migrate

# 5. Запуск
python manage.py runserver
```

Сайт откроется на [http://127.0.0.1:8000](http://127.0.0.1:8000).

> **Важно:** `GNEWS_API_KEY` и `GNEWS_LANG` читаются из `.env` один раз при старте, а ответы GNews кешируются в памяти процесса. После изменения `.env` **перезапусти** `runserver`, чтобы правки вступили в силу.

### Через Docker

```bash
cp .env.example .env           # не забудь вписать GNEWS_API_KEY
docker compose up --build
```

Сайт доступен на [http://localhost:8000](http://localhost:8000). PostgreSQL и миграции поднимаются автоматически.

---

## Получение ключа GNews

1. Зарегистрируйся на [gnews.io](https://gnews.io) и скопируй API-ключ из личного кабинета.
2. Впиши его в `.env`:

```dotenv
GNEWS_API_KEY=ваш_ключ
```

> На бесплатном плане GNews действует задержка публикации ~12 часов и небольшой лимит запросов. Чтобы не упираться в лимит, ответы кешируются на `GNEWS_CACHE_TTL` секунд. При ошибке `429 Too many requests` подожди несколько минут либо увеличь `GNEWS_CACHE_TTL`.

---

## Переменные окружения

Все настройки задаются через `.env` (шаблон — в `.env.example`).

| Переменная | По умолчанию | Описание |
|---|---|---|
| `SECRET_KEY` | *(в .env.example)* | Секретный ключ Django. Замени перед продом. |
| `DEBUG` | `True` | Режим отладки. В продакшне — `False`. |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Разрешённые хосты через запятую. |
| `LANGUAGE_CODE` | `ru` | Язык интерфейса Django. |
| `TIME_ZONE` | `Asia/Almaty` | Часовой пояс (влияет на отображение дат). |
| `GNEWS_API_KEY` | *(пусто)* | **Обязательно.** Ключ API GNews. |
| `GNEWS_LANG` | `ru` | Язык новостей, передаётся в GNews как `lang`. |
| `GNEWS_CACHE_TTL` | `1800` | Сколько секунд кешировать ответы GNews. |
| `DATABASE_URL` | *(не задан → SQLite)* | URL подключения к БД. |
| `STATIC_ROOT` | `staticfiles` | Папка для `collectstatic`. |
| `MEDIA_ROOT` | `media` | Папка для медиафайлов. |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | *(см. .env.example)* | Реквизиты Postgres для Docker. |

Сгенерировать новый `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Как это устроено

Сайт работает в режиме **прокси к GNews** — лента не хранится в БД целиком, каждая подборка запрашивается у GNews и смягчается коротким кешем (локально — в памяти, `LocMemCache`; на Vercel — в базе, см. [Деплой](#vercel)).

- **Клиент GNews** — [`apps/news/services.py`](apps/news/services.py): запросы к API, кеширование, парсер полного текста (`extract_fulltext`).
- **Вьюхи** — [`apps/news/views.py`](apps/news/views.py): лента, детальная страница с полным текстом и комментариями, избранное, регистрация.
- **В БД хранится только** избранное и комментарии — вместе со «снимком» той новости, к которой они привязаны ([`apps/news/models.py`](apps/news/models.py), `ArticleSnapshot`). Это позволяет показать новость, даже если она уже пропала из выдачи GNews.
- **Шаблоны** — [`templates/`](templates/), стили — [`static/css/site.css`](static/css/site.css).

### Маршруты сайта

| URL | Назначение |
|---|---|
| `/` | Лента новостей (разделы, поиск через `?category=`, `?q=`) |
| `/article/<id>/` | Страница новости с полным текстом и комментариями |
| `/favorites/` | Избранные новости и разделы (требует входа) |
| `/accounts/login/` · `/register/` · `/accounts/logout/` | Вход, регистрация, выход |
| `/admin/` | Django-админка |

---

## База данных

**SQLite (по умолчанию)** — ничего настраивать не нужно, после `migrate` появится `db.sqlite3`.

**PostgreSQL** — достаточно одной строки в `.env`, правок кода не требуется:

```dotenv
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

---

## REST API (наследие шаблона)

Проект построен на DRF-стартере, поэтому JWT-аутентификация и авто-документация остались доступны параллельно основному сайту.

| Интерфейс | URL |
|---|---|
| Swagger UI | [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/) |
| ReDoc | [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/) |

Основные эндпоинты аутентификации (`djoser` + SimpleJWT):

| Метод | URL | Описание |
|---|---|---|
| `POST` | `/api/auth/users/` | Регистрация пользователя |
| `POST` | `/api/auth/jwt/create/` | Получить access + refresh токены |
| `POST` | `/api/auth/jwt/refresh/` | Обновить access-токен |
| `GET` | `/api/auth/users/me/` | Данные текущего пользователя |

> Сам сайт использует **сессионную** аутентификацию Django, а не JWT — токены нужны только для REST API.

---

## Тесты и CI

```bash
pip install -r requirements-dev.txt   # dev-зависимости (ruff, pytest)

pytest                 # тесты
ruff check .           # линтер
ruff check --fix .     # автоисправление
python manage.py check # проверка конфигурации Django
```

При каждом `push` / `pull_request` в `main` GitHub Actions прогоняет линтер, `manage.py check`, миграции и тесты на SQLite (см. [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

---

## Деплой

### Vercel

Vercel поддерживает Django без отдельной конфигурации: находит `manage.py`, берёт WSGI-приложение (`core.wsgi:application`, явно указано в `[tool.vercel]` в [`pyproject.toml`](pyproject.toml)) и запускает его как одну Vercel Function. Статику Vercel собирает сам (`collectstatic` → `STATIC_ROOT`) и раздаёт её со своего CDN.

1. Залей репозиторий на GitHub/GitLab и импортируй его на [vercel.com/new](https://vercel.com/new) (или `vercel deploy` из папки проекта, Vercel CLI ≥ 50.38).
2. Подключи PostgreSQL: **Storage → Marketplace → Neon** (или любой внешний Postgres). Интеграция сама добавит `DATABASE_URL`. SQLite на Vercel не подходит: файловая система функции только для чтения и не переживает перезапуск.
3. В **Settings → Environment Variables** добавь:
   - `SECRET_KEY` — длинная случайная строка (`python -c "import secrets; print(secrets.token_urlsafe(50))"`);
   - `GNEWS_API_KEY` — ключ GNews;
   - `DEBUG=False`;
   - при желании `GNEWS_LANG`, `TIME_ZONE`, `GNEWS_CACHE_TTL`.
4. Запусти деплой. После установки зависимостей выполнится [`vercel_build.py`](vercel_build.py): `migrate` + `createcachetable`.
5. Создай суперпользователя локально, указав прод-базу: `DATABASE_URL=<url из Vercel> python manage.py createsuperuser`.

Что уже настроено под Vercel в коде:
- `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` автоматически дополняются доменами из `VERCEL_URL`, `VERCEL_BRANCH_URL` и `VERCEL_PROJECT_PRODUCTION_URL` (прод, preview-деплои и домены веток). Свой домен добавь в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` (`https://example.com`).
- **Кэш GNews на Vercel хранится в базе** (`dbcache://django_cache`): память функции теряется при холодном старте и не общая между инстансами, а с `LocMemCache` бесплатный лимит GNews быстро бы кончился. Бэкенд можно сменить через `CACHE_URL` (например, `redis://...` для Upstash Redis — тогда добавь пакет `redis` в зависимости).
- [`.vercelignore`](.vercelignore) не даёт загрузить `venv/`, локальную базу и Docker/Render-файлы.

> **Регион:** по умолчанию функции Vercel работают в `iad1` (США). Регион базы Neon выбирай рядом с регионом функций, иначе каждый запрос к БД будет идти через океан. Регион функций меняется в **Settings → Functions**.

> **Preview-деплои** используют те же переменные, что и прод, если не разделить их по окружениям. Чтобы миграции из веток не попадали в прод-базу, задай для окружения Preview отдельный `DATABASE_URL` (у Neon для этого есть ветки базы).

### Render.com (Blueprint)

В проекте есть готовый [`render.yaml`](render.yaml) — он поднимает веб-сервис (gunicorn + WhiteNoise) и базу PostgreSQL одним кликом.

1. Залей репозиторий на GitHub/GitLab.
2. В дашборде Render: **New → Blueprint** → выбери репозиторий. Render прочитает `render.yaml`.
3. Впиши единственную секретную переменную — **`GNEWS_API_KEY`** (в Blueprint она помечена `sync: false`, поэтому её нужно ввести вручную). Остальное подставится автоматически:
   - `SECRET_KEY` — Render сгенерирует сам;
   - `DATABASE_URL` — из созданной базы `apartnews-db`;
   - `DEBUG=False`, `GNEWS_LANG=ru`, `TIME_ZONE`, `PYTHON_VERSION` и т.д. — из `render.yaml`.
4. Нажми **Apply**. При деплое выполнится [`build.sh`](build.sh): `pip install` → `collectstatic` → `migrate`, затем стартует `gunicorn core.wsgi:application`.

Что уже настроено под Render в коде:
- **WhiteNoise** раздаёт собранную статику прямо из gunicorn — Nginx/CDN не нужны.
- `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` автоматически дополняются доменом из `RENDER_EXTERNAL_HOSTNAME` (иначе формы входа/комментариев ломались бы по CSRF на HTTPS).
- `SECURE_PROXY_SSL_HEADER` — учитывает, что TLS терминируется на прокси Render.

> **Про free-план Render:** веб-сервис засыпает после 15 минут простоя и просыпается при первом запросе (первый ответ будет медленным), а бесплатная база PostgreSQL живёт 30 дней. Для постоянной работы возьми платный план.

> **Про кеш GNews:** `LocMemCache` живёт в памяти одного процесса, поэтому при нескольких воркерах кеш у каждого свой. Для общего кеша между воркерами настрой Redis/Memcached в `CACHES`.

### Вручную / другой хостинг

1. Сгенерируй новый `SECRET_KEY`, выставь `DEBUG=False`, укажи домен в `ALLOWED_HOSTS`.
2. Переключись на PostgreSQL через `DATABASE_URL`.
3. Собери статику: `python manage.py collectstatic --no-input` и накати миграции `python manage.py migrate`.
4. Запускай через Gunicorn:

```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Структура проекта

```
news/
├── apps/news/                 # Новостное приложение
│   ├── services.py            # Клиент GNews + парсер полного текста (trafilatura)
│   ├── views.py               # Лента, детальная, избранное, регистрация
│   ├── models.py              # Избранное, комментарии, снимок новости
│   ├── forms.py               # Формы регистрации и комментариев
│   ├── urls.py
│   └── templatetags/          # Фильтр названий категорий
├── core/                      # Конфигурация проекта
│   ├── settings.py            # Настройки через django-environ (+ GNews)
│   └── urls.py                # Роутер: сайт, admin, REST API, swagger
├── templates/                 # Django-шаблоны (base, лента, статья, избранное, auth)
├── static/css/site.css        # Тема под ТАСС в зелёных тонах + адаптив
├── tests/
├── .env.example
├── render.yaml                # Blueprint для деплоя на Render (web + PostgreSQL)
├── build.sh                   # Build-скрипт Render: install → collectstatic → migrate
├── vercel_build.py            # Build-шаг Vercel: migrate + createcachetable
├── .vercelignore              # Что не загружать в Vercel
├── docker-compose.yml · Dockerfile
├── requirements.txt · requirements-dev.txt
├── manage.py
└── README.md
```

---

## Лицензия

[MIT](LICENSE)
