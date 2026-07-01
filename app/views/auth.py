"""Authentication views definitions (Register, Login, Verification, and Me)."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.serializers import (
    LoginSerializer,
    SignUpSerializer,
    TokenResponseSerializer,
    UserResponseSerializer,
)
from app.services.users import UserService
from shared.utils import get_tokens_for_user



class SignUpView(APIView):
    """
    Register a new user account.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=SignUpSerializer,
        responses={status.HTTP_201_CREATED: UserResponseSerializer, status.HTTP_400_BAD_REQUEST: None},
        summary="Register a new user account",
        description="Creates a new unverified user, hashes password using Argon2, and schedules email token.",
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserService.create_user(serializer.validated_data)
            response_serializer = UserResponseSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Login view returning JWT tokens.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={status.HTTP_200_OK: TokenResponseSerializer, status.HTTP_400_BAD_REQUEST: None},
        summary="Authenticate credentials and generate JWT tokens",
        description="Validates username/email and password, returning JWT access and refresh tokens.",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username_or_email = serializer.validated_data["username_or_email"]
        password = serializer.validated_data["password"]

        try:
            user = UserService.authenticate_user(username_or_email, password)
            tokens = get_tokens_for_user(user)
            token_serializer = TokenResponseSerializer(tokens)
            return Response(token_serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"detail": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Verify user registration email address.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[OpenApiParameter("token", type=str, required=True, description="Verification token UUID")],
        responses={status.HTTP_200_OK: None, status.HTTP_400_BAD_REQUEST: None},
        summary="Confirm email verification token",
        description="Validates the confirmation token and updates is_verified = True.",
    )
    def get(self, request):
        token_str = request.query_params.get("token")
        if not token_str:
            return Response({"detail": _("Token query parameter is required.")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            UserService.verify_email_token(token_str)
            return Response(
                {"detail": _("Email verified successfully. You can now create posts and comments.")},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response({"detail": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    Retrieve authenticated user profile detail.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={status.HTTP_200_OK: UserResponseSerializer, status.HTTP_401_UNAUTHORIZED: None},
        summary="Retrieve current user details",
        description="Returns detailed profile information for the authenticated user.",
    )
    def get(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
