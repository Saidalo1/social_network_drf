"""Shared project utility helper functions."""

import sys

from rest_framework_simplejwt.tokens import RefreshToken


def log_mock_email(username: str, token_str: str) -> None:
    """
    Mock prints a verification email link to stdout for development.
    """
    sys.stdout.write(
        f"\n[DEV MOCK EMAIL] Verification link for user {username}: "
        f"http://localhost:8000/auth/verify-email?token={token_str}\n\n"
    )
    sys.stdout.flush()


def get_tokens_for_user(user) -> dict:
    """Helper generating standard access and refresh JWT pair."""
    refresh = RefreshToken.for_user(user)
    return {"access_token": str(refresh.access_token), "refresh_token": str(refresh)}

