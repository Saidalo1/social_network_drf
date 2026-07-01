"""Users profile updates view."""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.serializers import UserResponseSerializer, UserUpdateSerializer


class UserUpdateView(UpdateAPIView):
    """
    Update authenticated user profile information.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(
        request=UserUpdateSerializer,
        responses={status.HTTP_200_OK: UserResponseSerializer, status.HTTP_400_BAD_REQUEST: None, status.HTTP_401_UNAUTHORIZED: None},
        summary="Update current user profile info",
        description="Updates the username and/or full name of the logged in user.",
    )
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Apply updates and validate uniqueness
        username = serializer.validated_data.get("username")
        if username and username != instance.username:
            from app.models import User

            if User.objects.filter(username=username).exists():
                return Response({"username": [_("Username is already taken.")]}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        response_serializer = UserResponseSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

