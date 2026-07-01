"""Social module views (Posts, Comments, Likes, Feed)."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Post
from app.serializers import (
    AuthorGroupResponseSerializer,
    CommentCreateSerializer,
    CommentResponseSerializer,
    PostCreateUpdateSerializer,
    PostDetailResponseSerializer,
    PostResponseSerializer,
)
from app.services import SocialService
from shared.filters import PostFilterBackend
from shared.pagination import PostLimitOffsetPagination
from shared.permissions import IsEmailVerified


class PostsListCreateView(ListCreateAPIView):
    """
    List flat posts or create a new post publication.
    """

    queryset = Post.objects.select_related("author")
    pagination_class = PostLimitOffsetPagination
    filter_backends = [PostFilterBackend]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateUpdateSerializer
        return PostResponseSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            # Enforce authenticated AND email verified check
            return [IsAuthenticated(), IsEmailVerified()]
        return [AllowAny()]

    @extend_schema(
        responses={200: PostResponseSerializer(many=True)},
        summary="Get flat list of posts",
        description="Returns a paginated list of posts matching search or date filters. Accessible by everyone.",
        tags=["Posts"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=PostCreateUpdateSerializer,
        responses={201: PostResponseSerializer, 400: None, 403: None},
        summary="Create a new post",
        description="Publishes a new post. Accessible by verified users only.",
        tags=["Posts"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        post = SocialService.create_post(request.user, serializer.validated_data)
        response_serializer = PostResponseSerializer(post)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PostDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """
    Get detailed post, update post, or delete post.
    """

    queryset = Post.objects.prefetch_related("comments")
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PostCreateUpdateSerializer
        return PostDetailResponseSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsEmailVerified()]
        return [AllowAny()]

    @extend_schema(
        responses={status.HTTP_200_OK: PostDetailResponseSerializer, status.HTTP_404_NOT_FOUND: None},
        summary="Get post details and comments",
        description="Retrieves single post by ID including its comments list. Accessible by everyone.",
        tags=["Posts"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=PostCreateUpdateSerializer,
        responses={
            status.HTTP_200_OK: PostResponseSerializer,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_403_FORBIDDEN: None,
            status.HTTP_404_NOT_FOUND: None,
        },
        summary="Update a post",
        description="Updates title and/or content fields. Restricts updates to the post's author (who must be verified).",
        tags=["Posts"],
    )
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = SocialService.update_post(request.user, self.kwargs["id"], serializer.validated_data)
            response_serializer = PostResponseSerializer(post)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=PostCreateUpdateSerializer,
        responses={
            status.HTTP_200_OK: PostResponseSerializer,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_403_FORBIDDEN: None,
            status.HTTP_404_NOT_FOUND: None,
        },
        summary="Replace a post",
        description="Replaces title and/or content fields. Restricts updates to the post's author (who must be verified).",
        tags=["Posts"],
        exclude=True,
    )
    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)

    @extend_schema(
        responses={status.HTTP_204_NO_CONTENT: None, status.HTTP_403_FORBIDDEN: None, status.HTTP_404_NOT_FOUND: None},
        summary="Delete a post",
        description="Deletes a post by ID. Restricts deletion to the post's author (who must be verified).",
        tags=["Posts"],
    )
    def delete(self, request, *args, **kwargs):
        try:
            SocialService.delete_post(request.user, self.kwargs["id"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class CommentCreateView(CreateAPIView):
    """
    Comment on a post.
    """

    permission_classes = [IsAuthenticated, IsEmailVerified]
    serializer_class = CommentCreateSerializer

    @extend_schema(
        request=CommentCreateSerializer,
        responses={
            status.HTTP_201_CREATED: CommentResponseSerializer,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_403_FORBIDDEN: None,
            status.HTTP_404_NOT_FOUND: None,
        },
        summary="Add a comment to a post",
        description="Creates a new comment on a specific post. Accessible by verified users only.",
        tags=["Comments"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = SocialService.create_comment(request.user, self.kwargs["id"], serializer.validated_data)
            response_serializer = CommentResponseSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class CommentDeleteView(DestroyAPIView):
    """
    Delete comment from a post.
    """

    permission_classes = [IsAuthenticated, IsEmailVerified]

    @extend_schema(
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_403_FORBIDDEN: None,
            status.HTTP_404_NOT_FOUND: None,
        },
        summary="Delete a comment",
        description="Deletes a specific comment by ID. Restricts deletion to the comment's author (who must be verified).",
        tags=["Comments"],
    )
    def delete(self, request, *args, **kwargs):
        try:
            SocialService.delete_comment(request.user, self.kwargs["post_id"], self.kwargs["comment_id"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class LikeUnlikeView(APIView):
    """
    Like or unlike a post.
    """

    permission_classes = [IsAuthenticated]  # Allowed for unverified users

    @extend_schema(
        responses={status.HTTP_201_CREATED: None, status.HTTP_400_BAD_REQUEST: None, status.HTTP_404_NOT_FOUND: None},
        summary="Like a post",
        description="Likes a post. Users cannot like their own posts, and cannot double like. Accessible by unverified users.",
        tags=["Likes"],
    )
    def post(self, request, id):
        try:
            SocialService.add_like(request.user, id)
            return Response({"detail": _("Post liked successfully.")}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        },
        summary="Unlike a post",
        description="Removes a previously placed like from a post. Accessible by unverified users.",
        tags=["Likes"],
    )
    def delete(self, request, id):
        try:
            SocialService.remove_like(request.user, id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({"detail": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class FeedView(APIView):
    """
    Author grouped posts feed endpoint.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("search", type=str, required=False, description="Keyword search term"),
            OpenApiParameter("date_from", type=str, required=False, description="ISO format start date"),
            OpenApiParameter("date_to", type=str, required=False, description="ISO format end date"),
            OpenApiParameter("limit", type=int, required=False, default=10),
            OpenApiParameter("offset", type=int, required=False, default=0),
        ],
        responses={status.HTTP_200_OK: AuthorGroupResponseSerializer(many=True)},
        summary="Get author-grouped posts feed",
        description="Returns the posts feed grouped by author username. Supports pagination and keyword/date filters. Accessible by everyone.",
        tags=["Feed"],
    )
    def get(self, request):
        search = request.query_params.get("search")
        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to")

        date_from = parse_datetime(date_from_str) if date_from_str else None
        date_to = parse_datetime(date_to_str) if date_to_str else None

        try:
            limit = int(request.query_params.get("limit", 10))
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            limit, offset = 10, 0

        grouped_feed = SocialService.get_feed(
            search=search, date_from=date_from, date_to=date_to, offset=offset, limit=limit
        )
        return Response(grouped_feed, status=status.HTTP_200_OK)

