"""Integration tests for authentication endpoints (registration, verification, login)."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from app.models import User

pytestmark = pytest.mark.django_db


def test_successful_auth_flow(client: APIClient):
    """
    Validates complete signup, token generation, email verification, and profile login.
    """
    signup_payload = {
        "email": "testuser@gmail.com",
        "username": "test_username",
        "full_name": "Test User Name",
        "password": "securepassword123",
    }

    # 1. Sign Up
    response = client.post(reverse("auth-register"), data=signup_payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    user_data = response.json()
    assert user_data["email"] == signup_payload["email"]
    assert user_data["username"] == signup_payload["username"]
    assert user_data["is_verified"] is False

    # Fetch token from database directly
    user = User.objects.get(email=signup_payload["email"])
    assert user.verification_token is not None
    token_str = user.verification_token.token

    # 2. Try accessing secure /me (should fail with 401 before logging in)
    response = client.get(reverse("auth-me"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Login (unverified users can login)
    login_payload = {"username_or_email": signup_payload["username"], "password": signup_payload["password"]}
    response = client.post(reverse("auth-login"), data=login_payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    tokens = response.json()
    assert "access_token" in tokens

    # Access secure /me (should succeed now but show is_verified=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    response = client.get(reverse("auth-me"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_verified"] is False

    # 3. Confirm email verification token
    response = client.get(f"{reverse('auth-verify-email')}?token={token_str}")
    assert response.status_code == status.HTTP_200_OK
    assert "verified successfully" in response.json()["detail"]

    # 4. Check status in DB is updated
    user.refresh_from_db()
    assert user.is_verified is True

    # 5. Access /me again (should show is_verified=True)
    response = client.get(reverse("auth-me"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_verified"] is True


def test_duplicate_registration_fails(client: APIClient):
    """
    Verifies unique email and username constraint checks.
    """
    signup_payload = {
        "email": "unique@gmail.com",
        "username": "unique_username",
        "full_name": "Unique Name",
        "password": "securepassword123",
    }

    # Register first time
    response = client.post(reverse("auth-register"), data=signup_payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Register with duplicate email
    duplicate_email = signup_payload.copy()
    duplicate_email["username"] = "different_username"
    response = client.post(reverse("auth-register"), data=duplicate_email, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email already exists" in response.json()["detail"].lower()

    # Register with duplicate username
    duplicate_username = signup_payload.copy()
    duplicate_username["email"] = "different_email@gmail.com"
    response = client.post(reverse("auth-register"), data=duplicate_username, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username is already taken" in response.json()["detail"].lower()


def test_login_validation(client: APIClient):
    """
    Verifies authentication with correct and incorrect credentials.
    """
    signup_payload = {
        "email": "login@gmail.com",
        "username": "login_user",
        "full_name": "Login User",
        "password": "password123",
    }
    client.post(reverse("auth-register"), data=signup_payload, format="json")

    # Login with correct username
    response = client.post(
        reverse("auth-login"), data={"username_or_email": "login_user", "password": "password123"}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK

    # Login with correct email
    response = client.post(
        reverse("auth-login"), data={"username_or_email": "login@gmail.com", "password": "password123"}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK

    # Login with incorrect password
    response = client.post(
        reverse("auth-login"), data={"username_or_email": "login_user", "password": "wrongpassword"}, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid" in response.json()["detail"].lower()
