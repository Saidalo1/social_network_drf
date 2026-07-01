"""Django REST Framework Serializers."""

import re

from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import (
    CharField,
    EmailField,
    ListField,
    ModelSerializer,
    Serializer,
    UUIDField,
    ValidationError,
)

from app.models import Comment, Post, User


class SignUpSerializer(Serializer):
    """
    Serializer validating registration payload inputs.
    """

    username = CharField(max_length=32)
    email = EmailField(max_length=255)
    password = CharField(max_length=128, write_only=True)
    full_name = CharField(max_length=100, required=False, default="", allow_blank=True)

    def validate_username(self, value: str) -> str:
        # Enforce regex constraints: username must be alphanumeric + underscores, 3 to 32 chars
        if not re.match(r"^[a-zA-Z0-9_]{3,32}$", value):
            raise ValidationError(
                _("Username must contain only letters, numbers, underscores and be 3 to 32 characters long.")
            )
        return value

    def validate_password(self, value: str) -> str:
        # Password must be at least 8 characters long
        if len(value) < 8:
            raise ValidationError(_("Password must be at least 8 characters long."))
        return value


class LoginSerializer(Serializer):
    """
    Serializer validating authentication credentials.
    """

    username_or_email = CharField(max_length=255)
    password = CharField(max_length=128, write_only=True)


class TokenResponseSerializer(Serializer):
    """
    Serializer defining JWT tokens output schema representation.
    """

    access_token = CharField()
    refresh_token = CharField()


class UserResponseSerializer(ModelSerializer):
    """
    Serializer defining User model output representation.
    """

    class Meta:
        model = User
        fields = ("id", "username", "email", "full_name", "role", "is_verified", "created_at")
        read_only_fields = fields


class UserUpdateSerializer(ModelSerializer):
    """
    Serializer validating profile update payload fields.
    """

    username = CharField(max_length=32, required=False)

    class Meta:
        model = User
        fields = ("username", "full_name")

    def validate_username(self, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,32}$", value):
            raise ValidationError(
                _("Username must contain only letters, numbers, underscores and be 3 to 32 characters long.")
            )
        return value


class PostCreateUpdateSerializer(ModelSerializer):
    """
    Serializer validating creation or updates of posts.
    """

    title = CharField(min_length=5, max_length=255)
    content = CharField(max_length=10000)

    class Meta:
        model = Post
        fields = ("title", "content")


class PostResponseSerializer(ModelSerializer):
    """
    Serializer defining basic post output representation.
    """

    author_id = UUIDField(source="author.id", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "author_id", "title", "content", "created_at", "updated_at")
        read_only_fields = fields


class CommentCreateSerializer(ModelSerializer):
    """
    Serializer validating comment creation.
    """

    content = CharField(max_length=2000)

    class Meta:
        model = Comment
        fields = ("content",)


class CommentResponseSerializer(ModelSerializer):
    """
    Serializer defining comment output representation.
    """

    author_id = UUIDField(source="author.id", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "post_id", "author_id", "content", "created_at")
        read_only_fields = fields


class PostDetailResponseSerializer(ModelSerializer):
    """
    Detailed serializer including eager loaded comments.
    """

    author_id = UUIDField(source="author.id", read_only=True)
    comments = CommentResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ("id", "author_id", "title", "content", "created_at", "updated_at", "comments")
        read_only_fields = fields


# ==========================================
# Spectacular Feed representation helper serializers
# ==========================================


class FeedPostSerializer(Serializer):
    id = UUIDField()
    title = CharField()
    content = CharField()
    likes = ListField(child=UUIDField())


class AuthorGroupResponseSerializer(Serializer):
    username = CharField()
    posts = FeedPostSerializer(many=True)
