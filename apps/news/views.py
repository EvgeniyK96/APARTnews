from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from . import services
from .forms import CommentForm, RegisterForm
from .models import Comment, FavoriteArticle, FavoriteCategory


# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------
def _user_favorite_categories(user) -> list[str]:
    if not user.is_authenticated:
        return []
    return list(
        user.favorite_categories.order_by("created_at").values_list("category", flat=True)
    )


def _user_favorite_article_ids(user) -> set[str]:
    if not user.is_authenticated:
        return set()
    return set(user.favorite_articles.values_list("article_id", flat=True))


def _build_categories_nav(user, active: str = ""):
    """Список категорий для навигации с пометкой избранных."""
    favorites = set(_user_favorite_categories(user))
    nav = []
    for slug in services.settings.GNEWS_CATEGORIES:
        nav.append(
            {
                "slug": slug,
                "label": services.category_label(slug),
                "is_favorite": slug in favorites,
                "is_active": slug == active,
            }
        )
    return nav


def _annotate(articles, favorite_ids):
    """Пометить статьи флагом is_favorite для текущего пользователя."""
    result = []
    for article in articles:
        item = dict(article)
        item["is_favorite"] = article.get("id") in favorite_ids
        item["source_name"] = (article.get("source") or {}).get("name", "")
        result.append(item)
    return result


def _prioritized_feed(favorite_categories: list[str], max_per_category: int = 10):
    """Подборка, где новости из избранных категорий идут первыми."""
    articles = []
    seen = set()
    ordered = favorite_categories + [
        c for c in services.settings.GNEWS_CATEGORIES if c not in favorite_categories
    ]
    for category in ordered:
        try:
            for article in services.top_headlines(category, max_results=max_per_category):
                article_id = article.get("id")
                if article_id and article_id not in seen:
                    seen.add(article_id)
                    articles.append(article)
        except services.GNewsError:
            continue
    return articles


# ------------------------------------------------------------
# Лента
# ------------------------------------------------------------
def feed(request):
    active_category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()
    favorite_categories = _user_favorite_categories(request.user)
    error = None
    articles = []
    heading = "Лента новостей"
    subheading = ""

    try:
        if query:
            articles = services.search(query, max_results=20)
            heading = f"Поиск: «{query}»"
        elif active_category:
            articles = services.top_headlines(active_category, max_results=20)
            heading = services.category_label(active_category)
        elif favorite_categories:
            articles = _prioritized_feed(favorite_categories)
            heading = "Ваша лента"
            subheading = "Сначала — новости из избранных категорий"
        else:
            articles = services.top_headlines("general", max_results=20)
            heading = "Главное"
    except services.GNewsError as exc:
        error = str(exc)

    context = {
        "articles": _annotate(articles, _user_favorite_article_ids(request.user)),
        "categories": _build_categories_nav(request.user, active_category),
        "active_category": active_category,
        "query": query,
        "heading": heading,
        "subheading": subheading,
        "error": error,
        "favorite_categories": favorite_categories,
    }
    return render(request, "news/feed.html", context)


# ------------------------------------------------------------
# Детальная страница + комментарии
# ------------------------------------------------------------
def _find_article(article_id: str):
    """Найти статью: сначала кэш GNews, затем снимки в БД."""
    article = services.get_article(article_id)
    if article:
        return article
    snapshot = (
        FavoriteArticle.objects.filter(article_id=article_id).first()
        or Comment.objects.filter(article_id=article_id).first()
    )
    if snapshot:
        return snapshot.as_article()
    return None


def _fill_snapshot(obj, article: dict):
    """Заполнить поля-снимка из словаря статьи GNews."""
    obj.article_id = article.get("id", "")
    obj.title = (article.get("title") or "")[:500]
    obj.description = article.get("description") or ""
    obj.url = article.get("url") or ""
    obj.image = article.get("image") or ""
    obj.source_name = (article.get("source") or {}).get("name", "")
    obj.category = article.get("category", "")
    published = article.get("publishedAt")
    obj.published_at = parse_datetime(published) if published else None


def article_detail(request, article_id):
    article = _find_article(article_id)
    if article is None:
        messages.error(
            request,
            "Новость недоступна — она могла пропасть из выдачи GNews. "
            "Откройте её из свежей ленты.",
        )
        return redirect("feed")

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            _fill_snapshot(comment, article)
            comment.save()
            messages.success(request, "Комментарий добавлен.")
            return redirect("article_detail", article_id=article_id)
    else:
        form = CommentForm()

    comments = Comment.objects.filter(article_id=article_id).select_related("user")
    article = _annotate([article], _user_favorite_article_ids(request.user))[0]

    # Полный текст статьи, извлечённый со страницы-источника,
    # чтобы читать новость прямо здесь, без перехода на сайт.
    paragraphs = services.extract_fulltext(article.get("url", "")) or []
    title = (article.get("title") or "").strip()
    body_paragraphs = [p for p in paragraphs if p != title]

    context = {
        "article": article,
        "body_paragraphs": body_paragraphs,
        "comments": comments,
        "form": form,
        "categories": _build_categories_nav(request.user),
    }
    return render(request, "news/article_detail.html", context)


# ------------------------------------------------------------
# Избранное
# ------------------------------------------------------------
@login_required
@require_POST
def toggle_favorite_category(request):
    category = request.POST.get("category", "").strip()
    next_url = request.POST.get("next") or "feed"
    if category not in services.settings.GNEWS_CATEGORIES:
        messages.error(request, "Неизвестная категория.")
        return redirect(next_url)

    obj, created = FavoriteCategory.objects.get_or_create(
        user=request.user, category=category
    )
    if not created:
        obj.delete()
        messages.info(
            request, f"Категория «{services.category_label(category)}» убрана из избранного."
        )
    else:
        messages.success(
            request, f"Категория «{services.category_label(category)}» в избранном."
        )
    return redirect(next_url)


@login_required
@require_POST
def toggle_favorite_article(request):
    article_id = request.POST.get("article_id", "").strip()
    next_url = request.POST.get("next") or "feed"
    existing = FavoriteArticle.objects.filter(user=request.user, article_id=article_id).first()
    if existing:
        existing.delete()
        messages.info(request, "Новость убрана из избранного.")
        return redirect(next_url)

    article = _find_article(article_id)
    if article is None:
        messages.error(request, "Не удалось сохранить новость в избранное.")
        return redirect(next_url)

    favorite = FavoriteArticle(user=request.user)
    _fill_snapshot(favorite, article)
    favorite.save()
    messages.success(request, "Новость добавлена в избранное.")
    return redirect(next_url)


@login_required
def favorites(request):
    context = {
        "favorite_articles": _annotate(
            [fa.as_article() for fa in request.user.favorite_articles.all()],
            _user_favorite_article_ids(request.user),
        ),
        "favorite_categories": [
            {"slug": slug, "label": services.category_label(slug)}
            for slug in _user_favorite_categories(request.user)
        ],
        "categories": _build_categories_nav(request.user),
    }
    return render(request, "news/favorites.html", context)


# ------------------------------------------------------------
# Регистрация
# ------------------------------------------------------------
def register(request):
    if request.user.is_authenticated:
        return redirect("feed")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Добро пожаловать! Аккаунт создан.")
            return redirect("feed")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
