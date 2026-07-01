"""Django Database Models for Social Network Application."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    EmailField,
    ForeignKey,
    Index,
    OneToOneField,
    TextField,
    UniqueConstraint,
    UUIDField,
)
from simple_history.models import HistoricalRecords

from shared.constants import UserRole
from shared.django.models import BaseModel, TimeBaseModel


class User(AbstractUser):
    """
    Custom user model inheriting from Django AbstractUser.

    Email and username are unique constraints.
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = EmailField(unique=True, max_length=255)
    full_name = CharField(max_length=100, default="", blank=True)
    is_verified = BooleanField(default=False)
    role = CharField(max_length=10, choices=UserRole.choices, default=UserRole.USER)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    # Use email for login or username, override default email behavior
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


def generate_token_string() -> str:
    """Helper generating string uuid verification tokens."""
    return str(uuid.uuid4())


class VerificationToken(TimeBaseModel):
    """
    Registration verification token mapped to a User.

    Expires after 24 hours.
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField(User, on_delete=CASCADE, related_name="verification_token")
    token = CharField(max_length=255, unique=True, default=generate_token_string)
    expires_at = DateTimeField()

    class Meta:
        db_table = "verification_tokens"

    def __str__(self) -> str:
        return f"Token for User={self.user.username}"


class Post(BaseModel):
    """
    Post publication database model containing title and content.
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = ForeignKey(User, on_delete=CASCADE, related_name="posts", db_index=True)
    title = CharField(max_length=255)
    content = TextField()

    history = HistoricalRecords()

    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]
        # Speed up feed descending sorting queries
        indexes = [
            Index(fields=["-created_at"], name="idx_posts_created_at_desc"),
        ]

    def __str__(self) -> str:
        return f"Post '{self.title[:20]}' by {self.author.username}"


class Comment(BaseModel):
    """
    Comment database model linking a comment to a specific Post.
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = ForeignKey(Post, on_delete=CASCADE, related_name="comments", db_index=True)
    author = ForeignKey(User, on_delete=CASCADE, related_name="comments", db_index=True)
    content = TextField()

    history = HistoricalRecords()

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comment by {self.author.username} on Post={self.post_id}"


class Like(TimeBaseModel):
    """
    Like database model representing a like placed on a Post.
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = ForeignKey(User, on_delete=CASCADE, related_name="likes")
    post = ForeignKey(Post, on_delete=CASCADE, related_name="likes", db_index=True)

    class Meta:
        db_table = "likes"
        constraints = [UniqueConstraint(fields=["user", "post"], name="uq_user_post_like")]

    def __str__(self) -> str:
        return f"Like by {self.user.username} on Post={self.post_id}"
