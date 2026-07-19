"""Клиент GNews (https://gnews.io).

Работаем в режиме proxy: каждая подборка запрашивается у GNews напрямую,
локально ничего не храним, кроме короткого кэша (LocMemCache) — чтобы не
упираться в лимиты бесплатного плана. Дополнительно кэшируем каждую
статью по её id, чтобы страница деталей могла показать новость без
отдельного запроса (у GNews нет endpoint'а «получить статью по id»).
"""

import logging

import requests
import trafilatura
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

BASE_URL = "https://gnews.io/api/v4"
ARTICLE_CACHE_TTL = 60 * 60 * 12  # 12 часов — снимок для страницы деталей
FULLTEXT_CACHE_TTL = 60 * 60 * 24  # сутки — извлечённый текст статьи

# Человекочитаемые названия категорий
CATEGORY_LABELS = {
    "general": "Главное",
    "world": "В мире",
    "nation": "Страна",
    "business": "Бизнес",
    "technology": "Технологии",
    "entertainment": "Развлечения",
    "sports": "Спорт",
    "science": "Наука",
    "health": "Здоровье",
}


def category_label(slug: str) -> str:
    return CATEGORY_LABELS.get(slug, slug.title())


class GNewsError(Exception):
    """Ошибка обращения к GNews."""


def _request(path: str, params: dict) -> dict:
    """Выполнить запрос к GNews с кэшированием ответа."""
    if not settings.GNEWS_API_KEY:
        raise GNewsError("GNEWS_API_KEY не задан в настройках.")

    query = {k: v for k, v in params.items() if v not in (None, "")}
    query["apikey"] = settings.GNEWS_API_KEY
    query.setdefault("lang", settings.GNEWS_LANG)

    cache_key = "gnews:" + path + ":" + ":".join(
        f"{k}={v}" for k, v in sorted(query.items()) if k != "apikey"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{BASE_URL}/{path}"
    try:
        response = requests.get(url, params=query, timeout=10)
    except requests.RequestException as exc:
        logger.warning("GNews request failed: %s", exc)
        raise GNewsError("Не удалось связаться с сервисом новостей.") from exc

    if response.status_code != 200:
        logger.warning("GNews returned %s: %s", response.status_code, response.text[:300])
        raise GNewsError(f"Сервис новостей вернул ошибку ({response.status_code}).")

    data = response.json()
    cache.set(cache_key, data, settings.GNEWS_CACHE_TTL)
    return data


def _cache_articles(articles: list[dict], category: str = "") -> None:
    for article in articles:
        if category and not article.get("category"):
            article["category"] = category
        article_id = article.get("id")
        if article_id:
            cache.set(f"gnews:article:{article_id}", article, ARTICLE_CACHE_TTL)


def top_headlines(category: str = "general", max_results: int = 10) -> list[dict]:
    """Заголовки по категории."""
    data = _request(
        "top-headlines",
        {"category": category, "max": max_results},
    )
    articles = data.get("articles", [])
    _cache_articles(articles, category=category)
    return articles


def search(query: str, max_results: int = 10) -> list[dict]:
    """Поиск новостей по запросу."""
    data = _request("search", {"q": query, "max": max_results})
    articles = data.get("articles", [])
    _cache_articles(articles)
    return articles


def get_article(article_id: str) -> dict | None:
    """Достать одну статью из кэша (наполняется при просмотре подборок)."""
    return cache.get(f"gnews:article:{article_id}")


def extract_fulltext(url: str) -> list[str] | None:
    """Скачать страницу-источник и вытащить полный текст статьи.

    У GNews в ответе только короткий обрезанный `content`, поэтому, чтобы
    показать новость целиком без перехода на сайт-источник, парсим саму
    страницу через trafilatura. Результат (список абзацев) кэшируем на сутки,
    чтобы не дёргать источник при каждом открытии.
    """
    if not url:
        return None

    cache_key = f"gnews:fulltext:{url}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached or None

    text = None
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
            )
    except Exception as exc:  # noqa: BLE001 — парсер не должен ронять страницу
        logger.warning("Не удалось разобрать статью %s: %s", url, exc)

    paragraphs: list[str] = []
    if text:
        for line in text.splitlines():
            line = line.strip()
            if len(line) > 1:
                paragraphs.append(line)

    cache.set(cache_key, paragraphs, FULLTEXT_CACHE_TTL)
    return paragraphs or None
