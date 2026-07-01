"""Users profile views."""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.serializers import UserResponseSerializer, UserUpdateSerializer


class UserUpdateView(RetrieveUpdateAPIView):
    """
    Get or update authenticated user profile information.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(
        responses={status.HTTP_200_OK: UserResponseSerializer, status.HTTP_401_UNAUTHORIZED: None},
        summary="Get current user profile info",
        description="Retrieves the profile data of the logged in user.",
        tags=["Users"],
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @extend_schema(
        request=UserUpdateSerializer,
        responses={
            status.HTTP_200_OK: UserResponseSerializer,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_401_UNAUTHORIZED: None,
        },
        summary="Update current user profile info",
        description="Updates the username and/or full name of the logged in user.",
        tags=["Users"],
    )
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        request=UserUpdateSerializer,
        responses={
            status.HTTP_200_OK: UserResponseSerializer,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_401_UNAUTHORIZED: None,
        },
        summary="Replace current user profile info",
        description="Replaces the username and/or full name of the logged in user.",
        tags=["Users"],
        exclude=True,  # Put is usually excluded or hidden if patch is preferred, but tags are present
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
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
