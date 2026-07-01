"""User service logic layer (Signup, Login, and Email Verification)."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _

from app.models import User, VerificationToken
from shared.utils import log_mock_email


class UserService:
    """
    Service executing User and Authentication domain business rules.
    """

    @staticmethod
    def create_user(data: dict) -> User:
        """
        Creates an unverified User, hashes password, and triggers mock email token.
        """
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name", "")

        # Enforce unique field checks before saving
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Email already exists in system."))
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("Username is already taken."))

        # Create user (uses password hasher configured in settings.py - Argon2)
        user = User.objects.create_user(
            username=username, email=email, password=password, full_name=full_name, is_verified=False
        )

        # Generate verification token expiring in 24 hours
        expiry = django_timezone.now() + timedelta(hours=24)
        token_obj = VerificationToken.objects.create(user=user, expires_at=expiry)

        # Log developer mock email containing verification token url
        log_mock_email(user.username, token_obj.token)

        return user

    @staticmethod
    def verify_email_token(token_str: str) -> User:
        """
        Validates email verification token. Sets is_verified = True.
        """
        try:
            token_obj = VerificationToken.objects.select_related("user").get(token=token_str)
        except VerificationToken.DoesNotExist:
            raise ValidationError(_("Invalid or expired verification token.")) from None

        # Check TTL expiration
        if token_obj.expires_at < django_timezone.now():
            raise ValidationError(_("Verification token has expired."))

        user = token_obj.user
        user.is_verified = True
        user.save()

        # Delete token once verified successfully
        token_obj.delete()

        return user

    @staticmethod
    def authenticate_user(username_or_email: str, password: str) -> User:
        """
        Verifies login credentials. Supports username or email authentication.
        """
        user = None
        # Support email address input
        if "@" in username_or_email:
            user = User.objects.filter(email=username_or_email).first()
        else:
            user = User.objects.filter(username=username_or_email).first()

        if not user:
            raise ValidationError(_("Invalid login credentials."))

        # Check hashed password matches
        if not user.check_password(password):
            raise ValidationError(_("Invalid login credentials."))

        return user
