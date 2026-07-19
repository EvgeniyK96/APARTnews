from django.conf import settings
from django.db import models


class FavoriteCategory(models.Model):
    """Категория, добавленная пользователем в избранное.

    Новости из избранных категорий поднимаются в начало подборки.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_categories",
        verbose_name="Пользователь",
    )
    category = models.CharField("Категория", max_length=32)
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        verbose_name = "Избранная категория"
        verbose_name_plural = "Избранные категории"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category"],
                name="unique_user_category",
            )
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user} → {self.category}"


class ArticleSnapshot(models.Model):
    """Общие поля-снимка новости из GNews.

    Мы не храним ленту целиком (proxy), но сохраняем снимок той новости,
    к которой пользователь привязал избранное или комментарий, — чтобы её
    можно было показать даже если она уже пропала из выдачи GNews.
    """

    article_id = models.CharField("ID новости (GNews)", max_length=64, db_index=True)
    title = models.CharField("Заголовок", max_length=500)
    description = models.TextField("Описание", blank=True)
    url = models.URLField("Ссылка на источник", max_length=1000)
    image = models.URLField("Изображение", max_length=1000, blank=True)
    source_name = models.CharField("Источник", max_length=200, blank=True)
    category = models.CharField("Категория", max_length=32, blank=True)
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True)

    class Meta:
        abstract = True

    def as_article(self):
        """Представить снимок в том же виде, что и статью из GNews."""
        return {
            "id": self.article_id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "image": self.image,
            "category": self.category,
            "publishedAt": self.published_at.isoformat() if self.published_at else "",
            "source": {"name": self.source_name},
        }


class FavoriteArticle(ArticleSnapshot):
    """Новость, добавленная пользователем в избранное."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_articles",
        verbose_name="Пользователь",
    )
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        verbose_name = "Избранная новость"
        verbose_name_plural = "Избранные новости"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "article_id"],
                name="unique_user_article",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ★ {self.title[:50]}"


class Comment(ArticleSnapshot):
    """Комментарий пользователя к новости."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    text = models.TextField("Комментарий")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.text[:50]}"
