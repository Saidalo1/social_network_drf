from django.db import models


class UserRole(models.TextChoices):
    """
    User system permissions roles.
    """

    USER = "USER", "User"
    ADMIN = "ADMIN", "Admin"
