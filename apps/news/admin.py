from django.contrib import admin

from .models import Comment, FavoriteArticle, FavoriteCategory


@admin.register(FavoriteCategory)
class FavoriteCategoryAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("user__username",)


@admin.register(FavoriteArticle)
class FavoriteArticleAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "category", "source_name", "created_at")
    list_filter = ("category",)
    search_fields = ("user__username", "title")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "text", "created_at")
    search_fields = ("user__username", "title", "text")
