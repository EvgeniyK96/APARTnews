from django.urls import path

from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("article/<str:article_id>/", views.article_detail, name="article_detail"),
    path("favorites/", views.favorites, name="favorites"),
    path(
        "favorites/category/toggle/",
        views.toggle_favorite_category,
        name="toggle_favorite_category",
    ),
    path(
        "favorites/article/toggle/",
        views.toggle_favorite_article,
        name="toggle_favorite_article",
    ),
    path("register/", views.register, name="register"),
]
