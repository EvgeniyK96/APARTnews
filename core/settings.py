from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    LANGUAGE_CODE=(str, "ru"),
    TIME_ZONE=(str, "Asia/Almaty"),
    GNEWS_API_KEY=(str, ""),
    GNEWS_CACHE_TTL=(int, 1800),
    GNEWS_LANG=(str, "ru"),
)

environ.Env.read_env(BASE_DIR / ".env")
# Vercel выставляет VERCEL=1 и при сборке, и в рантайме функции.
ON_VERCEL = bool(env("VERCEL", default=""))

SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ------------------------------------------------------------
# Деплой на Render (https://render.com)
# Render передаёт публичный домен в RENDER_EXTERNAL_HOSTNAME.
# ------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", default=[])
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    # Нужно, чтобы формы (вход, комментарии, избранное) проходили CSRF по HTTPS.
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# ------------------------------------------------------------
# Деплой на Vercel (https://vercel.com)
# VERCEL_URL — домен конкретного деплоя (в т.ч. preview),
# VERCEL_BRANCH_URL — домен ветки, VERCEL_PROJECT_PRODUCTION_URL — прод-домен.
# Свои домены добавляй через ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS.
# ------------------------------------------------------------
for _var in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    _host = env(_var, default="")
    if _host and _host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host)
        CSRF_TRUSTED_ORIGINS.append(f"https://{_host}")

# Render и Vercel терминируют TLS на своём прокси и проксируют запрос по HTTP.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "drf_yasg",
    "apps.news",
    # LOCAL_APPS_MARKER — не удаляй эту строку, она используется create_app.py
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / env("STATIC_ROOT", default="staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise раздаёт собранную статику прямо из gunicorn (без Nginx/CDN),
# со сжатием и хешированием имён файлов (см. core/storage.py).
# На Vercel статику раздаёт их CDN, поэтому там берём штатное хранилище
# без хеширования — его Vercel официально поддерживает.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage" if ON_VERCEL else "core.storage.StaticStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / env("MEDIA_ROOT", default="media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
}

DJOSER = {
    "SERIALIZERS": {},
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        }
    },
    "USE_SESSION_AUTH": False,
}

# ------------------------------------------------------------
# Server-rendered сайт: сессионная аутентификация
# ------------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "feed"
LOGOUT_REDIRECT_URL = "feed"

# Кэш для ответов GNews (proxy с коротким TTL, чтобы не упираться в лимиты).
# Локально — память процесса. На Vercel память живёт только в одном инстансе
# функции и теряется при холодном старте, поэтому там по умолчанию кэш в БД
# (таблицу создаёт `manage.py createcachetable` в vercel_build.py).
# Переопределяется через CACHE_URL, например redis://... или dbcache://table.
CACHES = {
    "default": env.cache(
        "CACHE_URL",
        default="dbcache://django_cache" if ON_VERCEL else "locmemcache://gnews-cache",
    )
}

# ------------------------------------------------------------
# GNews API
# ------------------------------------------------------------
GNEWS_API_KEY = env("GNEWS_API_KEY")
GNEWS_CACHE_TTL = env("GNEWS_CACHE_TTL")
GNEWS_LANG = env("GNEWS_LANG")
GNEWS_CATEGORIES = [
    "general",
    "world",
    "nation",
    "business",
    "technology",
    "entertainment",
    "sports",
    "science",
    "health",
]
