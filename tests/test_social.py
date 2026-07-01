"""Integration tests for social endpoints (Posts, Comments, Likes, Feed)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import User

pytestmark = pytest.mark.django_db


def _create_verified_user(email: str, username: str) -> dict:
    """Helper to create a verified user and return their client credentials."""
    user = User.objects.create_user(username=username, email=email, password="securepassword123", is_verified=True)
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return {"user": user, "client": client}


def _create_unverified_user(username: str) -> dict:
    """Helper to create an unverified user and return their client credentials."""
    user = User.objects.create_user(
        username=username, email=f"{username}@gmail.com", password="securepassword123", is_verified=False
    )
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return {"user": user, "client": client}


def test_access_rules_for_unverified_users():
    """
    Verifies that unverified users CANNOT write posts/comments, but CAN like posts.
    """
    verified = _create_verified_user("verified@gmail.com", "verified_user")
    unverified = _create_unverified_user("unverified_user")

    # 1. Verified user creates a post
    post_payload = {"title": "Verified Post Title", "content": "Verified post content description"}
    post_res = verified["client"].post(reverse("posts-list-create"), data=post_payload, format="json")
    assert post_res.status_code == status.HTTP_201_CREATED
    post_id = post_res.json()["id"]

    # 2. Unverified user attempts to create a post (should be 403 Forbidden)
    bad_post_res = unverified["client"].post(
        reverse("posts-list-create"), data={"title": "Bad Title", "content": "Bad Content"}, format="json"
    )
    assert bad_post_res.status_code == status.HTTP_403_FORBIDDEN
    assert "verify your email" in bad_post_res.json()["detail"].lower()

    # 3. Unverified user attempts to create a comment (should be 403 Forbidden)
    bad_comment_res = unverified["client"].post(
        reverse("comments-create", kwargs={"id": post_id}), data={"content": "Unverified comment"}, format="json"
    )
    assert bad_comment_res.status_code == status.HTTP_403_FORBIDDEN

    # 4. Unverified user likes the post (should succeed!)
    like_res = unverified["client"].post(reverse("posts-like-unlike", kwargs={"id": post_id}))
    assert like_res.status_code == status.HTTP_201_CREATED
    assert "liked successfully" in like_res.json()["detail"]


def test_post_crud_and_permissions():
    """
    Verifies post creation, modification, deletion, and author enforcement check.
    """
    user_a = _create_verified_user("usera@gmail.com", "user_a")
    user_b = _create_verified_user("userb@gmail.com", "user_b")

    # User A creates post
    post_payload = {"title": "Original Post Title", "content": "Original content of post A"}
    res = user_a["client"].post(reverse("posts-list-create"), data=post_payload, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    post_id = res.json()["id"]

    # User B attempts to edit A's post (should fail with 403)
    edit_payload = {"title": "Hacked Title", "content": "Hacked Content"}
    res = user_b["client"].patch(
        reverse("posts-detail-update-delete", kwargs={"id": post_id}), data=edit_payload, format="json"
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # User B attempts to delete A's post (should fail with 403)
    res = user_b["client"].delete(reverse("posts-detail-update-delete", kwargs={"id": post_id}))
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # User A edits own post
    res = user_a["client"].patch(
        reverse("posts-detail-update-delete", kwargs={"id": post_id}), data={"title": "Updated Title"}, format="json"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["title"] == "Updated Title"

    # User A deletes own post
    res = user_a["client"].delete(reverse("posts-detail-update-delete", kwargs={"id": post_id}))
    assert res.status_code == status.HTTP_204_NO_CONTENT


def test_comments_flow():
    """
    Verifies comment creation and author-only deletion rules.
    """
    user_a = _create_verified_user("comment_usera@gmail.com", "c_user_a")
    user_b = _create_verified_user("comment_userb@gmail.com", "c_user_b")

    # Create post
    post_res = user_a["client"].post(
        reverse("posts-list-create"), data={"title": "Comment Post", "content": "Content"}, format="json"
    )
    post_id = post_res.json()["id"]

    # User B adds a comment
    comment_payload = {"content": "This is a comment by B"}
    comment_res = user_b["client"].post(
        reverse("comments-create", kwargs={"id": post_id}), data=comment_payload, format="json"
    )
    assert comment_res.status_code == status.HTTP_201_CREATED
    comment_id = comment_res.json()["id"]

    # User A attempts to delete B's comment (should fail 403)
    res = user_a["client"].delete(reverse("comments-delete", kwargs={"post_id": post_id, "comment_id": comment_id}))
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # User B deletes own comment
    res = user_b["client"].delete(reverse("comments-delete", kwargs={"post_id": post_id, "comment_id": comment_id}))
    assert res.status_code == status.HTTP_204_NO_CONTENT


def test_likes_constraints():
    """
    Verifies self-liking restriction and double-liking DB uniqueness constraint.
    """
    user_a = _create_verified_user("likes_a@gmail.com", "likes_a")
    user_b = _create_verified_user("likes_b@gmail.com", "likes_b")

    # User A creates post
    post_res = user_a["client"].post(
        reverse("posts-list-create"), data={"title": "Likes post", "content": "content"}, format="json"
    )
    post_id = post_res.json()["id"]

    # 1. User A likes own post (should fail 400)
    res = user_a["client"].post(reverse("posts-like-unlike", kwargs={"id": post_id}))
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "own post" in res.json()["detail"].lower()

    # 2. User B likes A's post (should succeed)
    res = user_b["client"].post(reverse("posts-like-unlike", kwargs={"id": post_id}))
    assert res.status_code == status.HTTP_201_CREATED

    # 3. User B likes A's post again (should fail 400)
    res = user_b["client"].post(reverse("posts-like-unlike", kwargs={"id": post_id}))
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already liked" in res.json()["detail"].lower()

    # 4. User B unlikes post (should succeed)
    res = user_b["client"].delete(reverse("posts-like-unlike", kwargs={"id": post_id}))
    assert res.status_code == status.HTTP_204_NO_CONTENT


def test_feed_filters_pagination_and_format():
    """
    Verifies /feed grouping structure, search querying, date filters, and page sizes.
    """
    user_a = _create_verified_user("feeda@gmail.com", "feed_a")
    user_b = _create_verified_user("feedb@gmail.com", "feed_b")

    # Create posts
    post_a1_res = user_a["client"].post(
        reverse("posts-list-create"), data={"title": "Apple post", "content": "Eating apples is healthy"}, format="json"
    )
    user_a["client"].post(
        reverse("posts-list-create"),
        data={"title": "Banana post", "content": "Sweet yellow banana fruit"},
        format="json",
    )
    user_b["client"].post(
        reverse("posts-list-create"), data={"title": "Orange post", "content": "Orange citrus juice"}, format="json"
    )

    post_a1_id = post_a1_res.json()["id"]

    # User B likes post_a1
    user_b["client"].post(reverse("posts-like-unlike", kwargs={"id": post_a1_id}))

    client = APIClient()

    # 1. Check default feed format
    res = client.get(reverse("feed"))
    assert res.status_code == status.HTTP_200_OK
    feed_data = res.json()

    # Structure validation: must be list of author grouped posts
    assert isinstance(feed_data, list)
    assert len(feed_data) >= 2

    # Check details of user_a group
    user_a_group = next(g for g in feed_data if g["username"] == "feed_a")
    assert len(user_a_group["posts"]) == 2

    # Verify post likes contains User B's UUID
    post_a1_feed = next(p for p in user_a_group["posts"] if p["id"] == post_a1_id)
    assert str(user_b["user"].id) in post_a1_feed["likes"]

    # 2. Check search keyword filter (should match "Citrus" or "Orange")
    res = client.get(reverse("feed"), data={"search": "citrus"})
    feed_data = res.json()
    assert len(feed_data) == 1
    assert feed_data[0]["username"] == "feed_b"
    assert feed_data[0]["posts"][0]["title"] == "Orange post"

    # 3. Check Date filters
    from django.utils import timezone

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # date_from=yesterday and date_to=tomorrow should return all posts
    res = client.get(reverse("feed"), data={"date_from": yesterday.isoformat(), "date_to": tomorrow.isoformat()})
    assert len(res.json()) >= 2

    # date_to=yesterday should return no posts
    res = client.get(reverse("feed"), data={"date_to": yesterday.isoformat()})
    assert len(res.json()) == 0

    # 4. Check pagination (limit 1 post should return exactly 1 author group with 1 post)
    res = client.get(reverse("feed"), data={"limit": 1})
    feed_data = res.json()
    assert len(feed_data) == 1
    assert len(feed_data[0]["posts"]) == 1
