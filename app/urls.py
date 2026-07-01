from django.urls import path

from app.views import (
    CommentCreateView,
    CommentDeleteView,
    FeedView,
    LikeUnlikeView,
    LoginView,
    MeView,
    PostDetailUpdateDeleteView,
    PostsListCreateView,
    SignUpView,
    UserUpdateView,
    VerifyEmailView,
)


urlpatterns = [
    # Auth endpoints
    path("auth/register", SignUpView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/verify-email", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    # Users endpoints
    path("users/me", UserUpdateView.as_view(), name="users-me"),
    # Posts endpoints
    path("posts", PostsListCreateView.as_view(), name="posts-list-create"),
    path("posts/<uuid:id>", PostDetailUpdateDeleteView.as_view(), name="posts-detail-update-delete"),
    # Comments endpoints
    path("posts/<uuid:id>/comments", CommentCreateView.as_view(), name="comments-create"),
    path("posts/<uuid:post_id>/comments/<uuid:comment_id>", CommentDeleteView.as_view(), name="comments-delete"),
    # Likes endpoints
    path("posts/<uuid:id>/like", LikeUnlikeView.as_view(), name="posts-like-unlike"),
    # Feed endpoints
    path("feed", FeedView.as_view(), name="feed"),
]
