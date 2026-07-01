"""Integration tests for periodic database cleanup tasks (Celery)."""

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from app.models import Post, User
from app.tasks import cleanup_expired_posts, cleanup_unverified_users

pytestmark = pytest.mark.django_db


@override_settings(UNVERIFIED_USER_CLEANUP_HOURS=24)
def test_cleanup_unverified_users_task():
    """
    Verifies that unverified accounts older than 24h are deleted.
    """
    now = timezone.now()

    # 1. Old unverified user (should be deleted)
    old_unverified = User.objects.create_user(
        username="old_unverified", email="old_unverified@gmail.com", password="somepassword123", is_verified=False
    )
    # Update created_at using filter/update because Django auto_now_add is read-only at save()
    User.objects.filter(pk=old_unverified.pk).update(created_at=now - timedelta(hours=25))

    # 2. Recent unverified user (should NOT be deleted)
    recent_unverified = User.objects.create_user(
        username="recent_unverified", email="recent_unverified@gmail.com", password="somepassword123", is_verified=False
    )
    User.objects.filter(pk=recent_unverified.pk).update(created_at=now - timedelta(hours=2))

    # 3. Old verified user (should NOT be deleted)
    old_verified = User.objects.create_user(
        username="old_verified", email="old_verified@gmail.com", password="somepassword123", is_verified=True
    )
    User.objects.filter(pk=old_verified.pk).update(created_at=now - timedelta(hours=25))

    # Run the Celery task synchronously
    deleted_count = cleanup_unverified_users()
    assert deleted_count == 1

    # Verify results in the database
    # Old unverified should be gone
    assert not User.objects.filter(username="old_unverified").exists()

    # Recent unverified should remain
    assert User.objects.filter(username="recent_unverified").exists()

    # Old verified should remain
    assert User.objects.filter(username="old_verified").exists()


@override_settings(POST_TTL_DAYS=30)
def test_cleanup_expired_posts_task():
    """
    Verifies that posts older than 30 days are deleted.
    """
    now = timezone.now()

    # Create author
    author = User.objects.create_user(
        username="author_test", email="author@gmail.com", password="somepassword123", is_verified=True
    )

    # 1. Old post (should be deleted)
    old_post = Post.objects.create(author=author, title="Old Post", content="Old Content")
    Post.objects.filter(pk=old_post.pk).update(created_at=now - timedelta(days=31))

    # 2. Recent post (should NOT be deleted)
    recent_post = Post.objects.create(author=author, title="Recent Post", content="Recent Content")
    Post.objects.filter(pk=recent_post.pk).update(created_at=now - timedelta(days=5))

    # Run the Celery task synchronously
    deleted_count = cleanup_expired_posts()
    assert deleted_count == 1

    # Verify old post is gone
    assert not Post.objects.filter(title="Old Post").exists()

    # Verify recent post remains
    assert Post.objects.filter(title="Recent Post").exists()
