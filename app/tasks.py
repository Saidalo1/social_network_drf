"""Celery tasks for periodic database cleanup."""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import connection
from django.utils import timezone

from app.models import Post, User

logger = logging.getLogger(__name__)


@shared_task
def cleanup_unverified_users() -> int:
    """
    Periodic task to delete unverified users older than the configured TTL limit.
    """
    logger.info("Starting unverified users cleanup...")
    cutoff = timezone.now() - timedelta(hours=settings.UNVERIFIED_USER_CLEANUP_HOURS)

    try:
        # Find unverified users created before cutoff
        unverified_users = User.objects.filter(is_verified=False, created_at__lt=cutoff)
        count = unverified_users.count()
        if count > 0:
            unverified_users.delete()
            logger.info(f"Cleaned up {count} unverified users successfully.")
        else:
            logger.info("No unverified users met cleanup conditions.")
        return count
    except Exception as e:
        logger.error(f"Error executing cleanup_unverified_users task: {e}")
        raise e
    finally:
        # Explicitly close DB connections to prevent celery pool connection exhaustion, but preserve test suite database transactions
        if not connection.in_atomic_block:
            connection.close()


@shared_task
def cleanup_expired_posts() -> int:
    """
    Periodic task to delete posts exceeding their TTL limit.
    """
    logger.info("Starting expired posts cleanup...")
    cutoff = timezone.now() - timedelta(days=settings.POST_TTL_DAYS)

    try:
        expired_posts = Post.objects.filter(created_at__lt=cutoff)
        count = expired_posts.count()
        if count > 0:
            expired_posts.delete()
            logger.info(f"Cleaned up {count} expired posts successfully.")
        else:
            logger.info("No expired posts met cleanup conditions.")
        return count
    except Exception as e:
        logger.error(f"Error executing cleanup_expired_posts task: {e}")
        raise e
    finally:
        # Explicitly close DB connections to prevent celery pool connection exhaustion, but preserve test suite database transactions
        if not connection.in_atomic_block:
            connection.close()
