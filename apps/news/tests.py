from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Comment, FavoriteArticle, FavoriteCategory


class AuthGatingTests(TestCase):
    """Аноним только читает; действия требуют авторизации."""

    def setUp(self):
        self.user = User.objects.create_user("bob", password="pass12345")

    def test_favorites_page_requires_login(self):
        resp = self.client.get(reverse("favorites"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)

    def test_anonymous_cannot_toggle_favorite_category(self):
        resp = self.client.post(
            reverse("toggle_favorite_category"), {"category": "technology"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(FavoriteCategory.objects.count(), 0)

    def test_authenticated_can_favorite_category(self):
        self.client.force_login(self.user)
        self.client.post(reverse("toggle_favorite_category"), {"category": "technology"})
        self.assertTrue(
            FavoriteCategory.objects.filter(user=self.user, category="technology").exists()
        )

    def test_favorite_category_toggles_off(self):
        self.client.force_login(self.user)
        url = reverse("toggle_favorite_category")
        self.client.post(url, {"category": "science"})
        self.client.post(url, {"category": "science"})
        self.assertEqual(FavoriteCategory.objects.count(), 0)


class SnapshotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("kate", password="pass12345")

    def test_comment_keeps_article_snapshot(self):
        comment = Comment.objects.create(
            user=self.user,
            article_id="abc123",
            title="Test headline",
            url="https://example.com/a",
            text="nice",
        )
        self.assertEqual(comment.as_article()["title"], "Test headline")

    def test_favorite_article_unique_per_user(self):
        FavoriteArticle.objects.create(
            user=self.user, article_id="x1", title="t", url="https://e.io/x"
        )
        with self.assertRaises(IntegrityError):
            FavoriteArticle.objects.create(
                user=self.user, article_id="x1", title="t", url="https://e.io/x"
            )
