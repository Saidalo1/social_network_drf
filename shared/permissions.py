from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    """
    Allows access only to authenticated users who have verified their email address.
    """

    message = _("Access denied. Please verify your email first.")


    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_verified)
