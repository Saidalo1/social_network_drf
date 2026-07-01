"""Social service logic layer (Posts, Comments, Likes, Feed)."""

import uuid
from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q as models_q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from app.models import Comment, Like, Post, User


class SocialService:
    """
    Service executing Social domain business rules (Posts, Comments, Likes, Feed).
    """

    @staticmethod
    def create_post(author: User, data: dict) -> Post:
        """
        Creates and returns a new post.
        """
        post = Post.objects.create(author=author, title=data.get("title"), content=data.get("content"))
        return post

    @staticmethod
    def get_post_by_id(post_id: uuid.UUID) -> Post:
        """
        Retrieves a single post by ID.
        """
        return get_object_or_404(Post, pk=post_id)

    @staticmethod
    def update_post(user: User, post_id: uuid.UUID, data: dict) -> Post:
        """
        Updates an existing post checking author permissions.
        """
        post = SocialService.get_post_by_id(post_id)
        if post.author_id != user.id:
            raise PermissionDenied(_("You do not have permission to modify this post."))

        for field in ("title", "content"):
            if data.get(field) is not None:
                setattr(post, field, data[field])

        post.save()
        return post

    @staticmethod
    def delete_post(user: User, post_id: uuid.UUID) -> None:
        """
        Deletes a post checking author permissions.
        """
        post = SocialService.get_post_by_id(post_id)
        if post.author_id != user.id:
            raise PermissionDenied(_("You do not have permission to delete this post."))
        post.delete()

    @staticmethod
    def create_comment(author: User, post_id: uuid.UUID, data: dict) -> Comment:
        """
        Adds a comment to an existing post.
        """
        post = SocialService.get_post_by_id(post_id)
        comment = Comment.objects.create(post=post, author=author, content=data.get("content"))
        return comment

    @staticmethod
    def delete_comment(user: User, post_id: uuid.UUID, comment_id: uuid.UUID) -> None:
        """
        Deletes a comment checking author permissions.
        """
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.post_id != post_id:
            raise ValidationError(_("Comment does not belong to the specified post."))

        if comment.author_id != user.id:
            raise PermissionDenied(_("You do not have permission to delete this comment."))

        comment.delete()

    @staticmethod
    def add_like(user: User, post_id: uuid.UUID) -> Like:
        """
        Likes a post checking self-liking and duplicate like rules.
        """
        post = SocialService.get_post_by_id(post_id)

        # 1. User cannot like their own post
        if post.author_id == user.id:
            raise ValidationError(_("You cannot like your own post."))

        # 2. Check duplicate like
        if Like.objects.filter(user=user, post=post).exists():
            raise ValidationError(_("You have already liked this post."))

        like = Like.objects.create(user=user, post=post)
        return like

    @staticmethod
    def remove_like(user: User, post_id: uuid.UUID) -> None:
        """
        Removes a previously placed like.
        """
        post = SocialService.get_post_by_id(post_id)
        try:
            like = Like.objects.get(user=user, post=post)
        except Like.DoesNotExist:
            raise ValidationError(_("Like not found.")) from None
        like.delete()

    @staticmethod
    def get_feed(
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieves feed posts, groups them by author username, and returns grouped structures.
        """
        # Prefetch author and likes to prevent N+1 query issue
        queryset = Post.objects.select_related("author").prefetch_related("likes")

        if search:
            queryset = queryset.filter(models_q(title__icontains=search) | models_q(content__icontains=search))
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # Apply offset and limit pagination
        posts = queryset.order_by("-created_at")[offset : offset + limit]

        # Group posts by author username preserving the chronological order
        grouped = []
        author_map = {}

        for post in posts:
            username = post.author.username
            feed_post = {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "likes": [like.user_id for like in post.likes.all()],
            }

            if username in author_map:
                idx = author_map[username]
                grouped[idx]["posts"].append(feed_post)
            else:
                grouped.append({"username": username, "posts": [feed_post]})
                author_map[username] = len(grouped) - 1

        return grouped

